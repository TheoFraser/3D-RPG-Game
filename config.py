"""Game configuration settings."""

# Window settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "3D Exploration Game"
FULLSCREEN = False

# Rendering settings
FOV = 70  # Field of view in degrees
NEAR_PLANE = 0.1
FAR_PLANE = 1000.0
VSYNC = True

# Fog settings
FOG_ENABLED = True
FOG_COLOR = (0.7, 0.8, 0.9)  # Light blue-gray fog
FOG_START = 30.0  # Distance where fog starts
FOG_END = 80.0  # Distance where fog is at full density

# Shadow settings
SHADOW_MAP_RESOLUTION = 2048  # Resolution of shadow maps
SHADOW_SCENE_RADIUS = 50.0  # Radius of scene for shadow calculation
SHADOWS_ENABLED = True

# Lighting settings
SUN_DIRECTION = (-0.3, -1.0, -0.3)  # Directional light direction
SUN_COLOR = (1.0, 0.95, 0.9)  # Warm white sunlight
SUN_INTENSITY = 0.8

SPAWN_LIGHT_POSITION = (0.0, 3.0, 0.0)  # Position of spawn area light
SPAWN_LIGHT_COLOR = (1.0, 1.0, 1.0)
SPAWN_LIGHT_INTENSITY = 1.5
SPAWN_LIGHT_CONSTANT = 1.0
SPAWN_LIGHT_LINEAR = 0.07
SPAWN_LIGHT_QUADRATIC = 0.017

PUZZLE_LIGHT_POSITION = (-4.0, 2.0, 3.0)  # Position of puzzle area light
PUZZLE_LIGHT_COLOR = (0.8, 0.9, 1.0)  # Cool blue-white
PUZZLE_LIGHT_INTENSITY = 1.2
PUZZLE_LIGHT_CONSTANT = 1.0
PUZZLE_LIGHT_LINEAR = 0.09
PUZZLE_LIGHT_QUADRATIC = 0.032

# Skybox settings
SKYBOX_COLOR_TOP = (0.3, 0.5, 0.9)  # Deep blue zenith
SKYBOX_COLOR_BOTTOM = (0.7, 0.85, 1.0)  # Light blue horizon

# Performance settings
TARGET_FPS = 60
FIXED_TIMESTEP = 1.0 / 60.0  # 60 updates per second

# Camera settings
MOUSE_SENSITIVITY = 0.1
MOVEMENT_SPEED = 5.0
SPRINT_MULTIPLIER = 2.0

# Entity settings
ENTITY_DEFAULT_RADIUS = 2.0  # Conservative sphere radius for frustum culling
INTERACTION_DISTANCE = 5.0  # Maximum interaction distance in meters

# Player settings
PLAYER_SPAWN_HEIGHT = 15.0  # Initial spawn height (will fall to terrain)
PLAYER_SPAWN_POSITION = (0.0, PLAYER_SPAWN_HEIGHT, 0.0)  # Initial spawn coordinates

# NPC settings (Phase 5)
NPC_INTERACTION_RANGE = 3.0  # Distance NPCs can be interacted with
NPC_INTERACTION_COOLDOWN = 1.0  # Seconds between interactions
NPC_BOB_HEIGHT = 0.05  # Amplitude of bobbing animation
NPC_BOB_SPEED = 2.0  # Speed multiplier for bobbing animation
NPC_PATROL_WAIT_TIME = 2.0  # Seconds to wait at each patrol point
NPC_DEFAULT_SPEED = 2.0  # Units per second
NPC_SCALE = (0.4, 0.9, 0.4)  # Render scale (x, y, z) - tall and thin
NPC_CULLING_RADIUS = 0.5  # Radius for frustum culling

# UI settings (Phase 5)
UI_DIALOGUE_BOX_WIDTH = 800  # Width of dialogue box in pixels
UI_DIALOGUE_BOX_HEIGHT = 200  # Height of dialogue box in pixels
UI_DIALOGUE_BOX_MARGIN = 50  # Bottom margin for dialogue box
UI_DIALOGUE_MAX_LINES = 4  # Maximum lines of text in dialogue
UI_DIALOGUE_LINE_HEIGHT = 30  # Pixels between dialogue lines

# =============================================================================
# OPEN WORLD SETTINGS (Phase 1+)
# =============================================================================

# World settings
WORLD_SIZE = 2000  # Total world size in units (2000x2000)
WORLD_SEED = 42  # Master seed for world generation
USE_CHUNK_SYSTEM = True  # True = new chunk streaming, False = old single terrain

