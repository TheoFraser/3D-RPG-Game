"""Dialogue system for NPC conversations."""
import json
from enum import Enum
from typing import Dict, List, Optional, Callable
from game.logger import get_logger

logger = get_logger(__name__)


class DialogueNodeType(Enum):
    """Types of dialogue nodes."""
    TEXT = "text"           # Display text
    CHOICE = "choice"       # Player makes a choice
    QUEST_START = "quest_start"  # Start a quest
    QUEST_CHECK = "quest_check"  # Check quest completion
    CONDITION = "condition"  # Check game state condition
    END = "end"            # End dialogue


class DialogueNode:
    """A single node in a dialogue tree."""

    def __init__(self, node_id, node_type=DialogueNodeType.TEXT, text="", speaker=""):
        """
        Create a dialogue node.

        Args:
            node_id: Unique identifier for this node
            node_type: Type of node (DialogueNodeType)
            text: Dialogue text to display
            speaker: Name of who's speaking
        """
        self.node_id = node_id
        self.node_type = node_type
        self.text = text
        self.speaker = speaker

        # Navigation
        self.next_node = None  # ID of next node (for TEXT nodes)
        self.choices = []  # List of (choice_text, next_node_id) for CHOICE nodes

        # Quest-related
        self.quest_id = None

        # Conditions
        self.condition_func = None  # Function that returns bool
        self.condition_true = None  # Node if condition is true
        self.condition_false = None  # Node if condition is false

        # Callbacks
        self.on_enter = None  # Called when entering this node
        self.on_exit = None  # Called when leaving this node

    def add_choice(self, choice_text, next_node_id):
        """
        Add a choice option.

        Args:
            choice_text: Text to display for this choice
            next_node_id: ID of node to go to if chosen
        """
        self.choices.append((choice_text, next_node_id))

    def set_condition(self, condition_func, true_node, false_node):
        """
        Set a condition for branching dialogue.

        Args:
            condition_func: Function that returns bool
            true_node: Node ID if condition is true
            false_node: Node ID if condition is false
        """
        self.condition_func = condition_func
        self.condition_true = true_node
        self.condition_false = false_node


class DialogueTree:
    """A complete dialogue tree for an NPC."""

    def __init__(self, dialogue_id, npc_name="NPC"):
        """
        Create a dialogue tree.

        Args:
            dialogue_id: Unique identifier for this dialogue
            npc_name: Name of NPC who uses this dialogue
        """
        self.dialogue_id = dialogue_id
        self.npc_name = npc_name
        self.nodes = {}  # node_id -> DialogueNode
        self.start_node = None  # ID of starting node
        self.current_node = None  # Current node in conversation

    def add_node(self, node):
        """
        Add a node to the dialogue tree.

        Args:
            node: DialogueNode instance

        Returns:
            str: Node ID
        """
        self.nodes[node.node_id] = node
        if self.start_node is None:
            self.start_node = node.node_id
        return node.node_id

    def start(self):
        """Start the dialogue at the beginning."""
        self.current_node = self.start_node
        node = self.get_current_node()
        if node and node.on_enter:
            node.on_enter()
        return node

    def get_current_node(self):
        """Get the current dialogue node."""
        if self.current_node:
            return self.nodes.get(self.current_node)
        return None

    def advance(self, choice_index=0):
        """
        Advance to the next dialogue node.

        Args:
            choice_index: If current node has choices, index of chosen option

        Returns:
            DialogueNode or None: Next node, or None if dialogue ended
        """
        current = self.get_current_node()
        if not current:
            return None

        # Call exit callback
        if current.on_exit:
            current.on_exit()

        next_id = None

        # Determine next node based on type
        if current.node_type == DialogueNodeType.TEXT:
            next_id = current.next_node

        elif current.node_type == DialogueNodeType.CHOICE:
            if 0 <= choice_index < len(current.choices):
                next_id = current.choices[choice_index][1]

        elif current.node_type == DialogueNodeType.CONDITION:
            if current.condition_func and current.condition_func():
                next_id = current.condition_true
            else:
                next_id = current.condition_false

        elif current.node_type == DialogueNodeType.QUEST_START:
            next_id = current.next_node

        elif current.node_type == DialogueNodeType.QUEST_CHECK:
            next_id = current.next_node

        elif current.node_type == DialogueNodeType.END:
            self.current_node = None
            return None

        # Move to next node
        if next_id and next_id in self.nodes:
            self.current_node = next_id
            node = self.nodes[next_id]
            if node.on_enter:
                node.on_enter()
            return node
        else:
            self.current_node = None
            return None

    def reset(self):
        """Reset dialogue to the beginning."""
        self.current_node = self.start_node

    @staticmethod
    def from_dict(data):
        """
        Create a dialogue tree from a dictionary.

        Args:
            data: Dictionary with dialogue data

        Returns:
            DialogueTree
        """
        tree = DialogueTree(
            dialogue_id=data.get("id", "unknown"),
            npc_name=data.get("npc_name", "NPC")
        )

        # Create all nodes
        for node_data in data.get("nodes", []):
            node_type = DialogueNodeType(node_data.get("type", "text"))
            node = DialogueNode(
                node_id=node_data.get("id"),
                node_type=node_type,
                text=node_data.get("text", ""),
                speaker=node_data.get("speaker", data.get("npc_name", "NPC"))
            )

            # Set next node
            if "next" in node_data:
                node.next_node = node_data["next"]

            # Add choices
            for choice_data in node_data.get("choices", []):
                node.add_choice(choice_data["text"], choice_data["next"])

            # Quest data
            if "quest_id" in node_data:
                node.quest_id = node_data["quest_id"]

            tree.add_node(node)

        # Set start node
        if "start" in data:
            tree.start_node = data["start"]

        return tree


