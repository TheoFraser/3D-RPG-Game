"""Inventory system for tracking collected items."""
from typing import List, Optional, Dict
from game.equipment import EquipmentItem, EquipmentSlot, ItemRarity
from game.logger import get_logger

logger = get_logger(__name__)


class Inventory:
    """Player inventory for equipment, consumables, materials, and key items."""

    def __init__(self):
        """Initialize empty inventory."""
        self.equipment_items: List[EquipmentItem] = []  # Equipment that can be worn
        self.consumables = []  # Consumable items (potions, etc.)
        self.key_items = []  # Important items for progression
        self.materials: Dict[str, int] = {}  # Crafting materials with quantities

    def add_equipment(self, item: EquipmentItem) -> bool:
        """
        Add equipment to inventory.

        Args:
            item: Equipment item to add

        Returns:
            bool: True if item was added
        """
        self.equipment_items.append(item)
        rarity_name = item.rarity.name
        logger.info(f"[{rarity_name}] {item.name} acquired!")
        return True

    def add_material(self, item_id: str, quantity: int = 1) -> bool:
        """
        Add materials/stackable items to inventory.

        Args:
            item_id: Item ID to add
            quantity: Quantity to add

        Returns:
            bool: True if items were added
        """
        if quantity <= 0:
            return False

        if item_id in self.materials:
            self.materials[item_id] += quantity
        else:
            self.materials[item_id] = quantity

        logger.debug(f"Added {quantity}x {item_id} to materials")
        return True

    def remove_material(self, item_id: str, quantity: int = 1) -> bool:
        """
        Remove materials from inventory.

        Args:
            item_id: Item ID to remove
            quantity: Quantity to remove

        Returns:
            bool: True if items were removed, False if not enough
        """
        if item_id not in self.materials or self.materials[item_id] < quantity:
            logger.warning(f"Cannot remove {quantity}x {item_id} - not enough in inventory")
            return False

        self.materials[item_id] -= quantity

        # Remove entry if quantity is 0
        if self.materials[item_id] <= 0:
            del self.materials[item_id]

        logger.debug(f"Removed {quantity}x {item_id} from materials")
        return True

    def get_item_count(self, item_id: str) -> int:
        """
        Get quantity of a material/stackable item.

        Args:
            item_id: Item ID to count

        Returns:
            int: Quantity of item (0 if not found)
        """
        return self.materials.get(item_id, 0)

    def has_material(self, item_id: str, quantity: int = 1) -> bool:
        """
        Check if inventory has enough of a material.

        Args:
            item_id: Item ID to check
            quantity: Required quantity

        Returns:
            bool: True if has enough
        """
        return self.get_item_count(item_id) >= quantity

    def add_item(self, item_name, is_key_item=False, quantity=1):
        """
        Add a generic item to the inventory (backward compatibility).

        Args:
            item_name: Name of the item
            is_key_item: Whether this is a key item for progression
            quantity: Quantity to add (for materials/stackables)

        Returns:
            bool: True if item was added
        """
        if is_key_item:
            if item_name not in self.key_items:
                self.key_items.append(item_name)
                logger.info(f"Key Item Acquired: {item_name}")
                return True
        else:
            # Try to add as material first (stackable items)
            return self.add_material(item_name, quantity)

        return False

    def has_item(self, item_name, quantity=1):
        """Check if inventory contains an item (by name)."""
        # Check materials first
        if item_name in self.materials:
            return self.materials[item_name] >= quantity
        # Check equipment
        for item in self.equipment_items:
            if item.name == item_name or item.id == item_name:
                return True
        # Check consumables and key items
        return item_name in self.consumables or item_name in self.key_items

    def remove_equipment(self, item: EquipmentItem) -> bool:
        """Remove equipment from inventory."""
        if item in self.equipment_items:
            self.equipment_items.remove(item)
            return True
        return False

    def remove_item(self, item_name, quantity=1):
        """Remove an item from inventory (by name)."""
        # Try to remove as material first
        if item_name in self.materials:
            return self.remove_material(item_name, quantity)
        elif item_name in self.consumables:
            self.consumables.remove(item_name)
            return True
        elif item_name in self.key_items:
            self.key_items.remove(item_name)
            return True
        return False

    def get_total_item_count(self):
        """Get total number of unique item types."""
        return len(self.equipment_items) + len(self.consumables) + len(self.key_items) + len(self.materials)

    def get_equipment_count(self):
        """Get number of equipment items."""
        return len(self.equipment_items)

    def get_consumable_count(self):
        """Get number of consumable items."""
        return len(self.consumables)

    def get_key_item_count(self):
        """Get number of key items."""
        return len(self.key_items)

    def get_equipment_by_slot(self, slot: EquipmentSlot) -> List[EquipmentItem]:
        """Get all equipment items for a specific slot."""
        return [item for item in self.equipment_items if item.slot == slot]

    def get_equipment_by_rarity(self, rarity: ItemRarity) -> List[EquipmentItem]:
        """Get all equipment items of a specific rarity."""
        return [item for item in self.equipment_items if item.rarity == rarity]

    def sort_equipment(self, by='rarity'):
        """
        Sort equipment items.

        Args:
            by: Sort key ('rarity', 'level', 'name', 'slot')
        """
        if by == 'rarity':
            self.equipment_items.sort(key=lambda x: x.rarity.value, reverse=True)
        elif by == 'level':
            self.equipment_items.sort(key=lambda x: x.level_required, reverse=True)
        elif by == 'name':
            self.equipment_items.sort(key=lambda x: x.name)
        elif by == 'slot':
            self.equipment_items.sort(key=lambda x: x.slot.value)

    def clear(self):
        """Clear all items."""
        self.equipment_items.clear()
        self.consumables.clear()
        self.key_items.clear()
        self.materials.clear()

    def __str__(self):
        """String representation of inventory."""
        lines = [f"Inventory ({self.get_total_item_count()} items):"]

        if self.equipment_items:
            lines.append(f"  Equipment ({len(self.equipment_items)}):")
            for item in self.equipment_items:
                rarity = item.rarity.name
                stats = item.get_stat_summary()
                lines.append(f"    - [{rarity}] {item.name} (Lvl {item.level_required}) - {stats}")

        if self.materials:
            lines.append(f"  Materials ({len(self.materials)}):")
            for item_id, quantity in self.materials.items():
                lines.append(f"    - {item_id} x{quantity}")

        if self.consumables:
            lines.append(f"  Consumables ({len(self.consumables)}):")
            for item in self.consumables:
                lines.append(f"    - {item}")

        if self.key_items:
            lines.append("  Key Items:")
            for item in self.key_items:
                lines.append(f"    - {item}")

        return "\n".join(lines)