# Chunk settings
CHUNK_SIZE = 64  # World units per chunk (64x64)
CHUNK_RESOLUTION = 32  # Vertices per chunk side
LOAD_DISTANCE = 3  # Chunks around player to load (creates 7x7 active area)
UNLOAD_DISTANCE = 5  # Chunks to keep before unloading

# Biome settings
BIOME_SCALE = 200.0  # Scale for biome noise (larger = bigger biomes)
BIOME_BLEND_DISTANCE = 16.0  # Units over which biomes blend at edges

# Biome IDs
BIOME_GRASSLANDS = 0
BIOME_ENCHANTED_FOREST = 1
BIOME_CRYSTAL_CAVES = 2
BIOME_FLOATING_ISLANDS = 3
BIOME_ANCIENT_RUINS = 4

# Biome colors (R, G, B) for terrain tinting
BIOME_COLORS = {
    BIOME_GRASSLANDS: (0.3, 0.6, 0.2),  # Green
    BIOME_ENCHANTED_FOREST: (0.1, 0.4, 0.3),  # Dark teal
    BIOME_CRYSTAL_CAVES: (0.5, 0.3, 0.7),  # Purple
    BIOME_FLOATING_ISLANDS: (0.6, 0.7, 0.9),  # Sky blue
    BIOME_ANCIENT_RUINS: (0.5, 0.4, 0.3),  # Sandy brown
}

# Biome height multipliers
BIOME_HEIGHT_SCALE = {
    BIOME_GRASSLANDS: 5.0,  # Rolling hills
    BIOME_ENCHANTED_FOREST: 8.0,  # Varied terrain
    BIOME_CRYSTAL_CAVES: 3.0,  # Relatively flat with crystal spires
    BIOME_FLOATING_ISLANDS: 15.0,  # Dramatic elevation changes
    BIOME_ANCIENT_RUINS: 2.0,  # Mostly flat with ruins
}

# =============================================================================
# COMBAT SETTINGS (Phase 3+)
# =============================================================================

# Player combat stats
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_STAMINA = 100
PLAYER_BASE_DAMAGE = 10
PLAYER_DEFENSE = 5

# Stamina costs
STAMINA_ATTACK_COST = 15
STAMINA_DODGE_COST = 20
STAMINA_BLOCK_COST = 10
STAMINA_SPRINT_COST = 5  # Per second
STAMINA_REGEN_RATE = 20  # Per second when not using stamina

# Combat timing
ATTACK_COOLDOWN = 0.5  # Seconds between attacks
DODGE_COOLDOWN = 0.8  # Seconds between dodges
DODGE_DURATION = 0.3  # Seconds of invincibility during dodge
DODGE_DISTANCE = 3.0  # Units to move during dodge
STAGGER_DURATION = 0.5  # Seconds enemy is staggered after hit

# Damage calculation
CRIT_CHANCE = 0.1  # 10% chance
CRIT_MULTIPLIER = 2.0

# =============================================================================
# ENEMY SETTINGS (Phase 4+)
# =============================================================================

# Enemy spawn settings
ENEMY_SPAWN_DISTANCE_MIN = 30  # Minimum distance from player to spawn
ENEMY_SPAWN_DISTANCE_MAX = 80  # Maximum distance from player to spawn
ENEMY_DESPAWN_DISTANCE = 120  # Distance at which enemies despawn
MAX_ENEMIES_PER_CHUNK = 5  # Maximum enemies active per chunk

# Enemy AI
ENEMY_AGGRO_RANGE = 15.0  # Distance at which enemies notice player
ENEMY_CHASE_RANGE = 25.0  # Distance enemies will chase before giving up
ENEMY_ATTACK_RANGE = 2.0  # Distance at which enemies attack
ENEMY_RETREAT_HEALTH = 0.2  # Health percentage to trigger retreat

# =============================================================================
# EQUIPMENT SETTINGS (Phase 5+)
# =============================================================================

# Equipment slots
EQUIPMENT_SLOTS = ['weapon', 'helmet', 'chest', 'legs', 'boots', 'accessory']

# Rarity levels and color codes
RARITY_COMMON = 0
RARITY_UNCOMMON = 1
RARITY_RARE = 2
RARITY_EPIC = 3
RARITY_LEGENDARY = 4

RARITY_COLORS = {
    RARITY_COMMON: (0.7, 0.7, 0.7),  # Gray
    RARITY_UNCOMMON: (0.2, 0.8, 0.2),  # Green
    RARITY_RARE: (0.2, 0.4, 1.0),  # Blue
    RARITY_EPIC: (0.8, 0.2, 0.8),  # Purple
    RARITY_LEGENDARY: (1.0, 0.6, 0.0),  # Orange
}

