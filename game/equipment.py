"""Equipment system for player gear."""
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum, auto


class EquipmentSlot(Enum):
    """Equipment slot types."""
    WEAPON = auto()
    ARMOR = auto()
    ACCESSORY = auto()


class ItemRarity(Enum):
    """Item rarity levels."""
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()


# Rarity colors for UI
RARITY_COLORS = {
    ItemRarity.COMMON: (0.8, 0.8, 0.8),      # Gray
    ItemRarity.UNCOMMON: (0.3, 0.9, 0.3),    # Green
    ItemRarity.RARE: (0.3, 0.5, 1.0),        # Blue
    ItemRarity.EPIC: (0.7, 0.3, 0.9),        # Purple
    ItemRarity.LEGENDARY: (1.0, 0.6, 0.0),   # Orange
}


@dataclass
class Item:
    """Base item class."""
    id: str
    name: str
    description: str
    item_type: str = 'generic'  # 'equipment', 'consumable', 'material'
    rarity: ItemRarity = ItemRarity.COMMON
    value: int = 0  # Gold value
    stackable: bool = False
    max_stack: int = 1


@dataclass
class EquipmentItem(Item):
    """Equipment item with stats."""
    slot: EquipmentSlot = EquipmentSlot.WEAPON
    damage_bonus: int = 0
    defense_bonus: int = 0
    health_bonus: int = 0
    stamina_bonus: int = 0
    level_required: int = 1

    def __post_init__(self):
        """Set item type to equipment."""
        self.item_type = 'equipment'
        self.stackable = False
        self.max_stack = 1

    def get_stat_summary(self) -> str:
        """Get formatted stat summary."""
        stats = []
        if self.damage_bonus > 0:
            stats.append(f"+{self.damage_bonus} Damage")
        if self.defense_bonus > 0:
            stats.append(f"+{self.defense_bonus} Defense")
        if self.health_bonus > 0:
            stats.append(f"+{self.health_bonus} Health")
        if self.stamina_bonus > 0:
            stats.append(f"+{self.stamina_bonus} Stamina")
        return ", ".join(stats) if stats else "No bonuses"


class Equipment:
    """Manages equipped items for a character."""

    def __init__(self):
        """Initialize equipment slots."""
        self.slots: Dict[EquipmentSlot, Optional[EquipmentItem]] = {
            EquipmentSlot.WEAPON: None,
            EquipmentSlot.ARMOR: None,
            EquipmentSlot.ACCESSORY: None,
        }

    def equip(self, item: EquipmentItem) -> Optional[EquipmentItem]:
        """
        Equip an item.

        Args:
            item: Equipment item to equip

        Returns:
            Previously equipped item in that slot, or None
        """
        old_item = self.slots[item.slot]
        self.slots[item.slot] = item
        return old_item

    def unequip(self, slot: EquipmentSlot) -> Optional[EquipmentItem]:
        """
        Unequip an item from a slot.

        Args:
            slot: Equipment slot to unequip

        Returns:
            The unequipped item, or None
        """
        item = self.slots[slot]
        self.slots[slot] = None
        return item

    def get_equipped(self, slot: EquipmentSlot) -> Optional[EquipmentItem]:
        """Get currently equipped item in a slot."""
        return self.slots[slot]

    def get_total_damage_bonus(self) -> int:
        """Calculate total damage bonus from all equipment."""
        total = 0
        for item in self.slots.values():
            if item:
                total += item.damage_bonus
        return total

    def get_total_defense_bonus(self) -> int:
        """Calculate total defense bonus from all equipment."""
        total = 0
        for item in self.slots.values():
            if item:
                total += item.defense_bonus
        return total

    def get_total_health_bonus(self) -> int:
        """Calculate total health bonus from all equipment."""
        total = 0
        for item in self.slots.values():
            if item:
                total += item.health_bonus
        return total

    def get_total_stamina_bonus(self) -> int:
        """Calculate total stamina bonus from all equipment."""
        total = 0
        for item in self.slots.values():
            if item:
                total += item.stamina_bonus
        return total

    def get_all_equipped(self) -> Dict[EquipmentSlot, EquipmentItem]:
        """Get all currently equipped items."""
        return {slot: item for slot, item in self.slots.items() if item is not None}

    def is_slot_empty(self, slot: EquipmentSlot) -> bool:
        """Check if a slot is empty."""
        return self.slots[slot] is None

    def get_equipment_power(self) -> int:
        """Calculate total equipment power (sum of all bonuses)."""
        power = 0
        for item in self.slots.values():
            if item:
                power += item.damage_bonus
                power += item.defense_bonus
                power += item.health_bonus // 10  # Health contributes less to power
                power += item.stamina_bonus // 10  # Stamina contributes less to power
        return power


