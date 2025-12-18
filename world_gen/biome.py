"""Biome system for world generation."""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import config
from game.logger import get_logger

logger = get_logger(__name__)

# Try to use numba for performance
try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    prange = range


@dataclass
class BiomeDefinition:
    """Definition of a biome's properties."""
    id: int
    name: str
    color: Tuple[float, float, float]
    height_scale: float
    tree_density: float
    grass_density: float
    fog_color: Tuple[float, float, float]
    fog_density: float


# Biome definitions
BIOMES: Dict[int, BiomeDefinition] = {
    config.BIOME_GRASSLANDS: BiomeDefinition(
        id=config.BIOME_GRASSLANDS,
        name="Grasslands",
        color=(0.3, 0.6, 0.2),
        height_scale=5.0,
        tree_density=0.1,
        grass_density=0.8,
        fog_color=(0.7, 0.8, 0.9),
        fog_density=0.001
    ),
    config.BIOME_ENCHANTED_FOREST: BiomeDefinition(
        id=config.BIOME_ENCHANTED_FOREST,
        name="Enchanted Forest",
        color=(0.1, 0.4, 0.3),
        height_scale=8.0,
        tree_density=0.7,
        grass_density=0.5,
        fog_color=(0.2, 0.4, 0.3),
        fog_density=0.003
    ),
    config.BIOME_CRYSTAL_CAVES: BiomeDefinition(
        id=config.BIOME_CRYSTAL_CAVES,
        name="Crystal Caves",
        color=(0.5, 0.3, 0.7),
        height_scale=3.0,
        tree_density=0.0,
        grass_density=0.1,
        fog_color=(0.4, 0.2, 0.5),
        fog_density=0.002
    ),
    config.BIOME_FLOATING_ISLANDS: BiomeDefinition(
        id=config.BIOME_FLOATING_ISLANDS,
        name="Floating Islands",
        color=(0.6, 0.7, 0.9),
        height_scale=15.0,
        tree_density=0.3,
        grass_density=0.6,
        fog_color=(0.8, 0.9, 1.0),
        fog_density=0.0005
    ),
    config.BIOME_ANCIENT_RUINS: BiomeDefinition(
        id=config.BIOME_ANCIENT_RUINS,
        name="Ancient Ruins",
        color=(0.5, 0.4, 0.3),
        height_scale=2.0,
        tree_density=0.05,
        grass_density=0.2,
        fog_color=(0.6, 0.5, 0.4),
        fog_density=0.002
    ),
}


@njit(cache=True)
def _perlin_noise_2d(x: float, z: float, seed: int) -> float:
    """
    Simple 2D Perlin-like noise for biome generation.

    Args:
        x, z: World coordinates
        seed: Random seed

    Returns:
        Noise value in range [0, 1]
    """
    # Use large primes for pseudo-random gradient selection
    def hash_coord(ix: int, iz: int) -> float:
        n = ix * 374761393 + iz * 668265263 + seed * 1013904223
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0x7fffffff) / 0x7fffffff

    # Get grid cell
    x0 = int(np.floor(x))
    z0 = int(np.floor(z))
    x1 = x0 + 1
    z1 = z0 + 1

    # Fractional position
    fx = x - x0
    fz = z - z0

    # Smooth interpolation
    sx = fx * fx * (3 - 2 * fx)
    sz = fz * fz * (3 - 2 * fz)

    # Get corner values
    v00 = hash_coord(x0, z0)
    v10 = hash_coord(x1, z0)
    v01 = hash_coord(x0, z1)
    v11 = hash_coord(x1, z1)

    # Bilinear interpolation
    v0 = v00 * (1 - sx) + v10 * sx
    v1 = v01 * (1 - sx) + v11 * sx

    return v0 * (1 - sz) + v1 * sz


@njit(cache=True)
def _multi_octave_noise(
    x: float,
    z: float,
    seed: int,
    octaves: int = 3,
    persistence: float = 0.5
) -> float:
    """
    Multi-octave noise for more natural biome boundaries.

    Args:
        x, z: World coordinates
        seed: Random seed
        octaves: Number of noise layers
        persistence: Amplitude multiplier per octave

    Returns:
        Noise value in range [0, 1]
    """
    total = 0.0
    amplitude = 1.0
    max_value = 0.0
    frequency = 1.0

    for _ in range(octaves):
        total += _perlin_noise_2d(x * frequency, z * frequency, seed) * amplitude
        max_value += amplitude
        amplitude *= persistence
        frequency *= 2.0

    return total / max_value


