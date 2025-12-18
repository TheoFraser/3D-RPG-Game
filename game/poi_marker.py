"""POI visual markers in the game world."""
import glm
from game.entities import Entity
from world_gen.poi_generator import POI, POIType


class POIMarker(Entity):
    """Visual marker for a Point of Interest."""

    def __init__(self, poi: POI):
        """
        Create a POI marker.

        Args:
            poi: The POI this marker represents
        """
        # Spawn marker well above terrain to ensure visibility
        marker_pos = glm.vec3(poi.position.x, poi.position.y + 5.0, poi.position.z)
        super().__init__(marker_pos, name=poi.name)
        self.poi = poi
        self.interactable = True
        self.description = self._get_description()

        # Store base position for bobbing animation
        self.base_position = glm.vec3(marker_pos)

        # Visual properties based on POI type
        self.scale = self._get_scale()
        self.rotation_speed = 20.0  # Gentle rotation
        self.bob_height = 0.5
        self.bob_speed = 1.0
        self.time = 0.0

    def _get_description(self) -> str:
        """Get description based on POI type and discovery status."""
        if not self.poi.discovered:
            return f"??? (Press E to discover)"

        poi_descriptions = {
            POIType.VILLAGE: f"{self.poi.name} - Village with NPCs and merchants",
            POIType.SHRINE: f"{self.poi.name} - Rest and fast travel point",
            POIType.RUIN: f"{self.poi.name} - Ancient ruins with loot",
            POIType.DUNGEON: f"{self.poi.name} - Dangerous dungeon (Level {self.poi.data.get('difficulty', 1)})",
        }

        return poi_descriptions.get(self.poi.poi_type, self.poi.name)

    def _get_scale(self) -> glm.vec3:
        """Get scale based on POI type."""
        scales = {
            POIType.VILLAGE: glm.vec3(4.0, 8.0, 4.0),    # Large tower
            POIType.SHRINE: glm.vec3(2.0, 6.0, 2.0),     # Tall pillar
            POIType.RUIN: glm.vec3(3.0, 4.0, 3.0),       # Medium cube
            POIType.DUNGEON: glm.vec3(3.5, 3.0, 3.5),    # Wide entrance
        }
        return scales.get(self.poi.poi_type, glm.vec3(2.0, 2.0, 2.0))

    def get_color(self) -> tuple:
        """Get marker color based on type and discovery status."""
        if not self.poi.discovered:
            # Undiscovered - gray/subtle
            return (0.5, 0.5, 0.5)

        # Discovered - bright and type-specific
        colors = {
            POIType.VILLAGE: (0.2, 0.8, 0.2),   # Green
            POIType.SHRINE: (0.3, 0.7, 1.0),    # Light blue
            POIType.RUIN: (0.9, 0.7, 0.3),      # Gold/amber
            POIType.DUNGEON: (0.9, 0.2, 0.2),   # Red
        }
        return colors.get(self.poi.poi_type, (1.0, 1.0, 1.0))

    def update(self, delta_time: float):
        """Update marker animation."""
        self.time += delta_time

        # Gentle rotation
        self.rotation.y += self.rotation_speed * delta_time

        # Bobbing animation - bob upward from base position
        bob_offset = abs(glm.sin(self.time * self.bob_speed)) * self.bob_height
        self.position.y = self.base_position.y + bob_offset

        # Update description if discovery status changed
        if self.description != self._get_description():
            self.description = self._get_description()

    def discover(self):
        """Mark this POI as discovered."""
        if not self.poi.discovered:
            self.poi.discovered = True
            self.description = self._get_description()
            return True
        return False
