"""Chunk data structure for world streaming."""
import numpy as np
import moderngl
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import config


class ChunkState(Enum):
    """States a chunk can be in."""
    UNLOADED = auto()
    GENERATING = auto()
    MESHING = auto()
    READY = auto()
    UNLOADING = auto()


@dataclass
class ChunkData:
    """Raw data for a chunk before GPU upload."""
    heightmap: np.ndarray
    biome_map: np.ndarray
    vertices: Optional[np.ndarray] = None
    indices: Optional[np.ndarray] = None
    normals: Optional[np.ndarray] = None


class Chunk:
    """
    A chunk of terrain in the world.

    Chunks are CHUNK_SIZE x CHUNK_SIZE units in world space.
    Each chunk has its own heightmap, mesh, and GPU resources.
    """

    def __init__(self, chunk_x: int, chunk_z: int):
        """
        Create a new chunk.

        Args:
            chunk_x: Chunk X coordinate (not world coordinate)
            chunk_z: Chunk Z coordinate (not world coordinate)
        """
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z

        # World-space bounds
        self.world_x = chunk_x * config.CHUNK_SIZE
        self.world_z = chunk_z * config.CHUNK_SIZE
        self.world_x_max = self.world_x + config.CHUNK_SIZE
        self.world_z_max = self.world_z + config.CHUNK_SIZE

        # State
        self.state = ChunkState.UNLOADED

        # Data
        self.data: Optional[ChunkData] = None

        # GPU resources
        self.vao: Optional[moderngl.VertexArray] = None
        self.vbo: Optional[moderngl.Buffer] = None
        self.ibo: Optional[moderngl.Buffer] = None
        self.vertex_count: int = 0

        # Entities in this chunk
        self.entities: List[Any] = []
        self.npcs: List[Any] = []
        self.enemies: List[Any] = []
        self.vegetation: List[Any] = []  # Vegetation instances (Phase 2.2)

        # Primary biome for this chunk
        self.primary_biome: int = config.BIOME_GRASSLANDS

        # Min/max height for frustum culling
        self.min_height: float = 0.0
        self.max_height: float = 0.0

    @property
    def key(self) -> tuple:
        """Get chunk key for dictionary lookups."""
        return (self.chunk_x, self.chunk_z)

    @property
    def center_world(self) -> tuple:
        """Get world-space center of chunk."""
        return (
            self.world_x + config.CHUNK_SIZE / 2,
            (self.min_height + self.max_height) / 2,
            self.world_z + config.CHUNK_SIZE / 2
        )

    @property
    def is_ready(self) -> bool:
        """Check if chunk is ready for rendering."""
        return self.state == ChunkState.READY and self.vao is not None

    def contains_point(self, world_x: float, world_z: float) -> bool:
        """Check if a world point is within this chunk's bounds."""
        return (self.world_x <= world_x < self.world_x_max and
                self.world_z <= world_z < self.world_z_max)

    def distance_to(self, world_x: float, world_z: float) -> float:
        """Get distance from chunk center to a world point."""
        center_x = self.world_x + config.CHUNK_SIZE / 2
        center_z = self.world_z + config.CHUNK_SIZE / 2
        dx = world_x - center_x
        dz = world_z - center_z
        return (dx * dx + dz * dz) ** 0.5

    def get_height_at(self, world_x: float, world_z: float) -> float:
        """
        Get terrain height at world position within this chunk.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Height at that position, or 0 if no heightmap loaded
        """
        if self.data is None or self.data.heightmap is None:
            return 0.0

        # Convert world coords to local heightmap coords
        local_x = (world_x - self.world_x) / config.CHUNK_SIZE
        local_z = (world_z - self.world_z) / config.CHUNK_SIZE

        # Scale to heightmap resolution
        res = config.CHUNK_RESOLUTION
        hx = local_x * (res - 1)
        hz = local_z * (res - 1)

        # Clamp to bounds
        hx = max(0, min(res - 1, hx))
        hz = max(0, min(res - 1, hz))

        # Bilinear interpolation
        x0 = int(hx)
        z0 = int(hz)
        x1 = min(x0 + 1, res - 1)
        z1 = min(z0 + 1, res - 1)

        fx = hx - x0
        fz = hz - z0

        h00 = self.data.heightmap[z0, x0]
        h10 = self.data.heightmap[z0, x1]
        h01 = self.data.heightmap[z1, x0]
        h11 = self.data.heightmap[z1, x1]

        h0 = h00 * (1 - fx) + h10 * fx
        h1 = h01 * (1 - fx) + h11 * fx

        return h0 * (1 - fz) + h1 * fz

    def get_biome_at(self, world_x: float, world_z: float) -> int:
        """
        Get biome ID at world position within this chunk.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Biome ID at that position
        """
        if self.data is None or self.data.biome_map is None:
            return self.primary_biome

        # Convert world coords to local biome map coords
        local_x = (world_x - self.world_x) / config.CHUNK_SIZE
        local_z = (world_z - self.world_z) / config.CHUNK_SIZE

        # Scale to biome map resolution (same as heightmap)
        res = config.CHUNK_RESOLUTION
        bx = int(local_x * (res - 1))
        bz = int(local_z * (res - 1))

        # Clamp to bounds
        bx = max(0, min(res - 1, bx))
        bz = max(0, min(res - 1, bz))

        return int(self.data.biome_map[bz, bx])

    def upload_to_gpu(self, ctx: moderngl.Context, shader) -> None:
        """
        Upload chunk mesh data to GPU.

        Args:
            ctx: ModernGL context
            shader: Shader program for terrain
        """
        if self.data is None or self.data.vertices is None:
            return

        # Release old resources if any
        self.release_gpu()

        # Create buffers
        self.vbo = ctx.buffer(self.data.vertices.tobytes())
        self.ibo = ctx.buffer(self.data.indices.tobytes())

        # Create VAO with vertex format: position(3), UV(2), normal(3), color(3)
        self.vao = ctx.vertex_array(
            shader.program,
            [(self.vbo, '3f 2f 3f 3f', 'in_position', 'in_texcoord', 'in_normal', 'in_color')],
            self.ibo
        )

        self.vertex_count = len(self.data.indices)
        self.state = ChunkState.READY

        # Calculate height bounds for frustum culling
        if self.data.heightmap is not None:
            self.min_height = float(np.min(self.data.heightmap))
            self.max_height = float(np.max(self.data.heightmap))

    def release_gpu(self) -> None:
        """Release GPU resources."""
        if self.vao is not None:
            self.vao.release()
            self.vao = None
        if self.vbo is not None:
            self.vbo.release()
            self.vbo = None
        if self.ibo is not None:
            self.ibo.release()
            self.ibo = None
        self.vertex_count = 0

    def unload(self) -> None:
        """Fully unload chunk (GPU + data)."""
        self.release_gpu()
        self.data = None
        self.entities.clear()
        self.npcs.clear()
        self.enemies.clear()
        self.state = ChunkState.UNLOADED

    def render(self) -> None:
        """Render this chunk's terrain."""
        if self.vao is not None:
            self.vao.render()

    def __repr__(self) -> str:
        return f"Chunk({self.chunk_x}, {self.chunk_z}, state={self.state.name})"


def world_to_chunk(world_x: float, world_z: float) -> tuple:
    """
    Convert world coordinates to chunk coordinates.

    Args:
        world_x, world_z: World-space position

    Returns:
        Tuple of (chunk_x, chunk_z)
    """
    chunk_x = int(world_x // config.CHUNK_SIZE)
    chunk_z = int(world_z // config.CHUNK_SIZE)
    return (chunk_x, chunk_z)


def chunk_to_world(chunk_x: int, chunk_z: int) -> tuple:
    """
    Convert chunk coordinates to world coordinates (corner).

    Args:
        chunk_x, chunk_z: Chunk coordinates

    Returns:
        Tuple of (world_x, world_z) for chunk's corner
    """
    world_x = chunk_x * config.CHUNK_SIZE
    world_z = chunk_z * config.CHUNK_SIZE
    return (world_x, world_z)
