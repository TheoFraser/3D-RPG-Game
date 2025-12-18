"""Merchant system for buying and selling items."""
from typing import List, Dict, Optional
from game.equipment import EquipmentItem, EquipmentSlot, ItemRarity
import random


class MerchantInventory:
    """Represents a merchant's stock of items for sale."""

    def __init__(self, merchant_type: str = "general", level_range: tuple = (1, 5)):
        """
        Initialize merchant inventory.

        Args:
            merchant_type: Type of merchant (general, weapons, armor, potions)
            level_range: Min/max item level to stock
        """
        self.merchant_type = merchant_type
        self.level_range = level_range
        self.items: List[EquipmentItem] = []
        self.prices: Dict[str, int] = {}  # item_id -> price

        # Generate initial stock
        self.restock()

    def restock(self):
        """Generate new merchant inventory."""
        self.items.clear()
        self.prices.clear()

        # Number of items to stock
        item_count = random.randint(5, 10)

        for _ in range(item_count):
            item = self._generate_merchant_item()
            if item:
                self.items.append(item)
                # Price is based on item level and rarity
                base_price = item.level_required * 10
                rarity_mult = {
                    ItemRarity.COMMON: 1.0,
                    ItemRarity.UNCOMMON: 2.0,
                    ItemRarity.RARE: 4.0,
                    ItemRarity.EPIC: 8.0,
                    ItemRarity.LEGENDARY: 16.0
                }
                price = int(base_price * rarity_mult[item.rarity])
                self.prices[item.id] = price

    def _generate_merchant_item(self) -> Optional[EquipmentItem]:
        """Generate a random item for merchant stock."""
        from game.equipment import EquipmentGenerator

        # Determine slot based on merchant type
        if self.merchant_type == "weapons":
            slot = EquipmentSlot.WEAPON
        elif self.merchant_type == "armor":
            slot = EquipmentSlot.ARMOR
        elif self.merchant_type == "accessories":
            slot = EquipmentSlot.ACCESSORY
        else:  # general
            slot = random.choice(list(EquipmentSlot))

        level = random.randint(self.level_range[0], self.level_range[1])
        rarity = random.choices(
            [ItemRarity.COMMON, ItemRarity.UNCOMMON, ItemRarity.RARE, ItemRarity.EPIC],
            weights=[50, 30, 15, 5],
            k=1
        )[0]

        generator = EquipmentGenerator()
        return generator.generate_random_item(slot, level, rarity)

    def get_item_price(self, item_id: str) -> int:
        """Get the price of an item."""
        return self.prices.get(item_id, 0)

    def has_item(self, item_id: str) -> bool:
        """Check if merchant has an item in stock."""
        return any(item.id == item_id for item in self.items)

    def remove_item(self, item_id: str) -> Optional[EquipmentItem]:
        """Remove and return an item from merchant stock."""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                return self.items.pop(i)
        return None


class Merchant:
    """Represents a merchant NPC that can buy and sell items."""

    def __init__(self, name: str, merchant_type: str = "general", level_range: tuple = (1, 5)):
        """
        Initialize merchant.

        Args:
            name: Merchant's name
            merchant_type: Type of merchant (general, weapons, armor, potions)
            level_range: Min/max item level to stock
        """
        self.name = name
        self.merchant_type = merchant_type
        self.inventory = MerchantInventory(merchant_type, level_range)
        self.gold = 1000  # Merchant starting gold
        self.buy_price_modifier = 0.5  # Merchant pays 50% of item value
        self.sell_price_modifier = 1.0  # Merchant sells at full price

        # Dialogue
        self.greetings = [
            f"Welcome to my shop! I'm {name}.",
            f"Greetings, traveler! {name} at your service.",
            f"Looking to trade? You've come to the right place!",
        ]
        self.farewells = [
            "Come back anytime!",
            "Safe travels!",
            "May fortune favor you!",
        ]

    def get_greeting(self) -> str:
        """Get a random greeting."""
        return random.choice(self.greetings)

    def get_farewell(self) -> str:
        """Get a random farewell."""
        return random.choice(self.farewells)

    def get_sell_price(self, item: EquipmentItem) -> int:
        """
        Calculate how much the merchant will sell an item for.

        Args:
            item: Item to price

        Returns:
            Price in gold
        """
        if item.id in self.inventory.prices:
            return self.inventory.prices[item.id]

        # Calculate base price
        base_price = item.level_required * 10
        rarity_mult = {
            ItemRarity.COMMON: 1.0,
            ItemRarity.UNCOMMON: 2.0,
            ItemRarity.RARE: 4.0,
            ItemRarity.EPIC: 8.0,
            ItemRarity.LEGENDARY: 16.0
        }
        return int(base_price * rarity_mult[item.rarity] * self.sell_price_modifier)

    def get_buy_price(self, item: EquipmentItem) -> int:
        """
        Calculate how much the merchant will pay for an item.

        Args:
            item: Item to price

        Returns:
            Price in gold
        """
        sell_price = self.get_sell_price(item)
        return int(sell_price * self.buy_price_modifier)

    def can_afford(self, price: int) -> bool:
        """Check if merchant can afford a purchase."""
        return self.gold >= price

    def sell_to_player(self, item_id: str, player_gold: int) -> tuple[bool, str, Optional[EquipmentItem]]:
        """
        Attempt to sell an item to the player.

        Args:
            item_id: ID of item to sell
            player_gold: Player's current gold

        Returns:
            Tuple of (success, message, item)
        """
        # Find item in merchant inventory
        item = None
        for inv_item in self.inventory.items:
            if inv_item.id == item_id:
                item = inv_item
                break

        if not item:
            return False, "That item is not available.", None

        price = self.inventory.get_item_price(item_id)

        # Check if player can afford
        if player_gold < price:
            return False, f"You need {price - player_gold} more gold.", None

        # Complete transaction
        purchased_item = self.inventory.remove_item(item_id)
        self.gold += price

        return True, f"Sold {item.name} for {price} gold.", purchased_item

    def buy_from_player(self, item: EquipmentItem) -> tuple[bool, str, int]:
        """
        Attempt to buy an item from the player.

        Args:
            item: Item player wants to sell

        Returns:
            Tuple of (success, message, gold_earned)
        """
        price = self.get_buy_price(item)

        # Check if merchant can afford
        if not self.can_afford(price):
            return False, "I can't afford that right now.", 0

        # Complete transaction
        self.gold -= price
        self.inventory.items.append(item)
        self.inventory.prices[item.id] = self.get_sell_price(item)

        return True, f"Bought {item.name} for {price} gold.", price


class MerchantManager:
    """Manages all merchants in the game."""

    def __init__(self):
        """Initialize merchant manager."""
        self.merchants: Dict[str, Merchant] = {}

    def create_merchant(self, name: str, merchant_type: str = "general",
                       level_range: tuple = (1, 5)) -> Merchant:
        """
        Create a new merchant.

        Args:
            name: Merchant's name
            merchant_type: Type of merchant
            level_range: Level range for items

        Returns:
            Created merchant
        """
        merchant = Merchant(name, merchant_type, level_range)
        self.merchants[name] = merchant
        return merchant

    def get_merchant(self, name: str) -> Optional[Merchant]:
        """Get a merchant by name."""
        return self.merchants.get(name)

    def restock_all(self):
        """Restock all merchant inventories."""
        for merchant in self.merchants.values():
            merchant.inventory.restock()