class DialogueManager:
    """Manages all dialogue trees in the game."""

    def __init__(self):
        """Initialize dialogue manager."""
        self.dialogues = {}  # dialogue_id -> DialogueTree
        self.active_dialogue = None  # Currently active dialogue

    def register_dialogue(self, dialogue_tree):
        """
        Register a dialogue tree.

        Args:
            dialogue_tree: DialogueTree instance

        Returns:
            str: Dialogue ID
        """
        self.dialogues[dialogue_tree.dialogue_id] = dialogue_tree
        return dialogue_tree.dialogue_id

    @staticmethod
    def validate_dialogue_data(dialogue_data):
        """
        Validate dialogue JSON structure.

        Args:
            dialogue_data: Dictionary with dialogue data

        Raises:
            ValueError: If dialogue structure is invalid
        """
        # Check required top-level keys
        required_keys = ["id", "npc_name", "nodes"]
        missing_keys = [key for key in required_keys if key not in dialogue_data]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")

        # Validate dialogue ID
        if not isinstance(dialogue_data["id"], str) or not dialogue_data["id"]:
            raise ValueError(f"Invalid dialogue ID: {dialogue_data.get('id')}")

        # Validate nodes
        nodes = dialogue_data.get("nodes", [])
        if not isinstance(nodes, list) or len(nodes) == 0:
            raise ValueError(f"Dialogue '{dialogue_data['id']}' must have at least one node")

        # Validate each node
        valid_types = ["text", "choice", "quest_start", "quest_check", "condition", "end"]
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                raise ValueError(f"Node {i} must be a dictionary")

            if "id" not in node:
                raise ValueError(f"Node {i} missing required 'id' field")

            node_type = node.get("type", "text")
            if node_type not in valid_types:
                raise ValueError(f"Node '{node['id']}' has invalid type: {node_type}")

            # Validate choice nodes have choices
            if node_type == "choice" and "choices" not in node:
                raise ValueError(f"Choice node '{node['id']}' must have 'choices' field")

        # Validate start node exists
        if "start" in dialogue_data:
            start_id = dialogue_data["start"]
            node_ids = [node["id"] for node in nodes]
            if start_id not in node_ids:
                raise ValueError(f"Start node '{start_id}' not found in nodes")

    def load_dialogues_from_json(self, filepath):
        """
        Load multiple dialogues from a JSON file with validation.

        Args:
            filepath: Path to JSON file

        Returns:
            int: Number of dialogues loaded

        Raises:
            ValueError: If JSON structure is invalid
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for dialogue_data in data.get("dialogues", []):
                # Validate dialogue structure
                try:
                    self.validate_dialogue_data(dialogue_data)
                except ValueError as e:
                    logger.warning(f"Validation error in dialogue: {e}")
                    continue  # Skip invalid dialogue

                tree = DialogueTree.from_dict(dialogue_data)
                self.register_dialogue(tree)
                count += 1

            return count
        except FileNotFoundError as e:
            logger.error(f"Dialogue file not found: {filepath}")
            return 0
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {filepath}: {e}")
            return 0
        except (IOError, OSError) as e:
            logger.error(f"Error reading dialogue file {filepath}: {e}")
            return 0
        except (KeyError, ValueError, AttributeError) as e:
            logger.error(f"Invalid dialogue structure in {filepath}: {e}")
            return 0

    def start_dialogue(self, dialogue_id):
        """
        Start a dialogue.

        Args:
            dialogue_id: ID of dialogue to start

        Returns:
            DialogueNode or None: First node, or None if dialogue not found
        """
        if dialogue_id in self.dialogues:
            self.active_dialogue = self.dialogues[dialogue_id]
            return self.active_dialogue.start()
        return None

    def get_current_node(self):
        """Get the current dialogue node."""
        if self.active_dialogue:
            return self.active_dialogue.get_current_node()
        return None

    def advance_dialogue(self, choice_index=0):
        """
        Advance the current dialogue.

        Args:
            choice_index: Index of chosen option (for choice nodes)

        Returns:
            DialogueNode or None: Next node, or None if dialogue ended
        """
        if self.active_dialogue:
            node = self.active_dialogue.advance(choice_index)
            if node is None:
                # Dialogue ended
                self.end_dialogue()
            return node
        return None

    def end_dialogue(self):
        """End the current dialogue."""
        if self.active_dialogue:
            self.active_dialogue.reset()
        self.active_dialogue = None

    def is_dialogue_active(self):
        """Check if a dialogue is currently active."""
        return self.active_dialogue is not None

    def create_simple_dialogue(self, dialogue_id, npc_name, messages):
        """
        Create a simple linear dialogue.

        Args:
            dialogue_id: Unique ID for this dialogue
            npc_name: Name of NPC
            messages: List of message strings

        Returns:
            DialogueTree
        """
        tree = DialogueTree(dialogue_id, npc_name)

        prev_node = None
        for i, message in enumerate(messages):
            node_id = f"{dialogue_id}_node_{i}"
            node = DialogueNode(
                node_id=node_id,
                node_type=DialogueNodeType.TEXT,
                text=message,
                speaker=npc_name
            )

            # Link to previous node
            if prev_node:
                prev_node.next_node = node_id

            tree.add_node(node)
            prev_node = node

        # Last node ends dialogue
        if prev_node:
            prev_node.node_type = DialogueNodeType.END

        self.register_dialogue(tree)
        return tree

    def create_choice_dialogue(self, dialogue_id, npc_name, greeting, choices):
        """
        Create a dialogue with choices.

        Args:
            dialogue_id: Unique ID
            npc_name: NPC name
            greeting: Initial greeting text
            choices: List of (choice_text, response_text)

        Returns:
            DialogueTree
        """
        tree = DialogueTree(dialogue_id, npc_name)

        # Greeting node
        greeting_node = DialogueNode(
            node_id=f"{dialogue_id}_greeting",
            node_type=DialogueNodeType.TEXT,
            text=greeting,
            speaker=npc_name
        )
        greeting_node.next_node = f"{dialogue_id}_choice"
        tree.add_node(greeting_node)

        # Choice node
        choice_node = DialogueNode(
            node_id=f"{dialogue_id}_choice",
            node_type=DialogueNodeType.CHOICE,
            text="What would you like to say?",
            speaker="Player"
        )

        # Create response nodes for each choice
        for i, (choice_text, response_text) in enumerate(choices):
            response_id = f"{dialogue_id}_response_{i}"
            response_node = DialogueNode(
                node_id=response_id,
                node_type=DialogueNodeType.END,
                text=response_text,
                speaker=npc_name
            )
            tree.add_node(response_node)
            choice_node.add_choice(choice_text, response_id)

        tree.add_node(choice_node)

        self.register_dialogue(tree)
        return tree
