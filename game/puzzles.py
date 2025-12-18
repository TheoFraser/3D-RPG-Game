"""Puzzle mechanics and logic."""
import glm
from game.entities import Entity
from game.logger import get_logger

logger = get_logger(__name__)


class PuzzleElement(Entity):
    """Base class for puzzle elements."""

    def __init__(self, position, name="Puzzle Element"):
        super().__init__(position, name)
        self.state = "inactive"
        self.connected_elements = []
        self.interactable = True

    def connect_to(self, element):
        """Connect this element to another."""
        if element not in self.connected_elements:
            self.connected_elements.append(element)

    def activate(self):
        """Activate this element."""
        if self.state != "active":
            self.state = "active"
            self.on_activate()
            # Trigger connected elements
            for element in self.connected_elements:
                element.on_triggered(self)

    def deactivate(self):
        """Deactivate this element."""
        if self.state != "inactive":
            self.state = "inactive"
            self.on_deactivate()

    def on_activate(self):
        """Called when element is activated (override in subclasses)."""
        pass

    def on_deactivate(self):
        """Called when element is deactivated (override in subclasses)."""
        pass

    def on_triggered(self, source):
        """Called when a connected element triggers this one."""
        pass


class Lever(PuzzleElement):
    """A lever that can be pulled to activate/deactivate."""

    def __init__(self, position, name="Lever"):
        super().__init__(position, name)
        self.description = "A lever. Press E to pull."
        self.scale = glm.vec3(0.3, 0.8, 0.3)

    def interact(self):
        """Toggle the lever."""
        if self.state == "inactive":
            self.activate()
            logger.debug(f"{self.name} activated!")
        else:
            self.deactivate()
            logger.debug(f"{self.name} deactivated!")

    def on_activate(self):
        """Visual feedback when activated."""
        self.rotation.z = 45.0  # Tilt when pulled

    def on_deactivate(self):
        """Visual feedback when deactivated."""
        self.rotation.z = 0.0  # Return to upright


class Button(PuzzleElement):
    """A button that activates when pressed."""

    def __init__(self, position, name="Button", auto_reset=True):
        super().__init__(position, name)
        self.description = "A button. Press E to push."
        self.scale = glm.vec3(0.5, 0.2, 0.5)
        self.auto_reset = auto_reset
        self.reset_timer = 0.0
        self.reset_delay = 2.0  # Seconds until auto-reset

        # Store original position to prevent floating point drift
        self.base_position = glm.vec3(position)
        self.pressed_offset = -0.1

    def interact(self):
        """Press the button."""
        self.activate()
        logger.debug(f"{self.name} pressed!")

    def update(self, delta_time):
        """Handle auto-reset timer."""
        if self.state == "active" and self.auto_reset:
            self.reset_timer += delta_time
            if self.reset_timer >= self.reset_delay:
                self.deactivate()
                self.reset_timer = 0.0
                logger.debug(f"{self.name} reset.")

    def on_activate(self):
        """Visual feedback - button pressed down."""
        self.position = glm.vec3(self.base_position.x,
                                 self.base_position.y + self.pressed_offset,
                                 self.base_position.z)

    def on_deactivate(self):
        """Visual feedback - button pops back up."""
        self.position = glm.vec3(self.base_position)


class Door(PuzzleElement):
    """A door that can be opened/closed."""

    def __init__(self, position, name="Door", locked=True, timed=False, timer_duration=5.0):
        super().__init__(position, name)
        self.locked = locked
        self.state = "closed"
        self.description = f"A door. {'Locked.' if locked else 'Press E to open.'}"
        self.scale = glm.vec3(2.0, 3.0, 0.2)
        self.open_offset = glm.vec3(0.0, 2.5, 0.0)  # Move up when open
        self.closed_position = glm.vec3(position)
        self.interactable = not locked

        # Timed door properties
        self.timed = timed
        self.timer_duration = timer_duration
        self.timer = 0.0

    def update(self, delta_time):
        """Handle timed door closing."""
        if self.timed and self.state == "open":
            self.timer += delta_time
            if self.timer >= self.timer_duration:
                self.close()
                self.timer = 0.0
                logger.info(f"{self.name} timer expired - closing!")

    def interact(self):
        """Try to open/close the door."""
        if self.locked:
            logger.info(f"{self.name} is locked!")
            return

        if self.state == "closed":
            self.open()
        else:
            self.close()

    def open(self):
        """Open the door."""
        if self.state != "open":
            self.state = "open"
            self.position = self.closed_position + self.open_offset
            self.timer = 0.0
            if self.timed:
                logger.info(f"{self.name} opened! (Closes in {self.timer_duration}s)")
            else:
                logger.info(f"{self.name} opened!")

    def close(self):
        """Close the door."""
        if self.state != "closed":
            self.state = "closed"
            self.position = self.closed_position
            logger.info(f"{self.name} closed!")

    def unlock(self):
        """Unlock the door."""
        if self.locked:
            self.locked = False
            self.interactable = True
            self.description = f"A door. Press E to open."
            logger.info(f"{self.name} unlocked!")

    def on_triggered(self, source):
        """Open when triggered by connected element."""
        if self.locked:
            self.unlock()
        self.open()


class PressurePlate(PuzzleElement):
    """A pressure plate that activates when player stands on it."""

    def __init__(self, position, name="Pressure Plate"):
        super().__init__(position, name)
        self.description = "A pressure plate."
        self.scale = glm.vec3(1.5, 0.1, 1.5)
        self.interactable = False  # Automatic, not interactive
        self.active_height = -0.05

        # Store original position to prevent floating point drift
        self.base_position = glm.vec3(position)

    def check_activation(self, player_position):
        """Check if player is standing on the plate."""
        # Use base_position for consistent distance checking
        distance_xz = glm.length(glm.vec2(
            player_position.x - self.base_position.x,
            player_position.z - self.base_position.z
        ))

        # Player must be close in XZ and near ground level
        if distance_xz < 0.75 and abs(player_position.y - self.base_position.y) < 1.0:
            if self.state != "active":
                self.activate()
        else:
            if self.state != "inactive":
                self.deactivate()

    def on_activate(self):
        """Visual feedback - plate pressed down."""
        self.position = glm.vec3(self.base_position.x,
                                 self.base_position.y + self.active_height,
                                 self.base_position.z)

    def on_deactivate(self):
        """Visual feedback - plate rises back."""
        self.position = glm.vec3(self.base_position)
