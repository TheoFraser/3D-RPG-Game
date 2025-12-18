"""Skybox rendering for 3D game engine."""
import moderngl
import glm
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Skybox:
    """
    Skybox for rendering distant environment.

    Renders a large cube around the scene with sky/environment textures.
    Uses special rendering techniques:
    - Rendered first with depth = 1.0 (farthest)
    - Camera translation removed (only rotation)
    - No depth writing (or depth test = LEQUAL)
    """

    def __init__(self, ctx: moderngl.Context, shader):
        """
        Initialize skybox.

        Args:
            ctx: ModernGL context
            shader: Skybox shader program
        """
        self.ctx = ctx
        self.shader = shader

        # Create skybox cube mesh
        self._create_cube_mesh()

        logger.info("Skybox initialized")

    def _create_cube_mesh(self):
        """
        Create cube mesh for skybox.

        Uses only positions (no normals or texcoords needed for cubemap).
        Vertices are in NDC space [-1, 1].
        """
        # Skybox cube vertices (only positions)
        vertices = np.array([
            # Back face
            -1.0, -1.0, -1.0,
             1.0, -1.0, -1.0,
             1.0,  1.0, -1.0,
             1.0,  1.0, -1.0,
            -1.0,  1.0, -1.0,
            -1.0, -1.0, -1.0,

            # Front face
            -1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,
             1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,
            -1.0, -1.0,  1.0,
            -1.0,  1.0,  1.0,

            # Left face
            -1.0,  1.0,  1.0,
            -1.0, -1.0, -1.0,
            -1.0,  1.0, -1.0,
            -1.0, -1.0, -1.0,
            -1.0,  1.0,  1.0,
            -1.0, -1.0,  1.0,

            # Right face
             1.0,  1.0,  1.0,
             1.0,  1.0, -1.0,
             1.0, -1.0, -1.0,
             1.0, -1.0, -1.0,
             1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,

            # Bottom face
            -1.0, -1.0, -1.0,
             1.0, -1.0,  1.0,
             1.0, -1.0, -1.0,
             1.0, -1.0,  1.0,
            -1.0, -1.0, -1.0,
            -1.0, -1.0,  1.0,

            # Top face
            -1.0,  1.0, -1.0,
             1.0,  1.0, -1.0,
             1.0,  1.0,  1.0,
             1.0,  1.0,  1.0,
            -1.0,  1.0,  1.0,
            -1.0,  1.0, -1.0,
        ], dtype='f4')

        # Create vertex buffer
        vbo = self.ctx.buffer(vertices.tobytes())

        # Create vertex array object
        self.vao = self.ctx.vertex_array(
            self.shader.program,
            [(vbo, '3f', 'in_position')]
        )

    def render(self, view: glm.mat4, projection: glm.mat4,
               color_top: glm.vec3 = glm.vec3(0.5, 0.7, 1.0),
               color_bottom: glm.vec3 = glm.vec3(0.8, 0.9, 1.0)):
        """
        Render skybox.

        Args:
            view: View matrix from camera
            projection: Projection matrix
            color_top: Sky color at zenith (top)
            color_bottom: Sky color at horizon (bottom)
        """
        # Remove translation from view matrix (keep only rotation)
        # This makes skybox appear infinitely distant
        view_rotation = glm.mat4(glm.mat3(view))

        # Upload uniforms
        self.shader.program['view'].write(view_rotation)
        self.shader.program['projection'].write(projection)
        self.shader.program['color_top'].write(color_top)
        self.shader.program['color_bottom'].write(color_bottom)

        # Render skybox
        # Note: Depth function should be set to LEQUAL before this
        self.vao.render(moderngl.TRIANGLES)

    def release(self):
        """Release OpenGL resources."""
        if self.vao:
            self.vao.release()
        logger.info("Skybox released")

    def __str__(self):
        """String representation."""
        return "Skybox(gradient)"


