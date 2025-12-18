"""Terrain generation and mesh creation."""
import numpy as np
import moderngl
import glm
from world_gen.numba_terrain import (
    generate_terrain_heightmap,
    apply_terrain_curve,
    calculate_normals
)
from game.logger import get_logger

logger = get_logger(__name__)


class Terrain:
    """Procedurally generated terrain mesh."""

    def __init__(self, ctx, shader, size=50, resolution=64, seed=42):
        """
        Create procedural terrain.

        Args:
            ctx: ModernGL context
            shader: Shader program for rendering
            size: World-space size of terrain
            resolution: Number of vertices per side
            seed: Random seed for generation
        """
        self.ctx = ctx
        self.shader = shader
        self.size = size
        self.resolution = resolution
        self.seed = seed

        # Generate terrain
        logger.info(f"Generating terrain (Numba-optimized)...")
        self.heightmap = self.generate_heightmap()
        logger.info(f"Creating terrain mesh...")
        self.mesh = self.create_mesh()
        logger.info(f"Terrain ready: {resolution}x{resolution} vertices")

    def generate_heightmap(self):
        """Generate terrain heightmap using Numba."""
        heightmap = generate_terrain_heightmap(
            width=self.resolution,
            height=self.resolution,
            scale=50.0,        # Larger scale = broader, gentler features
            octaves=2,         # Fewer octaves = less detail, smoother
            persistence=0.3,   # Lower = each octave contributes less
            lacunarity=2.0,    # Frequency multiplier per octave
            seed=self.seed,
            offset_x=0.0,
            offset_z=0.0,
            chunk_size=self.size  # Legacy terrain uses self.size instead of CHUNK_SIZE
        )

        # Apply very gentle curve for subtle variation
        heightmap = apply_terrain_curve(heightmap, power=1.2)

        # Scale height to be nearly flat (good for puzzles)
        heightmap = heightmap * 0.5  # Max height of 0.5 units (very flat!)

        return heightmap

    def create_mesh(self):
        """Convert heightmap to 3D mesh."""
        vertices = []
        indices = []

        # Calculate normals
        normals = calculate_normals(
            self.heightmap,
            scale_xz=self.size / self.resolution,
            scale_y=1.0
        )

        # Generate vertices
        for z in range(self.resolution):
            for x in range(self.resolution):
                # Position
                world_x = (x / (self.resolution - 1) - 0.5) * self.size
                world_z = (z / (self.resolution - 1) - 0.5) * self.size
                world_y = self.heightmap[z, x]

                # UV coordinates
                u = x / (self.resolution - 1)
                v = z / (self.resolution - 1)

                # Normal
                nx, ny, nz = normals[z, x]

                vertices.extend([
                    world_x, world_y, world_z,  # Position
                    u * 5, v * 5,                # UV (tiled)
                    nx, ny, nz                   # Normal
                ])

        # Generate indices
        for z in range(self.resolution - 1):
            for x in range(self.resolution - 1):
                top_left = z * self.resolution + x
                top_right = top_left + 1
                bottom_left = (z + 1) * self.resolution + x
                bottom_right = bottom_left + 1

                # Two triangles per quad
                indices.extend([top_left, bottom_left, top_right])
                indices.extend([top_right, bottom_left, bottom_right])

        vertices = np.array(vertices, dtype='f4')
        indices = np.array(indices, dtype='i4')

        # Create buffers
        vbo = self.ctx.buffer(vertices.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())

        # Create VAO
        vao = self.ctx.vertex_array(
            self.shader.program,
            [(vbo, '3f 2f 3f', 'in_position', 'in_texcoord', 'in_normal')],
            ibo
        )

        return {
            'vao': vao,
            'vbo': vbo,
            'ibo': ibo,
            'vertex_count': len(indices)
        }

    def render(self):
        """Render the terrain."""
        self.mesh['vao'].render()

    def release(self):
        """Release GPU resources."""
        self.mesh['vao'].release()
        self.mesh['vbo'].release()
        self.mesh['ibo'].release()

    def get_height_at(self, world_x, world_z):
        """
        Get terrain height at world position.

        Args:
            world_x, world_z: World coordinates

        Returns:
            float: Height at that position
        """
        # Convert world coords to heightmap coords
        local_x = (world_x / self.size + 0.5) * (self.resolution - 1)
        local_z = (world_z / self.size + 0.5) * (self.resolution - 1)

        # Clamp to bounds
        local_x = max(0, min(self.resolution - 1, local_x))
        local_z = max(0, min(self.resolution - 1, local_z))

        # Bilinear interpolation
        x0 = int(local_x)
        z0 = int(local_z)
        x1 = min(x0 + 1, self.resolution - 1)
        z1 = min(z0 + 1, self.resolution - 1)

        fx = local_x - x0
        fz = local_z - z0

        h00 = self.heightmap[z0, x0]
        h10 = self.heightmap[z0, x1]
        h01 = self.heightmap[z1, x0]
        h11 = self.heightmap[z1, x1]

        h0 = h00 * (1 - fx) + h10 * fx
        h1 = h01 * (1 - fx) + h11 * fx

        return h0 * (1 - fz) + h1 * fz
