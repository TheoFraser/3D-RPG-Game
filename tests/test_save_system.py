"""Tests for the save/load system."""
import pytest
import os
import shutil
import json
import glm
from pathlib import Path
from game.save_system import SaveSystem, serialize_game_state, deserialize_game_state
from game.player import Player
from game.inventory import Inventory
from game.quests import QuestManager


class TestSaveSystem:
    """Test the save/load system."""

    @pytest.fixture
    def save_system(self, tmp_path):
        """Create a save system with temporary directory."""
        save_dir = tmp_path / "saves"
        return SaveSystem(str(save_dir))

    @pytest.fixture
    def sample_game_state(self):
        """Create sample game state for testing."""
        return {
            "player": {
                "position": [100.0, 50.0, 200.0],
                "camera_yaw": -90.0,
                "camera_pitch": 0.0,
                "health": 80,
                "max_health": 100,
                "stamina": 90,
                "max_stamina": 100,
                "level": 5,
                "gold": 500,
            },
            "inventory": {
                "equipment_items": [],
                "consumables": [],
                "key_items": [],
                "materials": {"iron_ore": 10, "wood": 20},
            },
            "equipment": {
                "weapon": None,
                "armor": None,
                "accessory": None,
            },
            "progression": {
                "level": 5,
                "xp": 1500,
                "skill_points": 0,
            },
            "quests": {
                "active": [],
                "completed": [],
            },
            "world": {},
            "play_time": 3600.0,
        }

    def test_save_system_initialization(self, save_system):
        """Test save system initializes correctly."""
        assert save_system.save_dir.exists()
        assert save_system.save_dir.is_dir()

    def test_save_game_valid_slot(self, save_system, sample_game_state):
        """Test saving to a valid slot."""
        result = save_system.save_game(1, sample_game_state)
        assert result is True

        save_file = save_system.save_dir / "save_slot_1.json"
        assert save_file.exists()

    def test_save_game_invalid_slot(self, save_system, sample_game_state):
        """Test saving to invalid slots."""
        assert save_system.save_game(0, sample_game_state) is False
        assert save_system.save_game(6, sample_game_state) is False
        assert save_system.save_game(-1, sample_game_state) is False

    def test_load_game_existing_save(self, save_system, sample_game_state):
        """Test loading an existing save."""
        save_system.save_game(2, sample_game_state)
        loaded_state = save_system.load_game(2)

        assert loaded_state is not None
        assert loaded_state["player"]["level"] == 5
        assert loaded_state["player"]["position"] == [100.0, 50.0, 200.0]
        assert loaded_state["player"]["gold"] == 500
        assert loaded_state["play_time"] == 3600.0

    def test_load_game_nonexistent_save(self, save_system):
        """Test loading from empty slot."""
        loaded_state = save_system.load_game(3)
        assert loaded_state is None

    def test_delete_save_existing(self, save_system, sample_game_state):
        """Test deleting an existing save."""
        save_system.save_game(4, sample_game_state)
        assert save_system.delete_save(4) is True

        save_file = save_system.save_dir / "save_slot_4.json"
        assert not save_file.exists()

    def test_delete_save_nonexistent(self, save_system):
        """Test deleting non-existent save."""
        result = save_system.delete_save(5)
        assert result is False

    def test_get_save_info(self, save_system, sample_game_state):
        """Test getting save metadata."""
        save_system.save_game(1, sample_game_state)
        info = save_system.get_save_info(1)

        assert info is not None
        assert "timestamp" in info
        assert "version" in info
        assert info["player_level"] == 5
        assert info["play_time"] == 3600.0

    def test_get_save_info_nonexistent(self, save_system):
        """Test getting info for non-existent save."""
        info = save_system.get_save_info(2)
        assert info is None

    def test_list_saves(self, save_system, sample_game_state):
        """Test listing all saves."""
        save_system.save_game(1, sample_game_state)
        save_system.save_game(3, sample_game_state)

        saves = save_system.list_saves()
        assert len(saves) == 2
        assert 1 in saves
        assert 3 in saves
        assert 2 not in saves

    def test_multiple_slots(self, save_system, sample_game_state):
        """Test using multiple save slots."""
        import copy
        state1 = copy.deepcopy(sample_game_state)
        state2 = copy.deepcopy(sample_game_state)
        state2["player"]["level"] = 10
        state2["player"]["gold"] = 1000

        save_system.save_game(1, state1)
        save_system.save_game(2, state2)

        loaded1 = save_system.load_game(1)
        loaded2 = save_system.load_game(2)

        assert loaded1["player"]["level"] == 5
        assert loaded2["player"]["level"] == 10
        assert loaded1["player"]["gold"] == 500
        assert loaded2["player"]["gold"] == 1000

    def test_overwrite_save(self, save_system, sample_game_state):
        """Test overwriting an existing save."""
        save_system.save_game(1, sample_game_state)

        new_state = sample_game_state.copy()
        new_state["player"]["level"] = 15

        save_system.save_game(1, new_state)
        loaded = save_system.load_game(1)

        assert loaded["player"]["level"] == 15


