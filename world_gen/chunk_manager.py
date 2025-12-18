"""Chunk manager for world streaming."""
import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from collections import deque
import threading
import config
from world_gen.chunk import Chunk, ChunkState, ChunkData, world_to_chunk
from world_gen.numba_terrain import (
    generate_terrain_heightmap,
    apply_terrain_curve,
    calculate_normals
)
from world_gen.spawn_system import SpawnSystem
from game.logger import get_logger

logger = get_logger(__name__)


class ChunkManager:
    """
    Manages chunk loading, generation, and streaming.

    Handles dynamic loading/unloading of terrain chunks based on
    player position to enable large open world exploration.
    """

    def __init__(self, ctx, shader, seed: int = None):
        """
        Initialize chunk manager.

        Args:
            ctx: ModernGL context
            shader: Terrain shader program
            seed: World generation seed
        """
        self.ctx = ctx
        self.shader = shader
        self.seed = seed if seed is not None else config.WORLD_SEED

        # Chunk storage
        self.chunks: Dict[Tuple[int, int], Chunk] = {}

        # Generation queue
        self.generation_queue: deque = deque()
        self.upload_queue: deque = deque()

        # Track player chunk for change detection
        self.player_chunk: Optional[Tuple[int, int]] = None

        # Stats
        self.chunks_loaded = 0
        self.chunks_generated = 0

        # Biome manager (will be set externally)
        self.biome_manager = None

        # Vegetation manager (will be set externally)
        self.vegetation_manager = None

        # Spawn system for enemies
        self.spawn_system = SpawnSystem(seed=self.seed)
        self.enemy_manager = None  # Will be set externally

        logger.info(f"ChunkManager initialized (seed={self.seed})")

    def set_biome_manager(self, biome_manager) -> None:
        """Set the biome manager for biome-aware generation."""
        self.biome_manager = biome_manager

    def set_vegetation_manager(self, vegetation_manager) -> None:
        """Set the vegetation manager for vegetation generation."""
        self.vegetation_manager = vegetation_manager

    def set_enemy_manager(self, enemy_manager) -> None:
        """Set the enemy manager for spawning enemies."""
        self.enemy_manager = enemy_manager

    def update(self, player_x: float, player_z: float) -> None:
        """
        Update chunk loading based on player position.

        Args:
            player_x, player_z: Player world position
        """
        # Get player's current chunk
        current_chunk = world_to_chunk(player_x, player_z)

        # Check if player moved to a new chunk
        if current_chunk != self.player_chunk:
            self.player_chunk = current_chunk
            self._update_loaded_chunks(current_chunk)

        # Process generation queue (generate one per frame)
        self._process_generation_queue()

        # Process upload queue (upload one per frame)
        self._process_upload_queue()

    def _update_loaded_chunks(self, center_chunk: Tuple[int, int]) -> None:
        """
        Update which chunks should be loaded.

        Args:
            center_chunk: Chunk coordinates the player is in
        """
        cx, cz = center_chunk

        # Calculate chunks that should be loaded
        should_load: Set[Tuple[int, int]] = set()
        for dx in range(-config.LOAD_DISTANCE, config.LOAD_DISTANCE + 1):
            for dz in range(-config.LOAD_DISTANCE, config.LOAD_DISTANCE + 1):
                chunk_key = (cx + dx, cz + dz)
                should_load.add(chunk_key)

        # Queue new chunks for loading
        for chunk_key in should_load:
            if chunk_key not in self.chunks:
                chunk = Chunk(chunk_key[0], chunk_key[1])
                self.chunks[chunk_key] = chunk
                self.generation_queue.append(chunk_key)

        # Find chunks to unload
        chunks_to_unload = []
        for chunk_key, chunk in self.chunks.items():
            dx = abs(chunk_key[0] - cx)
            dz = abs(chunk_key[1] - cz)
            if dx > config.UNLOAD_DISTANCE or dz > config.UNLOAD_DISTANCE:
                chunks_to_unload.append(chunk_key)

        # Unload distant chunks
        for chunk_key in chunks_to_unload:
            self._unload_chunk(chunk_key)

    def _process_generation_queue(self) -> None:
        """Process one chunk from the generation queue."""
        if not self.generation_queue:
            return

        chunk_key = self.generation_queue.popleft()
        if chunk_key not in self.chunks:
            return

        chunk = self.chunks[chunk_key]
        if chunk.state != ChunkState.UNLOADED:
            return

        chunk.state = ChunkState.GENERATING
        self._generate_chunk(chunk)
        chunk.state = ChunkState.MESHING

        # Queue for GPU upload
        self.upload_queue.append(chunk_key)

    def _process_upload_queue(self) -> None:
        """Process one chunk from the upload queue."""
        if not self.upload_queue:
            return

        chunk_key = self.upload_queue.popleft()
        if chunk_key not in self.chunks:
            return

        chunk = self.chunks[chunk_key]
        if chunk.state != ChunkState.MESHING:
            return

        chunk.upload_to_gpu(self.ctx, self.shader)
        self.chunks_loaded += 1

    def _generate_chunk(self, chunk: Chunk) -> None:
        """
        Generate terrain data for a chunk.

        Args:
            chunk: Chunk to generate
        """
        res = config.CHUNK_RESOLUTION

        # Get biome for this chunk
        if self.biome_manager:
            chunk.primary_biome = self.biome_manager.get_biome_at(
                chunk.world_x + config.CHUNK_SIZE / 2,
                chunk.world_z + config.CHUNK_SIZE / 2
            )
            height_scale = config.BIOME_HEIGHT_SCALE.get(
                chunk.primary_biome, 5.0
            )
        else:
            height_scale = 5.0

        # Generate heightmap with chunk offset
        heightmap = generate_terrain_heightmap(
            width=res,
            height=res,
            scale=50.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            seed=self.seed,
            offset_x=chunk.world_x,
            offset_z=chunk.world_z,
            chunk_size=config.CHUNK_SIZE
        )

        # Apply height curve
        heightmap = apply_terrain_curve(heightmap, power=1.5)

        # Scale by biome
        heightmap = heightmap * height_scale

        # Blend edges with neighboring chunks to ensure smooth transitions
        heightmap = self._blend_chunk_edges(chunk, heightmap)

        # Generate biome map
        biome_map = np.full((res, res), chunk.primary_biome, dtype=np.int32)
        if self.biome_manager:
            for z in range(res):
                for x in range(res):
                    world_x = chunk.world_x + (x / (res - 1)) * config.CHUNK_SIZE
                    world_z = chunk.world_z + (z / (res - 1)) * config.CHUNK_SIZE
                    biome_map[z, x] = self.biome_manager.get_biome_at(world_x, world_z)

        # Calculate normals
        normals = calculate_normals(
            heightmap,
            scale_xz=config.CHUNK_SIZE / res,
            scale_y=1.0
        )

        # Build mesh
        vertices, indices = self._build_mesh(chunk, heightmap, normals, biome_map)

        # Store data
        chunk.data = ChunkData(
            heightmap=heightmap,
            biome_map=biome_map,
            vertices=vertices,
            indices=indices,
            normals=normals
        )

        # Spawn enemies for this chunk (Phase 4.2)
        if self.enemy_manager is not None:
            enemies = self.spawn_system.generate_spawns_for_chunk(
                chunk.chunk_x,
                chunk.chunk_z,
                chunk.primary_biome,
                self
            )
            for enemy in enemies:
                self.enemy_manager.add_enemy(enemy)
                chunk.enemies.append(enemy)

        # Generate vegetation for this chunk (Phase 2.2)
        if self.vegetation_manager is not None:
            vegetation = self.vegetation_manager.generate_vegetation_for_chunk(
                chunk.chunk_x,
                chunk.chunk_z,
                config.CHUNK_SIZE,
                self.biome_manager,
                self.get_height_at
            )
            chunk.vegetation = vegetation

        self.chunks_generated += 1

    def _blend_chunk_edges(self, chunk: Chunk, heightmap: np.ndarray) -> np.ndarray:
        """
        Blend chunk edges with neighboring chunks for smooth transitions.

        Args:
            chunk: Current chunk
            heightmap: Heightmap to blend

        Returns:
            Blended heightmap
        """
        res = config.CHUNK_RESOLUTION
        blend_width = min(4, res // 4)  # Blend over 4 vertices (or fewer for small chunks)

        cx, cz = chunk.chunk_x, chunk.chunk_z

        # Check each neighbor and blend edges if they exist and are ready
        neighbors = {
            'left': (cx - 1, cz),
            'right': (cx + 1, cz),
            'front': (cx, cz - 1),
            'back': (cx, cz + 1)
        }

        for direction, (nx, nz) in neighbors.items():
            neighbor_key = (nx, nz)
            if neighbor_key not in self.chunks:
                continue

            neighbor = self.chunks[neighbor_key]
            if not neighbor.data or neighbor.data.heightmap is None:
                continue

            neighbor_heightmap = neighbor.data.heightmap

            # Blend edges based on direction
            if direction == 'left':  # x = 0
                # Current chunk's left edge should match neighbor's right edge
                for z in range(res):
                    neighbor_height = neighbor_heightmap[z, -1]  # Neighbor's right edge
                    current_height = heightmap[z, 0]

                    # Blend across blend_width vertices
                    for i in range(blend_width):
                        if i >= res:
                            break
                        blend_factor = 1.0 - (i / blend_width)  # 1.0 at edge, 0.0 at blend_width
                        heightmap[z, i] = current_height * (1.0 - blend_factor) + neighbor_height * blend_factor

            elif direction == 'right':  # x = res-1
                # Current chunk's right edge should match neighbor's left edge
                for z in range(res):
                    neighbor_height = neighbor_heightmap[z, 0]  # Neighbor's left edge
                    current_height = heightmap[z, -1]

                    for i in range(blend_width):
                        x = res - 1 - i
                        if x < 0:
                            break
                        blend_factor = 1.0 - (i / blend_width)
                        heightmap[z, x] = current_height * (1.0 - blend_factor) + neighbor_height * blend_factor

            elif direction == 'front':  # z = 0
                # Current chunk's front edge should match neighbor's back edge
                for x in range(res):
                    neighbor_height = neighbor_heightmap[-1, x]  # Neighbor's back edge
                    current_height = heightmap[0, x]

                    for i in range(blend_width):
                        if i >= res:
                            break
                        blend_factor = 1.0 - (i / blend_width)
                        heightmap[i, x] = current_height * (1.0 - blend_factor) + neighbor_height * blend_factor

            elif direction == 'back':  # z = res-1
                # Current chunk's back edge should match neighbor's front edge
                for x in range(res):
                    neighbor_height = neighbor_heightmap[0, x]  # Neighbor's front edge
                    current_height = heightmap[-1, x]

                    for i in range(blend_width):
                        z = res - 1 - i
                        if z < 0:
                            break
                        blend_factor = 1.0 - (i / blend_width)
                        heightmap[z, x] = current_height * (1.0 - blend_factor) + neighbor_height * blend_factor

        return heightmap

    def _build_mesh(
        self,
        chunk: Chunk,
        heightmap: np.ndarray,
        normals: np.ndarray,
        biome_map: np.ndarray = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build mesh data from heightmap with vertical skirts to prevent gaps.

        Args:
            chunk: Chunk being built
            heightmap: Height values
            normals: Normal vectors
            biome_map: Biome IDs for each vertex (optional)

        Returns:
            Tuple of (vertices, indices) arrays
        """
        res = config.CHUNK_RESOLUTION
        vertices = []
        indices = []

        # Generate main terrain vertices
        for z in range(res):
            for x in range(res):
                # World position
                world_x = chunk.world_x + (x / (res - 1)) * config.CHUNK_SIZE
                world_z = chunk.world_z + (z / (res - 1)) * config.CHUNK_SIZE
                world_y = heightmap[z, x]

                # UV coordinates (tiled)
                u = x / (res - 1) * 4
                v = z / (res - 1) * 4

                # Normal
                nx, ny, nz = normals[z, x]

                # Biome color
                if biome_map is not None:
                    biome_id = biome_map[z, x]
                    biome_color = config.BIOME_COLORS.get(biome_id, (0.5, 0.5, 0.5))
                else:
                    biome_color = (0.5, 0.5, 0.5)  # Default gray

                vertices.extend([
                    world_x, world_y, world_z,  # Position (3)
                    u, v,                        # UV (2)
                    nx, ny, nz,                  # Normal (3)
                    biome_color[0], biome_color[1], biome_color[2]  # Color (3)
                ])

        # Generate main terrain indices
        for z in range(res - 1):
            for x in range(res - 1):
                top_left = z * res + x
                top_right = top_left + 1
                bottom_left = (z + 1) * res + x
                bottom_right = bottom_left + 1

                indices.extend([top_left, bottom_left, top_right])
                indices.extend([top_right, bottom_left, bottom_right])

        # Add vertical skirts to cover gaps between chunks
        # Skirts drop from edge vertices down to a base level
        base_vertex_count = res * res
        skirt_base_y = np.min(heightmap) - 20.0  # Drop skirts well below terrain

        # Left edge skirt (x = 0)
        for z in range(res - 1):
            x = 0
            # Top vertices (already exist in main mesh)
            top_idx1 = z * res + x
            top_idx2 = (z + 1) * res + x

            # Bottom vertices (new)
            world_x = chunk.world_x + (x / (res - 1)) * config.CHUNK_SIZE
            world_z1 = chunk.world_z + (z / (res - 1)) * config.CHUNK_SIZE
            world_z2 = chunk.world_z + ((z + 1) / (res - 1)) * config.CHUNK_SIZE

            bottom_idx1 = len(vertices) // 11
            bottom_idx2 = bottom_idx1 + 1

            # Add bottom vertices
            for world_z, v_coord in [(world_z1, z / (res - 1) * 4), (world_z2, (z + 1) / (res - 1) * 4)]:
                vertices.extend([
                    world_x, skirt_base_y, world_z,  # Position
                    0, v_coord,                       # UV
                    -1, 0, 0,                         # Left-facing normal
                    0.3, 0.2, 0.1                     # Dark brown color for skirts
                ])

            # Add skirt quad
            indices.extend([top_idx1, bottom_idx1, top_idx2])
            indices.extend([top_idx2, bottom_idx1, bottom_idx2])

        # Right edge skirt (x = res-1)
        for z in range(res - 1):
            x = res - 1
            top_idx1 = z * res + x
            top_idx2 = (z + 1) * res + x

            world_x = chunk.world_x + (x / (res - 1)) * config.CHUNK_SIZE
            world_z1 = chunk.world_z + (z / (res - 1)) * config.CHUNK_SIZE
            world_z2 = chunk.world_z + ((z + 1) / (res - 1)) * config.CHUNK_SIZE

            bottom_idx1 = len(vertices) // 11
            bottom_idx2 = bottom_idx1 + 1

            for world_z, v_coord in [(world_z1, z / (res - 1) * 4), (world_z2, (z + 1) / (res - 1) * 4)]:
                vertices.extend([
                    world_x, skirt_base_y, world_z,  # Position
                    4, v_coord,                       # UV
                    1, 0, 0,                          # Right-facing normal
                    0.3, 0.2, 0.1                     # Dark brown color for skirts
                ])

            # Add skirt quad (reversed winding for outward face)
            indices.extend([top_idx1, top_idx2, bottom_idx1])
            indices.extend([top_idx2, bottom_idx2, bottom_idx1])

        # Front edge skirt (z = 0)
        for x in range(res - 1):
            z = 0
            top_idx1 = z * res + x
            top_idx2 = z * res + (x + 1)

            world_x1 = chunk.world_x + (x / (res - 1)) * config.CHUNK_SIZE
            world_x2 = chunk.world_x + ((x + 1) / (res - 1)) * config.CHUNK_SIZE
            world_z = chunk.world_z + (z / (res - 1)) * config.CHUNK_SIZE

            bottom_idx1 = len(vertices) // 11
            bottom_idx2 = bottom_idx1 + 1

            for world_x, u_coord in [(world_x1, x / (res - 1) * 4), (world_x2, (x + 1) / (res - 1) * 4)]:
                vertices.extend([
                    world_x, skirt_base_y, world_z,  # Position
                    u_coord, 0,                       # UV
                    0, 0, -1,                         # Front-facing normal
                    0.3, 0.2, 0.1                     # Dark brown color for skirts
                ])

            indices.extend([top_idx1, top_idx2, bottom_idx1])
            indices.extend([top_idx2, bottom_idx2, bottom_idx1])

        # Back edge skirt (z = res-1)
        for x in range(res - 1):
            z = res - 1
            top_idx1 = z * res + x
            top_idx2 = z * res + (x + 1)

            world_x1 = chunk.world_x + (x / (res - 1)) * config.CHUNK_SIZE
            world_x2 = chunk.world_x + ((x + 1) / (res - 1)) * config.CHUNK_SIZE
            world_z = chunk.world_z + (z / (res - 1)) * config.CHUNK_SIZE

            bottom_idx1 = len(vertices) // 11
            bottom_idx2 = bottom_idx1 + 1

            for world_x, u_coord in [(world_x1, x / (res - 1) * 4), (world_x2, (x + 1) / (res - 1) * 4)]:
                vertices.extend([
                    world_x, skirt_base_y, world_z,  # Position
                    u_coord, 4,                       # UV
                    0, 0, 1,                          # Back-facing normal
                    0.3, 0.2, 0.1                     # Dark brown color for skirts
                ])

            indices.extend([top_idx1, bottom_idx1, top_idx2])
            indices.extend([top_idx2, bottom_idx1, bottom_idx2])

        return (
            np.array(vertices, dtype='f4'),
            np.array(indices, dtype='i4')
        )

    def _unload_chunk(self, chunk_key: Tuple[int, int]) -> None:
        """
        Unload a chunk.

        Args:
            chunk_key: Key of chunk to unload
        """
        if chunk_key in self.chunks:
            self.chunks[chunk_key].unload()
            del self.chunks[chunk_key]

    def get_chunk_at(self, world_x: float, world_z: float) -> Optional[Chunk]:
        """
        Get the chunk at a world position.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Chunk at that position, or None if not loaded
        """
        chunk_key = world_to_chunk(world_x, world_z)
        return self.chunks.get(chunk_key)

    def get_height_at(self, world_x: float, world_z: float) -> float:
        """
        Get terrain height at world position.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Terrain height, or 0.0 if chunk not loaded
        """
        chunk = self.get_chunk_at(world_x, world_z)
        if chunk and chunk.is_ready:
            return chunk.get_height_at(world_x, world_z)
        return 0.0

    def get_biome_at(self, world_x: float, world_z: float) -> int:
        """
        Get biome at world position.

        Args:
            world_x, world_z: World coordinates

        Returns:
            Biome ID, or GRASSLANDS if chunk not loaded
        """
        chunk = self.get_chunk_at(world_x, world_z)
        if chunk and chunk.is_ready:
            return chunk.get_biome_at(world_x, world_z)
        return config.BIOME_GRASSLANDS

    def render(self) -> int:
        """
        Render all loaded chunks.

        Returns:
            Number of chunks rendered
        """
        rendered = 0
        for chunk in self.chunks.values():
            if chunk.is_ready:
                chunk.render()
                rendered += 1
        return rendered

    def render_in_frustum(self, frustum) -> int:
        """
        Render only chunks visible in frustum.

        Args:
            frustum: Frustum for culling

        Returns:
            Number of chunks rendered
        """
        rendered = 0
        for chunk in self.chunks.values():
            if not chunk.is_ready:
                continue

            # Simple frustum check using chunk center and bounding sphere
            cx, cy, cz = chunk.center_world
            radius = config.CHUNK_SIZE * 0.7  # Approximate

            if frustum.sphere_in_frustum(cx, cy, cz, radius):
                chunk.render()
                rendered += 1

        return rendered

    def get_stats(self) -> Dict:
        """Get chunk manager statistics."""
        ready_count = sum(1 for c in self.chunks.values() if c.is_ready)
        return {
            'total_chunks': len(self.chunks),
            'ready_chunks': ready_count,
            'generation_queue': len(self.generation_queue),
            'upload_queue': len(self.upload_queue),
            'chunks_generated': self.chunks_generated,
            'player_chunk': self.player_chunk
        }

    def release(self) -> None:
        """Release all GPU resources."""
        for chunk in self.chunks.values():
            chunk.release_gpu()
        self.chunks.clear()
        logger.info("ChunkManager released")
