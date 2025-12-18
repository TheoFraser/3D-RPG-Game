"""Item database with all game items."""
from typing import Dict, Any
from game.loot_system import LootRarity


class ItemType:
    """Item type categories."""
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST = "quest"
    CURRENCY = "currency"


# Complete item database
ITEM_DATABASE: Dict[str, Dict[str, Any]] = {
    # ===== WEAPONS =====
    "rusty_sword": {
        "name": "Rusty Sword",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.COMMON,
        "damage": 5,
        "description": "An old, rusted blade. Better than nothing.",
        "level_required": 1,
        "value": 10,
    },
    "iron_sword": {
        "name": "Iron Sword",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.COMMON,
        "damage": 15,
        "description": "A sturdy iron sword.",
        "level_required": 1,
        "value": 50,
    },
    "steel_sword": {
        "name": "Steel Sword",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.UNCOMMON,
        "damage": 25,
        "description": "A well-crafted steel blade.",
        "level_required": 5,
        "value": 150,
    },
    "forest_blade": {
        "name": "Forest Blade",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.LEGENDARY,
        "damage": 60,
        "description": "A legendary blade infused with nature's power.",
        "level_required": 15,
        "value": 2000,
        "special": "Deals bonus damage to undead",
    },
    "crystal_blade": {
        "name": "Crystal Blade",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.LEGENDARY,
        "damage": 65,
        "description": "A blade forged from pure crystal.",
        "level_required": 20,
        "value": 2500,
        "special": "Ignores 20% of enemy defense",
    },
    "reinforced_iron_sword": {
        "name": "Reinforced Iron Sword",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.UNCOMMON,
        "damage": 20,
        "description": "An iron sword reinforced with steel.",
        "level_required": 3,
        "value": 100,
    },
    "iron_pickaxe": {
        "name": "Iron Pickaxe",
        "type": ItemType.WEAPON,
        "rarity": LootRarity.COMMON,
        "damage": 8,
        "description": "A tool for mining ore.",
        "level_required": 1,
        "value": 40,
    },

    # ===== ARMOR =====
    "leather_armor": {
        "name": "Leather Armor",
        "type": ItemType.ARMOR,
        "rarity": LootRarity.COMMON,
        "defense": 10,
        "description": "Basic leather protection.",
        "level_required": 1,
        "value": 40,
    },
    "iron_armor": {
        "name": "Iron Armor",
        "type": ItemType.ARMOR,
        "rarity": LootRarity.UNCOMMON,
        "defense": 20,
        "description": "Sturdy iron plate armor.",
        "level_required": 5,
        "value": 120,
    },
    "chainmail": {
        "name": "Chainmail Armor",
        "type": ItemType.ARMOR,
        "rarity": LootRarity.UNCOMMON,
        "defense": 25,
        "description": "Flexible chainmail protection.",
        "level_required": 4,
        "value": 150,
    },
    "crystal_plate": {
        "name": "Crystal Plate Armor",
        "type": ItemType.ARMOR,
        "rarity": LootRarity.EPIC,
        "defense": 50,
        "health": 30,
        "description": "Magical armor forged from crystals.",
        "level_required": 9,
        "value": 800,
    },

    # ===== CONSUMABLES =====
    "health_potion": {
        "name": "Health Potion",
        "type": ItemType.CONSUMABLE,
        "rarity": LootRarity.COMMON,
        "description": "Restores 50 health.",
        "value": 25,
        "stackable": True,
        "max_stack": 20,
        "healing": 50,
    },
    "greater_health_potion": {
        "name": "Greater Health Potion",
        "type": ItemType.CONSUMABLE,
        "rarity": LootRarity.RARE,
        "description": "Restores 150 health.",
        "value": 80,
        "stackable": True,
        "max_stack": 20,
        "healing": 150,
    },
    "stamina_potion": {
        "name": "Stamina Potion",
        "type": ItemType.CONSUMABLE,
        "rarity": LootRarity.COMMON,
        "description": "Restores 30 stamina.",
        "value": 20,
        "stackable": True,
        "max_stack": 20,
        "stamina_restore": 30,
    },

    # ===== MATERIALS =====
    "wolf_pelt": {
        "name": "Wolf Pelt",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "Fur from a wolf. Can be sold or crafted.",
        "value": 15,
        "stackable": True,
        "max_stack": 50,
    },
    "bear_pelt": {
        "name": "Bear Pelt",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.UNCOMMON,
        "description": "Thick fur from a bear.",
        "value": 40,
        "stackable": True,
        "max_stack": 50,
    },
    "raw_meat": {
        "name": "Raw Meat",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "Fresh meat from an animal.",
        "value": 8,
        "stackable": True,
        "max_stack": 50,
    },
    "spirit_essence": {
        "name": "Spirit Essence",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.UNCOMMON,
        "description": "Essence from a forest spirit.",
        "value": 60,
        "stackable": True,
        "max_stack": 50,
    },
    "crystal_shard": {
        "name": "Crystal Shard",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.UNCOMMON,
        "description": "A shard of crystal.",
        "value": 70,
        "stackable": True,
        "max_stack": 50,
    },
    "wolf_fang": {
        "name": "Wolf Fang",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.UNCOMMON,
        "description": "Sharp fang from a wolf.",
        "value": 25,
        "stackable": True,
        "max_stack": 50,
    },
    "iron_ingot": {
        "name": "Iron Ingot",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "A bar of refined iron.",
        "value": 30,
        "stackable": True,
        "max_stack": 50,
    },
    "steel_ingot": {
        "name": "Steel Ingot",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.UNCOMMON,
        "description": "A bar of refined steel.",
        "value": 80,
        "stackable": True,
        "max_stack": 50,
    },
    "leather_strip": {
        "name": "Leather Strips",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "Strips of leather for crafting.",
        "value": 5,
        "stackable": True,
        "max_stack": 99,
    },
    "coal": {
        "name": "Coal",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "Used for smelting and crafting.",
        "value": 10,
        "stackable": True,
        "max_stack": 99,
    },
    "wooden_stick": {
        "name": "Wooden Stick",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "A simple wooden stick.",
        "value": 2,
        "stackable": True,
        "max_stack": 99,
    },
    "magic_essence": {
        "name": "Magic Essence",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.RARE,
        "description": "Raw magical energy.",
        "value": 150,
        "stackable": True,
        "max_stack": 50,
    },
    "red_herb": {
        "name": "Red Herb",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "A healing herb with red leaves.",
        "value": 12,
        "stackable": True,
        "max_stack": 99,
    },
    "blue_herb": {
        "name": "Blue Herb",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.COMMON,
        "description": "An herb that restores stamina.",
        "value": 10,
        "stackable": True,
        "max_stack": 99,
    },
    "ancient_herb": {
        "name": "Ancient Herb",
        "type": ItemType.MATERIAL,
        "rarity": LootRarity.RARE,
        "description": "A rare herb with powerful properties.",
        "value": 100,
        "stackable": True,
        "max_stack": 50,
    },

    # ===== CURRENCY =====
    "gold": {
        "name": "Gold",
        "type": ItemType.CURRENCY,
        "rarity": LootRarity.COMMON,
        "description": "Currency used throughout the land.",
        "value": 1,
        "stackable": True,
        "max_stack": 9999,
    },
}


def get_item(item_id: str) -> Dict[str, Any]:
    """Get item data by ID."""
    return ITEM_DATABASE.get(item_id)


def get_item_name(item_id: str) -> str:
    """Get display name for an item."""
    item = get_item(item_id)
    return item["name"] if item else "Unknown Item"
