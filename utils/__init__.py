"""Utility modules for the game."""
from utils.vector_utils import (
    create_vec3,
    vec3_from_tuple,
    vec3_to_tuple,
    vec3_distance,
    vec3_distance_squared,
    vec3_lerp,
    vec3_clamp,
    vec3_normalize_safe,
    vec3_horizontal_distance,
    is_position_in_bounds
)

__all__ = [
    'create_vec3',
    'vec3_from_tuple',
    'vec3_to_tuple',
    'vec3_distance',
    'vec3_distance_squared',
    'vec3_lerp',
    'vec3_clamp',
    'vec3_normalize_safe',
    'vec3_horizontal_distance',
    'is_position_in_bounds'
]
