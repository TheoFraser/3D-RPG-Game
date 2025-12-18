"""Integration tests to verify game systems work together correctly."""
import unittest
from unittest.mock import Mock, MagicMock
import glm


class TestLootIntegration(unittest.TestCase):
    """Test loot system integration with item database."""

    def test_get_items_by_rarity_function_exists(self):
        """Test that get_items_by_rarity function exists and works."""
        from game.item_database import get_items_by_rarity
        from game.loot_system import LootRarity

        # Test each rarity level
        for rarity in [LootRarity.COMMON, LootRarity.UNCOMMON, LootRarity.RARE,
                      LootRarity.EPIC, LootRarity.LEGENDARY]:
            items = get_items_by_rarity(rarity)
            self.assertIsInstance(items, list)

            # If items exist, verify they have the correct rarity
            for item in items:
                self.assertTrue(hasattr(item, 'id'))
                self.assertEqual(item.rarity, rarity)

    def test_loot_generation_from_enemy(self):
        """Test loot generation when enemy is defeated."""
        from game.loot import get_loot_system

        loot_system = get_loot_system()

        # Test generating loot for various enemy types
        enemy_types = ["wolf", "bear", "skeleton", "forest_spirit"]

        for enemy_type in enemy_types:
            # Should not raise errors
            loot = loot_system.generate_loot(enemy_type, f"Test {enemy_type}")
            self.assertIsInstance(loot, list)

    def test_all_item_database_items_have_rarity(self):
        """Test all items in database have a rarity field."""
        from game.item_database import ITEM_DATABASE

        for item_id, item_data in ITEM_DATABASE.items():
            self.assertIn("rarity", item_data,
                         f"Item {item_id} missing 'rarity' field")

    def test_loot_rarity_bonus_system(self):
        """Test the loot rarity bonus system works."""
        from game.loot import LootSystem
        from game.loot_system import LootRarity

        loot_system = LootSystem(seed=42)

        # Test rarity bonus for different enemy types
        # This should not raise ImportError
        try:
            bonus_item = loot_system._roll_rarity_bonus("wolf")
            # Bonus item can be None or a string
            self.assertTrue(bonus_item is None or isinstance(bonus_item, str))
        except ImportError as e:
            self.fail(f"ImportError during rarity bonus: {e}")


class TestItemDatabase(unittest.TestCase):
    """Test item database functions."""

    def test_get_item_function(self):
        """Test get_item returns correct data."""
        from game.item_database import get_item

        # Test getting a known item
        item = get_item("health_potion")
        if item:  # Item might not exist in all databases
            self.assertIsInstance(item, dict)
            self.assertIn("name", item)

    def test_get_item_name_function(self):
        """Test get_item_name returns string."""
        from game.item_database import get_item_name

        # Test known item
        name = get_item_name("health_potion")
        self.assertIsInstance(name, str)

        # Test unknown item
        unknown_name = get_item_name("nonexistent_item_xyz")
        self.assertEqual(unknown_name, "Unknown Item")


class TestImportIntegrity(unittest.TestCase):
    """Test that all imports work correctly."""

    def test_game_module_imports(self):
        """Test all game modules can be imported."""
        modules_to_test = [
            'game.player',
            'game.enemy',
            'game.loot',
            'game.loot_system',
            'game.item_database',
            'game.inventory',
            'game.equipment',
            'game.progression',
            'game.combat',
            'game.stats',
            'game.npc',
            'game.dialogue',
            'game.quests',
            'game.pathfinding',
            'game.save_system',
        ]

        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                self.fail(f"Failed to import {module_name}: {e}")

    def test_cross_module_imports(self):
        """Test imports between modules work."""
        # These are imports that happen during runtime
        try:
            from game.loot import get_loot_system
            from game.item_database import get_items_by_rarity, get_item, get_item_name
            from game.loot_system import LootRarity
            from game.progression import calculate_enemy_xp

            # If we get here, all imports succeeded
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Cross-module import failed: {e}")


class TestEnemyDefeat(unittest.TestCase):
    """Test enemy defeat handling."""

    def test_enemy_xp_calculation(self):
        """Test XP calculation for different enemy types."""
        from game.progression import calculate_enemy_xp

        # Test various enemy types
        enemy_types = ["WEAK", "NORMAL", "TANK", "FAST"]

        for enemy_type in enemy_types:
            xp = calculate_enemy_xp(enemy_type)
            self.assertIsInstance(xp, int)
            self.assertGreater(xp, 0)

    def test_loot_generation_complete_flow(self):
        """Test complete loot generation flow."""
        from game.loot import LootSystem

        loot_system = LootSystem(seed=42)

        # Simulate enemy defeat
        enemy_type = "wolf"
        enemy_name = "Alpha Wolf"

        loot_items = loot_system.generate_loot(enemy_type, enemy_name)

        self.assertIsInstance(loot_items, list)
        # Loot can be empty or contain items
        for item_id in loot_items:
            self.assertIsInstance(item_id, str)


class TestItemIntegration(unittest.TestCase):
    """Test item system integration."""

    def test_item_types_match(self):
        """Test ItemType class matches expected types."""
        from game.item_database import ItemType

        # Verify expected item types exist
        expected_types = ['WEAPON', 'ARMOR', 'ACCESSORY', 'CONSUMABLE',
                         'MATERIAL', 'QUEST', 'CURRENCY']

        for type_name in expected_types:
            self.assertTrue(hasattr(ItemType, type_name),
                          f"ItemType missing {type_name}")

    def test_loot_rarity_enum(self):
        """Test LootRarity enum exists and has expected values."""
        from game.loot_system import LootRarity

        # Verify rarity levels exist
        expected_rarities = ['COMMON', 'UNCOMMON', 'RARE', 'EPIC', 'LEGENDARY']

        for rarity_name in expected_rarities:
            self.assertTrue(hasattr(LootRarity, rarity_name),
                          f"LootRarity missing {rarity_name}")


class TestSaveLoadIntegration(unittest.TestCase):
    """Test save/load system integration."""

    def test_save_system_can_import_required_modules(self):
        """Test save system can import all needed modules."""
        try:
            from game.save_system import SaveSystem, serialize_game_state
            from game.player import Player
            from game.inventory import Inventory

            # If imports succeed, test passes
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Save system import failed: {e}")


if __name__ == '__main__':
    unittest.main()
