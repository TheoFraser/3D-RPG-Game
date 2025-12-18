"""Mesh and geometry handling."""
import moderngl
import numpy as np
from graphics.shader import Shader


class Mesh:
    """Represents a 3D mesh with vertices, indices, and textures."""

    def __init__(self, ctx: moderngl.Context, vertices: np.ndarray, indices: np.ndarray,
                 shader: Shader, vertex_format: str, vertex_attributes: list):
        """
        Create a mesh.

        Args:
            ctx: ModernGL context
            vertices: Vertex data as numpy array
            indices: Index data as numpy array
            shader: Shader program to use
            vertex_format: Format string (e.g., '3f 2f 3f' for pos, uv, normal)
            vertex_attributes: List of attribute names matching shader
        """
        self.ctx = ctx
        self.shader = shader

        # Create buffers
        self.vbo = ctx.buffer(vertices.tobytes())
        self.ibo = ctx.buffer(indices.tobytes())

        # Create VAO
        self.vao = ctx.vertex_array(
            shader.program,
            [(self.vbo, vertex_format, *vertex_attributes)],
            self.ibo
        )

        self.index_count = len(indices)

    def render(self):
        """Render the mesh."""
        self.vao.render()

    def release(self):
        """Release mesh resources."""
        self.vao.release()
        self.vbo.release()
        self.ibo.release()

    @staticmethod
    def create_cube(ctx: moderngl.Context, shader: Shader, textured=True):
        """
        Create a cube mesh.

        Args:
            ctx: ModernGL context
            shader: Shader program
            textured: Whether to include texture coordinates and normals
        """
        if textured:
            # Cube with texture coordinates, normals, and white vertex colors
            vertices = np.array([
                # Position        Normal         UV         Color (white)
                # Front face (+Z)
                -0.5, -0.5,  0.5,  0.0, 0.0, 1.0,  0.0, 0.0,  1.0, 1.0, 1.0,
                 0.5, -0.5,  0.5,  0.0, 0.0, 1.0,  1.0, 0.0,  1.0, 1.0, 1.0,
                 0.5,  0.5,  0.5,  0.0, 0.0, 1.0,  1.0, 1.0,  1.0, 1.0, 1.0,
                -0.5,  0.5,  0.5,  0.0, 0.0, 1.0,  0.0, 1.0,  1.0, 1.0, 1.0,

                # Back face (-Z)
                 0.5, -0.5, -0.5,  0.0, 0.0, -1.0,  0.0, 0.0,  1.0, 1.0, 1.0,
                -0.5, -0.5, -0.5,  0.0, 0.0, -1.0,  1.0, 0.0,  1.0, 1.0, 1.0,
                -0.5,  0.5, -0.5,  0.0, 0.0, -1.0,  1.0, 1.0,  1.0, 1.0, 1.0,
                 0.5,  0.5, -0.5,  0.0, 0.0, -1.0,  0.0, 1.0,  1.0, 1.0, 1.0,

                # Top face (+Y)
                -0.5,  0.5, -0.5,  0.0, 1.0, 0.0,  0.0, 0.0,  1.0, 1.0, 1.0,
                -0.5,  0.5,  0.5,  0.0, 1.0, 0.0,  0.0, 1.0,  1.0, 1.0, 1.0,
                 0.5,  0.5,  0.5,  0.0, 1.0, 0.0,  1.0, 1.0,  1.0, 1.0, 1.0,
                 0.5,  0.5, -0.5,  0.0, 1.0, 0.0,  1.0, 0.0,  1.0, 1.0, 1.0,

                # Bottom face (-Y)
                -0.5, -0.5,  0.5,  0.0, -1.0, 0.0,  0.0, 0.0,  1.0, 1.0, 1.0,
                -0.5, -0.5, -0.5,  0.0, -1.0, 0.0,  0.0, 1.0,  1.0, 1.0, 1.0,
                 0.5, -0.5, -0.5,  0.0, -1.0, 0.0,  1.0, 1.0,  1.0, 1.0, 1.0,
                 0.5, -0.5,  0.5,  0.0, -1.0, 0.0,  1.0, 0.0,  1.0, 1.0, 1.0,

                # Right face (+X)
                 0.5, -0.5,  0.5,  1.0, 0.0, 0.0,  0.0, 0.0,  1.0, 1.0, 1.0,
                 0.5, -0.5, -0.5,  1.0, 0.0, 0.0,  1.0, 0.0,  1.0, 1.0, 1.0,
                 0.5,  0.5, -0.5,  1.0, 0.0, 0.0,  1.0, 1.0,  1.0, 1.0, 1.0,
                 0.5,  0.5,  0.5,  1.0, 0.0, 0.0,  0.0, 1.0,  1.0, 1.0, 1.0,

                # Left face (-X)
                -0.5, -0.5, -0.5,  -1.0, 0.0, 0.0,  0.0, 0.0,  1.0, 1.0, 1.0,
                -0.5, -0.5,  0.5,  -1.0, 0.0, 0.0,  1.0, 0.0,  1.0, 1.0, 1.0,
                -0.5,  0.5,  0.5,  -1.0, 0.0, 0.0,  1.0, 1.0,  1.0, 1.0, 1.0,
                -0.5,  0.5, -0.5,  -1.0, 0.0, 0.0,  0.0, 1.0,  1.0, 1.0, 1.0,
            ], dtype='f4')

            indices = np.array([
                0, 1, 2,  2, 3, 0,    # Front
                4, 5, 6,  6, 7, 4,    # Back
                8, 9, 10, 10, 11, 8,  # Top
                12, 13, 14, 14, 15, 12,  # Bottom
                16, 17, 18, 18, 19, 16,  # Right
                20, 21, 22, 22, 23, 20,  # Left
            ], dtype='i4')

            return Mesh(ctx, vertices, indices, shader, '3f 3f 2f 3f',
                       ['in_position', 'in_normal', 'in_texcoord', 'in_color'])
        else:
            # Colored cube (from Phase 1)
            vertices = np.array([
                # Front face (red)
                -0.5, -0.5,  0.5,  1.0, 0.0, 0.0,
                 0.5, -0.5,  0.5,  1.0, 0.0, 0.0,
                 0.5,  0.5,  0.5,  1.0, 0.0, 0.0,
                -0.5,  0.5,  0.5,  1.0, 0.0, 0.0,

                # Back face (green)
                -0.5, -0.5, -0.5,  0.0, 1.0, 0.0,
                 0.5, -0.5, -0.5,  0.0, 1.0, 0.0,
                 0.5,  0.5, -0.5,  0.0, 1.0, 0.0,
                -0.5,  0.5, -0.5,  0.0, 1.0, 0.0,

                # Top face (blue)
                -0.5,  0.5, -0.5,  0.0, 0.0, 1.0,
                -0.5,  0.5,  0.5,  0.0, 0.0, 1.0,
                 0.5,  0.5,  0.5,  0.0, 0.0, 1.0,
                 0.5,  0.5, -0.5,  0.0, 0.0, 1.0,

                # Bottom face (yellow)
                -0.5, -0.5, -0.5,  1.0, 1.0, 0.0,
                -0.5, -0.5,  0.5,  1.0, 1.0, 0.0,
                 0.5, -0.5,  0.5,  1.0, 1.0, 0.0,
                 0.5, -0.5, -0.5,  1.0, 1.0, 0.0,

                # Right face (magenta)
                 0.5, -0.5, -0.5,  1.0, 0.0, 1.0,
                 0.5,  0.5, -0.5,  1.0, 0.0, 1.0,
                 0.5,  0.5,  0.5,  1.0, 0.0, 1.0,
                 0.5, -0.5,  0.5,  1.0, 0.0, 1.0,

                # Left face (cyan)
                -0.5, -0.5, -0.5,  0.0, 1.0, 1.0,
                -0.5,  0.5, -0.5,  0.0, 1.0, 1.0,
                -0.5,  0.5,  0.5,  0.0, 1.0, 1.0,
                -0.5, -0.5,  0.5,  0.0, 1.0, 1.0,
            ], dtype='f4')

            indices = np.array([
                0, 1, 2,  2, 3, 0,    # Front
                4, 5, 6,  6, 7, 4,    # Back
                8, 9, 10, 10, 11, 8,  # Top
                12, 13, 14, 14, 15, 12,  # Bottom
                16, 17, 18, 18, 19, 16,  # Right
                20, 21, 22, 22, 23, 20,  # Left
            ], dtype='i4')

            return Mesh(ctx, vertices, indices, shader, '3f 3f',
                       ['in_position', 'in_color'])

    @staticmethod
    def create_plane(ctx: moderngl.Context, shader: Shader, size=10.0, subdivisions=10):
        """
        Create a plane mesh (ground).

        Args:
            ctx: ModernGL context
            shader: Shader program
            size: Size of the plane
            subdivisions: Number of subdivisions for detail
        """
        vertices = []
        indices = []

        # Generate vertices
        for z in range(subdivisions + 1):
            for x in range(subdivisions + 1):
                # Position
                px = (x / subdivisions - 0.5) * size
                py = 0.0
                pz = (z / subdivisions - 0.5) * size

                # UV coordinates
                u = x / subdivisions * (size / 2)  # Tile texture
                v = z / subdivisions * (size / 2)

                # Normal (always up)
                nx, ny, nz = 0.0, 1.0, 0.0

                vertices.extend([px, py, pz, u, v, nx, ny, nz])

        # Generate indices
        for z in range(subdivisions):
            for x in range(subdivisions):
                # First triangle
                top_left = z * (subdivisions + 1) + x
                top_right = top_left + 1
                bottom_left = (z + 1) * (subdivisions + 1) + x
                bottom_right = bottom_left + 1

                indices.extend([top_left, bottom_left, top_right])
                indices.extend([top_right, bottom_left, bottom_right])

        vertices = np.array(vertices, dtype='f4')
        indices = np.array(indices, dtype='i4')

        return Mesh(ctx, vertices, indices, shader, '3f 2f 3f',
                   ['in_position', 'in_texcoord', 'in_normal'])
