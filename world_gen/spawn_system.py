"""Enemy spawn system for chunks."""
import random
from typing import List, Dict
import glm
import config
from game.enemy import Enemy, EnemyType


# Spawn tables per biome
BIOME_SPAWN_TABLES = {
    config.BIOME_GRASSLANDS: [
        (EnemyType.WEAK, 0.5),     # 50% weak enemies
        (EnemyType.NORMAL, 0.35),  # 35% normal enemies
        (EnemyType.TANK, 0.15),    # 15% tank enemies
    ],
    config.BIOME_ENCHANTED_FOREST: [
        (EnemyType.FAST, 0.4),     # 40% fast enemies (forest spirits)
        (EnemyType.WEAK, 0.35),    # 35% weak enemies (wisps)
        (EnemyType.NORMAL, 0.25),  # 25% normal enemies
    ],
    config.BIOME_CRYSTAL_CAVES: [
        (EnemyType.TANK, 0.5),     # 50% tank enemies (crystal golems)
        (EnemyType.NORMAL, 0.35),  # 35% normal enemies
        (EnemyType.FAST, 0.15),    # 15% fast enemies (cave bats)
    ],
    config.BIOME_FLOATING_ISLANDS: [
        (EnemyType.FAST, 0.5),     # 50% fast enemies (sky serpents)
        (EnemyType.NORMAL, 0.35),  # 35% normal enemies (wind elementals)
        (EnemyType.WEAK, 0.15),    # 15% weak enemies
    ],
    config.BIOME_ANCIENT_RUINS: [
        (EnemyType.TANK, 0.4),     # 40% tank enemies (undead guardians)
        (EnemyType.NORMAL, 0.4),   # 40% normal enemies (skeletons)
        (EnemyType.WEAK, 0.2),     # 20% weak enemies
    ],
}


# Enemy names per biome for flavor
BIOME_ENEMY_NAMES = {
    config.BIOME_GRASSLANDS: {
        EnemyType.WEAK: ["Wolf Pup", "Young Bear", "Wild Boar"],
        EnemyType.NORMAL: ["Wolf", "Bear", "Mountain Lion"],
        EnemyType.TANK: ["Alpha Wolf", "Grizzly Bear", "Elder Boar"],
        EnemyType.FAST: ["Swift Fox", "Rabid Wolf", "Pouncing Cat"],
    },
    config.BIOME_ENCHANTED_FOREST: {
        EnemyType.WEAK: ["Wisp", "Tiny Spirit", "Glowbug"],
        EnemyType.NORMAL: ["Forest Spirit", "Tree Guardian", "Fae Warrior"],
        EnemyType.TANK: ["Ancient Treant", "Elder Spirit", "Forest Colossus"],
        EnemyType.FAST: ["Swift Spirit", "Shadow Fae", "Flickering Wisp"],
    },
    config.BIOME_CRYSTAL_CAVES: {
        EnemyType.WEAK: ["Crystal Bat", "Cave Rat", "Gem Beetle"],
        EnemyType.NORMAL: ["Crystal Guardian", "Stone Elemental", "Cave Dweller"],
        EnemyType.TANK: ["Crystal Golem", "Stone Titan", "Gem Giant"],
        EnemyType.FAST: ["Swooping Bat", "Quick Crawler", "Darting Shade"],
    },
    config.BIOME_FLOATING_ISLANDS: {
        EnemyType.WEAK: ["Sky Minnow", "Cloud Wisp", "Wind Sprite"],
        EnemyType.NORMAL: ["Sky Serpent", "Wind Elemental", "Air Guardian"],
        EnemyType.TANK: ["Storm Drake", "Thunder Titan", "Sky Colossus"],
        EnemyType.FAST: ["Lightning Serpent", "Swift Wind", "Darting Drake"],
    },
    config.BIOME_ANCIENT_RUINS: {
        EnemyType.WEAK: ["Skeleton", "Zombie", "Restless Spirit"],
        EnemyType.NORMAL: ["Undead Warrior", "Cursed Knight", "Ancient Soldier"],
        EnemyType.TANK: ["Undead Guardian", "Tomb Lord", "Ancient Champion"],
        EnemyType.FAST: ["Wraith", "Shadow Fiend", "Quick Revenant"],
    },
}


