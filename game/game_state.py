"""Game state management."""
from enum import Enum
from game.logger import get_logger

logger = get_logger(__name__)


class GameState(Enum):
    """Game states."""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    INVENTORY = "inventory"
    EQUIPMENT = "equipment"  # Phase 5: Equipment and stats
    MAP = "map"
    JOURNAL = "journal"
    DIALOGUE = "dialogue"  # Phase 5: Talking to NPCs
    QUEST_LOG = "quest_log"  # Phase 5: Viewing quests


class StateManager:
    """Manages game state transitions."""

    def __init__(self):
        """Initialize state manager."""
        self.current_state = GameState.PLAYING
        self.previous_state = None

    def set_state(self, new_state):
        """Change game state."""
        if new_state != self.current_state:
            self.previous_state = self.current_state
            self.current_state = new_state
            logger.debug(f"State: {self.previous_state.value} -> {self.current_state.value}")

    def toggle_pause(self):
        """Toggle between playing and paused."""
        if self.current_state == GameState.PLAYING:
            self.set_state(GameState.PAUSED)
            return True
        elif self.current_state == GameState.PAUSED:
            self.set_state(GameState.PLAYING)
            return False
        return self.is_paused()

    def is_paused(self):
        """Check if game is paused."""
        return self.current_state == GameState.PAUSED

    def is_playing(self):
        """Check if game is in play state."""
        return self.current_state == GameState.PLAYING

    def can_move(self):
        """Check if player can move."""
        return self.current_state == GameState.PLAYING
