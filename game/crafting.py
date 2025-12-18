"""Crafting system for creating items from materials."""
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from game.equipment import ItemRarity
from game.logger import get_logger

logger = get_logger(__name__)


class RecipeCategory(Enum):
    """Categories of craftable items."""
    WEAPON = auto()
    ARMOR = auto()
    CONSUMABLE = auto()
    TOOL = auto()
    MISC = auto()


@dataclass
class CraftingRecipe:
    """A recipe for crafting an item."""
    recipe_id: str
    name: str
    category: RecipeCategory
    result_item_id: str
    result_quantity: int
    required_materials: List[Tuple[str, int]]  # (item_id, quantity)
    required_level: int
    crafting_time: float  # seconds
    description: str
    rarity: ItemRarity


# Weapon Recipes
WEAPON_RECIPES = {
    "craft_reinforced_sword": CraftingRecipe(
        recipe_id="craft_reinforced_sword",
        name="Reinforced Iron Sword",
        category=RecipeCategory.WEAPON,
        result_item_id="reinforced_iron_sword",
        result_quantity=1,
        required_materials=[
            ("iron_sword", 1),
            ("steel_ingot", 3),
            ("leather_strip", 2),
        ],
        required_level=3,
        crafting_time=5.0,
        description="Strengthen an iron sword with steel reinforcement.",
        rarity=ItemRarity.UNCOMMON
    ),
    "craft_steel_sword": CraftingRecipe(
        recipe_id="craft_steel_sword",
        name="Steel Sword",
        category=RecipeCategory.WEAPON,
        result_item_id="steel_sword",
        result_quantity=1,
        required_materials=[
            ("steel_ingot", 5),
            ("leather_strip", 3),
            ("wolf_fang", 2),
        ],
        required_level=5,
        crafting_time=8.0,
        description="Forge a strong steel sword.",
        rarity=ItemRarity.RARE
    ),
    "craft_crystal_blade": CraftingRecipe(
        recipe_id="craft_crystal_blade",
        name="Crystal Blade",
        category=RecipeCategory.WEAPON,
        result_item_id="crystal_blade",
        result_quantity=1,
        required_materials=[
            ("crystal_shard", 10),
            ("steel_sword", 1),
            ("magic_essence", 5),
        ],
        required_level=8,
        crafting_time=12.0,
        description="Infuse a steel sword with crystal power.",
        rarity=ItemRarity.EPIC
    ),
}


# Armor Recipes
ARMOR_RECIPES = {
    "craft_leather_armor": CraftingRecipe(
        recipe_id="craft_leather_armor",
        name="Leather Armor",
        category=RecipeCategory.ARMOR,
        result_item_id="leather_armor",
        result_quantity=1,
        required_materials=[
            ("wolf_pelt", 8),
            ("leather_strip", 6),
        ],
        required_level=2,
        crafting_time=6.0,
        description="Craft basic leather armor from wolf pelts.",
        rarity=ItemRarity.COMMON
    ),
    "craft_chainmail": CraftingRecipe(
        recipe_id="craft_chainmail",
        name="Chainmail Armor",
        category=RecipeCategory.ARMOR,
        result_item_id="chainmail",
        result_quantity=1,
        required_materials=[
            ("iron_ingot", 12),
            ("leather_armor", 1),
        ],
        required_level=4,
        crafting_time=10.0,
        description="Forge chainmail from iron ingots.",
        rarity=ItemRarity.UNCOMMON
    ),
    "craft_crystal_plate": CraftingRecipe(
        recipe_id="craft_crystal_plate",
        name="Crystal Plate Armor",
        category=RecipeCategory.ARMOR,
        result_item_id="crystal_plate",
        result_quantity=1,
        required_materials=[
            ("crystal_shard", 15),
            ("steel_ingot", 8),
            ("magic_essence", 6),
        ],
        required_level=9,
        crafting_time=15.0,
        description="Create magical crystal plate armor.",
        rarity=ItemRarity.EPIC
    ),
}