# =============================================================================
# POI SETTINGS (Phase 6+)
# =============================================================================

# Point of Interest spawn rates (per chunk)
POI_VILLAGE_CHANCE = 0.02  # 2% chance per chunk
POI_DUNGEON_CHANCE = 0.01  # 1% chance per chunk
POI_SHRINE_CHANCE = 0.03  # 3% chance per chunk
POI_RUINS_CHANCE = 0.05  # 5% chance per chunk

# Village settings
VILLAGE_NPC_COUNT_MIN = 3
VILLAGE_NPC_COUNT_MAX = 8
VILLAGE_RADIUS = 30  # Units


def validate_config():
    """
    Validate configuration settings.

    Raises:
        ValueError: If any configuration value is invalid
    """
    errors = []

    # Validate window settings
    if WINDOW_WIDTH <= 0 or WINDOW_HEIGHT <= 0:
        errors.append(f"Invalid window size: {WINDOW_WIDTH}x{WINDOW_HEIGHT} (must be > 0)")
    if WINDOW_WIDTH < 640 or WINDOW_HEIGHT < 480:
        errors.append(f"Window size {WINDOW_WIDTH}x{WINDOW_HEIGHT} is too small (minimum 640x480)")

    # Validate rendering settings
    if not (10 <= FOV <= 120):
        errors.append(f"Invalid FOV: {FOV} (must be between 10 and 120 degrees)")
    if NEAR_PLANE <= 0:
        errors.append(f"Invalid NEAR_PLANE: {NEAR_PLANE} (must be > 0)")
    if FAR_PLANE <= NEAR_PLANE:
        errors.append(f"Invalid FAR_PLANE: {FAR_PLANE} (must be > NEAR_PLANE)")

    # Validate performance settings
    if TARGET_FPS <= 0:
        errors.append(f"Invalid TARGET_FPS: {TARGET_FPS} (must be > 0)")
    if TARGET_FPS > 1000:
        errors.append(f"TARGET_FPS {TARGET_FPS} is unusually high (recommended: 30-144)")

    # Validate camera settings
    if MOUSE_SENSITIVITY <= 0:
        errors.append(f"Invalid MOUSE_SENSITIVITY: {MOUSE_SENSITIVITY} (must be > 0)")
    if MOVEMENT_SPEED <= 0:
        errors.append(f"Invalid MOVEMENT_SPEED: {MOVEMENT_SPEED} (must be > 0)")
    if SPRINT_MULTIPLIER < 1.0:
        errors.append(f"Invalid SPRINT_MULTIPLIER: {SPRINT_MULTIPLIER} (must be >= 1.0)")

    # Validate entity settings
    if ENTITY_DEFAULT_RADIUS <= 0:
        errors.append(f"Invalid ENTITY_DEFAULT_RADIUS: {ENTITY_DEFAULT_RADIUS} (must be > 0)")
    if INTERACTION_DISTANCE <= 0:
        errors.append(f"Invalid INTERACTION_DISTANCE: {INTERACTION_DISTANCE} (must be > 0)")

    # Validate world settings
    if WORLD_SIZE <= 0:
        errors.append(f"Invalid WORLD_SIZE: {WORLD_SIZE} (must be > 0)")
    if CHUNK_SIZE <= 0:
        errors.append(f"Invalid CHUNK_SIZE: {CHUNK_SIZE} (must be > 0)")
    if CHUNK_RESOLUTION <= 0:
        errors.append(f"Invalid CHUNK_RESOLUTION: {CHUNK_RESOLUTION} (must be > 0)")
    if LOAD_DISTANCE <= 0:
        errors.append(f"Invalid LOAD_DISTANCE: {LOAD_DISTANCE} (must be > 0)")
    if UNLOAD_DISTANCE <= LOAD_DISTANCE:
        errors.append(f"UNLOAD_DISTANCE ({UNLOAD_DISTANCE}) must be > LOAD_DISTANCE ({LOAD_DISTANCE})")

    # Validate combat settings
    if PLAYER_MAX_HEALTH <= 0:
        errors.append(f"Invalid PLAYER_MAX_HEALTH: {PLAYER_MAX_HEALTH} (must be > 0)")
    if PLAYER_MAX_STAMINA <= 0:
        errors.append(f"Invalid PLAYER_MAX_STAMINA: {PLAYER_MAX_STAMINA} (must be > 0)")
    if STAMINA_REGEN_RATE <= 0:
        errors.append(f"Invalid STAMINA_REGEN_RATE: {STAMINA_REGEN_RATE} (must be > 0)")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n  " + "\n  ".join(errors)
        )

    return True