class ProceduralSky:
    """
    Procedural sky with gradient and optional sun/moon.

    Simpler alternative to textured skybox.
    Uses vertex colors for gradient from horizon to zenith.
    """

    def __init__(self, ctx: moderngl.Context, shader):
        """
        Initialize procedural sky.

        Args:
            ctx: ModernGL context
            shader: Sky shader program
        """
        self.ctx = ctx
        self.shader = shader

        # Sky colors
        self.zenith_color = glm.vec3(0.3, 0.5, 0.9)   # Deep blue at top
        self.horizon_color = glm.vec3(0.7, 0.8, 0.95)  # Light blue at horizon

        # Time of day (0-24, affects colors)
        self.time_of_day = 12.0  # Noon

        # Create sky dome mesh
        self._create_sky_dome()

        logger.info("Procedural sky initialized")

    def _create_sky_dome(self):
        """
        Create hemisphere sky dome.

        More efficient than full skybox for outdoor scenes.
        """
        # For simplicity, use same cube as skybox
        # In production, would use hemisphere with better vertex distribution
        vertices = np.array([
            # Positions for skybox cube (same as Skybox class)
            -1.0, -1.0, -1.0,  1.0, -1.0, -1.0,  1.0,  1.0, -1.0,
             1.0,  1.0, -1.0, -1.0,  1.0, -1.0, -1.0, -1.0, -1.0,
            -1.0, -1.0,  1.0,  1.0,  1.0,  1.0,  1.0, -1.0,  1.0,
             1.0,  1.0,  1.0, -1.0, -1.0,  1.0, -1.0,  1.0,  1.0,
            -1.0,  1.0,  1.0, -1.0, -1.0, -1.0, -1.0,  1.0, -1.0,
            -1.0, -1.0, -1.0, -1.0,  1.0,  1.0, -1.0, -1.0,  1.0,
             1.0,  1.0,  1.0,  1.0,  1.0, -1.0,  1.0, -1.0, -1.0,
             1.0, -1.0, -1.0,  1.0, -1.0,  1.0,  1.0,  1.0,  1.0,
            -1.0, -1.0, -1.0,  1.0, -1.0,  1.0,  1.0, -1.0, -1.0,
             1.0, -1.0,  1.0, -1.0, -1.0, -1.0, -1.0, -1.0,  1.0,
            -1.0,  1.0, -1.0,  1.0,  1.0, -1.0,  1.0,  1.0,  1.0,
             1.0,  1.0,  1.0, -1.0,  1.0,  1.0, -1.0,  1.0, -1.0,
        ], dtype='f4')

        vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.shader.program,
            [(vbo, '3f', 'in_position')]
        )

    def set_time_of_day(self, time: float):
        """
        Set time of day (0-24 hours).

        Affects sky colors:
        - Dawn/Dusk: Orange/red tints
        - Day: Blue sky
        - Night: Dark blue/black

        Args:
            time: Time in hours (0-24)
        """
        self.time_of_day = time % 24.0

        # Calculate sky colors based on time
        if 6.0 <= time < 8.0:  # Dawn
            t = (time - 6.0) / 2.0
            self.horizon_color = glm.mix(
                glm.vec3(1.0, 0.6, 0.3),  # Orange
                glm.vec3(0.7, 0.8, 0.95),  # Day horizon
                t
            )
            self.zenith_color = glm.mix(
                glm.vec3(0.3, 0.3, 0.6),  # Dark blue
                glm.vec3(0.3, 0.5, 0.9),  # Day zenith
                t
            )
        elif 8.0 <= time < 18.0:  # Day
            self.horizon_color = glm.vec3(0.7, 0.8, 0.95)
            self.zenith_color = glm.vec3(0.3, 0.5, 0.9)
        elif 18.0 <= time < 20.0:  # Dusk
            t = (time - 18.0) / 2.0
            self.horizon_color = glm.mix(
                glm.vec3(0.7, 0.8, 0.95),  # Day horizon
                glm.vec3(0.9, 0.5, 0.3),  # Orange/red
                t
            )
            self.zenith_color = glm.mix(
                glm.vec3(0.3, 0.5, 0.9),  # Day zenith
                glm.vec3(0.2, 0.2, 0.4),  # Dark blue
                t
            )
        else:  # Night
            self.horizon_color = glm.vec3(0.1, 0.1, 0.2)
            self.zenith_color = glm.vec3(0.05, 0.05, 0.15)

    def render(self, view: glm.mat4, projection: glm.mat4):
        """Render procedural sky."""
        # Remove translation from view matrix
        view_rotation = glm.mat4(glm.mat3(view))

        # Upload uniforms
        self.shader.program['view'].write(view_rotation)
        self.shader.program['projection'].write(projection)
        self.shader.program['color_top'].write(self.zenith_color)
        self.shader.program['color_bottom'].write(self.horizon_color)

        # Render
        self.vao.render(moderngl.TRIANGLES)

    def release(self):
        """Release resources."""
        if self.vao:
            self.vao.release()
        logger.info("Procedural sky released")