# Spawn density per biome (enemies per chunk)
BIOME_SPAWN_DENSITY = {
    config.BIOME_GRASSLANDS: (1, 3),           # 1-3 enemies per chunk
    config.BIOME_ENCHANTED_FOREST: (2, 4),     # 2-4 enemies per chunk
    config.BIOME_CRYSTAL_CAVES: (1, 2),        # 1-2 enemies per chunk (dense, dangerous)
    config.BIOME_FLOATING_ISLANDS: (1, 3),     # 1-3 enemies per chunk
    config.BIOME_ANCIENT_RUINS: (2, 5),        # 2-5 enemies per chunk (many undead)
}


class SpawnSystem:
    """Handles enemy spawning per chunk based on biome."""

    def __init__(self, seed: int = None):
        """
        Initialize spawn system.

        Args:
            seed: Random seed for spawn generation
        """
        self.seed = seed if seed is not None else config.WORLD_SEED
        self.random = random.Random(self.seed)

    def generate_spawns_for_chunk(
        self,
        chunk_x: int,
        chunk_z: int,
        biome: int,
        chunk_manager
    ) -> List[Enemy]:
        """
        Generate enemy spawns for a chunk.

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            biome: Primary biome ID for chunk
            chunk_manager: Chunk manager for terrain height queries

        Returns:
            List of Enemy objects to spawn in this chunk
        """
        # Use chunk coordinates to seed random for deterministic spawns
        chunk_seed = self.seed + chunk_x * 1000 + chunk_z
        chunk_random = random.Random(chunk_seed)

        # Get spawn density for biome
        min_spawns, max_spawns = BIOME_SPAWN_DENSITY.get(biome, (1, 2))
        num_spawns = chunk_random.randint(min_spawns, max_spawns)

        # Get spawn table for biome
        spawn_table = BIOME_SPAWN_TABLES.get(biome, BIOME_SPAWN_TABLES[config.BIOME_GRASSLANDS])
        name_table = BIOME_ENEMY_NAMES.get(biome, BIOME_ENEMY_NAMES[config.BIOME_GRASSLANDS])

        enemies = []
        world_x_base = chunk_x * config.CHUNK_SIZE
        world_z_base = chunk_z * config.CHUNK_SIZE

        for _ in range(num_spawns):
            # Random position within chunk (avoiding edges)
            local_x = chunk_random.uniform(8, config.CHUNK_SIZE - 8)
            local_z = chunk_random.uniform(8, config.CHUNK_SIZE - 8)
            world_x = world_x_base + local_x
            world_z = world_z_base + local_z

            # Get terrain height at spawn position
            world_y = chunk_manager.get_height_at(world_x, world_z)

            # Select enemy type based on spawn table
            enemy_type = self._weighted_choice(spawn_table, chunk_random)

            # Get random name for this enemy type
            possible_names = name_table.get(enemy_type, ["Enemy"])
            enemy_name = chunk_random.choice(possible_names)

            # Create enemy
            position = glm.vec3(world_x, world_y, world_z)
            enemy = Enemy(position, enemy_type, enemy_name)
            enemies.append(enemy)

        return enemies

    def _weighted_choice(self, choices: List[tuple], rng: random.Random):
        """
        Make weighted random choice from list of (value, weight) tuples.

        Args:
            choices: List of (value, weight) tuples
            rng: Random number generator

        Returns:
            Selected value
        """
        total = sum(weight for _, weight in choices)
        r = rng.uniform(0, total)
        cumulative = 0

        for value, weight in choices:
            cumulative += weight
            if r <= cumulative:
                return value

        # Fallback to first choice
        return choices[0][0]
