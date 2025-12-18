"""Object interaction system."""
import glm
from game.logger import get_logger

logger = get_logger(__name__)


class InteractionSystem:
    """Manages player interactions with objects."""

    def __init__(self, max_distance=5.0, inventory=None, sound_manager=None, journal=None):
        """
        Initialize the interaction system.

        Args:
            max_distance: Maximum interaction distance in meters
            inventory: Player inventory system
            sound_manager: Sound manager for audio feedback
            journal: Journal system for tracking objectives
        """
        self.max_distance = max_distance
        self.looking_at = None
        self.inventory = inventory
        self.sound_manager = sound_manager
        self.journal = journal

    def update(self, player_position, player_forward, entities):
        """
        Update what the player is looking at using raycasting.

        Args:
            player_position: Player's eye position (glm.vec3)
            player_forward: Player's forward vector (glm.vec3)
            entities: List of entities to check

        Returns:
            Entity or None: The entity the player is looking at
        """
        self.looking_at = None
        closest_distance = self.max_distance
        closest_entity = None

        # Raycast against all entities
        for entity in entities:
            if not entity.interactable or (hasattr(entity, 'collected') and entity.collected):
                continue

            # Simple sphere-ray intersection for now
            to_entity = entity.position - player_position
            distance = glm.length(to_entity)

            if distance > self.max_distance:
                continue

            # Check if entity is in front of player
            to_entity_normalized = glm.normalize(to_entity)
            dot = glm.dot(player_forward, to_entity_normalized)

            # Entity must be within a cone in front of player
            if dot > 0.95:  # Approximately 18-degree cone
                if distance < closest_distance:
                    closest_distance = distance
                    closest_entity = entity

        self.looking_at = closest_entity
        return self.looking_at

    def interact(self):
        """
        Interact with the object the player is looking at.

        Returns:
            bool: True if an interaction occurred
        """
        if self.looking_at:
            # Handle collectibles
            if hasattr(self.looking_at, 'collect'):
                self.looking_at.collect()
                item_name = self.looking_at.name

                if self.inventory:
                    self.inventory.add_item(item_name)

                if self.sound_manager:
                    self.sound_manager.play('collect')

                # Update journal
                if self.journal:
                    # Update collect gems objective
                    collect_obj = self.journal.get_objective("collect_gems")
                    if collect_obj:
                        collect_obj.progress += 1
                        if collect_obj.progress >= collect_obj.progress_max:
                            collect_obj.complete()

                    # Discover lore based on item
                    lore_map = {
                        "Golden Orb": "golden_orb",
                        "Crystal Shard": "crystal_shard",
                        "Secret Gem": "secret_gem"
                    }
                    if item_name in lore_map:
                        self.journal.discover_lore(lore_map[item_name])

                return True

            # Handle puzzle elements (levers, buttons, doors, etc.)
            if hasattr(self.looking_at, 'interact'):
                # Get the type for sound selection
                entity_type = type(self.looking_at).__name__.lower()
                entity_name = self.looking_at.name
                self.looking_at.interact()

                # Play appropriate sound
                if self.sound_manager:
                    if 'lever' in entity_type:
                        self.sound_manager.play('lever')
                    elif 'button' in entity_type:
                        self.sound_manager.play('button')
                    elif 'door' in entity_type:
                        self.sound_manager.play('door_open')

                # Update journal for door openings
                if self.journal and 'door' in entity_type:
                    puzzle_obj = self.journal.get_objective("solve_puzzles")
                    if puzzle_obj and hasattr(self.looking_at, 'state') and self.looking_at.state == "open":
                        # Map door names to sub-task indices
                        door_task_map = {
                            "Main Door": 0,
                            "Side Door": 1,
                            "Timed Door": 2,
                            "Secret Door": 3
                        }
                        if entity_name in door_task_map:
                            task_index = door_task_map[entity_name]
                            puzzle_obj.complete_sub_task(task_index)

                            # Discover related lore
                            if entity_name == "Main Door":
                                self.journal.discover_lore("ruins_history")
                                self.journal.discover_lore("door_mechanisms")
                            elif entity_name == "Secret Door":
                                self.journal.discover_lore("sequence_puzzle")

                return True

            # Generic interaction
            logger.debug(f"Interacting with: {self.looking_at.name}")
            return True

        return False