class BiomeManager:
    """
    Manages biome determination across the world.

    Uses layered noise to create natural-looking biome regions
    with smooth transitions between them.
    """

    def __init__(self, seed: int = None):
        """
        Initialize biome manager.

        Args:
            seed: World seed for biome generation
        """
        self.seed = seed if seed is not None else config.WORLD_SEED
        self.biome_scale = config.BIOME_SCALE
        self.blend_distance = config.BIOME_BLEND_DISTANCE

        # Cache for performance
        self._cache: Dict[Tuple[int, int], int] = {}
        self._cache_resolution = 16  # Cache every 16 units

        logger.info(f"BiomeManager initialized (seed={self.seed})")

    def get_biome_at(self, world_x: float, world_z: float) -> int:
        """
        Get the primary biome at a world position.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Biome ID
        """
        # Check cache
        cache_x = int(world_x // self._cache_resolution)
        cache_z = int(world_z // self._cache_resolution)
        cache_key = (cache_x, cache_z)

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Calculate biome
        biome = self._calculate_biome(world_x, world_z)

        # Store in cache
        self._cache[cache_key] = biome

        return biome

    def _calculate_biome(self, world_x: float, world_z: float) -> int:
        """
        Calculate biome at position using noise layers.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Biome ID
        """
        # Scale coordinates for biome-sized features
        sx = world_x / self.biome_scale
        sz = world_z / self.biome_scale

        # Get noise values for biome selection
        # Use different seeds for different noise layers
        temperature = _multi_octave_noise(sx, sz, self.seed, octaves=2)
        moisture = _multi_octave_noise(sx, sz, self.seed + 1000, octaves=2)
        magic = _multi_octave_noise(sx, sz, self.seed + 2000, octaves=3)

        # Determine biome based on noise values
        # This creates a natural distribution of biomes

        # High magic areas get special biomes
        if magic > 0.7:
            if temperature > 0.5:
                return config.BIOME_FLOATING_ISLANDS
            else:
                return config.BIOME_CRYSTAL_CAVES

        # Ancient ruins appear in dry, hot areas
        if temperature > 0.6 and moisture < 0.3:
            return config.BIOME_ANCIENT_RUINS

        # Enchanted forest in moist, cool areas
        if moisture > 0.6 and temperature < 0.5:
            return config.BIOME_ENCHANTED_FOREST

        # Default to grasslands
        return config.BIOME_GRASSLANDS

    def get_biome_blend(
        self,
        world_x: float,
        world_z: float
    ) -> Dict[int, float]:
        """
        Get biome blend weights at a position.

        Useful for smooth transitions between biomes.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Dictionary mapping biome IDs to blend weights
        """
        # Sample surrounding points
        samples = []
        step = self.blend_distance / 2

        for dx in [-step, 0, step]:
            for dz in [-step, 0, step]:
                biome = self.get_biome_at(world_x + dx, world_z + dz)
                samples.append(biome)

        # Count occurrences
        counts: Dict[int, int] = {}
        for biome in samples:
            counts[biome] = counts.get(biome, 0) + 1

        # Convert to weights
        total = len(samples)
        weights = {biome: count / total for biome, count in counts.items()}

        return weights

    def get_biome_definition(self, biome_id: int) -> BiomeDefinition:
        """
        Get the definition for a biome.

        Args:
            biome_id: Biome ID

        Returns:
            BiomeDefinition for that biome
        """
        return BIOMES.get(biome_id, BIOMES[config.BIOME_GRASSLANDS])

    def get_height_scale(self, world_x: float, world_z: float) -> float:
        """
        Get terrain height scale at position, with biome blending.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Blended height scale
        """
        weights = self.get_biome_blend(world_x, world_z)

        total_scale = 0.0
        for biome_id, weight in weights.items():
            definition = self.get_biome_definition(biome_id)
            total_scale += definition.height_scale * weight

        return total_scale

    def get_biome_color(self, world_x: float, world_z: float) -> Tuple[float, float, float]:
        """
        Get terrain color tint at position, with biome blending.

        Args:
            world_x, world_z: World coordinates

        Returns:
            RGB color tuple
        """
        weights = self.get_biome_blend(world_x, world_z)

        r, g, b = 0.0, 0.0, 0.0
        for biome_id, weight in weights.items():
            definition = self.get_biome_definition(biome_id)
            r += definition.color[0] * weight
            g += definition.color[1] * weight
            b += definition.color[2] * weight

        return (r, g, b)

    def clear_cache(self) -> None:
        """Clear the biome cache."""
        self._cache.clear()

    def get_debug_info(self, world_x: float, world_z: float) -> str:
        """Get debug info about biome at position."""
        biome = self.get_biome_at(world_x, world_z)
        definition = self.get_biome_definition(biome)
        weights = self.get_biome_blend(world_x, world_z)

        lines = [
            f"Position: ({world_x:.1f}, {world_z:.1f})",
            f"Primary Biome: {definition.name}",
            f"Biome Weights:"
        ]

        for biome_id, weight in sorted(weights.items(), key=lambda x: -x[1]):
            name = self.get_biome_definition(biome_id).name
            lines.append(f"  {name}: {weight:.1%}")

        return "\n".join(lines)
