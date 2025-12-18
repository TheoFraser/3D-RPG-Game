"""Loot drop system for enemies."""
import random
from typing import List, Tuple, Optional
from game.equipment import ItemRarity
from game.item_database import get_item
from game.loot_system import ENEMY_LOOT_TABLES as COMPREHENSIVE_LOOT_TABLES, LootRarity
from game.logger import get_logger

logger = get_logger(__name__)


# Loot tables per enemy type (item_id, drop_chance)
ENEMY_LOOT_TABLES = {
    "WEAK": [
        ("rusty_sword", 0.15),
        ("tattered_clothes", 0.15),
        ("bronze_ring", 0.10),
        ("wooden_club", 0.10),
    ],
    "NORMAL": [
        ("iron_sword", 0.20),
        ("leather_armor", 0.20),
        ("steel_sword", 0.10),
        ("chainmail", 0.10),
        ("silver_amulet", 0.08),
        ("power_ring", 0.08),
    ],
    "TANK": [
        ("chainmail", 0.25),
        ("crystal_plate", 0.12),
        ("ancient_plate", 0.05),
        ("iron_sword", 0.15),
        ("steel_sword", 0.15),
    ],
    "FAST": [
        ("steel_sword", 0.20),
        ("forest_blade", 0.15),
        ("sky_blade", 0.08),
        ("forest_garb", 0.15),
        ("sky_mantle", 0.08),
        ("power_ring", 0.12),
    ],
}


# Bonus loot by rarity (higher chance for better enemies)
RARITY_BONUS_TABLES = {
    "WEAK": [
        (ItemRarity.COMMON, 0.80),
        (ItemRarity.UNCOMMON, 0.15),
        (ItemRarity.RARE, 0.05),
    ],
    "NORMAL": [
        (ItemRarity.COMMON, 0.60),
        (ItemRarity.UNCOMMON, 0.30),
        (ItemRarity.RARE, 0.08),
        (ItemRarity.EPIC, 0.02),
    ],
    "TANK": [
        (ItemRarity.COMMON, 0.50),
        (ItemRarity.UNCOMMON, 0.30),
        (ItemRarity.RARE, 0.15),
        (ItemRarity.EPIC, 0.05),
    ],
    "FAST": [
        (ItemRarity.COMMON, 0.55),
        (ItemRarity.UNCOMMON, 0.30),
        (ItemRarity.RARE, 0.12),
        (ItemRarity.EPIC, 0.03),
    ],
}


class LootSystem:
    """Manages loot drops from enemies."""

    def __init__(self, seed: int = None):
        """
        Initialize loot system.

        Args:
            seed: Random seed for deterministic loot
        """
        self.random = random.Random(seed)

    def generate_loot(self, enemy_type: str, enemy_name: str = "Enemy") -> List[str]:
        """
        Generate loot drops for a defeated enemy.

        Args:
            enemy_type: Enemy type (WEAK, NORMAL, TANK, FAST) or specific enemy name
            enemy_name: Enemy name (for logging)

        Returns:
            List of item IDs dropped
        """
        # Try comprehensive loot tables first (specific enemies)
        enemy_key = enemy_name.lower().replace(" ", "_")
        if enemy_key in COMPREHENSIVE_LOOT_TABLES:
            return self._generate_from_comprehensive(enemy_key, enemy_name)

        # Fall back to generic type-based loot
        loot_table = ENEMY_LOOT_TABLES.get(enemy_type, ENEMY_LOOT_TABLES.get("NORMAL", []))

        drops = []

        # Check each possible drop
        for item_id, drop_chance in loot_table:
            if self.random.random() < drop_chance:
                drops.append(item_id)

        # Chance for bonus rare drop (25% chance to roll for rarity bonus)
        if self.random.random() < 0.25:
            bonus_item = self._roll_rarity_bonus(enemy_type)
            if bonus_item:
                drops.append(bonus_item)

        return drops

    def generate_boss_loot(self, enemy_type: str, enemy_name: str = "Boss") -> List[str]:
        """
        Generate special loot drops for boss enemies.

        Bosses get guaranteed high-quality loot with better chances for rare items.

        Args:
            enemy_type: Boss enemy type
            enemy_name: Boss name (for logging)

        Returns:
            List of item IDs dropped (guaranteed to be multiple high-quality items)
        """
        drops = []

        # Bosses always drop gold (lots of it)
        gold_count = self.random.randint(3, 6)  # 3-6 gold drops
        for _ in range(gold_count):
            drops.append("gold")

        # Guaranteed epic or legendary equipment (2-3 items)
        epic_legendary_items = [
            "ancient_plate", "mythril_armor", "dragon_plate",
            "sky_blade", "forest_blade", "ancient_sword",
            "crystal_amulet", "ancient_ring", "power_amulet"
        ]
        num_guaranteed = self.random.randint(2, 3)
        for _ in range(num_guaranteed):
            item = self.random.choice(epic_legendary_items)
            if item not in drops:  # Avoid exact duplicates
                drops.append(item)

        # Additional rare items (50% chance each)
        rare_items = [
            "steel_sword", "chainmail", "crystal_plate",
            "silver_amulet", "power_ring"
        ]
        for item in rare_items:
            if self.random.random() < 0.5:
                drops.append(item)

        logger.info(f"Boss {enemy_name} dropped {len(drops)} items (boss loot)")
        return drops

    def _generate_from_comprehensive(self, enemy_key: str, enemy_name: str) -> List[str]:
        """Generate loot using comprehensive loot tables."""
        loot_table = COMPREHENSIVE_LOOT_TABLES[enemy_key]
        drops = []

        # Add guaranteed drops
        for item_id, quantity, rarity in loot_table.get("guaranteed", []):
            drops.append(item_id)

        # Roll for possible drops
        for entry in loot_table.get("possible", []):
            item_id, quantity, chance, rarity = entry
            if self.random.random() < chance:
                drops.append(item_id)

        logger.debug(f"Generated {len(drops)} drops from {enemy_name}")
        return drops

    def _roll_rarity_bonus(self, enemy_type: str) -> Optional[str]:
        """
        Roll for a bonus item based on rarity table.

        Args:
            enemy_type: Enemy type

        Returns:
            Item ID or None
        """
        rarity_table = RARITY_BONUS_TABLES.get(enemy_type, RARITY_BONUS_TABLES["NORMAL"])

        # Roll for rarity
        roll = self.random.random()
        cumulative = 0.0

        target_rarity = None
        for rarity, chance in rarity_table:
            cumulative += chance
            if roll <= cumulative:
                target_rarity = rarity
                break

        if target_rarity is None:
            return None

        # Get items of that rarity from database
        from game.item_database import get_items_by_rarity
        items = get_items_by_rarity(target_rarity)

        if not items:
            return None

        # Pick random item
        item = self.random.choice(items)
        return item.id


# Global loot system instance
_loot_system = None


def get_loot_system(seed: int = None) -> LootSystem:
    """Get or create global loot system."""
    global _loot_system
    if _loot_system is None:
        _loot_system = LootSystem(seed)
    return _loot_system


def reset_loot_system(seed: int = None) -> None:
    """Reset the global loot system with a new seed."""
    global _loot_system
    _loot_system = LootSystem(seed)
