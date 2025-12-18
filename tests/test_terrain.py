"""Unit tests for terrain generation."""
import unittest
import numpy as np
from world_gen.numba_terrain import (
    perlin_fade,
    perlin_lerp,
    generate_terrain_heightmap,
    apply_terrain_curve,
    calculate_normals
)


class TestTerrainFunctions(unittest.TestCase):
    """Test terrain generation utility functions."""

    def test_perlin_fade(self):
        """Test perlin fade function."""
        # Test boundary values
        self.assertAlmostEqual(perlin_fade(0.0), 0.0, places=5)
        self.assertAlmostEqual(perlin_fade(1.0), 1.0, places=5)

        # Test mid-point
        mid_value = perlin_fade(0.5)
        self.assertGreater(mid_value, 0.0)
        self.assertLess(mid_value, 1.0)

    def test_perlin_lerp(self):
        """Test linear interpolation."""
        # Test boundary cases
        self.assertAlmostEqual(perlin_lerp(0.0, 10.0, 20.0), 10.0, places=5)
        self.assertAlmostEqual(perlin_lerp(1.0, 10.0, 20.0), 20.0, places=5)

        # Test mid-point
        self.assertAlmostEqual(perlin_lerp(0.5, 10.0, 20.0), 15.0, places=5)

    def test_generate_terrain_heightmap_shape(self):
        """Test terrain heightmap has correct shape."""
        width, height = 32, 32
        heightmap = generate_terrain_heightmap(
            width=width,
            height=height,
            scale=10.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            seed=42
        )

        self.assertEqual(heightmap.shape, (height, width))

    def test_generate_terrain_heightmap_range(self):
        """Test terrain heightmap values are in valid range [0, 1]."""
        heightmap = generate_terrain_heightmap(
            width=32,
            height=32,
            scale=10.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            seed=42
        )

        self.assertGreaterEqual(heightmap.min(), 0.0)
        self.assertLessEqual(heightmap.max(), 1.0)

    def test_generate_terrain_deterministic(self):
        """Test terrain generation is deterministic with same seed."""
        heightmap1 = generate_terrain_heightmap(
            width=32, height=32, scale=10.0, octaves=4,
            persistence=0.5, lacunarity=2.0, seed=42
        )

        heightmap2 = generate_terrain_heightmap(
            width=32, height=32, scale=10.0, octaves=4,
            persistence=0.5, lacunarity=2.0, seed=42
        )

        np.testing.assert_array_equal(heightmap1, heightmap2)

    def test_generate_terrain_different_seeds(self):
        """Test different seeds produce different terrain."""
        heightmap1 = generate_terrain_heightmap(
            width=32, height=32, scale=10.0, octaves=4,
            persistence=0.5, lacunarity=2.0, seed=42
        )

        heightmap2 = generate_terrain_heightmap(
            width=32, height=32, scale=10.0, octaves=4,
            persistence=0.5, lacunarity=2.0, seed=123
        )

        self.assertFalse(np.array_equal(heightmap1, heightmap2))

    def test_apply_terrain_curve(self):
        """Test applying curve to terrain."""
        heightmap = np.array([[0.0, 0.5, 1.0]], dtype=np.float32)
        curved = apply_terrain_curve(heightmap, power=2.0)

        self.assertAlmostEqual(curved[0, 0], 0.0, places=5)
        self.assertAlmostEqual(curved[0, 1], 0.25, places=5)
        self.assertAlmostEqual(curved[0, 2], 1.0, places=5)

    def test_calculate_normals_shape(self):
        """Test normal calculation produces correct shape."""
        heightmap = np.random.rand(32, 32).astype(np.float32)
        normals = calculate_normals(heightmap, scale_xz=1.0, scale_y=1.0)

        self.assertEqual(normals.shape, (32, 32, 3))

    def test_calculate_normals_normalized(self):
        """Test calculated normals are approximately normalized."""
        heightmap = np.random.rand(16, 16).astype(np.float32)
        normals = calculate_normals(heightmap, scale_xz=1.0, scale_y=1.0)

        # Check a few random normals are unit length
        for i in range(5):
            y = np.random.randint(0, 16)
            x = np.random.randint(0, 16)
            normal = normals[y, x]
            length = np.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
            self.assertAlmostEqual(length, 1.0, places=4)


if __name__ == '__main__':
    unittest.main()
