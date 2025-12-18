"""Vector utility functions to reduce code duplication."""
import glm
from typing import Union, Tuple


def create_vec3(x: Union[float, int] = 0.0, y: Union[float, int] = 0.0,
                z: Union[float, int] = 0.0) -> glm.vec3:
    """
    Create a vec3 with validation.

    Args:
        x: X coordinate
        y: Y coordinate
        z: Z coordinate

    Returns:
        glm.vec3 instance
    """
    return glm.vec3(float(x), float(y), float(z))


def vec3_from_tuple(coords: Tuple[Union[float, int], Union[float, int], Union[float, int]]) -> glm.vec3:
    """
    Create a vec3 from a tuple.

    Args:
        coords: Tuple of (x, y, z) coordinates

    Returns:
        glm.vec3 instance

    Raises:
        ValueError: If tuple doesn't have exactly 3 elements
    """
    if len(coords) != 3:
        raise ValueError(f"Expected 3 coordinates, got {len(coords)}")

    return glm.vec3(float(coords[0]), float(coords[1]), float(coords[2]))


def vec3_to_tuple(vec: glm.vec3) -> Tuple[float, float, float]:
    """
    Convert a vec3 to a tuple.

    Args:
        vec: Vector to convert

    Returns:
        Tuple of (x, y, z) coordinates
    """
    return (float(vec.x), float(vec.y), float(vec.z))


def vec3_distance(a: glm.vec3, b: glm.vec3) -> float:
    """
    Calculate distance between two vec3 points.

    Args:
        a: First point
        b: Second point

    Returns:
        Distance between points
    """
    return glm.distance(a, b)


def vec3_distance_squared(a: glm.vec3, b: glm.vec3) -> float:
    """
    Calculate squared distance between two vec3 points (faster than distance).

    Args:
        a: First point
        b: Second point

    Returns:
        Squared distance between points
    """
    dx = a.x - b.x
    dy = a.y - b.y
    dz = a.z - b.z
    return dx * dx + dy * dy + dz * dz


def vec3_lerp(a: glm.vec3, b: glm.vec3, t: float) -> glm.vec3:
    """
    Linear interpolation between two vec3 points.

    Args:
        a: Start point
        b: End point
        t: Interpolation factor (0.0 to 1.0)

    Returns:
        Interpolated point
    """
    t = max(0.0, min(1.0, t))  # Clamp t to [0, 1]
    return glm.mix(a, b, t)


def vec3_clamp(vec: glm.vec3, min_val: glm.vec3, max_val: glm.vec3) -> glm.vec3:
    """
    Clamp each component of a vec3 to a range.

    Args:
        vec: Vector to clamp
        min_val: Minimum values for each component
        max_val: Maximum values for each component

    Returns:
        Clamped vector
    """
    return glm.vec3(
        max(min_val.x, min(max_val.x, vec.x)),
        max(min_val.y, min(max_val.y, vec.y)),
        max(min_val.z, min(max_val.z, vec.z))
    )


def vec3_normalize_safe(vec: glm.vec3, fallback: glm.vec3 = None) -> glm.vec3:
    """
    Normalize a vector, returning a fallback if the vector is zero-length.

    Args:
        vec: Vector to normalize
        fallback: Fallback vector if normalization fails (default: (0, 1, 0))

    Returns:
        Normalized vector or fallback
    """
    if fallback is None:
        fallback = glm.vec3(0.0, 1.0, 0.0)

    length = glm.length(vec)
    if length < 1e-6:  # Very small threshold
        return fallback

    return glm.normalize(vec)


def vec3_horizontal_distance(a: glm.vec3, b: glm.vec3) -> float:
    """
    Calculate horizontal (XZ plane) distance between two points, ignoring Y.

    Args:
        a: First point
        b: Second point

    Returns:
        Horizontal distance
    """
    dx = a.x - b.x
    dz = a.z - b.z
    return (dx * dx + dz * dz) ** 0.5


def is_position_in_bounds(pos: glm.vec3, min_bounds: glm.vec3, max_bounds: glm.vec3) -> bool:
    """
    Check if a position is within axis-aligned bounds.

    Args:
        pos: Position to check
        min_bounds: Minimum bounds (inclusive)
        max_bounds: Maximum bounds (inclusive)

    Returns:
        True if position is within bounds
    """
    return (min_bounds.x <= pos.x <= max_bounds.x and
            min_bounds.y <= pos.y <= max_bounds.y and
            min_bounds.z <= pos.z <= max_bounds.z)
