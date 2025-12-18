"""Unit tests for collision detection system."""
import unittest
import glm
from physics.collision import AABB, ray_cast


class TestAABB(unittest.TestCase):
    """Test AABB collision detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.aabb1 = AABB(glm.vec3(0, 0, 0), glm.vec3(2, 2, 2))
        self.aabb2 = AABB(glm.vec3(1, 1, 1), glm.vec3(3, 3, 3))
        self.aabb3 = AABB(glm.vec3(5, 5, 5), glm.vec3(7, 7, 7))

    def test_aabb_creation(self):
        """Test AABB can be created with min and max points."""
        aabb = AABB(glm.vec3(0, 0, 0), glm.vec3(1, 1, 1))
        self.assertEqual(aabb.min, glm.vec3(0, 0, 0))
        self.assertEqual(aabb.max, glm.vec3(1, 1, 1))

    def test_aabb_from_center_size(self):
        """Test creating AABB from center and size."""
        aabb = AABB.from_center_size(glm.vec3(0, 0, 0), glm.vec3(2, 2, 2))
        self.assertEqual(aabb.min, glm.vec3(-1, -1, -1))
        self.assertEqual(aabb.max, glm.vec3(1, 1, 1))

    def test_aabb_intersection_overlapping(self):
        """Test AABB intersection detection for overlapping boxes."""
        self.assertTrue(self.aabb1.intersects(self.aabb2))
        self.assertTrue(self.aabb2.intersects(self.aabb1))

    def test_aabb_intersection_non_overlapping(self):
        """Test AABB intersection detection for non-overlapping boxes."""
        self.assertFalse(self.aabb1.intersects(self.aabb3))
        self.assertFalse(self.aabb3.intersects(self.aabb1))

    def test_aabb_contains_point_inside(self):
        """Test point containment for point inside AABB."""
        point = glm.vec3(1, 1, 1)
        self.assertTrue(self.aabb1.contains_point(point))

    def test_aabb_contains_point_outside(self):
        """Test point containment for point outside AABB."""
        point = glm.vec3(5, 5, 5)
        self.assertFalse(self.aabb1.contains_point(point))

    def test_aabb_contains_point_on_boundary(self):
        """Test point containment for point on AABB boundary."""
        point = glm.vec3(2, 2, 2)
        self.assertTrue(self.aabb1.contains_point(point))

    def test_aabb_get_center(self):
        """Test getting center of AABB."""
        center = self.aabb1.get_center()
        self.assertEqual(center, glm.vec3(1, 1, 1))

    def test_aabb_get_size(self):
        """Test getting size of AABB."""
        size = self.aabb1.get_size()
        self.assertEqual(size, glm.vec3(2, 2, 2))

    def test_aabb_translate(self):
        """Test translating AABB."""
        offset = glm.vec3(1, 1, 1)
        self.aabb1.translate(offset)
        self.assertEqual(self.aabb1.min, glm.vec3(1, 1, 1))
        self.assertEqual(self.aabb1.max, glm.vec3(3, 3, 3))


class TestRaycast(unittest.TestCase):
    """Test raycasting functions."""

    def test_raycast_hits_ground(self):
        """Test ray hitting ground plane at y=0."""
        origin = glm.vec3(0, 5, 0)
        direction = glm.vec3(0, -1, 0)
        hit, distance, point = ray_cast(origin, direction, 10.0)

        self.assertTrue(hit)
        self.assertAlmostEqual(distance, 5.0, places=5)
        self.assertIsNotNone(point)
        if point:
            self.assertAlmostEqual(point.y, 0.0, places=5)

    def test_raycast_misses_ground(self):
        """Test ray missing ground plane."""
        origin = glm.vec3(0, 5, 0)
        direction = glm.vec3(0, 1, 0)  # Pointing up
        hit, distance, point = ray_cast(origin, direction, 10.0)

        self.assertFalse(hit)
        self.assertIsNone(distance)
        self.assertIsNone(point)

    def test_raycast_max_distance(self):
        """Test ray beyond max distance."""
        origin = glm.vec3(0, 100, 0)
        direction = glm.vec3(0, -1, 0)
        hit, distance, point = ray_cast(origin, direction, 50.0)

        self.assertFalse(hit)


if __name__ == '__main__':
    unittest.main()
