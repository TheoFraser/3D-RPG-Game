# Open World Action-Adventure RPG Development Plan

## Overview
A 3D open world action-adventure RPG built in Python featuring a vast fantasy world, combat system, story-driven quests, and rich exploration. Performance-critical calculations (terrain generation, physics, pathfinding, combat) are optimized with Numba JIT compilation.

## Game Concept
- **Genre**: Open World Action-Adventure RPG
- **Core Pillars**: Exploration, Combat, Story, Progression
- **Perspective**: First-person (with potential third-person option)
- **World**: Huge open world (2000x2000 units) with fantasy biomes

## World Design

### World Size & Structure
- **Total Size**: 2000 x 2000 units (approximately 31x31 chunks)
- **Chunk Size**: 64 x 64 units per chunk
- **Streaming**: Dynamic loading/unloading based on player position
- **Travel Time**: 30+ minutes to cross the entire world

### Fantasy Biomes
| Biome | Description | Enemies | Resources |
|-------|-------------|---------|-----------|
| **Grasslands** | Rolling hills, default starting area | Wolves, Bears | Wood, Stone, Herbs |
| **Enchanted Forest** | Dense magical trees, glowing particles | Forest Spirits, Wisps | Magic Herbs, Crystal Shards |
| **Crystal Caves** | Underground areas, crystalline structures | Crystal Golems, Cave Bats | Rare Crystals, Gems |
| **Floating Islands** | Raised plateaus with mystical atmosphere | Sky Serpents, Wind Elementals | Sky Flowers, Floating Stones |
| **Ancient Ruins** | Stone structures, dusty, mysterious | Undead Guardians, Skeletons | Ancient Artifacts, Gold |

### Points of Interest
- **Villages** (3-5): Towns with merchants, quest givers, rest points
- **Dungeons** (5-10): Combat challenge areas with boss encounters
- **Shrines** (10-15): Fast travel points, rest/save locations
- **Ruins** (15-20): Lore collectibles, treasure, exploration rewards
- **Resource Nodes**: Mining spots, gathering areas

---

## Technology Stack

### Core Technologies
| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Python 3.11+ | Main game logic |
| 3D Rendering | ModernGL + PyGLM | OpenGL-based rendering |
| Windowing | Pygame | Window management and input |
| Math/Physics | Numba + NumPy | High-performance calculations |
| Audio | Pygame.mixer | Sound effects and music |
| Assets | Pillow, PyWavefront | Texture and model loading |

### Performance Strategy
- **Numba JIT**: Terrain generation, physics, pathfinding, combat calculations
- **Chunk Streaming**: Only load nearby chunks to manage memory
- **Frustum Culling**: Skip rendering objects outside view
- **Spatial Hashing**: Efficient collision and enemy detection

---

## Project Structure

```
3D-Game/
├── main.py                 # Entry point and game loop
├── config.py               # Game configuration
├── requirements.txt        # Dependencies
│
├── engine/                 # Core engine systems
│   ├── window.py           # Window and context
│   ├── camera.py           # FPS camera system
│   ├── frustum.py          # View frustum culling
│   └── resource_manager.py # Asset caching
│
├── graphics/               # Rendering
│   ├── shader.py           # Shader management
│   ├── mesh.py             # Geometry handling
│   ├── texture.py          # Texture system
│   ├── lighting.py         # Lights and shadows
│   └── skybox.py           # Environment
│
├── physics/                # Physics (Numba-optimized)
│   ├── collision.py        # Collision detection
│   ├── numba_physics.py    # Numba physics kernels
│   └── combat_physics.py   # Combat hit detection
│
├── game/                   # Game systems
│   ├── player.py           # Player controller + stats
│   ├── combat.py           # Combat system
│   ├── stats.py            # Character statistics
│   ├── enemy.py            # Enemy AI
│   ├── npc.py              # NPC system
│   ├── dialogue.py         # Dialogue trees
│   ├── quests.py           # Quest tracking
│   ├── inventory.py        # Item management
│   ├── equipment.py        # Gear system
│   ├── ui.py               # User interface
│   └── game_state.py       # State machine
│
├── world_gen/              # World generation
│   ├── chunk.py            # Chunk data structure
│   ├── chunk_manager.py    # Streaming system
│   ├── terrain.py          # Terrain mesh generation
│   ├── numba_terrain.py    # Numba noise functions
│   ├── biome.py            # Biome definitions
│   ├── biome_generator.py  # Biome placement
│   ├── vegetation.py       # Trees/plants
│   ├── structures.py       # Ruins/landmarks
│   ├── poi_generator.py    # POI placement
│   └── spawn_system.py     # Enemy spawning
│
├── audio/                  # Audio system
│   ├── sound_manager.py    # Sound effects
│   └── ambient_manager.py  # Biome ambiance
│
├── assets/                 # Game assets
│   ├── shaders/            # GLSL shaders
│   ├── textures/           # Image textures
│   ├── dialogues.json      # Dialogue data
│   ├── quests/             # Quest definitions
│   └── items/              # Item database
│
└── tests/                  # Unit tests
```

