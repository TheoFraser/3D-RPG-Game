"""Loot system for enemy drops and treasure."""
import random
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from game.logger import get_logger

logger = get_logger(__name__)


@dataclass
class LootDrop:
    """Represents a dropped item."""
    item_id: str
    quantity: int
    rarity: str = "common"


class LootRarity:
    """Item rarity tiers."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


# Loot tables for different enemy types
ENEMY_LOOT_TABLES = {
    "wolf": {
        "guaranteed": [
            ("wolf_pelt", 1, LootRarity.COMMON),
        ],
        "possible": [
            ("raw_meat", 1, 0.7, LootRarity.COMMON),
            ("wolf_fang", 1, 0.3, LootRarity.UNCOMMON),
            ("gold", 5, 0.5, LootRarity.COMMON),
        ],
    },
    "bear": {
        "guaranteed": [
            ("bear_pelt", 1, LootRarity.UNCOMMON),
        ],
        "possible": [
            ("raw_meat", 2, 0.8, LootRarity.COMMON),
            ("bear_claw", 1, 0.4, LootRarity.UNCOMMON),
            ("gold", 10, 0.6, LootRarity.COMMON),
        ],
    },
    "forest_spirit": {
        "guaranteed": [
            ("spirit_essence", 1, LootRarity.UNCOMMON),
        ],
        "possible": [
            ("magic_dust", 1, 0.6, LootRarity.UNCOMMON),
            ("forest_crystal", 1, 0.2, LootRarity.RARE),
            ("gold", 15, 0.5, LootRarity.COMMON),
        ],
    },
    "wisp": {
        "guaranteed": [],
        "possible": [
            ("wisp_essence", 1, 0.8, LootRarity.UNCOMMON),
            ("magic_dust", 1, 0.5, LootRarity.UNCOMMON),
            ("gold", 8, 0.4, LootRarity.COMMON),
        ],
    },
    "crystal_golem": {
        "guaranteed": [
            ("crystal_shard", 2, LootRarity.UNCOMMON),
        ],
        "possible": [
            ("crystal_core", 1, 0.3, LootRarity.RARE),
            ("rare_gem", 1, 0.15, LootRarity.EPIC),
            ("gold", 25, 0.7, LootRarity.COMMON),
        ],
    },
    "cave_bat": {
        "guaranteed": [],
        "possible": [
            ("bat_wing", 1, 0.6, LootRarity.COMMON),
            ("gold", 3, 0.3, LootRarity.COMMON),
        ],
    },
    "sky_serpent": {
        "guaranteed": [
            ("serpent_scale", 1, LootRarity.UNCOMMON),
        ],
        "possible": [
            ("sky_essence", 1, 0.4, LootRarity.RARE),
            ("serpent_fang", 1, 0.3, LootRarity.UNCOMMON),
            ("gold", 20, 0.6, LootRarity.COMMON),
        ],
    },
    "wind_elemental": {
        "guaranteed": [],
        "possible": [
            ("wind_essence", 1, 0.7, LootRarity.UNCOMMON),
            ("elemental_core", 1, 0.2, LootRarity.RARE),
            ("gold", 15, 0.5, LootRarity.COMMON),
        ],
    },
    "undead_guardian": {
        "guaranteed": [
            ("ancient_bone", 1, LootRarity.UNCOMMON),
        ],
        "possible": [
            ("cursed_essence", 1, 0.5, LootRarity.UNCOMMON),
            ("ancient_artifact", 1, 0.15, LootRarity.EPIC),
            ("gold", 30, 0.8, LootRarity.COMMON),
        ],
    },
    "skeleton": {
        "guaranteed": [
            ("bone", 1, LootRarity.COMMON),
        ],
        "possible": [
            ("rusty_sword", 1, 0.2, LootRarity.COMMON),
            ("gold", 5, 0.4, LootRarity.COMMON),
        ],
    },
    # Boss enemies
    "forest_guardian": {
        "guaranteed": [
            ("guardian_heart", 1, LootRarity.EPIC),
            ("gold", 100, LootRarity.COMMON),
        ],
        "possible": [
            ("legendary_wood", 1, 0.5, LootRarity.RARE),
            ("nature_amulet", 1, 0.3, LootRarity.EPIC),
            ("forest_blade", 1, 0.15, LootRarity.LEGENDARY),
        ],
    },
    "crystal_king": {
        "guaranteed": [
            ("crystal_crown", 1, LootRarity.EPIC),
            ("gold", 150, LootRarity.COMMON),
        ],
        "possible": [
            ("perfect_crystal", 1, 0.4, LootRarity.RARE),
            ("crystal_armor", 1, 0.2, LootRarity.EPIC),
            ("crystal_blade", 1, 0.1, LootRarity.LEGENDARY),
        ],
    },
    "ancient_lich": {
        "guaranteed": [
            ("lich_phylactery", 1, LootRarity.LEGENDARY),
            ("gold", 200, LootRarity.COMMON),
        ],
        "possible": [
            ("death_essence", 3, 0.8, LootRarity.RARE),
            ("necromancer_staff", 1, 0.3, LootRarity.EPIC),
            ("dark_grimoire", 1, 0.15, LootRarity.LEGENDARY),
        ],
    },
}


# Treasure chest loot tables (for dungeons/ruins)
TREASURE_LOOT_TABLES = {
    "common_chest": {
        "guaranteed": [
            ("gold", 20, LootRarity.COMMON),
        ],
        "possible": [
            ("health_potion", 1, 0.7, LootRarity.COMMON),
            ("stamina_potion", 1, 0.5, LootRarity.COMMON),
            ("iron_ore", 2, 0.4, LootRarity.COMMON),
        ],
    },
    "rare_chest": {
        "guaranteed": [
            ("gold", 50, LootRarity.COMMON),
        ],
        "possible": [
            ("rare_gem", 1, 0.6, LootRarity.RARE),
            ("magic_scroll", 1, 0.4, LootRarity.UNCOMMON),
            ("enchanted_weapon", 1, 0.2, LootRarity.RARE),
        ],
    },
    "dungeon_chest": {
        "guaranteed": [
            ("gold", 100, LootRarity.COMMON),
        ],
        "possible": [
            ("epic_weapon", 1, 0.3, LootRarity.EPIC),
            ("epic_armor", 1, 0.3, LootRarity.EPIC),
            ("rare_gem", 2, 0.8, LootRarity.RARE),
            ("ancient_artifact", 1, 0.15, LootRarity.LEGENDARY),
        ],
    },
}


class LootSystem:
    """Manages loot generation and drops."""

    def __init__(self, seed: int = 42):
        """
        Initialize loot system.

        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        self.rng = random.Random(seed)

        logger.info(f"LootSystem initialized (seed={seed})")

    def generate_enemy_loot(
        self,
        enemy_type: str,
        luck_multiplier: float = 1.0
    ) -> List[LootDrop]:
        """
        Generate loot drops from an enemy.

        Args:
            enemy_type: Type of enemy (e.g., "wolf", "bear")
            luck_multiplier: Multiplier for drop chances (e.g., from player stats)

        Returns:
            List of LootDrop objects
        """
        if enemy_type not in ENEMY_LOOT_TABLES:
            logger.warning(f"Unknown enemy type for loot: {enemy_type}")
            return []

        loot_table = ENEMY_LOOT_TABLES[enemy_type]
        drops = []

        # Add guaranteed drops
        for item_id, quantity, rarity in loot_table.get("guaranteed", []):
            drops.append(LootDrop(
                item_id=item_id,
                quantity=quantity,
                rarity=rarity
            ))

        # Roll for possible drops
        for entry in loot_table.get("possible", []):
            item_id, quantity, chance, rarity = entry

            # Apply luck multiplier
            effective_chance = min(1.0, chance * luck_multiplier)

            if self.rng.random() < effective_chance:
                drops.append(LootDrop(
                    item_id=item_id,
                    quantity=quantity,
                    rarity=rarity
                ))

        logger.debug(f"Generated {len(drops)} loot drops from {enemy_type}")
        return drops

    def generate_treasure_loot(
        self,
        chest_type: str,
        luck_multiplier: float = 1.0
    ) -> List[LootDrop]:
        """
        Generate loot from a treasure chest.

        Args:
            chest_type: Type of chest (e.g., "common_chest", "rare_chest")
            luck_multiplier: Multiplier for drop chances

        Returns:
            List of LootDrop objects
        """
        if chest_type not in TREASURE_LOOT_TABLES:
            logger.warning(f"Unknown chest type for loot: {chest_type}")
            return []

        loot_table = TREASURE_LOOT_TABLES[chest_type]
        drops = []

        # Add guaranteed drops
        for item_id, quantity, rarity in loot_table.get("guaranteed", []):
            drops.append(LootDrop(
                item_id=item_id,
                quantity=quantity,
                rarity=rarity
            ))

        # Roll for possible drops
        for entry in loot_table.get("possible", []):
            item_id, quantity, chance, rarity = entry

            # Apply luck multiplier
            effective_chance = min(1.0, chance * luck_multiplier)

            if self.rng.random() < effective_chance:
                drops.append(LootDrop(
                    item_id=item_id,
                    quantity=quantity,
                    rarity=rarity
                ))

        logger.info(f"Generated {len(drops)} loot drops from {chest_type}")
        return drops

    def get_rarity_color(self, rarity: str) -> Tuple[float, float, float]:
        """
        Get display color for item rarity.

        Args:
            rarity: Item rarity level

        Returns:
            RGB color tuple
        """
        colors = {
            LootRarity.COMMON: (0.7, 0.7, 0.7),      # Gray
            LootRarity.UNCOMMON: (0.3, 0.9, 0.3),    # Green
            LootRarity.RARE: (0.3, 0.5, 1.0),        # Blue
            LootRarity.EPIC: (0.7, 0.3, 0.9),        # Purple
            LootRarity.LEGENDARY: (1.0, 0.6, 0.0),   # Orange
        }
        return colors.get(rarity, (1.0, 1.0, 1.0))

    def get_rarity_name(self, rarity: str) -> str:
        """Get display name for rarity."""
        names = {
            LootRarity.COMMON: "Common",
            LootRarity.UNCOMMON: "Uncommon",
            LootRarity.RARE: "Rare",
            LootRarity.EPIC: "Epic",
            LootRarity.LEGENDARY: "Legendary",
        }
        return names.get(rarity, "Unknown")

    def add_loot_table(
        self,
        entity_type: str,
        guaranteed: List[Tuple],
        possible: List[Tuple]
    ):
        """
        Add or modify a loot table.

        Args:
            entity_type: Type of entity (enemy or chest)
            guaranteed: List of guaranteed drops (item_id, quantity, rarity)
            possible: List of possible drops (item_id, quantity, chance, rarity)
        """
        ENEMY_LOOT_TABLES[entity_type] = {
            "guaranteed": guaranteed,
            "possible": possible,
        }
        logger.info(f"Added loot table for {entity_type}")
