"""Numba-optimized terrain generation functions."""
import numpy as np
from numba import njit, prange
import math


@njit(fastmath=True)
def perlin_fade(t):
    """Perlin smoothstep function."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


@njit(fastmath=True)
def perlin_lerp(t, a, b):
    """Linear interpolation."""
    return a + t * (b - a)


@njit(fastmath=True)
def perlin_grad(hash_val, x, y):
    """Compute gradient vector."""
    h = hash_val & 3
    if h == 0:
        return x + y
    elif h == 1:
        return -x + y
    elif h == 2:
        return x - y
    else:
        return -x - y


@njit(fastmath=True)
def perlin_noise_2d(x, y, perm):
    """
    2D Perlin noise implementation (Numba-optimized).

    Args:
        x, y: Coordinates
        perm: Permutation table (length 512)

    Returns:
        float: Noise value between -1 and 1
    """
    # Find unit square coordinates
    xi = int(math.floor(x)) & 255
    yi = int(math.floor(y)) & 255

    # Find relative x,y in square
    xf = x - math.floor(x)
    yf = y - math.floor(y)

    # Compute fade curves
    u = perlin_fade(xf)
    v = perlin_fade(yf)

    # Hash coordinates of square corners
    aa = perm[perm[xi] + yi]
    ab = perm[perm[xi] + yi + 1]
    ba = perm[perm[xi + 1] + yi]
    bb = perm[perm[xi + 1] + yi + 1]

    # Add blended results from corners
    x1 = perlin_lerp(u, perlin_grad(aa, xf, yf), perlin_grad(ba, xf - 1, yf))
    x2 = perlin_lerp(u, perlin_grad(ab, xf, yf - 1), perlin_grad(bb, xf - 1, yf - 1))

    return perlin_lerp(v, x1, x2)


@njit(parallel=True, fastmath=True)
def generate_terrain_heightmap(width, height, scale, octaves, persistence, lacunarity, seed, offset_x=0.0, offset_z=0.0, chunk_size=64.0):
    """
    Generate terrain heightmap using fractal Perlin noise (Numba-optimized).

    Args:
        width, height: Heightmap dimensions
        scale: Overall scale of terrain features
        octaves: Number of noise layers
        persistence: Amplitude multiplier per octave
        lacunarity: Frequency multiplier per octave
        seed: Random seed
        offset_x: World X offset for chunk-based generation
        offset_z: World Z offset for chunk-based generation
        chunk_size: Size of chunk in world units (for coordinate mapping)

    Returns:
        np.ndarray: Heightmap of shape (height, width)
    """
    # Create permutation table from seed
    np.random.seed(seed)
    perm = np.arange(256, dtype=np.int32)
    np.random.shuffle(perm)
    perm = np.concatenate((perm, perm))  # Duplicate for overflow

    heightmap = np.zeros((height, width), dtype=np.float32)

    max_value = 0.0
    amplitude = 1.0
    for i in range(octaves):
        max_value += amplitude
        amplitude *= persistence

    for y in prange(height):
        for x in range(width):
            amplitude = 1.0
            frequency = 1.0
            noise_value = 0.0

            # Convert heightmap index to world coordinate
            # For seamless chunks, edge vertices must sample at exact world positions
            world_x = offset_x + (x / (width - 1)) * chunk_size
            world_z = offset_z + (y / (height - 1)) * chunk_size

            for octave in range(octaves):
                # Sample noise at world coordinate
                sample_x = (world_x / scale) * frequency
                sample_y = (world_z / scale) * frequency

                noise = perlin_noise_2d(sample_x, sample_y, perm)
                noise_value += noise * amplitude

                amplitude *= persistence
                frequency *= lacunarity

            # Normalize to [0, 1]
            heightmap[y, x] = (noise_value / max_value + 1.0) * 0.5

    return heightmap


@njit(fastmath=True)
def apply_terrain_curve(heightmap, power=2.0):
    """
    Apply power curve to heightmap for more dramatic terrain.

    Args:
        heightmap: Input heightmap
        power: Curve exponent (>1 makes valleys deeper, <1 makes peaks higher)

    Returns:
        np.ndarray: Modified heightmap
    """
    result = np.zeros_like(heightmap)
    for y in range(heightmap.shape[0]):
        for x in range(heightmap.shape[1]):
            result[y, x] = math.pow(heightmap[y, x], power)
    return result


@njit(parallel=True, fastmath=True)
def calculate_normals(heightmap, scale_xz, scale_y):
    """
    Calculate vertex normals for terrain heightmap.

    Args:
        heightmap: Height values
        scale_xz: Horizontal scale
        scale_y: Vertical scale

    Returns:
        np.ndarray: Normal vectors of shape (height, width, 3)
    """
    height, width = heightmap.shape
    normals = np.zeros((height, width, 3), dtype=np.float32)

    for y in prange(height):
        for x in range(width):
            # Get neighboring heights
            hL = heightmap[y, max(x - 1, 0)]
            hR = heightmap[y, min(x + 1, width - 1)]
            hD = heightmap[max(y - 1, 0), x]
            hU = heightmap[min(y + 1, height - 1), x]

            # Calculate normal using finite differences
            nx = (hL - hR) * scale_y / scale_xz
            ny = 2.0
            nz = (hD - hU) * scale_y / scale_xz

            # Normalize
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            if length > 0:
                normals[y, x, 0] = nx / length
                normals[y, x, 1] = ny / length
                normals[y, x, 2] = nz / length
            else:
                normals[y, x, 1] = 1.0

    return normals