---

## Implementation Phases

### Phase 1: World Chunking & Streaming (CRITICAL FOUNDATION)
**Goal**: Enable large 2000x2000 world with dynamic loading

**Status**: Not Started

#### 1.1 Chunk System
**Files to Create**:
- `world_gen/chunk.py` - Chunk data structure
- `world_gen/chunk_manager.py` - Loading/unloading system

**Implementation**:
```python
# Chunk data structure
class Chunk:
    def __init__(self, chunk_x, chunk_z):
        self.position = (chunk_x, chunk_z)
        self.heightmap = None      # 32x32 float array
        self.mesh = None           # ModernGL VAO
        self.entities = []         # Objects in chunk
        self.biome = None          # Biome type
        self.loaded = False
```

**Tasks**:
- [ ] Create Chunk class with position, heightmap, mesh
- [ ] Create ChunkManager to track loaded chunks
- [ ] Implement chunk loading based on player position
- [ ] Implement chunk unloading when player moves away
- [ ] Background thread for chunk generation

**Config Additions**:
```python
WORLD_SIZE = 2000          # Total world size
CHUNK_SIZE = 64            # Units per chunk
CHUNK_RESOLUTION = 32      # Vertices per chunk side
LOAD_DISTANCE = 3          # Chunks around player to load
UNLOAD_DISTANCE = 5        # Chunks to keep before unloading
```

#### 1.2 Terrain Refactoring
**Files to Modify**:
- `world_gen/terrain.py` - Chunk-based generation
- `world_gen/numba_terrain.py` - Biome-aware height

**Tasks**:
- [ ] Refactor terrain generation to work per-chunk
- [ ] Add seed-based deterministic generation
- [ ] Ensure seamless chunk boundaries
- [ ] Optimize mesh creation for streaming

**Player Experience**: Walk through vast world that generates as you explore

---

### Phase 2: Biome System
**Goal**: Create distinct fantasy regions with visual variety

**Status**: Not Started

#### 2.1 Biome Definitions
**Files to Create**:
- `world_gen/biome.py` - Biome data classes
- `world_gen/biome_generator.py` - Biome placement algorithm

**Biome Parameters**:
```python
BIOMES = {
    "grasslands": {
        "base_height": 0.3,
        "height_variation": 0.2,
        "ground_color": (0.3, 0.5, 0.2),
        "vegetation_density": 0.3,
        "enemy_types": ["wolf", "bear"],
    },
    "enchanted_forest": {
        "base_height": 0.4,
        "height_variation": 0.3,
        "ground_color": (0.2, 0.4, 0.3),
        "vegetation_density": 0.8,
        "enemy_types": ["forest_spirit", "wisp"],
        "particles": ["glow", "firefly"],
    },
    # ... more biomes
}
```

**Tasks**:
- [ ] Define 5 biome types with unique parameters
- [ ] Implement Voronoi-based biome placement
- [ ] Create biome blending at boundaries
- [ ] Apply biome-specific height modifiers
- [ ] Add biome-specific ground colors

