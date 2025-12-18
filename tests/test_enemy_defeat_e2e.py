"""End-to-end tests for enemy defeat and loot generation flow."""
import unittest
from unittest.mock import Mock, patch
import glm

from game.player import Player
from game.enemy import Enemy, EnemyType
from game.loot import LootSystem
from game.item_database import get_item, ITEM_DATABASE
from game.equipment import EquipmentItem, EquipmentSlot, ItemRarity
from game.progression import calculate_enemy_xp


class TestEnemyDefeatEndToEnd(unittest.TestCase):
    """Test complete enemy defeat flow end-to-end."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(position=glm.vec3(0, 0, 0))
        self.loot_system = LootSystem(seed=42)  # Fixed seed for reproducibility

    def test_defeat_weak_enemy_and_get_loot(self):
        """Test defeating a WEAK enemy and receiving loot."""
        enemy = Enemy(
            position=glm.vec3(0, 0, 0),
            enemy_type=EnemyType.WEAK
        )

        # Generate loot for weak enemy
        loot_items = self.loot_system.generate_loot("WEAK", "Test Goblin")

        # Verify loot is a list
        self.assertIsInstance(loot_items, list)

        # Verify each item exists in database and can be created
        for item_id in loot_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found in database")
            self.assertIn("name", item_data)
            self.assertIn("description", item_data)
            self.assertIn("type", item_data)
            self.assertIn("rarity", item_data)

    def test_defeat_normal_enemy_and_get_loot(self):
        """Test defeating a NORMAL enemy and receiving loot."""
        enemy = Enemy(
            position=glm.vec3(0, 0, 0),
            enemy_type=EnemyType.NORMAL
        )

        # Generate loot
        loot_items = self.loot_system.generate_loot("NORMAL", "Test Bandit")

        self.assertIsInstance(loot_items, list)

        # Verify all items can be retrieved
        for item_id in loot_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found in database")

    def test_defeat_tank_enemy_and_get_loot(self):
        """Test defeating a TANK enemy and receiving loot."""
        enemy = Enemy(
            position=glm.vec3(0, 0, 0),
            enemy_type=EnemyType.TANK
        )

        # Generate loot
        loot_items = self.loot_system.generate_loot("TANK", "Test Ogre")

        self.assertIsInstance(loot_items, list)

        # Verify all items exist
        for item_id in loot_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found in database")

    def test_defeat_fast_enemy_and_get_loot(self):
        """Test defeating a FAST enemy and receiving loot."""
        enemy = Enemy(
            position=glm.vec3(0, 0, 0),
            enemy_type=EnemyType.FAST
        )

        # Generate loot
        loot_items = self.loot_system.generate_loot("FAST", "Test Rogue")

        self.assertIsInstance(loot_items, list)

        # Verify all items exist
        for item_id in loot_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found in database")

    def test_equipment_item_creation_from_loot(self):
        """Test creating EquipmentItem objects from loot drops."""
        # Simulate getting weapon drops
        weapon_items = ["rusty_sword", "iron_sword", "steel_sword", "wooden_club"]

        for item_id in weapon_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found")

            # Try creating EquipmentItem like main.py does
            try:
                # Convert LootRarity to ItemRarity
                from game.loot_system import LootRarity
                loot_rarity = item_data.get("rarity")
                # Handle both enum and string rarity values
                if isinstance(loot_rarity, str):
                    item_rarity = ItemRarity[loot_rarity.upper()]
                else:
                    item_rarity = ItemRarity[loot_rarity.name]

                equip_item = EquipmentItem(
                    id=item_id,
                    name=item_data["name"],
                    description=item_data.get("description", ""),
                    rarity=item_rarity,
                    slot=EquipmentSlot.WEAPON,
                    damage_bonus=item_data.get("damage", 0),
                    defense_bonus=item_data.get("defense", 0),
                    health_bonus=item_data.get("health", 0),
                    stamina_bonus=item_data.get("stamina", 0),
                    level_required=item_data.get("level_required", 1)
                )
                self.assertIsNotNone(equip_item)
                self.assertEqual(equip_item.id, item_id)
            except TypeError as e:
                self.fail(f"Failed to create EquipmentItem for {item_id}: {e}")

    def test_armor_item_creation_from_loot(self):
        """Test creating armor EquipmentItem objects from loot drops."""
        armor_items = ["leather_armor", "iron_armor", "chainmail", "tattered_clothes"]

        for item_id in armor_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found")

            # Try creating EquipmentItem
            try:
                # Convert LootRarity to ItemRarity
                from game.loot_system import LootRarity
                loot_rarity = item_data.get("rarity")
                # Handle both enum and string rarity values
                if isinstance(loot_rarity, str):
                    item_rarity = ItemRarity[loot_rarity.upper()]
                else:
                    item_rarity = ItemRarity[loot_rarity.name]

                equip_item = EquipmentItem(
                    id=item_id,
                    name=item_data["name"],
                    description=item_data.get("description", ""),
                    rarity=item_rarity,
                    slot=EquipmentSlot.ARMOR,
                    damage_bonus=item_data.get("damage", 0),
                    defense_bonus=item_data.get("defense", 0),
                    health_bonus=item_data.get("health", 0),
                    stamina_bonus=item_data.get("stamina", 0),
                    level_required=item_data.get("level_required", 1)
                )
                self.assertIsNotNone(equip_item)
            except TypeError as e:
                self.fail(f"Failed to create EquipmentItem for {item_id}: {e}")

    def test_accessory_item_creation_from_loot(self):
        """Test creating accessory items from loot drops."""
        accessory_items = ["bronze_ring", "silver_amulet", "power_ring"]

        for item_id in accessory_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Item {item_id} not found")

            # Accessories should have all required fields
            self.assertIn("name", item_data)
            self.assertIn("description", item_data)
            self.assertIn("type", item_data)
            self.assertIn("rarity", item_data)

    def test_all_loot_table_items_exist_in_database(self):
        """Test that every item in loot tables exists in the database."""
        from game.loot_system import ENEMY_LOOT_TABLES

        missing_items = []
        for enemy_type, loot_data in ENEMY_LOOT_TABLES.items():
            # Check guaranteed drops
            for item_tuple in loot_data.get("guaranteed", []):
                item_id = item_tuple[0]
                item_data = get_item(item_id)
                if item_data is None:
                    missing_items.append(f"{enemy_type} (guaranteed): {item_id}")

            # Check possible drops
            for item_tuple in loot_data.get("possible", []):
                item_id = item_tuple[0]
                item_data = get_item(item_id)
                if item_data is None:
                    missing_items.append(f"{enemy_type} (possible): {item_id}")

        if missing_items:
            self.fail(f"Missing items in database:\n" + "\n".join(missing_items))

    def test_all_loot_table_items_have_required_fields(self):
        """Test that all items in loot tables have required fields."""
        from game.loot_system import ENEMY_LOOT_TABLES

        required_fields = ["name", "description", "type", "rarity", "value"]
        items_with_missing_fields = []

        checked_items = set()
        for enemy_type, loot_data in ENEMY_LOOT_TABLES.items():
            # Check guaranteed drops
            for item_tuple in loot_data.get("guaranteed", []):
                item_id = item_tuple[0]
                if item_id not in checked_items:
                    checked_items.add(item_id)
                    item_data = get_item(item_id)
                    if item_data:
                        missing = [field for field in required_fields if field not in item_data]
                        if missing:
                            items_with_missing_fields.append(
                                f"{item_id}: missing {', '.join(missing)}"
                            )

            # Check possible drops
            for item_tuple in loot_data.get("possible", []):
                item_id = item_tuple[0]
                if item_id not in checked_items:
                    checked_items.add(item_id)
                    item_data = get_item(item_id)
                    if item_data:
                        missing = [field for field in required_fields if field not in item_data]
                        if missing:
                            items_with_missing_fields.append(
                                f"{item_id}: missing {', '.join(missing)}"
                            )

        if items_with_missing_fields:
            self.fail(
                f"Items with missing fields:\n" + "\n".join(items_with_missing_fields)
            )

    def test_xp_calculation_for_all_enemy_types(self):
        """Test XP calculation works for all enemy types."""
        enemy_types = ["WEAK", "NORMAL", "TANK", "FAST"]

        for enemy_type in enemy_types:
            xp = calculate_enemy_xp(enemy_type)
            self.assertIsInstance(xp, int)
            self.assertGreater(xp, 0, f"XP for {enemy_type} should be positive")

    def test_complete_enemy_defeat_simulation(self):
        """Simulate complete enemy defeat flow with multiple enemy types."""
        enemy_types = [
            (EnemyType.WEAK, "WEAK"),
            (EnemyType.NORMAL, "NORMAL"),
            (EnemyType.TANK, "TANK"),
            (EnemyType.FAST, "FAST")
        ]

        for enemy_type_enum, enemy_type_str in enemy_types:
            with self.subTest(enemy_type=enemy_type_str):
                # Create enemy
                enemy = Enemy(
                    position=glm.vec3(0, 0, 0),
                    enemy_type=enemy_type_enum
                )

                # Calculate XP
                xp = calculate_enemy_xp(enemy_type_str)
                self.assertGreater(xp, 0)

                # Generate loot
                loot_items = self.loot_system.generate_loot(enemy_type_str, f"Test {enemy_type_str}")
                self.assertIsInstance(loot_items, list)

                # Verify each loot item can be retrieved and has required fields
                for item_id in loot_items:
                    item_data = get_item(item_id)
                    self.assertIsNotNone(
                        item_data,
                        f"Item {item_id} from {enemy_type_str} enemy not found"
                    )
                    self.assertIn("name", item_data)
                    self.assertIn("description", item_data)

    def test_legendary_items_can_be_created(self):
        """Test that legendary items can be properly created as equipment."""
        legendary_items = ["forest_blade", "crystal_blade"]

        for item_id in legendary_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Legendary item {item_id} not found")

            # Try creating the item
            try:
                # Convert LootRarity to ItemRarity
                from game.loot_system import LootRarity
                loot_rarity = item_data.get("rarity")
                # Handle both enum and string rarity values
                if isinstance(loot_rarity, str):
                    item_rarity = ItemRarity[loot_rarity.upper()]
                else:
                    item_rarity = ItemRarity[loot_rarity.name]

                equip_item = EquipmentItem(
                    id=item_id,
                    name=item_data["name"],
                    description=item_data.get("description", ""),
                    rarity=item_rarity,
                    slot=EquipmentSlot.WEAPON,
                    damage_bonus=item_data.get("damage", 0),
                    defense_bonus=item_data.get("defense", 0),
                    health_bonus=item_data.get("health", 0),
                    stamina_bonus=item_data.get("stamina", 0),
                    level_required=item_data.get("level_required", 1)
                )
                self.assertIsNotNone(equip_item)
            except TypeError as e:
                self.fail(f"Failed to create legendary item {item_id}: {e}")

    def test_rarity_bonus_system_doesnt_crash(self):
        """Test that rarity bonus system works without errors."""
        # This previously caused ImportError
        try:
            for _ in range(100):  # Run multiple times
                bonus_item = self.loot_system._roll_rarity_bonus("NORMAL")
                if bonus_item is not None:
                    # If we got a bonus item, verify it exists
                    item_data = get_item(bonus_item)
                    self.assertIsNotNone(
                        item_data,
                        f"Bonus item {bonus_item} not found in database"
                    )
        except ImportError as e:
            self.fail(f"ImportError in rarity bonus system: {e}")
        except Exception as e:
            self.fail(f"Unexpected error in rarity bonus system: {e}")

    def test_epic_items_exist_and_can_be_created(self):
        """Test epic rarity items from loot tables."""
        epic_items = ["sky_blade", "ancient_plate", "crystal_plate"]

        for item_id in epic_items:
            item_data = get_item(item_id)
            self.assertIsNotNone(item_data, f"Epic item {item_id} not found")

            # Verify it's actually epic rarity
            from game.loot_system import LootRarity
            self.assertEqual(
                item_data.get("rarity"),
                LootRarity.EPIC,
                f"Item {item_id} should be EPIC rarity"
            )


class TestLootSystemRobustness(unittest.TestCase):
    """Test loot system handles edge cases."""

    def test_generate_loot_for_unknown_enemy(self):
        """Test loot generation for unknown enemy type."""
        loot_system = LootSystem(seed=42)

        # Should not crash
        loot = loot_system.generate_loot("UNKNOWN_TYPE", "Mystery Enemy")
        self.assertIsInstance(loot, list)

    def test_generate_lots_of_loot(self):
        """Test generating loot many times doesn't crash."""
        loot_system = LootSystem(seed=42)

        for i in range(1000):
            enemy_type = ["WEAK", "NORMAL", "TANK", "FAST"][i % 4]
            loot = loot_system.generate_loot(enemy_type, f"Enemy {i}")

            # All items should exist
            for item_id in loot:
                item_data = get_item(item_id)
                self.assertIsNotNone(
                    item_data,
                    f"Item {item_id} not found on iteration {i}"
                )


if __name__ == '__main__':
    unittest.main()
