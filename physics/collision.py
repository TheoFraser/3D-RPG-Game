"""Collision detection systems."""
from typing import Tuple, Optional
import glm


class AABB:
    """Axis-Aligned Bounding Box for collision detection."""

    def __init__(self, min_point: glm.vec3, max_point: glm.vec3) -> None:
        """
        Create an AABB.

        Args:
            min_point: Minimum corner (glm.vec3)
            max_point: Maximum corner (glm.vec3)
        """
        self.min = min_point
        self.max = max_point

    @classmethod
    def from_center_size(cls, center: glm.vec3, size: glm.vec3) -> 'AABB':
        """
        Create AABB from center point and size.

        Args:
            center: Center position (glm.vec3)
            size: Size in each dimension (glm.vec3)
        """
        half_size = size * 0.5
        return cls(center - half_size, center + half_size)

    def intersects(self, other: 'AABB') -> bool:
        """
        Check if this AABB intersects with another AABB.

        Args:
            other: Another AABB

        Returns:
            bool: True if the AABBs intersect
        """
        return (self.min.x <= other.max.x and self.max.x >= other.min.x and
                self.min.y <= other.max.y and self.max.y >= other.min.y and
                self.min.z <= other.max.z and self.max.z >= other.min.z)

    def contains_point(self, point: glm.vec3) -> bool:
        """
        Check if a point is inside this AABB.

        Args:
            point: Point to check (glm.vec3)

        Returns:
            bool: True if the point is inside
        """
        return (self.min.x <= point.x <= self.max.x and
                self.min.y <= point.y <= self.max.y and
                self.min.z <= point.z <= self.max.z)

    def get_center(self) -> glm.vec3:
        """Get the center point of the AABB."""
        return (self.min + self.max) * 0.5

    def get_size(self) -> glm.vec3:
        """Get the size of the AABB."""
        return self.max - self.min

    def translate(self, offset: glm.vec3) -> None:
        """
        Translate the AABB by an offset.

        Args:
            offset: Translation offset (glm.vec3)
        """
        self.min += offset
        self.max += offset

    def __repr__(self) -> str:
        return f"AABB(min={self.min}, max={self.max})"


def ray_cast(origin: glm.vec3, direction: glm.vec3, max_distance: float = 100.0) -> Tuple[bool, Optional[float], Optional[glm.vec3]]:
    """
    Cast a ray and check for intersections.

    Args:
        origin: Ray origin (glm.vec3)
        direction: Ray direction (glm.vec3, normalized)
        max_distance: Maximum ray distance

    Returns:
        tuple: (hit, distance, point) or (False, None, None)
    """
    # Simple ray-ground plane intersection for now
    # Ground is at y = 0
    if abs(direction.y) < 0.0001:
        return False, None, None

    t = -origin.y / direction.y

    if t < 0 or t > max_distance:
        return False, None, None

    hit_point = origin + direction * t
    return True, t, hit_point