#### 2.2 Vegetation System
**Files to Create**:
- `world_gen/vegetation.py` - Tree/plant placement

**Tasks**:
- [ ] Place trees based on biome vegetation density
- [ ] Different tree types per biome
- [ ] Instanced rendering for vegetation
- [ ] LOD for distant trees

**Player Experience**: Explore visually distinct magical regions

---

### Phase 3: Combat System
**Goal**: Action combat with player and enemy interactions

**Status**: Not Started

#### 3.1 Player Combat
**Files to Create**:
- `game/combat.py` - Combat system core
- `game/stats.py` - Health, stamina, damage stats
- `game/weapons.py` - Weapon types and attacks

**Files to Modify**:
- `game/player.py` - Add combat actions
- `game/ui.py` - Health/stamina bars

**Player Stats**:
```python
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_STAMINA = 100
PLAYER_BASE_DAMAGE = 10
STAMINA_REGEN_RATE = 15      # Per second
ATTACK_STAMINA_COST = 20
DODGE_STAMINA_COST = 25
ATTACK_COOLDOWN = 0.5        # Seconds
DODGE_DURATION = 0.3         # Seconds of invincibility
```

**Combat Actions**:
- **Attack** (Left Click): Swing weapon, costs stamina
- **Block** (Right Click): Reduce incoming damage
- **Dodge** (Shift + Direction): Quick dash with invincibility frames
- **Heavy Attack** (Hold Left Click): Stronger but slower

**Tasks**:
- [ ] Create Stats class with health, stamina, damage
- [ ] Implement attack action with hitbox
- [ ] Add stamina consumption and regeneration
- [ ] Implement dodge with invincibility frames
- [ ] Add health/stamina UI bars
- [ ] Create damage numbers display

#### 3.2 Hit Detection
**Files to Create**:
- `physics/combat_physics.py` - Numba hit detection

**Implementation**:
```python
@njit(fastmath=True)
def check_attack_hits(attacker_pos, attack_dir, attack_range,
                      target_positions, target_radii, n_targets):
    """Check which targets are hit by an attack."""
    hits = np.zeros(n_targets, dtype=np.bool_)
    for i in range(n_targets):
        # Sphere-cone intersection for attack arc
        # ...
    return hits
```

**Tasks**:
- [ ] Implement sphere-based hit detection
- [ ] Add attack cone/arc detection
- [ ] Create knockback physics
- [ ] Add hit feedback (screen shake, sound)

**Player Experience**: Satisfying action combat with responsive controls

---

### Phase 4: Enemies & Wildlife
**Goal**: Populate the world with creatures to fight

**Status**: Not Started

#### 4.1 Enemy AI
**Files to Create**:
- `game/enemy.py` - Enemy AI (extends NPC)
- `game/creature_definitions.py` - Enemy stat blocks

**Files to Modify**:
- `game/npc.py` - Add combat AI states

**New NPC States**:
```python
class NPCState(Enum):
    IDLE = "idle"
    PATROL = "patrol"
    AGGRO = "aggro"        # NEW: Spotted player
    CHASE = "chase"        # NEW: Pursuing player
    ATTACK = "attack"      # NEW: In attack range
    STAGGER = "stagger"    # NEW: Hit recovery
    RETREAT = "retreat"    # NEW: Low health
    DEAD = "dead"          # NEW: Defeated
```

**Enemy Types**:
```python
ENEMIES = {
    "wolf": {
        "health": 30, "damage": 8, "speed": 5.0,
        "aggro_range": 15, "attack_range": 2,
        "biomes": ["grasslands"],
        "loot": [("wolf_pelt", 0.8), ("gold", 0.5)]
    },
    "forest_spirit": {
        "health": 25, "damage": 12, "speed": 4.0,
        "aggro_range": 10, "attack_range": 3,
        "biomes": ["enchanted_forest"],
        "loot": [("spirit_essence", 0.7), ("magic_dust", 0.4)]
    },
    # ... more enemies
}
```