# Consumable Recipes
CONSUMABLE_RECIPES = {
    "craft_health_potion": CraftingRecipe(
        recipe_id="craft_health_potion",
        name="Health Potion",
        category=RecipeCategory.CONSUMABLE,
        result_item_id="health_potion",
        result_quantity=1,
        required_materials=[
            ("red_herb", 3),
            ("crystal_shard", 1),
        ],
        required_level=1,
        crafting_time=2.0,
        description="Brew a potion that restores 50 health.",
        rarity=ItemRarity.COMMON
    ),
    "craft_greater_health_potion": CraftingRecipe(
        recipe_id="craft_greater_health_potion",
        name="Greater Health Potion",
        category=RecipeCategory.CONSUMABLE,
        result_item_id="greater_health_potion",
        result_quantity=1,
        required_materials=[
            ("health_potion", 2),
            ("magic_essence", 2),
            ("ancient_herb", 1),
        ],
        required_level=5,
        crafting_time=4.0,
        description="Brew a powerful potion that restores 150 health.",
        rarity=ItemRarity.RARE
    ),
    "craft_stamina_potion": CraftingRecipe(
        recipe_id="craft_stamina_potion",
        name="Stamina Potion",
        category=RecipeCategory.CONSUMABLE,
        result_item_id="stamina_potion",
        result_quantity=1,
        required_materials=[
            ("blue_herb", 3),
            ("raw_meat", 2),
        ],
        required_level=2,
        crafting_time=2.0,
        description="Brew a potion that restores 30 stamina.",
        rarity=ItemRarity.COMMON
    ),
}


# Tool/Misc Recipes
TOOL_RECIPES = {
    "craft_pickaxe": CraftingRecipe(
        recipe_id="craft_pickaxe",
        name="Iron Pickaxe",
        category=RecipeCategory.TOOL,
        result_item_id="iron_pickaxe",
        result_quantity=1,
        required_materials=[
            ("iron_ingot", 3),
            ("wooden_stick", 2),
        ],
        required_level=1,
        crafting_time=3.0,
        description="Craft a pickaxe for mining ore.",
        rarity=ItemRarity.COMMON
    ),
    "craft_steel_ingot": CraftingRecipe(
        recipe_id="craft_steel_ingot",
        name="Steel Ingot",
        category=RecipeCategory.MISC,
        result_item_id="steel_ingot",
        result_quantity=1,
        required_materials=[
            ("iron_ingot", 2),
            ("coal", 1),
        ],
        required_level=2,
        crafting_time=4.0,
        description="Smelt iron and coal into steel.",
        rarity=ItemRarity.UNCOMMON
    ),
    "craft_leather_strip": CraftingRecipe(
        recipe_id="craft_leather_strip",
        name="Leather Strips",
        category=RecipeCategory.MISC,
        result_item_id="leather_strip",
        result_quantity=4,
        required_materials=[
            ("wolf_pelt", 1),
        ],
        required_level=1,
        crafting_time=1.0,
        description="Cut leather into strips for crafting.",
        rarity=ItemRarity.COMMON
    ),
}


# Combine all recipes
ALL_RECIPES = {
    **WEAPON_RECIPES,
    **ARMOR_RECIPES,
    **CONSUMABLE_RECIPES,
    **TOOL_RECIPES,
}


