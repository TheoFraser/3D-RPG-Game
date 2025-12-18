"""Game world management system."""
import glm
import config
from game.logger import get_logger
from game.npc import NPCManager, NPC, NPCBehavior
from game.enemy import EnemyManager
from game.entities import Entity
from game.merchant import MerchantManager
from game.fast_travel import FastTravelSystem
from world_gen.chunk_manager import ChunkManager
from world_gen.biome import BiomeManager
from world_gen.vegetation import VegetationManager
from world_gen.poi_generator import POIGenerator, POIType
from game.poi_marker import POIMarker
from game.pathfinding import NavigationGrid
from typing import List, Optional

logger = get_logger(__name__)


class GameWorld:
    """
    Manages the game world including terrain, entities, NPCs, and enemies.

    This class consolidates world-related functionality to reduce complexity
    in the main Game class.
    """

    def __init__(self, ctx, lit_shader, enemy_manager):
        """
        Initialize the game world.

        Args:
            ctx: ModernGL context
            lit_shader: Shader for rendering lit objects
            enemy_manager: Enemy manager instance (created in Game for loot callback)
        """
        self.ctx = ctx
        self.lit_shader = lit_shader
        self.entities: List[Entity] = []
        self.enemy_manager = enemy_manager

        # Initialize chunk-based streaming system
        logger.info("Initializing chunk-based world system...")
        self.biome_manager = BiomeManager(seed=config.WORLD_SEED)
        self.vegetation_manager = VegetationManager(seed=config.WORLD_SEED)
        self.chunk_manager = ChunkManager(
            self.ctx,
            self.lit_shader,
            seed=config.WORLD_SEED
        )
        self.chunk_manager.set_biome_manager(self.biome_manager)
        self.chunk_manager.set_enemy_manager(self.enemy_manager)
        self.chunk_manager.set_vegetation_manager(self.vegetation_manager)
        logger.info(f"Chunk system ready (chunk size: {config.CHUNK_SIZE}, load distance: {config.LOAD_DISTANCE})")

        # Initialize NPC system
        self.npc_manager = NPCManager()
        self.nav_grid = NavigationGrid(width=100, height=100, cell_size=1.0)

        # Initialize merchant system (Phase 6)
        self.merchant_manager = MerchantManager()

        # Initialize fast travel system (Phase 6)
        self.fast_travel = FastTravelSystem()

        # Initialize POI system
        self.poi_generator = POIGenerator(world_size=config.WORLD_SIZE, seed=config.WORLD_SEED)
        self.poi_generator.generate_all_pois(self.chunk_manager)
        logger.info(f"Generated {len(self.poi_generator.pois)} Points of Interest")

        # Create visual markers for all POIs
        self.poi_markers: List[POIMarker] = []
        for poi in self.poi_generator.pois:
            marker = POIMarker(poi)
            self.poi_markers.append(marker)
        logger.info(f"Created {len(self.poi_markers)} POI markers")

        # Setup NPCs, merchants, fast travel points, and dungeon bosses in the world
        self._setup_npcs()
        self._setup_merchants()
        self._setup_fast_travel()
        self._setup_dungeon_bosses()

        # Track game time for NPC cooldowns
        self.game_time = 0.0

    def _setup_npcs(self):
        """Setup NPCs in the game world."""
        # Setup navigation grid obstacles
        self.nav_grid.block_rect(-10, -12, 10, 8)  # Outer perimeter
        self.nav_grid.block_rect(-9, -10, 9, 6)    # Inner room

        # Helper to get position on terrain
        def get_terrain_position(x, z, offset=0.5):
            """Get position on terrain surface with offset."""
            y = self.chunk_manager.get_height_at(x, z) + offset
            return glm.vec3(x, y, z)

        # Village Guard - Patrols near entrance
        guard = NPC(get_terrain_position(-6.0, -8.0), name="Village Guard", npc_id="guard_1")
        guard.behavior = NPCBehavior.FRIENDLY
        guard.dialogue_id = "guard_greeting"
        guard.set_patrol_points([
            get_terrain_position(-6.0, -8.0),
            get_terrain_position(6.0, -8.0),
            get_terrain_position(6.0, -6.0),
            get_terrain_position(-6.0, -6.0)
        ])
        self.npc_manager.add_npc(guard)

        # Wandering Merchant - Idle near collectibles
        merchant = NPC(get_terrain_position(5.0, 2.0), name="Wandering Merchant", npc_id="merchant")
        merchant.behavior = NPCBehavior.FRIENDLY
        merchant.dialogue_id = "merchant_greeting"
        self.npc_manager.add_npc(merchant)

        # Wise Elder - Quest giver
        elder = NPC(get_terrain_position(-5.0, 1.0), name="Wise Elder", npc_id="elder")
        elder.behavior = NPCBehavior.QUEST_GIVER
        elder.dialogue_id = "elder_quest"
        elder.quest_id = "explore_ruins"
        self.npc_manager.add_npc(elder)

        # Mysterious Figure - Appears near secret door
        stranger = NPC(get_terrain_position(-6.0, 5.0), name="Mysterious Figure", npc_id="stranger")
        stranger.behavior = NPCBehavior.NEUTRAL
        stranger.dialogue_id = "mysterious_stranger"
        self.npc_manager.add_npc(stranger)

        logger.info(f"NPCs initialized: {len(self.npc_manager)} NPCs at terrain heights")
        logger.info("Enemy spawn system initialized - enemies will spawn as chunks load")

    def _setup_merchants(self):
        """Setup merchants at village POIs."""
        merchant_names = ["Greta the Trader", "Marcus the Merchant", "Elena the Vendor", "Bjorn the Blacksmith"]
        merchant_types = ["general", "weapons", "armor", "general"]

        village_count = 0
        for i, poi in enumerate(self.poi_generator.pois):
            if poi.poi_type == POIType.VILLAGE and village_count < len(merchant_names):
                # Create merchant for this village
                merchant = self.merchant_manager.create_merchant(
                    name=merchant_names[village_count],
                    merchant_type=merchant_types[village_count],
                    level_range=(1, 10)
                )

                # Store merchant reference in POI data
                poi.data["merchant"] = merchant

                village_count += 1

        logger.info(f"Created {village_count} merchants at villages")

    def _setup_fast_travel(self):
        """Setup fast travel points at shrine POIs."""
        shrine_count = 0
        for poi in self.poi_generator.pois:
            if poi.poi_type == POIType.SHRINE:
                self.fast_travel.register_shrine(poi)
                shrine_count += 1

        logger.info(f"Registered {shrine_count} shrines for fast travel")

    def _setup_dungeon_bosses(self):
        """Spawn boss enemies in dungeons."""
        from world_gen.spawn_system import SpawnSystem
        spawn_system = SpawnSystem(seed=config.WORLD_SEED)

        boss_count = 0
        for poi in self.poi_generator.pois:
            if poi.poi_type == POIType.DUNGEON and poi.data.get("has_boss", False):
                # Get biome at dungeon location to determine appropriate boss
                biome = self.biome_manager.get_biome_at(poi.position.x, poi.position.z)

                # Spawn boss at dungeon location
                boss = spawn_system.spawn_dungeon_boss(poi.position, biome)

                # Add boss to enemy manager
                self.enemy_manager.add_enemy(boss)

                # Store boss reference in POI data for potential quest integration
                poi.data["boss"] = boss
                poi.data["boss_defeated"] = False

                boss_count += 1
                logger.info(f"Spawned {boss.name} at {poi.name}")

        logger.info(f"Spawned {boss_count} dungeon bosses")

    def update(self, delta_time: float, player_position: glm.vec3):
        """
        Update all world systems.

        Args:
            delta_time: Time since last frame in seconds
            player_position: Current player position for chunk streaming
        """
        # Update game time
        self.game_time += delta_time

        # Update chunk streaming
        self.chunk_manager.update(player_position.x, player_position.z)

        # Update entities
        for entity in self.entities:
            entity.update(delta_time)

        # Update POI markers
        for marker in self.poi_markers:
            marker.update(delta_time)

        # Update NPCs
        self.npc_manager.update_all(delta_time, player_position)

        # Update enemies
        self.enemy_manager.update_all(delta_time, player_position, self.chunk_manager)

        # Check for POI discoveries
        discovered_poi = self.poi_generator.discover_poi(player_position, discovery_radius=20.0)
        if discovered_poi:
            logger.info(f"Discovered {discovered_poi.poi_type.value}: {discovered_poi.name}!")

            # If it's a shrine, unlock it for fast travel
            if discovered_poi.poi_type == POIType.SHRINE:
                self.fast_travel.unlock_shrine(discovered_poi.name)
                logger.info(f"Shrine unlocked for fast travel!")

    def get_interactable_npc(self, player_position: glm.vec3) -> Optional[NPC]:
        """
        Get NPC that can be interacted with at current position.

        Args:
            player_position: Player's current position

        Returns:
            NPC if one is in range and available, None otherwise
        """
        return self.npc_manager.get_interactable_npc(player_position, self.game_time)

    def get_height_at(self, x: float, z: float) -> float:
        """
        Get terrain height at world position.

        Args:
            x: World x coordinate
            z: World z coordinate

        Returns:
            Height at that position
        """
        return self.chunk_manager.get_height_at(x, z)

    def get_nearby_merchant(self, player_position: glm.vec3, max_distance: float = 20.0):
        """
        Get merchant at nearby village POI.

        Args:
            player_position: Player's current position
            max_distance: Maximum distance to search

        Returns:
            Merchant if player is near a village, None otherwise
        """
        village_poi = self.poi_generator.get_nearby_poi(
            player_position,
            poi_type=POIType.VILLAGE,
            max_distance=max_distance
        )

        if village_poi and "merchant" in village_poi.data:
            return village_poi.data["merchant"]

        return None

    def add_entity(self, entity: Entity):
        """
        Add an entity to the world.

        Args:
            entity: Entity to add
        """
        self.entities.append(entity)

    def remove_entity(self, entity: Entity):
        """
        Remove an entity from the world.

        Args:
            entity: Entity to remove
        """
        if entity in self.entities:
            self.entities.remove(entity)

    def cleanup(self):
        """Clean up world resources."""
        self.chunk_manager.release()