**Tasks**:
- [ ] Create Enemy class extending NPC
- [ ] Implement aggro detection (distance to player)
- [ ] Add chase behavior using pathfinding
- [ ] Implement attack patterns per enemy type
- [ ] Add enemy health bars
- [ ] Create death and loot drop system

#### 4.2 Spawn System
**Files to Create**:
- `game/spawn_system.py` - Per-chunk spawning
- `game/loot_tables.py` - Drop tables

**Tasks**:
- [ ] Generate spawn points per chunk based on biome
- [ ] Limit active enemies to prevent performance issues
- [ ] Implement respawn timers
- [ ] Create loot drop system

**Player Experience**: Encounter and fight creatures throughout the world

---

### Phase 5: Equipment & Progression
**Goal**: RPG progression through gear and levels

**Status**: Not Started

#### 5.1 Equipment System
**Files to Create**:
- `game/equipment.py` - Equipment slots, bonuses
- `game/item_database.py` - All items

**Files to Modify**:
- `game/inventory.py` - Add equipment slots
- `game/player.py` - Apply equipment bonuses
- `game/ui.py` - Equipment screen

**Equipment Slots**:
```python
EQUIPMENT_SLOTS = {
    "weapon": {"stat_bonus": "damage"},
    "armor": {"stat_bonus": "defense"},
    "accessory": {"stat_bonus": "special"},
}

# Example items
ITEMS = {
    "iron_sword": {
        "slot": "weapon",
        "damage": 15,
        "description": "A sturdy iron sword."
    },
    "leather_armor": {
        "slot": "armor",
        "defense": 10,
        "description": "Basic leather protection."
    },
}
```

**Tasks**:
- [ ] Create Equipment class with slots
- [ ] Implement equip/unequip actions
- [ ] Apply equipment stats to player
- [ ] Create equipment comparison UI
- [ ] Add equipment drops from enemies

#### 5.2 Leveling System
**Files to Create**:
- `game/character_stats.py` - Level-up system

**Progression**:
```python
LEVEL_XP = [0, 100, 300, 600, 1000, 1500, ...]  # XP thresholds
STAT_PER_LEVEL = {
    "max_health": 10,
    "max_stamina": 5,
    "base_damage": 2,
}
```

**Tasks**:
- [ ] Create XP and level tracking
- [ ] Implement level-up stat bonuses
- [ ] Add XP gain from enemies
- [ ] Create level-up notification

**Player Experience**: Grow stronger through gear and levels

---

### Phase 6: Points of Interest & Villages
**Goal**: Meaningful locations to discover

**Status**: Not Started

#### 6.1 POI System
**Files to Create**:
- `world_gen/poi_generator.py` - POI placement
- `game/village.py` - Village management
- `game/merchant.py` - Buy/sell system
- `assets/poi_definitions.json` - POI data

**POI Types**:
```python
POI_TYPES = {
    "village": {
        "count": 4,
        "npcs": ["merchant", "quest_giver", "villager"],
        "services": ["shop", "rest", "save"]
    },
    "dungeon": {
        "count": 8,
        "enemy_density": "high",
        "has_boss": True,
        "loot_quality": "rare"
    },
    "shrine": {
        "count": 12,
        "services": ["fast_travel", "rest", "save"]
    },
    "ruin": {
        "count": 20,
        "loot": ["gold", "artifact"],
        "lore": True
    }
}
```

**Tasks**:
- [ ] Generate POI locations (spread across world)
- [ ] Create village with NPCs
- [ ] Implement merchant buy/sell interface
- [ ] Add shrine fast travel system
- [ ] Create dungeon entrances

**Player Experience**: Find villages to rest and resupply, discover dungeons

---

### Phase 7: Story & Quests
**Goal**: Main campaign and side content

**Status**: Not Started

#### 7.1 Quest System Enhancement
**Files to Create**:
- `game/main_quest.py` - Main storyline
- `game/side_quests.py` - Side quest definitions
- `assets/quests/` - Quest data files

