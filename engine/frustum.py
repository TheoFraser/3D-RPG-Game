"""View frustum culling for optimized rendering."""
import glm
import numpy as np


class Frustum:
    """View frustum for culling objects outside camera view."""

    def __init__(self):
        """Initialize frustum with 6 planes (left, right, bottom, top, near, far)."""
        self.planes = [glm.vec4(0) for _ in range(6)]

    def update(self, view_projection_matrix):
        """
        Extract frustum planes from view-projection matrix.

        Args:
            view_projection_matrix: Combined view * projection matrix (glm.mat4)
        """
        m = view_projection_matrix

        # Left plane
        self.planes[0] = glm.vec4(
            m[0][3] + m[0][0],
            m[1][3] + m[1][0],
            m[2][3] + m[2][0],
            m[3][3] + m[3][0]
        )

        # Right plane
        self.planes[1] = glm.vec4(
            m[0][3] - m[0][0],
            m[1][3] - m[1][0],
            m[2][3] - m[2][0],
            m[3][3] - m[3][0]
        )

        # Bottom plane
        self.planes[2] = glm.vec4(
            m[0][3] + m[0][1],
            m[1][3] + m[1][1],
            m[2][3] + m[2][1],
            m[3][3] + m[3][1]
        )

        # Top plane
        self.planes[3] = glm.vec4(
            m[0][3] - m[0][1],
            m[1][3] - m[1][1],
            m[2][3] - m[2][1],
            m[3][3] - m[3][1]
        )

        # Near plane
        self.planes[4] = glm.vec4(
            m[0][3] + m[0][2],
            m[1][3] + m[1][2],
            m[2][3] + m[2][2],
            m[3][3] + m[3][2]
        )

        # Far plane
        self.planes[5] = glm.vec4(
            m[0][3] - m[0][2],
            m[1][3] - m[1][2],
            m[2][3] - m[2][2],
            m[3][3] - m[3][2]
        )

        # Normalize planes
        for i in range(6):
            length = glm.length(glm.vec3(self.planes[i]))
            self.planes[i] /= length

    def is_sphere_visible(self, center, radius):
        """
        Test if a sphere is visible in the frustum.

        Args:
            center: Sphere center position (glm.vec3)
            radius: Sphere radius (float)

        Returns:
            bool: True if sphere is visible (or partially visible)
        """
        for plane in self.planes:
            # Distance from plane to sphere center
            distance = glm.dot(glm.vec3(plane), center) + plane.w

            # If sphere is completely outside any plane, it's not visible
            if distance < -radius:
                return False

        return True

    def is_box_visible(self, min_point, max_point):
        """
        Test if an axis-aligned bounding box is visible in the frustum.

        Args:
            min_point: Box minimum corner (glm.vec3)
            max_point: Box maximum corner (glm.vec3)

        Returns:
            bool: True if box is visible (or partially visible)
        """
        for plane in self.planes:
            # Get the positive vertex (furthest point in plane normal direction)
            positive_vertex = glm.vec3(
                max_point.x if plane.x >= 0 else min_point.x,
                max_point.y if plane.y >= 0 else min_point.y,
                max_point.z if plane.z >= 0 else min_point.z
            )

            # If positive vertex is outside, box is completely outside
            if glm.dot(glm.vec3(plane), positive_vertex) + plane.w < 0:
                return False

        return True

    def is_point_visible(self, point):
        """
        Test if a point is visible in the frustum.

        Args:
            point: Point position (glm.vec3)

        Returns:
            bool: True if point is visible
        """
        for plane in self.planes:
            if glm.dot(glm.vec3(plane), point) + plane.w < 0:
                return False
        return True