class TestPlayerSerialization:
    """Test serialization/deserialization of actual Player objects."""

    def test_serialize_player_state(self):
        """Test serializing a real player object."""
        player = Player(position=glm.vec3(100, 50, 200))
        player.camera.yaw = 45.0
        player.camera.pitch = 15.0
        player.stats.current_health = 75
        player.gold = 500
        player.progression.level = 5

        inventory = Inventory()
        inventory.materials = {"iron_ore": 10}
        quest_manager = QuestManager()

        game_state = serialize_game_state(
            player, inventory, quest_manager,
            player.equipment, player.progression,
            {}, 3600.0
        )

        assert game_state["player"]["position"] == [100.0, 50.0, 200.0]
        assert game_state["player"]["camera_yaw"] == 45.0
        assert game_state["player"]["health"] == 75
        assert game_state["player"]["level"] == 5
        assert game_state["player"]["gold"] == 500
        assert game_state["inventory"]["materials"] == {"iron_ore": 10}

    def test_deserialize_to_player(self):
        """Test deserializing into a real player object."""
        game_state = {
            "player": {
                "position": [100.0, 50.0, 200.0],
                "camera_yaw": 45.0,
                "camera_pitch": 15.0,
                "health": 75,
                "max_health": 100,
                "stamina": 90,
                "max_stamina": 100,
                "level": 5,
                "gold": 500,
            },
            "inventory": {
                "equipment_items": [],
                "consumables": [],
                "key_items": [],
                "materials": {"iron_ore": 10},
            },
            "equipment": {"weapon": None, "armor": None, "accessory": None},
            "progression": {"level": 5, "xp": 1500, "skill_points": 0},
            "quests": {"active": [], "completed": []},
            "world": {},
            "play_time": 3600.0,
        }

        player = Player()
        inventory = Inventory()
        quest_manager = QuestManager()

        success, play_time = deserialize_game_state(
            game_state, player, inventory,
            quest_manager, player.equipment, player.progression
        )

        assert success
        assert play_time == 3600.0
        assert player.position.x == 100.0
        assert player.position.y == 50.0
        assert player.position.z == 200.0
        assert player.camera.yaw == 45.0
        assert player.camera.pitch == 15.0
        assert player.stats.current_health == 75
        assert player.gold == 500
        assert inventory.materials == {"iron_ore": 10}

    def test_roundtrip_player_state(self):
        """Test save -> load -> save produces identical data."""
        # Create player with specific state
        player1 = Player(position=glm.vec3(123.456, 78.9, 234.567))
        player1.camera.yaw = 37.5
        player1.camera.pitch = -22.3
        player1.stats.current_health = 67
        player1.gold = 1234

        inventory1 = Inventory()
        inventory1.materials = {"wood": 50, "stone": 30}
        quest_manager1 = QuestManager()

        # Serialize
        state1 = serialize_game_state(
            player1, inventory1, quest_manager1,
            player1.equipment, player1.progression,
            {}, 5432.1
        )

        # Deserialize into new objects
        player2 = Player()
        inventory2 = Inventory()
        quest_manager2 = QuestManager()

        deserialize_game_state(
            state1, player2, inventory2,
            quest_manager2, player2.equipment, player2.progression
        )

        # Serialize again
        state2 = serialize_game_state(
            player2, inventory2, quest_manager2,
            player2.equipment, player2.progression,
            {}, 5432.1
        )

        # States should be identical
        assert state1["player"] == state2["player"]
        assert state1["inventory"] == state2["inventory"]