class EquipmentGenerator:
    """Generates random equipment items for loot and merchants."""

    def __init__(self):
        """Initialize equipment generator."""
        self.weapon_names = ["Sword", "Axe", "Mace", "Dagger", "Spear", "Hammer"]
        self.armor_names = ["Helmet", "Chestplate", "Leggings", "Boots", "Gauntlets"]
        self.accessory_names = ["Ring", "Amulet", "Belt", "Cloak"]
        self.material_prefixes = {
            ItemRarity.COMMON: ["Rusty", "Worn", "Old", "Basic"],
            ItemRarity.UNCOMMON: ["Iron", "Steel", "Bronze", "Sturdy"],
            ItemRarity.RARE: ["Silver", "Reinforced", "Enchanted", "Fine"],
            ItemRarity.EPIC: ["Mythril", "Blessed", "Masterwork", "Ancient"],
            ItemRarity.LEGENDARY: ["Dragon", "Celestial", "Legendary", "Divine"]
        }

    def generate_random_item(self, slot: EquipmentSlot, level: int = 1,
                            rarity: ItemRarity = ItemRarity.COMMON) -> EquipmentItem:
        """
        Generate a random equipment item.

        Args:
            slot: Equipment slot type
            level: Item level (affects stats)
            rarity: Item rarity

        Returns:
            Generated equipment item
        """
        import random
        import uuid

        # Get base name
        if slot == EquipmentSlot.WEAPON:
            base_name = random.choice(self.weapon_names)
        elif slot == EquipmentSlot.ARMOR:
            base_name = random.choice(self.armor_names)
        else:  # ACCESSORY
            base_name = random.choice(self.accessory_names)

        # Add material prefix
        prefix = random.choice(self.material_prefixes[rarity])
        name = f"{prefix} {base_name}"

        # Calculate stats based on level and rarity
        rarity_mult = {
            ItemRarity.COMMON: 1.0,
            ItemRarity.UNCOMMON: 1.5,
            ItemRarity.RARE: 2.0,
            ItemRarity.EPIC: 3.0,
            ItemRarity.LEGENDARY: 5.0
        }[rarity]

        base_stat = level * 5
        stat_value = int(base_stat * rarity_mult)

        # Distribute stats based on slot
        damage_bonus = 0
        defense_bonus = 0
        health_bonus = 0
        stamina_bonus = 0

        if slot == EquipmentSlot.WEAPON:
            damage_bonus = stat_value
            stamina_bonus = int(stat_value * 0.2)
        elif slot == EquipmentSlot.ARMOR:
            defense_bonus = stat_value
            health_bonus = int(stat_value * 2)
        else:  # ACCESSORY
            # Accessories have balanced stats
            damage_bonus = int(stat_value * 0.5)
            defense_bonus = int(stat_value * 0.5)
            health_bonus = int(stat_value * 1.5)
            stamina_bonus = int(stat_value * 0.5)

        # Create item
        item_id = f"{slot.name.lower()}_{uuid.uuid4().hex[:8]}"
        description = f"A {rarity.name.lower()} {base_name.lower()} suitable for level {level} adventurers."

        return EquipmentItem(
            id=item_id,
            name=name,
            description=description,
            rarity=rarity,
            value=level * 10 * int(rarity_mult),
            slot=slot,
            damage_bonus=damage_bonus,
            defense_bonus=defense_bonus,
            health_bonus=health_bonus,
            stamina_bonus=stamina_bonus,
            level_required=level
        )
