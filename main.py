"""3D Exploration Game - Main Entry Point"""
import pygame
from pygame.locals import (
    QUIT, KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION,
    K_ESCAPE, K_TAB, K_e, K_i, K_m, K_j, K_c, K_q, K_v, K_n, K_p,
    K_SPACE, K_RETURN, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8,
    K_LSHIFT, K_w, K_s, K_a, K_d, K_r,
    K_F5, K_F9, K_UP, K_DOWN, K_DELETE, K_EQUALS, K_PLUS, K_MINUS
)
import glm
import numpy as np
import time
import logging
from typing import Any

import config
from engine.window import Window
from engine.frustum import Frustum
from engine.resource_manager import ResourceManager
from graphics.shader import Shader
from graphics.mesh import Mesh
from graphics.texture import Texture
from graphics.lighting import LightManager, DirectionalLight, PointLight
from graphics.shadow_map import ShadowMapManager
from graphics.skybox import Skybox
from game.player import Player
from game.entities import Cube, CollectibleCube, Wall
from game.interaction import InteractionSystem
from game.inventory import Inventory
from game.game_state import StateManager, GameState
from game.ui import UI
from game.journal import Journal, create_default_objectives, create_default_lore
from game.logger import setup_logging, get_logger
from audio.sound_manager import SoundManager
from game.game_world import GameWorld
from game.dialogue import DialogueManager
from game.quests import QuestManager
from game.enemy import Enemy, EnemyManager, EnemyType
from game.loot import get_loot_system
from game.item_database import get_item
from game.progression import calculate_enemy_xp
from game.damage_numbers import DamageNumberManager
from engine.camera_shake import ShakePresets
from game.spell_system import SpellManager, get_spell_particle_type
from graphics.particles import ParticleType

# Initialize logging
logger = get_logger(__name__)


class ResourceLifecycleManager:
    """Manages resources with proper initialization and cleanup ordering."""

    def __init__(self) -> None:
        """Initialize the resource lifecycle manager."""
        self.resources: list[tuple[str, Any, str]] = []  # List of (name, resource, cleanup_method) tuples

    def register(self, name: str, resource: Any, cleanup_method: str = "cleanup") -> None:
        """
        Register a resource for lifecycle management.

        Args:
            name: Human-readable name for the resource
            resource: The resource object
            cleanup_method: Name of the cleanup method to call (default: "cleanup")
        """
        if resource is not None:
            self.resources.append((name, resource, cleanup_method))
            logger.debug(f"Registered resource: {name}")

    def cleanup_all(self) -> None:
        """Clean up all registered resources in reverse order of registration."""
        # Clean up in reverse order (LIFO - last in, first out)
        for name, resource, cleanup_method in reversed(self.resources):
            try:
                if hasattr(resource, cleanup_method):
                    method = getattr(resource, cleanup_method)
                    method()
                    logger.debug(f"Cleaned up resource: {name}")
                elif hasattr(resource, 'release'):
                    resource.release()
                    logger.debug(f"Released resource: {name}")
                else:
                    logger.warning(f"Resource {name} has no cleanup method")
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")

        self.resources.clear()


