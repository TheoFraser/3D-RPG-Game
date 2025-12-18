"""Sequence puzzle system - activate elements in correct order."""
from game.puzzles import PuzzleElement
import glm
from game.logger import get_logger

logger = get_logger(__name__)


class SequencePuzzle:
    """A puzzle that requires activating elements in a specific order."""

    def __init__(self, name="Sequence Puzzle"):
        """Initialize sequence puzzle."""
        self.name = name
        self.sequence = []  # List of element references in correct order
        self.current_index = 0
        self.completed = False
        self.connected_elements = []

    def add_to_sequence(self, element):
        """Add an element to the required sequence."""
        self.sequence.append(element)
        # Store original interact method
        if not hasattr(element, '_original_interact'):
            element._original_interact = element.interact
            # Replace interact method with properly captured closure
            # Use default argument to capture 'element' value (not reference)
            element.interact = lambda e=element: self.on_element_activated(e)

    def connect_to(self, element):
        """Connect elements that activate when sequence completes."""
        self.connected_elements.append(element)

    def on_element_activated(self, element):
        """Called when a sequence element is activated."""
        # Call original interact first
        if hasattr(element, '_original_interact'):
            element._original_interact()

        if self.completed:
            return

        expected = self.sequence[self.current_index]
        if element == expected:
            self.current_index += 1
            logger.info(f"{self.name}: {self.current_index}/{len(self.sequence)} correct")

            if self.current_index >= len(self.sequence):
                self.complete()
        else:
            # Wrong order - reset
            logger.info(f"{self.name}: Wrong order! Resetting...")
            self.reset()

    def complete(self):
        """Called when sequence is completed successfully."""
        self.completed = True
        logger.info(f"{self.name}: COMPLETED!")

        # Activate all connected elements
        for element in self.connected_elements:
            if hasattr(element, 'on_triggered'):
                element.on_triggered(self)
            elif hasattr(element, 'unlock'):
                element.unlock()

    def reset(self):
        """Reset the sequence progress."""
        self.current_index = 0

    def get_progress(self):
        """Get current progress string."""
        return f"{self.current_index}/{len(self.sequence)}"


class ColoredButton(PuzzleElement):
    """A colored button for sequence puzzles."""

    def __init__(self, position, color_name, color_rgb, name=None):
        """
        Create a colored button.

        Args:
            position: World position
            color_name: Name of color (e.g., "Red")
            color_rgb: RGB color tuple (e.g., (1.0, 0.0, 0.0))
            name: Optional custom name
        """
        if name is None:
            name = f"{color_name} Button"
        super().__init__(position, name)
        self.color_name = color_name
        self.color = color_rgb
        self.description = f"A {color_name.lower()} button."
        self.scale = glm.vec3(0.6, 0.3, 0.6)

        # Store original position to prevent floating point drift
        self.base_position = glm.vec3(position)
        self.pressed_offset = -0.15

    def interact(self):
        """Press the colored button."""
        logger.debug(f"{self.name} pressed!")
        self.activate()

    def on_activate(self):
        """Visual feedback."""
        self.position = glm.vec3(self.base_position.x,
                                 self.base_position.y + self.pressed_offset,
                                 self.base_position.z)

    def on_deactivate(self):
        """Reset visual."""
        self.position = glm.vec3(self.base_position)