class TestSaveFileIntegrity:
    """Test handling of corrupted or invalid save files."""

    @pytest.fixture
    def save_system(self, tmp_path):
        save_dir = tmp_path / "saves"
        return SaveSystem(str(save_dir))

    def test_corrupted_json(self, save_system):
        """Test loading a corrupted JSON file."""
        save_file = save_system.save_dir / "save_slot_1.json"
        save_system.save_dir.mkdir(exist_ok=True)

        # Write invalid JSON
        with open(save_file, 'w') as f:
            f.write("{ this is not valid json }")

        # Should return None for corrupted save
        result = save_system.load_game(1)
        assert result is None

    def test_empty_save_file(self, save_system):
        """Test loading an empty save file."""
        save_file = save_system.save_dir / "save_slot_2.json"
        save_system.save_dir.mkdir(exist_ok=True)

        # Write empty file
        with open(save_file, 'w') as f:
            f.write("")

        result = save_system.load_game(2)
        assert result is None

    def test_missing_game_state_key(self, save_system):
        """Test save file missing game_state key."""
        save_file = save_system.save_dir / "save_slot_3.json"
        save_system.save_dir.mkdir(exist_ok=True)

        # Write JSON without game_state
        with open(save_file, 'w') as f:
            json.dump({"metadata": {"version": "1.0.0"}}, f)

        result = save_system.load_game(3)
        # Should return None or empty dict
        assert result is None or result == {}


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def save_system(self, tmp_path):
        save_dir = tmp_path / "saves"
        return SaveSystem(str(save_dir))

    def test_save_with_large_materials_dict(self, save_system):
        """Test saving with many materials."""
        game_state = {
            "player": {
                "position": [0, 0, 0],
                "camera_yaw": 0,
                "camera_pitch": 0,
                "health": 100,
                "max_health": 100,
                "stamina": 100,
                "max_stamina": 100,
                "level": 1,
                "gold": 0,
            },
            "inventory": {
                "equipment_items": [],
                "consumables": [],
                "key_items": [],
                "materials": {f"item_{i}": i for i in range(1000)},  # 1000 items
            },
            "equipment": {"weapon": None, "armor": None, "accessory": None},
            "progression": {"level": 1, "xp": 0, "skill_points": 0},
            "quests": {"active": [], "completed": []},
            "world": {},
            "play_time": 0.0,
        }

        # Should handle large saves
        result = save_system.save_game(1, game_state)
        assert result is True

        loaded = save_system.load_game(1)
        assert loaded is not None
        assert len(loaded["inventory"]["materials"]) == 1000

    def test_save_with_zero_values(self, save_system):
        """Test saving with zero/minimal values."""
        game_state = {
            "player": {
                "position": [0.0, 0.0, 0.0],
                "camera_yaw": 0.0,
                "camera_pitch": 0.0,
                "health": 0,
                "max_health": 1,
                "stamina": 0,
                "max_stamina": 1,
                "level": 1,
                "gold": 0,
            },
            "inventory": {
                "equipment_items": [],
                "consumables": [],
                "key_items": [],
                "materials": {},
            },
            "equipment": {"weapon": None, "armor": None, "accessory": None},
            "progression": {"level": 1, "xp": 0, "skill_points": 0},
            "quests": {"active": [], "completed": []},
            "world": {},
            "play_time": 0.0,
        }

        result = save_system.save_game(1, game_state)
        assert result is True

        loaded = save_system.load_game(1)
        assert loaded["player"]["health"] == 0
        assert loaded["player"]["gold"] == 0

    def test_save_with_negative_values(self, save_system):
        """Test saving with negative camera angles."""
        game_state = {
            "player": {
                "position": [-100.0, -50.0, -200.0],
                "camera_yaw": -180.0,
                "camera_pitch": -90.0,
                "health": 100,
                "max_health": 100,
                "stamina": 100,
                "max_stamina": 100,
                "level": 1,
                "gold": 0,
            },
            "inventory": {
                "equipment_items": [],
                "consumables": [],
                "key_items": [],
                "materials": {},
            },
            "equipment": {"weapon": None, "armor": None, "accessory": None},
            "progression": {"level": 1, "xp": 0, "skill_points": 0},
            "quests": {"active": [], "completed": []},
            "world": {},
            "play_time": 0.0,
        }

        save_system.save_game(1, game_state)
        loaded = save_system.load_game(1)

        assert loaded["player"]["position"] == [-100.0, -50.0, -200.0]
        assert loaded["player"]["camera_yaw"] == -180.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