class Game:
    """Main game class."""

    def __init__(self):
        """Initialize the game."""
        # Initialize resource lifecycle manager first
        self.resource_lifecycle = ResourceLifecycleManager()

        self.window = Window()
        self.resource_lifecycle.register("window", self.window)

        self.resource_manager = ResourceManager(self.window.ctx)
        self.resource_lifecycle.register("resource_manager", self.resource_manager, "clear_cache")

        self.player = Player(position=glm.vec3(*config.PLAYER_SPAWN_POSITION))  # Start high, will drop to terrain
        self.clock = pygame.time.Clock()
        self.running = True

        # Time tracking
        self.delta_time = 0.0
        self.last_frame = time.time()

        # FPS tracking
        self.fps_update_time = 0.0
        self.fps_counter = 0
        self.current_fps = 0

        # Frustum culling
        self.frustum = Frustum()
        self.culled_count = 0
        self.total_entities = 0

        # Input state
        self.keys = {}

        # Game systems
        self.inventory = Inventory()
        self.sound_manager = SoundManager(enabled=True)
        self.resource_lifecycle.register("sound_manager", self.sound_manager)

        self.state_manager = StateManager()
        self.ui = UI(self.window.width, self.window.height, ctx=self.window.ctx)
        self.light_manager = LightManager(max_lights=8)

        self.shadow_map_manager = ShadowMapManager(self.window.ctx, max_shadow_maps=4)
        self.resource_lifecycle.register("shadow_map_manager", self.shadow_map_manager, "clear_all")

        # Combat system (Phase 3) - Create enemy manager first for world
        self.enemy_manager = EnemyManager()
        self.enemy_manager.on_enemy_defeated = self._on_enemy_defeated
        self.loot_system = get_loot_system()

        # Game world system - manages terrain, entities, NPCs, enemies
        self.world = GameWorld(self.window.ctx, None, self.enemy_manager)  # Will set shader in setup_scene
        self.resource_lifecycle.register("world", self.world)

        # Phase 5 systems
        self.dialogue_manager = DialogueManager()
        self.quest_manager = QuestManager()
        self.active_npc = None  # Currently interacting NPC

        # Waypoint system for quest navigation
        from game.quest_waypoints import WaypointManager
        self.waypoint_manager = WaypointManager()

        # Crafting system
        from game.crafting import get_crafting_manager
        self.crafting_manager = get_crafting_manager()
        self.selected_recipe_index = 0  # Currently selected recipe in crafting menu
        self.cached_recipes = []  # Cache discovered recipes to avoid recalculating every frame
        logger.info(f"Crafting system initialized with {len(self.crafting_manager.recipes)} recipes")

        # Save/Load system
        from game.save_system import SaveSystem
        self.save_system = SaveSystem()
        self.selected_save_slot = 1  # Currently selected slot in save/load menu
        self.play_time = 0.0  # Total playtime in seconds

        # Combat feedback systems
        self.damage_numbers = DamageNumberManager()

        # Spell system
        self.spell_manager = SpellManager()

        # Phase 8: Atmosphere systems
        from graphics.particles import ParticleSystem
        from graphics.day_night import DayNightCycle
        from graphics.weather import WeatherSystem

        self.particle_system = ParticleSystem(self.window.ctx)
        self.day_night_cycle = DayNightCycle(day_length=600.0, start_time=0.5)  # 10 min days, start at noon
        self.weather_system = WeatherSystem(self.particle_system)

        # Setup level-up particle effect callback
        original_on_level_up = self.player.progression.on_level_up
        def level_up_with_particles(new_level: int):
            # Call original callback
            if original_on_level_up:
                original_on_level_up(new_level)
            # Create level-up particle burst at player position
            from graphics.particles import ParticleType
            self.particle_system.create_spell_burst(
                self.player.position + glm.vec3(0, 1.0, 0),  # Slightly above player
                ParticleType.LEVEL_UP,
                particle_count=50
            )
        self.player.progression.on_level_up = level_up_with_particles

        # Biome audio system (Phase 7)
        from game.biome_audio import get_biome_audio_manager
        self.biome_audio = get_biome_audio_manager()
        logger.info("Biome audio system initialized")

        # Vegetation renderer (Phase 7)
        from graphics.vegetation_renderer import VegetationRenderer
        self.vegetation_renderer = VegetationRenderer(self.window.ctx)
        self.resource_lifecycle.register("vegetation_renderer", self.vegetation_renderer, "release")
        logger.info("Vegetation renderer initialized")

        # Initialize journal with default objectives and lore
        self.journal = Journal()
        for objective in create_default_objectives():
            self.journal.add_objective(objective)
        for lore_entry in create_default_lore():
            self.journal.add_lore_entry(lore_entry)

        # Initialize rendering
        self.setup_scene()

        # Cached matrices for performance (avoid recalculating identity matrices)
        self.identity_model = glm.mat4(1.0)
        self.identity_normal_matrix = glm.mat3(1.0)

        # Capture mouse for FPS controls
        self.window.capture_mouse()

    def setup_scene(self):
        """Set up the scene with textured cube and ground plane."""
        # Load textured shader using ResourceManager
        self.textured_shader = self.resource_manager.load_shader(
            "textured",
            "assets/shaders/textured_vertex.glsl",
            "assets/shaders/textured_fragment.glsl"
        )

        # Load lit shader for multi-light rendering (Phase 3)
        self.lit_shader = self.resource_manager.load_shader(
            "lit",
            "assets/shaders/lit_vertex.glsl",
            "assets/shaders/lit_fragment.glsl"
        )

        # Load shadow mapping shader (Phase 3.2)
        self.shadow_shader = self.resource_manager.load_shader(
            "shadow",
            "assets/shaders/shadow_vertex.glsl",
            "assets/shaders/shadow_fragment.glsl"
        )

        # Create shadow map for directional light (sun)
        self.sun_shadow_map = self.shadow_map_manager.create_shadow_map("sun", resolution=config.SHADOW_MAP_RESOLUTION)

        # Load skybox shader (Phase 3.3)
        self.skybox_shader = self.resource_manager.load_shader(
            "skybox",
            "assets/shaders/skybox_vertex.glsl",
            "assets/shaders/skybox_fragment.glsl"
        )

        # Create skybox
        self.skybox = Skybox(self.window.ctx, self.skybox_shader)
        self.resource_lifecycle.register("skybox", self.skybox, "release")

        # Set lit shader for world rendering (now that it's loaded)
        self.world.lit_shader = self.lit_shader
        self.world.chunk_manager.shader = self.lit_shader

        # Create textures using ResourceManager
        self.cube_texture = self.resource_manager.create_procedural_texture(
            "checkerboard", "checkerboard", size=256, tile_size=32
        )
        self.ground_texture = self.resource_manager.create_procedural_texture(
            "grid", "grid", size=512, grid_size=64, line_width=3
        )
        # Create white texture for colored objects (projectiles, particles)
        import numpy as np
        white_data = np.full((4, 4, 3), 255, dtype=np.uint8)
        self.white_texture = self.window.ctx.texture((4, 4), 3, white_data.tobytes())
        self.white_texture.filter = (self.window.ctx.LINEAR, self.window.ctx.LINEAR)

        # Create meshes (using lit shader for proper lighting)
        self.cube_mesh = Mesh.create_cube(self.window.ctx, self.lit_shader, textured=True)
        self.resource_lifecycle.register("cube_mesh", self.cube_mesh, "release")

        # Test OBJ model loading (Phase 2.2)
        try:
            test_model_meshes = self.resource_manager.load_obj_model(
                "test_cube",
                "assets/models/test_cube.obj",
                self.lit_shader
            )
            if test_model_meshes:
                # Use the first mesh from the loaded model
                first_mesh_name = list(test_model_meshes.keys())[0]
                self.test_obj_mesh = test_model_meshes[first_mesh_name]
                logger.info(f"Loaded OBJ model with mesh: {first_mesh_name}")
            else:
                self.test_obj_mesh = None
                logger.warning("No meshes found in test OBJ model")
        except FileNotFoundError:
            logger.error("Test OBJ model file not found")
            self.test_obj_mesh = None
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Failed to parse test OBJ model: {e}")
            self.test_obj_mesh = None

        # Setup lighting (Phase 3.1)
        self.setup_lights()

        # Interaction system
        self.interaction = InteractionSystem(
            max_distance=config.INTERACTION_DISTANCE,
            inventory=self.inventory,
            sound_manager=self.sound_manager,
            journal=self.journal
        )

        # Setup Phase 5 systems
        self.setup_dialogues_and_quests()

        # Initialize lighting based on day/night cycle (fixes dark start)
        self._update_dynamic_lighting()

    def _on_enemy_defeated(self, enemy: Enemy) -> None:
        """
        Handle enemy defeat - award loot and XP.

        Args:
            enemy: Defeated enemy
        """
        try:
            # Validate enemy has required attributes
            if not hasattr(enemy, 'enemy_type') or enemy.enemy_type is None:
                logger.error(f"Enemy {getattr(enemy, 'name', 'Unknown')} has no enemy_type attribute")
                return

            if not hasattr(enemy, 'name') or not enemy.name:
                logger.error(f"Enemy has no name attribute")
                return

            enemy_type_name = enemy.enemy_type.name  # WEAK, NORMAL, TANK, FAST

            # Calculate and grant XP
            try:
                xp_amount = calculate_enemy_xp(enemy_type_name, enemy_level=1)
                levels_gained = self.player.gain_xp(xp_amount)

                # Print level up messages
                if levels_gained:
                    logger.info(f"{enemy.name} defeated! Gained {len(levels_gained)} level(s)!")
            except (AttributeError, ValueError, TypeError) as e:
                logger.error(f"Failed to calculate/grant XP for {enemy.name}: {e}", exc_info=True)
                # Continue with loot generation even if XP fails

            # Generate loot drops
            try:
                from game.item_database import ItemType

                # Bosses get special loot treatment
                is_boss = hasattr(enemy, 'is_boss') and enemy.is_boss
                if is_boss:
                    # Bosses drop guaranteed epic/legendary items and more gold
                    logger.info(f"Boss defeated: {enemy.name}!")
                    loot_item_ids = self.loot_system.generate_boss_loot(enemy_type_name, enemy.name)

                    # Progress boss quest objectives
                    self._progress_boss_quest(enemy)
                else:
                    loot_item_ids = self.loot_system.generate_loot(enemy_type_name, enemy.name)

                if loot_item_ids:
                    logger.info(f"{enemy.name} dropped {len(loot_item_ids)} item(s)!")

                    # Add each item to inventory
                    items_added = 0
                    for item_id in loot_item_ids:
                        try:
                            item_data = get_item(item_id)
                            if item_data:
                                item_type = item_data.get("type")

                                # Handle different item types
                                if item_type == ItemType.CURRENCY:
                                    # Add gold directly
                                    gold_amount = item_data.get("value", 1)
                                    self.player.add_gold(gold_amount)
                                    logger.info(f"  +{gold_amount} gold")
                                    items_added += 1
                                elif item_type in [ItemType.MATERIAL, ItemType.CONSUMABLE]:
                                    # Add to materials inventory
                                    quantity = item_data.get("quantity", 1)
                                    self.player.inventory.add_material(item_id, quantity)
                                    logger.info(f"  +{quantity}x {item_data['name']}")
                                    items_added += 1
                                elif item_type in [ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY]:
                                    # Create EquipmentItem and add to equipment inventory
                                    from game.equipment import EquipmentItem, EquipmentSlot, ItemRarity
                                    from game.loot_system import LootRarity

                                    # Map item type to equipment slot
                                    slot_map = {
                                        ItemType.WEAPON: EquipmentSlot.WEAPON,
                                        ItemType.ARMOR: EquipmentSlot.ARMOR,
                                        ItemType.ACCESSORY: EquipmentSlot.ACCESSORY,
                                    }

                                    # Validate slot mapping exists
                                    if item_type not in slot_map:
                                        logger.error(f"Unknown equipment type {item_type} for item {item_id}")
                                        continue

                                    # Convert LootRarity to ItemRarity
                                    loot_rarity = item_data.get("rarity", LootRarity.COMMON)
                                    # Handle both enum and string rarity values
                                    if isinstance(loot_rarity, str):
                                        item_rarity = ItemRarity[loot_rarity.upper()]
                                    else:
                                        item_rarity = ItemRarity[loot_rarity.name]

                                    equip_item = EquipmentItem(
                                        id=item_id,
                                        name=item_data["name"],
                                        description=item_data.get("description", ""),
                                        rarity=item_rarity,
                                        slot=slot_map[item_type],
                                        damage_bonus=item_data.get("damage", 0),
                                        defense_bonus=item_data.get("defense", 0),
                                        health_bonus=item_data.get("health", 0),
                                        stamina_bonus=item_data.get("stamina", 0),
                                        level_required=item_data.get("level_required", 1)
                                    )
                                    self.player.inventory.add_equipment(equip_item)
                                    logger.info(f"  +{item_data['name']}")
                                    items_added += 1
                                else:
                                    logger.warning(f"Unknown item type {item_type} for {item_id}")
                            else:
                                logger.warning(f"Item {item_id} returned None from database")
                        except ValueError as e:
                            logger.error(f"Failed to get item {item_id} from database: {e}")
                        except (AttributeError, KeyError, TypeError) as e:
                            logger.error(f"Failed to add item {item_id} to inventory: {e}", exc_info=True)

                    if items_added < len(loot_item_ids):
                        logger.warning(f"Only added {items_added}/{len(loot_item_ids)} items to inventory")
                else:
                    logger.info(f"{enemy.name} defeated! No loot dropped.")
            except (ImportError, AttributeError, ValueError) as e:
                logger.error(f"Failed to generate loot for {enemy.name}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Critical error in _on_enemy_defeated: {e}", exc_info=True)

    def _progress_boss_quest(self, boss: Enemy) -> None:
        """
        Progress quest objectives when a boss is defeated.

        Args:
            boss: The defeated boss enemy
        """
        try:
            # Map boss types to quest IDs
            boss_quest_map = {
                EnemyType.BOSS_CORRUPTED_GUARDIAN: "corrupted_forest_boss",
                EnemyType.BOSS_CRYSTAL_TYRANT: "crystal_tyrant_boss",
                EnemyType.BOSS_ANCIENT_WARDEN: "ancient_warden_boss",
                EnemyType.BOSS_VOID_KNIGHT: "void_knight_boss",
                EnemyType.BOSS_SKY_SERPENT: "sky_serpent_boss",
            }

            quest_id = boss_quest_map.get(boss.enemy_type)
            if not quest_id:
                logger.warning(f"No quest found for boss type {boss.enemy_type}")
                return

            quest = self.quest_manager.get_quest(quest_id)
            if not quest:
                logger.debug(f"Quest {quest_id} not found or not active")
                return

            # Progress the defeat objective for this boss
            objective_map = {
                "corrupted_forest_boss": "defeat_guardian",
                "crystal_tyrant_boss": "defeat_tyrant",
                "ancient_warden_boss": "defeat_warden",
                "void_knight_boss": "defeat_void_knight",
                "sky_serpent_boss": "defeat_serpent",
            }

            objective_id = objective_map.get(quest_id)
            if objective_id:
                self.quest_manager.progress_objective(quest_id, objective_id, 1)
                logger.info(f"Quest objective '{objective_id}' progressed for defeating {boss.name}")

        except Exception as e:
            logger.error(f"Error progressing boss quest: {e}", exc_info=True)

    def setup_lights(self):
        """Setup scene lighting (Phase 3.1)."""
        # Add sun (directional light)
        sun = DirectionalLight(
            direction=glm.vec3(*config.SUN_DIRECTION),
            color=glm.vec3(*config.SUN_COLOR),
            intensity=config.SUN_INTENSITY
        )
        self.light_manager.add_directional_light(sun)

        # Configure shadow map for sun (Phase 3.2)
        self.sun_shadow_map.setup_directional_light(
            sun.direction,
            scene_center=glm.vec3(0.0, 0.0, 0.0),
            scene_radius=config.SHADOW_SCENE_RADIUS
        )

        # Add point light at spawn position (ambient lighting)
        spawn_light = PointLight(
            position=glm.vec3(*config.SPAWN_LIGHT_POSITION),
            color=glm.vec3(*config.SPAWN_LIGHT_COLOR),
            intensity=config.SPAWN_LIGHT_INTENSITY,
            constant=config.SPAWN_LIGHT_CONSTANT,
            linear=config.SPAWN_LIGHT_LINEAR,
            quadratic=config.SPAWN_LIGHT_QUADRATIC
        )
        self.light_manager.add_point_light(spawn_light)

        # Add point light near puzzle area
        puzzle_light = PointLight(
            position=glm.vec3(*config.PUZZLE_LIGHT_POSITION),
            color=glm.vec3(*config.PUZZLE_LIGHT_COLOR),
            intensity=config.PUZZLE_LIGHT_INTENSITY,
            constant=config.PUZZLE_LIGHT_CONSTANT,
            linear=config.PUZZLE_LIGHT_LINEAR,
            quadratic=config.PUZZLE_LIGHT_QUADRATIC
        )
        self.light_manager.add_point_light(puzzle_light)

        logger.info(f"Lighting setup complete: {self.light_manager}")

    def _update_dynamic_lighting(self):
        """Update lighting based on day/night cycle and weather."""
        # Update sun (directional light) based on time of day
        if self.light_manager.directional_lights:
            sun = self.light_manager.directional_lights[0]

            # Update sun direction based on time
            sun.direction = self.day_night_cycle.get_sun_direction()

            # Update sun color
            sun.color = self.day_night_cycle.get_sun_color()

            # Update sun intensity (dimmer at night, brighter at noon)
            base_intensity = self.day_night_cycle.get_sun_intensity()
            weather_mult = self.weather_system.get_ambient_light_multiplier()
            sun.intensity = base_intensity * weather_mult

            # Update shadow map to follow sun
            self.sun_shadow_map.setup_directional_light(
                sun.direction,
                scene_center=self.player.position,  # Center shadows on player
                scene_radius=config.SHADOW_SCENE_RADIUS
            )

        # Update ambient light color
        ambient = self.day_night_cycle.get_ambient_color()
        weather_mult = self.weather_system.get_ambient_light_multiplier()
        self.light_manager.ambient_color = ambient * weather_mult

    def setup_dialogues_and_quests(self):
        """Load dialogues and create quests (Phase 5)."""
        # Try to load dialogues from JSON
        try:
            count = self.dialogue_manager.load_dialogues_from_json("assets/dialogues.json")
            logger.info(f"Loaded {count} dialogues from file")
        except FileNotFoundError:
            logger.warning("dialogues.json not found, using fallback dialogues")
            self._create_fallback_dialogues()
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Invalid dialogues.json format: {e}, using fallback dialogues")
            self._create_fallback_dialogues()

        # Create quests
        self._create_quests()

        logger.info("Dialogues and quests initialized")

    def _create_fallback_dialogues(self):
        """Create fallback dialogues if JSON loading fails."""
        # Define all fallback dialogues in a data-driven way
        simple_dialogues = {
            "guard_greeting": {
                "npc_name": "Village Guard",
                "messages": [
                    "Greetings, traveler!",
                    "Welcome to the Ancient Ruins.",
                    "Be careful in there - many have entered, few return."
                ]
            },
            "elder_quest": {
                "npc_name": "Wise Elder",
                "messages": [
                    "Ah, a brave soul approaches.",
                    "These ruins hold many secrets...",
                    "Explore them well, and you may find great rewards."
                ]
            },
            "mysterious_stranger": {
                "npc_name": "Mysterious Figure",
                "messages": [
                    "...",
                    "*The figure says nothing*",
                    "..."
                ]
            }
        }

        choice_dialogues = {
            "merchant_greeting": {
                "npc_name": "Wandering Merchant",
                "greeting": "Well met, adventurer! Looking for supplies?",
                "choices": [
                    ("What are you selling?", "Potions, tools, maps... the usual goods."),
                    ("Any tips for exploring?", "Watch your step and collect everything you find!"),
                    ("Farewell.", "Safe travels!")
                ]
            }
        }

        # Create all simple dialogues
        for dialogue_id, data in simple_dialogues.items():
            self.dialogue_manager.create_simple_dialogue(
                dialogue_id,
                data["npc_name"],
                data["messages"]
            )

        # Create all choice dialogues
        for dialogue_id, data in choice_dialogues.items():
            self.dialogue_manager.create_choice_dialogue(
                dialogue_id,
                data["npc_name"],
                data["greeting"],
                data["choices"]
            )

    def _create_quests(self):
        """Create game quests."""
        from game.boss_quests import register_all_boss_quests
        from game.main_quest import register_main_quest_line
        from game.side_quests import register_all_side_quests

        # Register main quest storyline (3 acts)
        main_quest_ids = register_main_quest_line(self.quest_manager, self.player)
        logger.info(f"Registered {len(main_quest_ids)} main quest acts")

        # Register all boss encounter quests
        boss_quest_ids = register_all_boss_quests(self.quest_manager, self.player)
        logger.info(f"Registered {len(boss_quest_ids)} boss quests")

        # Register side quests
        side_quest_ids = register_all_side_quests(self.quest_manager, self.player)
        logger.info(f"Registered {len(side_quest_ids)} side quests")

        total_quests = len(main_quest_ids) + len(boss_quest_ids) + len(side_quest_ids)
        logger.info(f"Quest system initialized with {total_quests} total quests")

    def handle_input(self):
        """Handle all input events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            elif event.type == MOUSEBUTTONDOWN:
                # Combat controls (Phase 3)
                if self.state_manager.is_playing():
                    if event.button == 1:  # Left click - Attack
                        try:
                            # Find nearest enemy in attack range
                            nearest_enemy = self.enemy_manager.get_nearest_enemy(
                                self.player.position,
                                self.player.attack_range
                            )
                            if nearest_enemy:
                                # Attack the enemy
                                result = self.player.attack(nearest_enemy)
                                if result and result.hit:
                                    logger.info(f"Hit enemy for {result.damage:.1f} damage! {'CRITICAL!' if result.critical else ''}")
                                    # Add damage number
                                    self.damage_numbers.add_damage_number(
                                        result.damage,
                                        nearest_enemy.position,
                                        result.critical
                                    )
                                    # Add screen shake
                                    shake_amount = ShakePresets.HEAVY_HIT if result.critical else ShakePresets.LIGHT_HIT
                                    self.player.camera.shake.add_trauma(shake_amount)
                            else:
                                # Attack animation even if no target
                                self.player.attack()
                        except (AttributeError, TypeError, ValueError) as e:
                            logger.error(f"Error during combat attack: {e}", exc_info=True)

            elif event.type == MOUSEBUTTONUP:
                # Stop blocking on right mouse release
                if event.button == 3:  # Right mouse button
                    try:
                        self.player.stop_block()
                    except AttributeError as e:
                        logger.error(f"Error stopping block: {e}")

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    # ESC toggles pause or exits menus/UI
                    if self.state_manager.current_state == GameState.PLAYING:
                        self.state_manager.toggle_pause()
                    elif self.state_manager.current_state in [GameState.PAUSED, GameState.INVENTORY, GameState.EQUIPMENT, GameState.CRAFTING, GameState.MAP, GameState.JOURNAL, GameState.QUEST_LOG, GameState.SAVE_MENU, GameState.LOAD_MENU]:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.current_state == GameState.DIALOGUE:
                        # Exit dialogue
                        self.dialogue_manager.end_dialogue()
                        if self.active_npc:
                            self.active_npc.end_interaction()
                            self.active_npc = None
                        self.state_manager.set_state(GameState.PLAYING)
                    else:
                        self.running = False
                elif event.key == K_TAB:
                    self.window.toggle_mouse_capture()
                elif event.key == K_e:
                    if self.state_manager.is_playing():
                        # Check for NPC interaction first (Phase 5)
                        nearby_npc = self.world.get_interactable_npc(self.player.position)
                        if nearby_npc:
                            # Start dialogue with NPC
                            self.active_npc = nearby_npc
                            nearby_npc.start_interaction(self.world.game_time)

                            # Start dialogue
                            if nearby_npc.dialogue_id:
                                self.dialogue_manager.start_dialogue(nearby_npc.dialogue_id)
                                self.state_manager.set_state(GameState.DIALOGUE)

                            # Start quest if NPC has one
                            if nearby_npc.quest_id and not self.quest_manager.is_quest_active(nearby_npc.quest_id):
                                self.quest_manager.start_quest(nearby_npc.quest_id)
                                logger.info(f"Quest started: {nearby_npc.quest_id}")
                        else:
                            # No NPC nearby, check for POI markers
                            if self.interaction.looking_at:
                                from game.poi_marker import POIMarker
                                if isinstance(self.interaction.looking_at, POIMarker):
                                    if self.interaction.looking_at.discover():
                                        poi = self.interaction.looking_at.poi
                                        logger.info(f"Discovered {poi.poi_type.value}: {poi.name}!")
                                        self.sound_manager.play('collect')
                                else:
                                    # Normal interaction
                                    self.interaction.interact()
                            else:
                                self.interaction.interact()
                elif event.key == K_i:
                    # Toggle inventory
                    if self.state_manager.current_state == GameState.INVENTORY:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.is_playing():
                        self.state_manager.set_state(GameState.INVENTORY)
                elif event.key == K_m:
                    # Toggle map
                    if self.state_manager.current_state == GameState.MAP:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.is_playing():
                        self.state_manager.set_state(GameState.MAP)
                elif event.key == K_j:
                    # Toggle journal
                    if self.state_manager.current_state == GameState.JOURNAL:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.is_playing():
                        self.state_manager.set_state(GameState.JOURNAL)
                elif event.key == K_c:
                    # Toggle equipment screen (Character sheet)
                    if self.state_manager.current_state == GameState.EQUIPMENT:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.is_playing():
                        self.state_manager.set_state(GameState.EQUIPMENT)
                elif event.key == K_v:
                    # Toggle crafting menu
                    if self.state_manager.current_state == GameState.CRAFTING:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.is_playing():
                        self.selected_recipe_index = 0  # Reset selection when opening
                        # Cache discovered recipes to avoid recalculating every frame
                        self.cached_recipes = self.crafting_manager.get_all_discovered_recipes()
                        self.state_manager.set_state(GameState.CRAFTING)
                elif event.key == K_q:
                    # Toggle quest log
                    if self.state_manager.current_state == GameState.QUEST_LOG:
                        self.state_manager.set_state(GameState.PLAYING)
                    elif self.state_manager.is_playing():
                        self.state_manager.set_state(GameState.QUEST_LOG)
                elif event.key == K_n:
                    # Toggle mini-map
                    if self.state_manager.is_playing():
                        status = self.ui.toggle_minimap()
                        logger.info(f"Mini-map {'enabled' if status else 'disabled'}")
                elif event.key == K_EQUALS or event.key == K_PLUS:
                    # Zoom in mini-map
                    if self.state_manager.is_playing():
                        zoom = self.ui.zoom_minimap(1)
                        logger.info(f"Mini-map zoom: {zoom:.1f}x")
                elif event.key == K_MINUS:
                    # Zoom out mini-map
                    if self.state_manager.is_playing():
                        zoom = self.ui.zoom_minimap(-1)
                        logger.info(f"Mini-map zoom: {zoom:.1f}x")
                elif event.key == K_p:
                    # Cycle mini-map position
                    if self.state_manager.is_playing():
                        position = self.ui.cycle_minimap_position()
                        logger.info(f"Mini-map position: {position}")
                elif event.key == K_F5:
                    # Open save menu
                    if self.state_manager.is_playing() or self.state_manager.is_paused():
                        self.state_manager.set_state(GameState.SAVE_MENU)
                elif event.key == K_F9:
                    # Open load menu
                    if self.state_manager.is_playing() or self.state_manager.is_paused():
                        self.state_manager.set_state(GameState.LOAD_MENU)

                # Save/Load menu controls
                if self.state_manager.current_state == GameState.SAVE_MENU:
                    if event.key == K_UP:
                        self.selected_save_slot = max(1, self.selected_save_slot - 1)
                    elif event.key == K_DOWN:
                        self.selected_save_slot = min(5, self.selected_save_slot + 1)
                    elif event.key == K_RETURN:
                        # Perform save
                        from game.save_system import serialize_game_state
                        game_state = serialize_game_state(
                            self.player, self.inventory, self.quest_manager,
                            self.player.equipment, self.player.progression,
                            {}, self.play_time
                        )
                        if self.save_system.save_game(self.selected_save_slot, game_state):
                            logger.info(f"Game saved to slot {self.selected_save_slot}")
                        self.state_manager.set_state(GameState.PLAYING)
                elif self.state_manager.current_state == GameState.LOAD_MENU:
                    if event.key == K_UP:
                        # Find previous slot with save
                        saves = self.save_system.list_saves()
                        for slot in range(self.selected_save_slot - 1, 0, -1):
                            if slot in saves:
                                self.selected_save_slot = slot
                                break
                    elif event.key == K_DOWN:
                        # Find next slot with save
                        saves = self.save_system.list_saves()
                        for slot in range(self.selected_save_slot + 1, 6):
                            if slot in saves:
                                self.selected_save_slot = slot
                                break
                    elif event.key == K_RETURN:
                        # Perform load
                        game_state = self.save_system.load_game(self.selected_save_slot)
                        if game_state:
                            from game.save_system import deserialize_game_state
                            success, play_time = deserialize_game_state(
                                game_state, self.player, self.inventory,
                                self.quest_manager, self.player.equipment,
                                self.player.progression
                            )
                            if success:
                                self.play_time = play_time
                                logger.info(f"Game loaded from slot {self.selected_save_slot}")
                        self.state_manager.set_state(GameState.PLAYING)
                    elif event.key == K_DELETE:
                        # Delete save
                        if self.save_system.delete_save(self.selected_save_slot):
                            logger.info(f"Deleted save in slot {self.selected_save_slot}")

                # Crafting menu controls
                if self.state_manager.current_state == GameState.CRAFTING:
                    max_recipes = len(self.cached_recipes)

                    if event.key == K_UP:
                        # Navigate up in recipe list
                        self.selected_recipe_index = max(0, self.selected_recipe_index - 1)
                    elif event.key == K_DOWN:
                        # Navigate down in recipe list
                        self.selected_recipe_index = min(max_recipes - 1, self.selected_recipe_index + 1)
                    elif event.key == K_RETURN or event.key == K_SPACE:
                        # Craft selected recipe
                        if 0 <= self.selected_recipe_index < max_recipes:
                            recipe = self.cached_recipes[self.selected_recipe_index]
                            success, message = self.crafting_manager.craft_item(
                                recipe.recipe_id,
                                self.player.inventory,
                                self.player.progression.level
                            )
                            if success:
                                logger.info(f"Successfully crafted: {message}")
                                self.sound_manager.play_sound('pickup')  # Reuse pickup sound
                            else:
                                logger.warning(f"Cannot craft: {message}")
                                self.sound_manager.play_sound('error')  # Play error sound if available

                # Dialogue controls (Phase 5)
                if self.state_manager.current_state == GameState.DIALOGUE:
                    if event.key == K_SPACE or event.key == K_RETURN:
                        # Advance dialogue
                        node = self.dialogue_manager.advance_dialogue()
                        if node is None:
                            # Dialogue ended
                            self.dialogue_manager.end_dialogue()
                            if self.active_npc:
                                self.active_npc.end_interaction()
                                self.active_npc = None
                            self.state_manager.set_state(GameState.PLAYING)
                    elif event.key == K_ESCAPE:
                        # Exit dialogue early
                        self.dialogue_manager.end_dialogue()
                        if self.active_npc:
                            self.active_npc.end_interaction()
                            self.active_npc = None
                        self.state_manager.set_state(GameState.PLAYING)
                    elif event.key in [K_1, K_2, K_3, K_4]:
                        # Choice selection
                        choice_index = event.key - K_1
                        node = self.dialogue_manager.advance_dialogue(choice_index)
                        if node is None:
                            self.dialogue_manager.end_dialogue()
                            if self.active_npc:
                                self.active_npc.end_interaction()
                                self.active_npc = None
                            self.state_manager.set_state(GameState.PLAYING)

                self.keys[event.key] = True

            elif event.type == KEYUP:
                self.keys[event.key] = False

            elif event.type == MOUSEMOTION and self.window.mouse_captured:
                # Use relative mouse movement for unlimited rotation
                xoffset, yoffset = event.rel
                self.player.process_mouse_movement(xoffset, -yoffset)  # Negative Y for correct direction

    def update(self):
        """Update game state."""
        from graphics.particles import ParticleType

        # Track play time
        if self.state_manager.is_playing():
            self.play_time += self.delta_time

        # Only allow movement and interaction when playing
        if self.state_manager.can_move():
            # Process keyboard movement
            sprinting = self.keys.get(K_LSHIFT, False)

            if self.keys.get(K_w, False):
                self.player.move("forward", self.delta_time, sprinting)
            if self.keys.get(K_s, False):
                self.player.move("backward", self.delta_time, sprinting)
            if self.keys.get(K_a, False):
                self.player.move("left", self.delta_time, sprinting)
            if self.keys.get(K_d, False):
                self.player.move("right", self.delta_time, sprinting)
            if self.keys.get(K_SPACE, False):
                if self.player.is_grounded:  # Only play sound if actually jumping
                    self.sound_manager.play('jump')
                self.player.jump()

            # Combat controls (Phase 3)
            # Dodge roll - R key
            if self.keys.get(K_r, False):
                self.player.dodge()

            # Block - Right mouse button (check mouse state)
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[2]:  # Right mouse button held
                self.player.start_block()
            else:
                self.player.stop_block()

            # Spell casting - Number keys 1-8
            for i, key in enumerate([K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8]):
                if self.keys.get(key, False):
                    # Cast spell from slot i
                    if self.player.cast_spell(i, self.spell_manager):
                        logger.info(f"Cast spell from slot {i + 1}")

                        # Create spell cast particle effect
                        spell = self.player.spell_caster.equipped_spells[i]
                        if spell:
                            particle_type = get_spell_particle_type(spell.element)
                            self.particle_system.create_spell_burst(
                                self.player.camera.position,
                                particle_type,
                                particle_count=10
                            )

                            # Handle instant target spells (like Lightning Bolt)
                            if spell.is_instant and not spell.is_self_target:
                                # Find nearest enemy in range
                                nearest_enemy = self.enemy_manager.get_nearest_enemy(
                                    self.player.position,
                                    spell.stats.range
                                )

                                if nearest_enemy and nearest_enemy.is_alive():
                                    # Apply damage
                                    damage = spell.get_damage()
                                    nearest_enemy.take_damage(damage)
                                    logger.info(f"Lightning struck {nearest_enemy.name} for {damage:.1f} damage!")

                                    # Create lightning particle trail from player to enemy
                                    num_particles = 15
                                    for j in range(num_particles):
                                        # Interpolate position from player to enemy
                                        t = j / (num_particles - 1)
                                        particle_pos = self.player.camera.position * (1 - t) + nearest_enemy.position * t
                                        self.particle_system.create_spell_burst(
                                            particle_pos,
                                            ParticleType.LIGHTNING_SPARK,
                                            particle_count=3
                                        )

                                    # Create impact burst at enemy
                                    self.particle_system.create_spell_burst(
                                        nearest_enemy.position + glm.vec3(0, 0.5, 0),
                                        ParticleType.LIGHTNING_SPARK,
                                        particle_count=30
                                    )

                                    # Add damage number
                                    self.damage_numbers.add_damage_number(
                                        damage,
                                        nearest_enemy.position,
                                        critical=False
                                    )

                                    # Add screen shake
                                    from engine.camera_shake import ShakePresets
                                    self.player.camera.shake.add_trauma(ShakePresets.HEAVY_HIT)

                    # Clear key to prevent repeated casting
                    self.keys[key] = False

            # Update interaction system (check what player is looking at)
            # Include POI markers in interactable objects
            all_interactables = self.world.entities + self.world.poi_markers
            self.interaction.update(
                self.player.camera.position,
                self.player.camera.front,
                all_interactables
            )

        # Update physics (gravity) and entities
        self.player.update(self.delta_time, terrain=self.world.chunk_manager)

        # Update spell system
        self.spell_manager.update(self.delta_time)

        # Update spell projectiles (removed excessive debug logging)

        # Update spell projectile particles and check collisions
        projectiles_to_remove = []
        for projectile in self.spell_manager.get_projectiles():
            # Create trail particles for projectile
            particle_type = get_spell_particle_type(projectile.spell.element)
            self.particle_system.create_spell_trail_particle(projectile.position, particle_type)

            # Check collision with enemies (larger radius for better hit detection)
            hit_enemy = False

            for enemy in self.enemy_manager.get_all_enemies():
                if enemy.is_alive():
                    # Use larger collision radius (3.0 for even better detection)
                    if projectile.check_collision(enemy.position, target_radius=3.0):
                        # Apply spell damage
                        damage = projectile.spell.get_damage()
                        enemy.take_damage(damage)
                        logger.info(f"Spell hit {enemy.name} for {damage:.1f} damage!")

                        # Add damage number
                        self.damage_numbers.add_damage_number(damage, enemy.position, critical=False)

                        # Create impact particle burst
                        self.particle_system.create_spell_burst(
                            enemy.position,
                            ParticleType.SPELL_IMPACT,
                            particle_count=20
                        )

                        # Apply status effects
                        if projectile.spell.stats.status_effect:
                            # Status effects would be applied here when implemented
                            pass

                        # Mark projectile for removal
                        projectiles_to_remove.append(projectile)
                        hit_enemy = True
                        break

        # Remove hit projectiles safely after iteration
        for proj in projectiles_to_remove:
            if proj in self.spell_manager.active_projectiles:
                self.spell_manager.active_projectiles.remove(proj)

        # Update game world (terrain, entities, NPCs, enemies)
        self.world.update(self.delta_time, self.player.position)

        # Process enemy attacks on player
        for enemy in self.enemy_manager.get_all_enemies():
            if enemy.is_alive() and enemy.combat.is_attacking:
                # Check if enemy is still in range of player
                distance = glm.length(self.player.position - enemy.position)
                if distance <= enemy.attack_range:
                    # Deal damage at the midpoint of attack animation
                    # This prevents damage being dealt every frame during the attack
                    if 0.05 < enemy.combat.attack_timer <= 0.15:
                        # Execute attack on player
                        from game.combat import CombatSystem, AttackType
                        result = CombatSystem.execute_attack(
                            enemy.stats,
                            self.player.stats,
                            AttackType.LIGHT,
                            defender_is_blocking=self.player.combat.is_blocking
                        )

                        if result.hit:
                            logger.info(f"{enemy.name} hit player for {result.damage:.1f} damage!")

                            # Add damage number above player
                            self.damage_numbers.add_damage_number(
                                result.damage,
                                self.player.position + glm.vec3(0, 2, 0),
                                result.critical
                            )

                            # Add screen shake when player is hit
                            from engine.camera_shake import ShakePresets
                            shake_amount = ShakePresets.MEDIUM_HIT if result.critical else ShakePresets.LIGHT_HIT
                            self.player.camera.shake.add_trauma(shake_amount)

                            # Play hit sound
                            self.sound_manager.play('hit')

        # Update damage numbers
        self.damage_numbers.update(self.delta_time)

        # Update atmosphere systems (Phase 8)
        self.day_night_cycle.update(self.delta_time)
        self.particle_system.update(self.delta_time)
        self.weather_system.update(self.delta_time, self.player.position)
        self.weather_system.update_weather_emitter_positions(self.player.position)

        # Update biome audio based on player position and time
        current_biome = self.world.chunk_manager.biome_manager.get_biome_at(
            self.player.position.x, self.player.position.z
        )
        self.biome_audio.update(
            self.delta_time,
            current_biome,
            self.day_night_cycle.time
        )

        # Update camera shake
        self.player.camera.shake.update(self.delta_time)

        # Update lighting based on day/night cycle
        self._update_dynamic_lighting()

        # Update quests (Phase 5)
        self.quest_manager.update()

        # Update waypoints based on player position
        self.waypoint_manager.update_waypoint_states(
            self.player.position[0],
            self.player.position[2]
        )

    def render_shadow_pass(self):
        """Render shadow map from light's perspective (Phase 3.2)."""
        # Begin shadow map rendering
        self.sun_shadow_map.begin_render()

        # Get light space matrix
        light_space_matrix = self.sun_shadow_map.get_light_space_matrix()
        self.shadow_shader.program['light_space_matrix'].write(light_space_matrix)

        # Render terrain to shadow map
        terrain_model = glm.mat4(1.0)
        self.shadow_shader.program['model'].write(terrain_model)
        self.world.chunk_manager.render()

        # Render entities to shadow map
        for entity in self.world.entities:
            # Skip entities without model matrix
            if not hasattr(entity, 'model_matrix') or entity.model_matrix is None:
                continue

            self.shadow_shader.program['model'].write(entity.model_matrix)
            self.cube_mesh.render()

        # Render NPCs to shadow map (Phase 5)
        for npc in self.world.npc_manager.get_all_npcs():
            npc_model = npc.get_model_matrix()
            self.shadow_shader.program['model'].write(npc_model)
            self.cube_mesh.render()

        # Render enemies to shadow map (Phase 3)
        for enemy in self.enemy_manager.get_all_enemies():
            if enemy.is_alive():
                enemy_model = enemy.get_model_matrix()
                self.shadow_shader.program['model'].write(enemy_model)
                self.cube_mesh.render()

        # End shadow map rendering
        self.sun_shadow_map.end_render()

        # Restore screen framebuffer and viewport
        self.window.ctx.screen.use()
        self.window.ctx.viewport = (0, 0, self.window.width, self.window.height)

    def render(self):
        """Render the scene."""
        # Render shadow map first (Phase 3.2)
        self.render_shadow_pass()

        # Clear the screen (depth only, skybox will provide color)
        self.window.ctx.clear(0.0, 0.0, 0.0, depth=1.0)

        # Get view and projection matrices for skybox and scene
        view = self.player.camera.get_view_matrix()
        projection = self.player.camera.get_projection_matrix(self.window.aspect_ratio)

        # Render skybox first (Phase 3.3)
        # Set depth function to LEQUAL so skybox renders at max depth
        self.window.ctx.depth_func = '<='
        self.skybox.render(
            view,
            projection,
            color_top=glm.vec3(*config.SKYBOX_COLOR_TOP),
            color_bottom=glm.vec3(*config.SKYBOX_COLOR_BOTTOM)
        )
        # Restore default depth function
        self.window.ctx.depth_func = '<'

        # Update frustum for culling
        view_projection = projection * view
        self.frustum.update(view_projection)

        # Upload common uniforms to lit shader
        self.lit_shader.program['view'].write(view)
        self.lit_shader.program['projection'].write(projection)
        self.lit_shader.program['view_pos'].write(self.player.camera.position)

        # Upload shadow mapping uniforms (Phase 3.2)
        light_space_matrix = self.sun_shadow_map.get_light_space_matrix()
        self.lit_shader.program['light_space_matrix'].write(light_space_matrix)
        self.lit_shader.program['shadows_enabled'] = config.SHADOWS_ENABLED

        # Bind shadow map texture to texture unit 1
        self.sun_shadow_map.bind_for_sampling(texture_unit=1)
        self.lit_shader.program['shadow_map'] = 1

        # Upload fog uniforms (Phase 3.3 + Phase 8 dynamic fog)
        self.lit_shader.program['fog_enabled'] = config.FOG_ENABLED
        # Use day/night cycle fog color
        fog_color = self.day_night_cycle.get_fog_color()
        self.lit_shader.program['fog_color'].write(fog_color)
        # Adjust fog distance based on weather
        fog_mult = self.weather_system.get_fog_density_multiplier()
        self.lit_shader.program['fog_start'] = config.FOG_START / fog_mult
        self.lit_shader.program['fog_end'] = config.FOG_END / fog_mult

        # Upload lighting data
        self.light_manager.upload_to_shader(self.lit_shader.program, self.player.camera.position)

        # Set default object color to white (will be overridden for specific objects)
        self.lit_shader.program['objectColor'].write(glm.vec3(1.0, 1.0, 1.0))

        # Render terrain (chunk-based system)
        self.lit_shader.program['model'].write(self.identity_model)
        self.lit_shader.program['normal_matrix'].write(self.identity_normal_matrix)
        self.ground_texture.use(0)
        self.lit_shader.program['texture0'] = 0
        chunks_rendered = self.world.chunk_manager.render()

        # Render vegetation (Phase 7)
        self._render_vegetation()

        # Render entities with frustum culling
        self.cube_texture.use(0)
        self.total_entities = 0
        self.culled_count = 0

        for entity in self.world.entities:
            if hasattr(entity, 'collected') and entity.collected:
                continue  # Don't render collected items

            self.total_entities += 1

            # Frustum culling - check if entity is visible
            if not self.frustum.is_sphere_visible(entity.position, config.ENTITY_DEFAULT_RADIUS):
                self.culled_count += 1
                continue  # Skip rendering if outside frustum

            # Use cached matrices for performance
            entity_model = entity.get_model_matrix()
            entity_normal_matrix = entity.get_normal_matrix()
            self.lit_shader.program['model'].write(entity_model)
            self.lit_shader.program['normal_matrix'].write(entity_normal_matrix)
            self.cube_mesh.render()

        # Render NPCs (Phase 5)
        for npc in self.world.npc_manager.get_all_npcs():
            npc_pos = npc.get_render_position()  # Includes bobbing animation

            # Frustum culling
            if not self.frustum.is_sphere_visible(npc_pos, config.NPC_CULLING_RADIUS):
                continue

            # Get cached model and normal matrices from NPC
            npc_model = npc.get_model_matrix()
            npc_normal_matrix = npc.get_normal_matrix()
            self.lit_shader.program['model'].write(npc_model)
            self.lit_shader.program['normal_matrix'].write(npc_normal_matrix)
            self.cube_mesh.render()

        # Render enemies (Phase 3)
        for enemy in self.enemy_manager.get_all_enemies():
            if not enemy.is_alive():
                continue

            enemy_pos = enemy.get_render_position()

            # Frustum culling
            if not self.frustum.is_sphere_visible(enemy_pos, 0.5):
                continue

            # Get cached model and normal matrices from enemy
            enemy_model = enemy.get_model_matrix()
            enemy_normal_matrix = enemy.get_normal_matrix()
            self.lit_shader.program['model'].write(enemy_model)
            self.lit_shader.program['normal_matrix'].write(enemy_normal_matrix)
            self.cube_mesh.render()

        # Render spell projectiles (make them larger and more visible)
        # Use white texture so objectColor shows through
        self.white_texture.use(0)
        self.lit_shader.program['texture0'] = 0

        for projectile in self.spell_manager.get_projectiles():
            # Get spell color based on element
            from game.spell_system import get_spell_color
            spell_color = get_spell_color(projectile.spell.element)

            # Create model matrix for projectile (larger for visibility)
            proj_model = glm.mat4(1.0)
            proj_model = glm.translate(proj_model, projectile.position)
            # Make projectiles larger (1.0 instead of 0.3)
            proj_model = glm.scale(proj_model, glm.vec3(1.0, 1.0, 1.0))

            proj_normal_matrix = glm.mat3(glm.transpose(glm.inverse(proj_model)))
            self.lit_shader.program['model'].write(proj_model)
            self.lit_shader.program['normal_matrix'].write(proj_normal_matrix)
            self.lit_shader.program['objectColor'].write(spell_color)
            self.cube_mesh.render()

        # Render particles (make them MUCH larger and more visible)
        # White texture is already bound from projectiles
        all_particles = self.particle_system.get_all_particles()
        for particle in all_particles:
            # Create model matrix for particle (5x larger for visibility)
            particle_model = glm.mat4(1.0)
            particle_model = glm.translate(particle_model, particle.position)
            # Make particles 5x larger so they're visible
            scale = particle.size * 5.0
            particle_model = glm.scale(particle_model, glm.vec3(scale, scale, scale))

            particle_normal_matrix = glm.mat3(glm.transpose(glm.inverse(particle_model)))
            self.lit_shader.program['model'].write(particle_model)
            self.lit_shader.program['normal_matrix'].write(particle_normal_matrix)
            self.lit_shader.program['objectColor'].write(particle.color)
            self.cube_mesh.render()

        # Reset objectColor to white for other objects
        self.lit_shader.program['objectColor'].write(glm.vec3(1.0, 1.0, 1.0))

        # Render POI markers (Phase 6)
        for marker in self.world.poi_markers:
            # Frustum culling - use larger radius for tall markers
            if not self.frustum.is_sphere_visible(marker.position, 10.0):
                continue

            # Get model matrix from marker
            marker_model = marker.get_model_matrix()
            marker_normal_matrix = marker.get_normal_matrix()
            self.lit_shader.program['model'].write(marker_model)
            self.lit_shader.program['normal_matrix'].write(marker_normal_matrix)

            # Render with color - note: basic rendering, color will be applied via lighting
            self.cube_mesh.render()

        # Draw UI overlay
        self.draw_ui()

        # Swap buffers
        self.window.swap_buffers()

    def _render_vegetation(self):
        """Render vegetation for all loaded chunks."""
        # Get view and projection matrices
        view_matrix = self.player.camera.get_view_matrix()
        projection_matrix = self.player.camera.get_projection_matrix(
            self.window.width / self.window.height
        )

        # Render vegetation from all loaded chunks
        for chunk in self.world.chunk_manager.chunks.values():
            if chunk.is_ready and chunk.vegetation:
                self.vegetation_renderer.render(
                    chunk.vegetation,
                    self.lit_shader,
                    view_matrix,
                    projection_matrix
                )

    def draw_ui(self):
        """Draw UI elements based on current game state."""
        # Clear UI surface
        self.ui.clear()

        # Debug: Print current state
        # logger.info(f"Drawing UI for state: {self.state_manager.current_state.value}")

        # Draw UI based on current state
        if self.state_manager.current_state == GameState.PLAYING:
            # Draw damage numbers in 3D space
            if self.damage_numbers.get_active_numbers():
                view = self.player.camera.get_view_matrix()
                projection = self.player.camera.get_projection_matrix(self.window.aspect_ratio)
                self.ui.draw_damage_numbers(
                    self.damage_numbers.get_active_numbers(),
                    view,
                    projection
                )

            # Find nearby boss for boss health bar
            nearby_boss = None
            boss_detection_range = 40.0  # Show boss bar within 40 units
            for enemy in self.enemy_manager.get_all_enemies():
                if enemy.is_boss and enemy.is_alive():
                    distance = glm.length(enemy.position - self.player.position)
                    if distance <= boss_detection_range:
                        nearby_boss = enemy
                        break

            # Draw HUD (crosshair, item count, interaction prompt, culling stats, waypoints)
            self.ui.draw_hud(self.player, self.inventory, self.interaction.looking_at,
                            self.culled_count, self.total_entities, nearby_boss, self.quest_manager)

            # Draw mini-map overlay
            self.ui.draw_minimap(
                self.player.position,
                self.player.camera.yaw,
                self.world.chunk_manager,
                self.quest_manager
            )
        elif self.state_manager.current_state == GameState.PAUSED:
            # Draw pause menu
            self.ui.draw_pause_menu()
        elif self.state_manager.current_state == GameState.INVENTORY:
            # Draw inventory screen
            self.ui.draw_inventory(self.player.inventory)
        elif self.state_manager.current_state == GameState.EQUIPMENT:
            # Draw equipment screen (Phase 5)
            self.ui.draw_equipment(self.player, self.player.inventory)
        elif self.state_manager.current_state == GameState.CRAFTING:
            # Draw crafting screen (use cached recipes for performance)
            self.ui.draw_crafting(self.cached_recipes, self.crafting_manager, self.player, self.selected_recipe_index)
        elif self.state_manager.current_state == GameState.MAP:
            # Draw map
            self.ui.draw_map(self.player.position, self.world.chunk_manager, self.quest_manager)
        elif self.state_manager.current_state == GameState.JOURNAL:
            # Draw journal with objectives and lore
            self.ui.draw_journal(self.journal)
        elif self.state_manager.current_state == GameState.DIALOGUE:
            # Draw dialogue (Phase 5)
            node = self.dialogue_manager.get_current_node()
            if node:
                self.ui.draw_dialogue(node, self.active_npc.name if self.active_npc else "Unknown")
        elif self.state_manager.current_state == GameState.QUEST_LOG:
            # Draw quest log (Phase 5)
            self.ui.draw_quest_log(self.quest_manager)
        elif self.state_manager.current_state == GameState.SAVE_MENU:
            # Draw save menu
            self.ui.draw_save_menu(self.save_system, self.selected_save_slot)
        elif self.state_manager.current_state == GameState.LOAD_MENU:
            # Draw load menu
            self.ui.draw_load_menu(self.save_system, self.selected_save_slot)

        # Render UI to screen
        self.ui.render(self.window.screen)

        # Update window title with FPS
        if self.interaction.looking_at and self.state_manager.is_playing():
            pygame.display.set_caption(
                f"{config.WINDOW_TITLE} - FPS: {self.current_fps} | "
                f"Looking at: {self.interaction.looking_at.name} (Press E)"
            )
        else:
            pygame.display.set_caption(f"{config.WINDOW_TITLE} - FPS: {self.current_fps}")

    def update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        self.fps_update_time += self.delta_time

        if self.fps_update_time >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_update_time = 0.0

    def run(self):
        """Main game loop."""
        logger.info("\n=== 3D Exploration Game ===")
        logger.info("\nControls:")
        logger.info("  WASD - Move")
        logger.info("  Mouse - Look around (360° rotation!)")
        logger.info("  Space - Jump")
        logger.info("  Shift - Sprint")
        logger.info("  Left Click - Attack")
        logger.info("  Right Click (Hold) - Block")
        logger.info("  R - Dodge Roll")
        logger.info("  1-8 - Cast Spells")
        logger.info("  E - Interact with NPCs")
        logger.info("  I - Inventory")
        logger.info("  C - Equipment")
        logger.info("  V - Crafting")
        logger.info("  M - Map")
        logger.info("  N - Toggle Mini-Map")
        logger.info("  +/- - Zoom Mini-Map")
        logger.info("  P - Move Mini-Map")
        logger.info("  J - Journal")
        logger.info("  Q - Quest Log")
        logger.info("  Tab - Toggle mouse capture")
        logger.info("  ESC - Pause/Resume\n")
        logger.info("Features: Open world with chunk streaming, biomes, NPCs, combat!\n")
        logger.info("Explore the vast world, fight enemies, and discover quests!\n")

        # Start biome audio
        self.biome_audio.load_all_layers()
        self.biome_audio.start()

        try:
            while self.running:
                try:
                    # Calculate delta time
                    current_frame = time.time()
                    self.delta_time = current_frame - self.last_frame
                    self.last_frame = current_frame

                    # Handle input, update, and render
                    self.handle_input()
                    self.update()
                    self.render()

                    # Update FPS display
                    self.update_fps()

                    # Limit framerate
                    self.clock.tick(config.TARGET_FPS)
                except KeyboardInterrupt:
                    logger.info("\nGame interrupted by user")
                    self.running = False
                except Exception as e:
                    logger.error(f"\nError in game loop: {e}", exc_info=True)
                    self.running = False
        finally:
            # Always cleanup resources, even on exception
            logger.info("Cleaning up resources...")
            self.cleanup()

    def cleanup(self):
        """Clean up resources before exiting."""
        logger.info("Cleaning up resources...")

        # Use resource lifecycle manager for proper cleanup ordering
        if hasattr(self, 'resource_lifecycle'):
            self.resource_lifecycle.cleanup_all()
        else:
            logger.warning("Resource lifecycle manager not initialized, skipping cleanup")

        logger.info("Cleanup complete")


if __name__ == "__main__":
    # Setup logging
    setup_logging(level=logging.INFO)

    logger.info("Starting 3D Exploration Game...")

    # Validate configuration
    try:
        config.validate_config()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.critical(f"Configuration validation failed: {e}")
        raise

    try:
        game = Game()
        game.run()
    except Exception as e:
        logger.critical(f"Fatal error during game initialization: {e}", exc_info=True)
        raise
    logger.info("Game exited.")