**Quest Structure**:
```python
MAIN_QUEST = {
    "prologue": {
        "name": "Awakening",
        "objectives": ["Talk to Elder in starting village"],
        "rewards": {"xp": 100, "item": "basic_sword"},
        "next": "act1_investigation"
    },
    "act1_investigation": {
        "name": "The Corruption",
        "objectives": [
            "Investigate the Enchanted Forest",
            "Find the source of dark magic",
            "Defeat the Forest Guardian"
        ],
        "rewards": {"xp": 500, "item": "forest_amulet"},
        "next": "act2_gathering"
    },
    # ... more acts
}
```

**Tasks**:
- [ ] Design main quest storyline (3 acts)
- [ ] Create 10+ side quests
- [ ] Implement quest prerequisites
- [ ] Add boss encounters
- [ ] Create ending sequence

**Player Experience**: Engaging story that drives exploration

---

### Phase 8: Polish & Atmosphere
**Goal**: Immersive world with atmosphere

**Status**: Not Started

#### 8.1 Visual Polish
**Files to Create**:
- `graphics/particles.py` - Environmental effects
- `graphics/weather.py` - Weather system

**Files to Modify**:
- `graphics/lighting.py` - Day/night cycle
- `graphics/skybox.py` - Dynamic sky

**Tasks**:
- [ ] Implement day/night cycle
- [ ] Add biome-specific particles (fireflies, dust)
- [ ] Create weather effects (rain, fog)
- [ ] Add dynamic sky colors

#### 8.2 Audio
**Files to Create**:
- `audio/ambient_manager.py` - Biome sounds

**Tasks**:
- [ ] Create ambient soundscapes per biome
- [ ] Add combat sound effects
- [ ] Implement dynamic music

**Player Experience**: Living, breathing world

---

## Controls

### Movement
| Key | Action |
|-----|--------|
| W/A/S/D | Move |
| Mouse | Look around |
| Space | Jump |
| Shift | Sprint (hold) / Dodge (tap + direction) |

### Combat
| Key | Action |
|-----|--------|
| Left Click | Attack |
| Right Click | Block |
| Shift + Direction | Dodge |
| Hold Left Click | Heavy Attack |

### Interface
| Key | Action |
|-----|--------|
| E | Interact |
| I | Inventory / Equipment |
| Q | Quest Log |
| M | Map |
| J | Journal |
| Tab | Toggle mouse |
| ESC | Pause / Back |

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Frame Rate | 60 FPS | Minimum acceptable |
| World Size | 2000x2000 | With chunk streaming |
| Loaded Chunks | ~25-49 | 3-7 chunk radius |
| Active Enemies | 50+ | Spatial culling |
| Load Time | < 10 seconds | Initial load |
| Memory | < 2 GB | With streaming |

---

## Dependencies

```
moderngl>=5.8.0
pygame>=2.5.0
numpy>=1.24.0
numba>=0.58.0
PyGLM>=2.7.0
Pillow>=10.0.0
PyWavefront>=1.3.3
```

---

## Current Progress

### ✅ Completed Features

#### Core Systems
- [x] Core engine (window, camera, frustum culling)
- [x] Rendering pipeline (shaders, meshes, textures, lighting, shadows)
- [x] Physics engine (Numba-optimized collision detection)
- [x] Resource management with lifecycle tracking
- [x] Save/Load system with multiple slots
- [x] Audio system (sound effects, biome ambiance)

#### Phase 1: World & Chunking ✅ COMPLETE
- [x] Chunk system with 64x64 unit chunks
- [x] Dynamic loading/unloading based on player position
- [x] Thread-pool async chunk generation
- [x] Seamless chunk edge blending
- [x] 2000x2000 world fully operational
- [x] Frustum culling for chunk rendering

#### Phase 2: Biomes & Vegetation ✅ COMPLETE
- [x] BiomeManager with 5 distinct biomes
- [x] Voronoi-based biome placement
- [x] Biome-specific terrain heights and colors
- [x] VegetationManager with instanced rendering
- [x] Biome-specific vegetation density
- [x] Biome ambient audio system

