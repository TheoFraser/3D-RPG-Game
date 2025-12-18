"""Game entities and objects."""
import glm
from physics.collision import AABB
from game.logger import get_logger

logger = get_logger(__name__)


class Entity:
    """Base class for game entities."""

    def __init__(self, position, name="Object"):
        """
        Create an entity.

        Args:
            position: World position (glm.vec3)
            name: Display name
        """
        self._position = position
        self._rotation = glm.vec3(0.0, 0.0, 0.0)
        self._scale = glm.vec3(1.0, 1.0, 1.0)
        self.name = name
        self.interactable = False
        self.description = ""

        # Rendering cache for performance optimization
        self._cached_model_matrix = None
        self._cached_normal_matrix = None
        self._matrix_dirty = True

    @property
    def position(self):
        """Get entity position."""
        return self._position

    @position.setter
    def position(self, value):
        """Set entity position and mark matrices as dirty."""
        self._position = value
        self._matrix_dirty = True

    @property
    def rotation(self):
        """Get entity rotation."""
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        """Set entity rotation and mark matrices as dirty."""
        self._rotation = value
        self._matrix_dirty = True

    @property
    def scale(self):
        """Get entity scale."""
        return self._scale

    @scale.setter
    def scale(self, value):
        """Set entity scale and mark matrices as dirty."""
        self._scale = value
        self._matrix_dirty = True

    def get_model_matrix(self):
        """Get the model matrix for rendering (cached for performance)."""
        if self._matrix_dirty or self._cached_model_matrix is None:
            model = glm.mat4(1.0)
            model = glm.translate(model, self._position)
            model = glm.rotate(model, glm.radians(self._rotation.y), glm.vec3(0.0, 1.0, 0.0))
            model = glm.rotate(model, glm.radians(self._rotation.x), glm.vec3(1.0, 0.0, 0.0))
            model = glm.rotate(model, glm.radians(self._rotation.z), glm.vec3(0.0, 0.0, 1.0))
            model = glm.scale(model, self._scale)
            self._cached_model_matrix = model

            # Recalculate normal matrix when model matrix changes
            self._cached_normal_matrix = glm.mat3(glm.transpose(glm.inverse(model)))
            self._matrix_dirty = False

        return self._cached_model_matrix

    def get_normal_matrix(self):
        """Get the normal matrix for rendering (cached for performance)."""
        if self._matrix_dirty or self._cached_normal_matrix is None:
            # Ensure model matrix is calculated first (which also calculates normal matrix)
            self.get_model_matrix()
        return self._cached_normal_matrix

    def get_collision_box(self):
        """Get the entity's collision AABB."""
        size = self.scale * 2.0  # Default cube is 1 unit, scaled by entity scale
        return AABB.from_center_size(self.position, size)

    def update(self, delta_time):
        """Update the entity (override in subclasses)."""
        pass


class Cube(Entity):
    """A simple cube object."""

    def __init__(self, position, name="Cube", color=(1.0, 1.0, 1.0)):
        super().__init__(position, name)
        self.color = color
        self.interactable = True
        self.description = f"A mysterious {name.lower()}"


class CollectibleCube(Cube):
    """A collectible cube that can be picked up."""

    def __init__(self, position, name="Collectible"):
        super().__init__(position, name, color=(1.0, 0.8, 0.2))
        self.collected = False
        self.description = "A shiny collectible cube. Press E to collect."
        self.rotation_speed = 45.0  # degrees per second

    def update(self, delta_time):
        """Rotate the collectible."""
        if not self.collected:
            self.rotation.y += self.rotation_speed * delta_time

    def collect(self):
        """Mark this collectible as collected."""
        self.collected = True
        logger.info(f"Collected: {self.name}!")


class Wall(Entity):
    """A wall structure."""

    def __init__(self, position, width=1.0, height=3.0, depth=0.2):
        super().__init__(position, "Wall")
        self.scale = glm.vec3(width, height, depth)
        self.interactable = False
