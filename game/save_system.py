"""Save/Load system for persisting game state."""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from game.equipment import EquipmentSlot
from game.logger import get_logger
from game.input_validation import validate_slot_number, ValidationError

logger = get_logger(__name__)

# Current save format version
CURRENT_SAVE_VERSION = "1.0.0"


class SaveDataValidator:
    """Validates save data format and handles version migrations."""

    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> bool:
        """
        Validate save metadata structure.

        Args:
            metadata: Metadata dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_keys = ["timestamp", "slot", "version"]

        for key in required_keys:
            if key not in metadata:
                logger.error(f"Missing required metadata key: {key}")
                return False

        # Validate types
        if not isinstance(metadata["slot"], int):
            logger.error(f"Invalid metadata slot type: {type(metadata['slot'])}")
            return False

        if not isinstance(metadata["version"], str):
            logger.error(f"Invalid metadata version type: {type(metadata['version'])}")
            return False

        # Validate slot range
        if metadata["slot"] < 1 or metadata["slot"] > 5:
            logger.error(f"Invalid metadata slot value: {metadata['slot']}")
            return False

        return True

    @staticmethod
    def validate_game_state(game_state: Dict[str, Any]) -> bool:
        """
        Validate game state structure.

        Args:
            game_state: Game state dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_sections = ["player", "inventory", "equipment", "progression", "quests", "world", "play_time"]

        for section in required_sections:
            if section not in game_state:
                logger.error(f"Missing required game state section: {section}")
                return False

        # Validate player section
        player = game_state["player"]
        player_keys = ["position", "camera_yaw", "camera_pitch", "health", "max_health",
                       "stamina", "max_stamina", "level", "gold"]
        for key in player_keys:
            if key not in player:
                logger.error(f"Missing required player key: {key}")
                return False

        # Validate position is a list of 3 numbers
        if not isinstance(player["position"], list) or len(player["position"]) != 3:
            logger.error(f"Invalid player position format: {player['position']}")
            return False

        # Validate numeric fields
        numeric_fields = {
            "health": (int, float),
            "max_health": (int, float),
            "stamina": (int, float),
            "max_stamina": (int, float),
            "level": int,
            "gold": int,
            "camera_yaw": (int, float),
            "camera_pitch": (int, float)
        }

        for field, expected_types in numeric_fields.items():
            if not isinstance(player[field], expected_types):
                logger.error(f"Invalid player {field} type: {type(player[field])}")
                return False

        # Validate inventory section
        inventory = game_state["inventory"]
        inventory_keys = ["equipment_items", "consumables", "key_items", "materials"]
        for key in inventory_keys:
            if key not in inventory:
                logger.error(f"Missing required inventory key: {key}")
                return False

        # Validate inventory lists
        if not isinstance(inventory["equipment_items"], list):
            logger.error(f"Invalid equipment_items type: {type(inventory['equipment_items'])}")
            return False
        if not isinstance(inventory["consumables"], list):
            logger.error(f"Invalid consumables type: {type(inventory['consumables'])}")
            return False
        if not isinstance(inventory["key_items"], list):
            logger.error(f"Invalid key_items type: {type(inventory['key_items'])}")
            return False
        if not isinstance(inventory["materials"], dict):
            logger.error(f"Invalid materials type: {type(inventory['materials'])}")
            return False

        # Validate equipment section
        equipment = game_state["equipment"]
        equipment_slots = ["weapon", "armor", "accessory"]
        for slot in equipment_slots:
            if slot not in equipment:
                logger.error(f"Missing required equipment slot: {slot}")
                return False

        # Validate progression section
        progression = game_state["progression"]
        progression_keys = ["level", "xp", "skill_points"]
        for key in progression_keys:
            if key not in progression:
                logger.error(f"Missing required progression key: {key}")
                return False

        # Validate progression numeric fields
        if not isinstance(progression["level"], int):
            logger.error(f"Invalid progression level type: {type(progression['level'])}")
            return False
        if not isinstance(progression["xp"], int):
            logger.error(f"Invalid progression xp type: {type(progression['xp'])}")
            return False
        if not isinstance(progression["skill_points"], int):
            logger.error(f"Invalid progression skill_points type: {type(progression['skill_points'])}")
            return False

        # Validate quests section
        quests = game_state["quests"]
        if "active" not in quests or "completed" not in quests:
            logger.error("Missing required quests keys: active or completed")
            return False
        if not isinstance(quests["active"], list):
            logger.error(f"Invalid quests active type: {type(quests['active'])}")
            return False
        if not isinstance(quests["completed"], list):
            logger.error(f"Invalid quests completed type: {type(quests['completed'])}")
            return False

        # Validate play_time
        if not isinstance(game_state["play_time"], (int, float)):
            logger.error(f"Invalid play_time type: {type(game_state['play_time'])}")
            return False

        return True

    @staticmethod
    def migrate_save_data(save_data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Migrate save data from one version to another.

        Args:
            save_data: Save data to migrate
            from_version: Current version of save data
            to_version: Target version to migrate to

        Returns:
            Migrated save data
        """
        logger.info(f"Migrating save data from version {from_version} to {to_version}")

        # Currently only one version, so no migrations needed
        # Future migrations would be handled here
        # Example:
        # if from_version == "1.0.0" and to_version == "1.1.0":
        #     save_data = SaveDataValidator._migrate_1_0_to_1_1(save_data)

        # Update version in metadata
        save_data["metadata"]["version"] = to_version

        return save_data


class SaveSystem:
    """Manages saving and loading game state."""

    def __init__(self, save_dir: str = "saves") -> None:
        """
        Initialize the save system.

        Args:
            save_dir: Directory to store save files
        """
        self.save_dir: Path = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        logger.info(f"SaveSystem initialized (save directory: {self.save_dir})")

    def save_game(self, slot: int, game_state: Dict[str, Any]) -> bool:
        """
        Save game state to a slot.

        Args:
            slot: Save slot number (1-5)
            game_state: Dictionary containing all game state to save

        Returns:
            True if save successful, False otherwise
        """
        # Validate slot number
        try:
            slot = validate_slot_number(slot)
        except ValidationError as e:
            logger.error(f"Invalid save slot: {e}")
            return False

        try:
            # Validate game state before saving
            if not SaveDataValidator.validate_game_state(game_state):
                logger.error(f"Invalid game state structure, cannot save to slot {slot}")
                return False

            # Add metadata
            save_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "slot": slot,
                    "version": CURRENT_SAVE_VERSION
                },
                "game_state": game_state
            }

            # Validate metadata
            if not SaveDataValidator.validate_metadata(save_data["metadata"]):
                logger.error(f"Invalid metadata structure, cannot save to slot {slot}")
                return False

            # Save to file
            save_file = self.save_dir / f"save_slot_{slot}.json"
            with open(save_file, 'w') as f:
                json.dump(save_data, f, indent=2)

            logger.info(f"Game saved to slot {slot}: {save_file}")
            return True

        except (IOError, OSError) as e:
            logger.error(f"Failed to write save file to slot {slot}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize game state for slot {slot}: {e}")
            return False

    def load_game(self, slot: int) -> Optional[Dict[str, Any]]:
        """
        Load game state from a slot.

        Args:
            slot: Save slot number (1-5)

        Returns:
            Game state dictionary if successful, None otherwise
        """
        # Validate slot number
        try:
            slot = validate_slot_number(slot)
        except ValidationError as e:
            logger.error(f"Invalid load slot: {e}")
            return None

        try:
            save_file = self.save_dir / f"save_slot_{slot}.json"

            if not save_file.exists():
                logger.warning(f"No save file found in slot {slot}")
                return None

            with open(save_file, 'r') as f:
                save_data = json.load(f)

            # Validate metadata
            metadata = save_data.get("metadata", {})
            if not SaveDataValidator.validate_metadata(metadata):
                logger.error(f"Invalid save metadata in slot {slot}")
                return None

            # Check version and migrate if needed
            save_version = metadata.get("version", "1.0.0")
            if save_version != CURRENT_SAVE_VERSION:
                logger.info(f"Save file version {save_version} differs from current {CURRENT_SAVE_VERSION}")
                save_data = SaveDataValidator.migrate_save_data(save_data, save_version, CURRENT_SAVE_VERSION)

            # Validate game state
            game_state = save_data.get("game_state")
            if game_state is None:
                logger.error(f"No game_state found in save file for slot {slot}")
                return None

            if not SaveDataValidator.validate_game_state(game_state):
                logger.error(f"Invalid game state structure in slot {slot}")
                return None

            logger.info(f"Game loaded from slot {slot}: {save_file}")
            return game_state

        except (IOError, OSError) as e:
            logger.error(f"Failed to read save file from slot {slot}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted save file in slot {slot}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Invalid save file format in slot {slot}, missing key: {e}")
            return None

    def delete_save(self, slot: int) -> bool:
        """
        Delete a save file.

        Args:
            slot: Save slot number (1-5)

        Returns:
            True if deletion successful, False otherwise
        """
        # Validate slot number
        try:
            slot = validate_slot_number(slot)
        except ValidationError as e:
            logger.error(f"Invalid delete slot: {e}")
            return False

        try:
            save_file = self.save_dir / f"save_slot_{slot}.json"

            if save_file.exists():
                save_file.unlink()
                logger.info(f"Deleted save file in slot {slot}")
                return True
            else:
                logger.warning(f"No save file to delete in slot {slot}")
                return False

        except (IOError, OSError, PermissionError) as e:
            logger.error(f"Failed to delete save in slot {slot}: {e}")
            return False

    def get_save_info(self, slot: int) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a save file without loading full game state.

        Args:
            slot: Save slot number (1-5)

        Returns:
            Save metadata if file exists, None otherwise
        """
        # Validate slot number
        try:
            slot = validate_slot_number(slot)
        except ValidationError:
            return None

        try:
            save_file = self.save_dir / f"save_slot_{slot}.json"

            if not save_file.exists():
                return None

            with open(save_file, 'r') as f:
                save_data = json.load(f)

            # Return metadata and basic player info
            metadata = save_data.get("metadata", {})
            game_state = save_data.get("game_state", {})

            return {
                "timestamp": metadata.get("timestamp"),
                "version": metadata.get("version"),
                "player_level": game_state.get("player", {}).get("level", 1),
                "player_position": game_state.get("player", {}).get("position", [0, 0, 0]),
                "play_time": game_state.get("play_time", 0),
            }

        except (IOError, OSError) as e:
            logger.error(f"Failed to read save file for slot {slot}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted save file in slot {slot}: {e}")
            return None

    def list_saves(self) -> Dict[int, Dict[str, Any]]:
        """
        List all available save files with their metadata.

        Returns:
            Dictionary mapping slot numbers to save metadata
        """
        saves = {}
        for slot in range(1, 6):
            info = self.get_save_info(slot)
            if info:
                saves[slot] = info
        return saves


def serialize_game_state(player, inventory, quest_manager, equipment,
                         progression, world_state, play_time: float) -> Dict[str, Any]:
    """
    Serialize complete game state for saving.

    Args:
        player: Player object
        inventory: Inventory object
        quest_manager: QuestManager object
        equipment: Equipment object
        progression: Progression object
        world_state: Dictionary of world state (discovered POIs, etc.)
        play_time: Total play time in seconds

    Returns:
        Dictionary containing all serializable game state
    """
    return {
        "player": {
            "position": [player.position.x, player.position.y, player.position.z],
            "camera_yaw": player.camera.yaw,
            "camera_pitch": player.camera.pitch,
            "health": player.stats.current_health,
            "max_health": player.stats.max_health,
            "stamina": player.stats.current_stamina,
            "max_stamina": player.stats.max_stamina,
            "level": player.progression.level,
            "gold": player.gold,
        },
        "inventory": {
            "equipment_items": [item.item_id for item in inventory.equipment_items],
            "consumables": inventory.consumables,
            "key_items": inventory.key_items,
            "materials": inventory.materials,
        },
        "equipment": {
            "weapon": equipment.slots[EquipmentSlot.WEAPON].id if equipment.slots.get(EquipmentSlot.WEAPON) else None,
            "armor": equipment.slots[EquipmentSlot.ARMOR].id if equipment.slots.get(EquipmentSlot.ARMOR) else None,
            "accessory": equipment.slots[EquipmentSlot.ACCESSORY].id if equipment.slots.get(EquipmentSlot.ACCESSORY) else None,
        },
        "progression": {
            "level": progression.level,
            "xp": progression.xp,
            "skill_points": progression.skill_points if hasattr(progression, 'skill_points') else 0,
        },
        "quests": {
            "active": [
                {
                    "quest_id": quest.quest_id,
                    "objectives_completed": [obj.completed for obj in quest.objectives]
                }
                for quest in quest_manager.get_active_quests()
            ],
            "completed": [quest.quest_id for quest in quest_manager.get_completed_quests()],
        },
        "world": world_state,
        "play_time": play_time,
    }


def deserialize_game_state(game_state: Dict[str, Any], player, inventory,
                           quest_manager, equipment, progression):
    """
    Restore game state from saved data.

    Args:
        game_state: Saved game state dictionary
        player: Player object to restore
        inventory: Inventory object to restore
        quest_manager: QuestManager object to restore
        equipment: Equipment object to restore
        progression: Progression object to restore

    Returns:
        Tuple of (success: bool, play_time: float)
    """
    try:
        # Restore player state
        player_data = game_state.get("player", {})
        player.position.x = player_data.get("position", [0, 15, 0])[0]
        player.position.y = player_data.get("position", [0, 15, 0])[1]
        player.position.z = player_data.get("position", [0, 15, 0])[2]
        player.camera.yaw = player_data.get("camera_yaw", -90.0)
        player.camera.pitch = player_data.get("camera_pitch", 0.0)
        player.camera.update_camera_vectors()
        player.stats.current_health = player_data.get("health", 100)
        player.stats.max_health = player_data.get("max_health", 100)
        player.stats.current_stamina = player_data.get("stamina", 100)
        player.stats.max_stamina = player_data.get("max_stamina", 100)
        player.progression.level = player_data.get("level", 1)
        player.gold = player_data.get("gold", 0)

        # Restore inventory
        inventory_data = game_state.get("inventory", {})
        inventory.equipment_items = []  # Clear existing items
        inventory.consumables = inventory_data.get("consumables", [])
        inventory.key_items = inventory_data.get("key_items", [])
        inventory.materials = inventory_data.get("materials", {})
        # Note: Equipment items would need to be recreated from item database

        # Restore equipment
        equipment_data = game_state.get("equipment", {})
        # Note: Equipment items would need to be recreated from item database

        # Restore progression
        progression_data = game_state.get("progression", {})
        progression.level = progression_data.get("level", 1)
        progression.xp = progression_data.get("xp", 0)

        # Restore quests
        # Note: Quest restoration would need quest definitions

        play_time = game_state.get("play_time", 0)

        logger.info("Game state restored successfully")
        return True, play_time

    except (KeyError, IndexError) as e:
        logger.error(f"Invalid game state data format: {e}")
        return False, 0.0
    except (AttributeError, TypeError) as e:
        logger.error(f"Failed to restore game objects: {e}")
        return False, 0.0