#### Phase 3: Combat System ✅ COMPLETE
- [x] Player combat with attack/block/dodge
- [x] Stamina system with regeneration
- [x] Hit detection with hitboxes
- [x] Damage numbers and combat feedback
- [x] Spell system with 8 unique spells
- [x] Mana management
- [x] Combat animations and effects

#### Phase 4: Enemies & Wildlife ✅ COMPLETE
- [x] Enemy AI with aggro, chase, attack states
- [x] Multiple enemy types per biome
- [x] Enemy spawning per chunk
- [x] Enemy health bars and death animations
- [x] Loot drop system with rarity tiers
- [x] Boss enemies in dungeons

#### Phase 5: Equipment & Progression ✅ COMPLETE
- [x] Equipment system (weapon, armor, accessory slots)
- [x] Equipment stats (damage, defense, health, stamina)
- [x] Rarity system (Common, Uncommon, Rare, Epic, Legendary)
- [x] Leveling system with XP
- [x] Stat bonuses per level
- [x] Equipment UI with comparison
- [x] Crafting system with 12 recipes
- [x] Recipe discovery system

#### Phase 6: POI & Villages ✅ COMPLETE
- [x] POI generation system (42 POIs across world)
- [x] 4 villages with NPCs
- [x] 12 shrines for fast travel
- [x] 20 ruins for exploration
- [x] 6 dungeons with bosses
- [x] Merchant system with buy/sell
- [x] Village rest/save points
- [x] POI markers on map

#### Phase 7: Story & Quests ✅ COMPLETE
- [x] Quest system with multi-objective tracking
- [x] Quest prerequisites and dependencies
- [x] Main questline (4 acts: Prologue, Act 1-3)
- [x] 10 side quests
- [x] 5 boss quest chains
- [x] Quest callbacks (on_start, on_complete)
- [x] Quest log UI
- [x] NPC dialogue system
- [x] Dialogue trees with branching

#### Phase 8: Polish & Atmosphere ✅ COMPLETE
- [x] Particle system (environmental effects)
- [x] Weather system (rain, fog)
- [x] Shadow mapping with cascaded shadows
- [x] Day/night cycle (placeholder)
- [x] Skybox with atmosphere
- [x] Post-processing effects
- [x] Biome-specific ambient sounds
- [x] Combat sound effects

### 🎯 Recent Enhancements (2025-12-18)
- [x] Boss quest integration with main game loop
- [x] Main quest storyline (3-act campaign)
- [x] Side quests (10 quests with varied objectives)
- [x] Quest prerequisite system with validation
- [x] Interactive crafting UI with selection
- [x] Technical review and critical bug fixes
- [x] Performance optimizations (O(1) quest lookups, recipe caching)
- [x] Memory management improvements

### 🔧 Next Potential Enhancements
1. **Polish & Content**
   - Add more quest variety (fetch, escort, puzzle quests)
   - Expand crafting recipes
   - Add more unique boss encounters
   - Create more spell variety

2. **Quality of Life**
   - Mini-map enhancement
   - Quest waypoint markers
   - Inventory sorting/filtering
   - Keybinding customization

3. **Performance**
   - LOD (Level of Detail) for distant enemies
   - Occlusion culling for POIs
   - Spatial audio optimization
   - Chunk generation priority queue

4. **New Features**
   - Companion/pet system
   - Mount system for faster travel
   - Fishing/gathering minigames
   - Guild/faction system

---

## Getting Started

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows

# Install dependencies (if needed)
pip install -r requirements.txt

# Run the game
python main.py
```

---

## Game Inspirations
- **The Elder Scrolls (Skyrim)** - Open world exploration, fantasy setting
- **Dark Souls** - Action combat, challenging enemies
- **The Witcher 3** - Story quests, interesting NPCs
- **Breath of the Wild** - Exploration freedom, discovery
- **Monster Hunter** - Combat feel, creature variety