class CraftingManager:
    """Manages crafting operations and recipes."""

    def __init__(self):
        """Initialize crafting manager."""
        self.recipes = ALL_RECIPES
        self.discovered_recipes: set = set()

        # Start with basic recipes discovered
        self._discover_basic_recipes()

        logger.info(f"Crafting system initialized with {len(self.recipes)} recipes")

    def _discover_basic_recipes(self):
        """Unlock basic starter recipes."""
        basic_recipes = [
            "craft_leather_strip",
            "craft_health_potion",
            "craft_leather_armor",
            "craft_pickaxe",
        ]
        for recipe_id in basic_recipes:
            self.discovered_recipes.add(recipe_id)
        logger.info(f"Discovered {len(basic_recipes)} basic recipes")

    def discover_recipe(self, recipe_id: str) -> bool:
        """
        Discover a new recipe.

        Args:
            recipe_id: ID of recipe to discover

        Returns:
            True if newly discovered, False if already known
        """
        if recipe_id not in self.recipes:
            logger.warning(f"Unknown recipe: {recipe_id}")
            return False

        if recipe_id in self.discovered_recipes:
            return False

        self.discovered_recipes.add(recipe_id)
        recipe = self.recipes[recipe_id]
        logger.info(f"Discovered recipe: {recipe.name}")
        return True

    def get_recipe(self, recipe_id: str) -> Optional[CraftingRecipe]:
        """
        Get a recipe by ID.

        Args:
            recipe_id: Recipe ID

        Returns:
            Recipe if found, None otherwise
        """
        return self.recipes.get(recipe_id)

    def get_recipes_by_category(self, category: RecipeCategory) -> List[CraftingRecipe]:
        """
        Get all discovered recipes in a category.

        Args:
            category: Recipe category

        Returns:
            List of recipes in category
        """
        return [
            recipe for recipe in self.recipes.values()
            if recipe.category == category and recipe.recipe_id in self.discovered_recipes
        ]

    def get_all_discovered_recipes(self) -> List[CraftingRecipe]:
        """Get all discovered recipes."""
        return [
            self.recipes[recipe_id]
            for recipe_id in self.discovered_recipes
            if recipe_id in self.recipes
        ]

    def can_craft(self, recipe_id: str, inventory, player_level: int) -> Tuple[bool, str]:
        """
        Check if player can craft an item.

        Args:
            recipe_id: Recipe to check
            inventory: Player's inventory
            player_level: Player's current level

        Returns:
            Tuple of (can_craft: bool, reason: str)
        """
        # Check if recipe exists
        recipe = self.get_recipe(recipe_id)
        if recipe is None:
            return False, "Recipe not found"

        # Check if recipe is discovered
        if recipe_id not in self.discovered_recipes:
            return False, "Recipe not discovered"

        # Check level requirement
        if player_level < recipe.required_level:
            return False, f"Requires level {recipe.required_level}"

        # Check materials
        for material_id, required_qty in recipe.required_materials:
            available_qty = inventory.get_item_count(material_id)
            if available_qty < required_qty:
                return False, f"Insufficient {material_id} ({available_qty}/{required_qty})"

        return True, "Can craft"

    def craft_item(self, recipe_id: str, inventory, player_level: int) -> Tuple[bool, str]:
        """
        Attempt to craft an item.

        Args:
            recipe_id: Recipe to craft
            inventory: Player's inventory
            player_level: Player's current level

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if can craft
        can_craft, reason = self.can_craft(recipe_id, inventory, player_level)
        if not can_craft:
            return False, reason

        recipe = self.get_recipe(recipe_id)

        # Remove materials from inventory
        for material_id, required_qty in recipe.required_materials:
            success = inventory.remove_item(material_id, required_qty)
            if not success:
                logger.error(f"Failed to remove {material_id} x{required_qty} during crafting")
                return False, "Failed to remove materials"

        # Add crafted item to inventory
        success = inventory.add_item(recipe.result_item_id, is_key_item=False, quantity=recipe.result_quantity)
        if not success:
            logger.error(f"Failed to add crafted item {recipe.result_item_id}")
            # Try to restore materials (best effort)
            for material_id, required_qty in recipe.required_materials:
                inventory.add_item(material_id, is_key_item=False, quantity=required_qty)
            return False, "Inventory full"

        logger.info(f"Crafted {recipe.name} x{recipe.result_quantity}")
        return True, f"Crafted {recipe.name} x{recipe.result_quantity}"

    def get_craftable_count(self, recipe_id: str, inventory) -> int:
        """
        Get how many times a recipe can be crafted with current materials.

        Args:
            recipe_id: Recipe to check
            inventory: Player's inventory

        Returns:
            Number of times recipe can be crafted
        """
        recipe = self.get_recipe(recipe_id)
        if recipe is None or recipe_id not in self.discovered_recipes:
            return 0

        # Find the limiting material
        max_crafts = float('inf')
        for material_id, required_qty in recipe.required_materials:
            available_qty = inventory.get_item_count(material_id)
            possible_crafts = available_qty // required_qty
            max_crafts = min(max_crafts, possible_crafts)

        return int(max_crafts) if max_crafts != float('inf') else 0


# Global crafting manager instance
_crafting_manager = None


def get_crafting_manager() -> CraftingManager:
    """Get or create global crafting manager."""
    global _crafting_manager
    if _crafting_manager is None:
        _crafting_manager = CraftingManager()
    return _crafting_manager


def reset_crafting_manager() -> None:
    """Reset the global crafting manager."""
    global _crafting_manager
    _crafting_manager = CraftingManager()
