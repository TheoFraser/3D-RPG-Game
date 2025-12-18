"""Spatial partitioning system for efficient proximity queries."""
from typing import Dict, List, Set, Tuple, Optional, TypeVar, Generic, Callable
import glm
from game.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class SpatialGrid(Generic[T]):
    """
    2D spatial hash grid for efficient proximity queries.

    Divides world space into a grid of cells. Each cell contains entities
    within that region, allowing O(1) lookup of nearby entities instead of O(N).
    """

    def __init__(self, cell_size: float = 10.0):
        """
        Initialize spatial grid.

        Args:
            cell_size: Size of each grid cell (larger = fewer cells, less precise)
        """
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], Set[T]] = {}
        self.entity_cells: Dict[T, Tuple[int, int]] = {}  # Track which cell each entity is in

        logger.debug(f"SpatialGrid initialized with cell_size={cell_size}")

    def _get_cell(self, x: float, z: float) -> Tuple[int, int]:
        """
        Get grid cell coordinates for a world position.

        Args:
            x: World X coordinate
            z: World Z coordinate

        Returns:
            Tuple[int, int]: Grid cell coordinates (cell_x, cell_z)
        """
        cell_x = int(x // self.cell_size)
        cell_z = int(z // self.cell_size)
        return (cell_x, cell_z)

    def insert(self, entity: T, position: glm.vec3) -> None:
        """
        Insert an entity into the grid.

        Args:
            entity: Entity to insert
            position: Entity's world position
        """
        cell = self._get_cell(position.x, position.z)

        # Create cell if it doesn't exist
        if cell not in self.grid:
            self.grid[cell] = set()

        # Add entity to cell
        self.grid[cell].add(entity)
        self.entity_cells[entity] = cell

    def remove(self, entity: T) -> None:
        """
        Remove an entity from the grid.

        Args:
            entity: Entity to remove
        """
        if entity not in self.entity_cells:
            return

        cell = self.entity_cells[entity]

        # Remove from cell
        if cell in self.grid:
            self.grid[cell].discard(entity)

            # Remove empty cells to save memory
            if not self.grid[cell]:
                del self.grid[cell]

        del self.entity_cells[entity]

    def update(self, entity: T, new_position: glm.vec3) -> None:
        """
        Update an entity's position in the grid.

        Args:
            entity: Entity to update
            new_position: Entity's new world position
        """
        new_cell = self._get_cell(new_position.x, new_position.z)

        # Check if entity moved to a different cell
        if entity in self.entity_cells:
            old_cell = self.entity_cells[entity]

            if old_cell == new_cell:
                return  # Still in same cell, no update needed

            # Remove from old cell
            if old_cell in self.grid:
                self.grid[old_cell].discard(entity)
                if not self.grid[old_cell]:
                    del self.grid[old_cell]

        # Add to new cell
        if new_cell not in self.grid:
            self.grid[new_cell] = set()

        self.grid[new_cell].add(entity)
        self.entity_cells[entity] = new_cell

    def query_radius(
        self,
        position: glm.vec3,
        radius: float,
        filter_func: Optional[Callable[[T], bool]] = None
    ) -> List[T]:
        """
        Query all entities within a radius of a position.

        Args:
            position: Center position
            radius: Search radius
            filter_func: Optional filter function to exclude entities

        Returns:
            List[T]: Entities within radius
        """
        results = []

        # Calculate which cells to check
        cell_radius = int(radius // self.cell_size) + 1
        center_cell = self._get_cell(position.x, position.z)

        # Check all cells within the radius
        for dx in range(-cell_radius, cell_radius + 1):
            for dz in range(-cell_radius, cell_radius + 1):
                cell = (center_cell[0] + dx, center_cell[1] + dz)

                if cell not in self.grid:
                    continue

                # Check each entity in the cell
                for entity in self.grid[cell]:
                    # Apply filter if provided
                    if filter_func and not filter_func(entity):
                        continue

                    results.append(entity)

        return results

    def get_nearest(
        self,
        position: glm.vec3,
        max_radius: float,
        get_position_func: Callable[[T], glm.vec3],
        filter_func: Optional[Callable[[T], bool]] = None
    ) -> Optional[T]:
        """
        Get the nearest entity to a position within a maximum radius.

        Args:
            position: Center position
            max_radius: Maximum search radius
            get_position_func: Function to get entity's position
            filter_func: Optional filter function to exclude entities

        Returns:
            Optional[T]: Nearest entity, or None if none found
        """
        candidates = self.query_radius(position, max_radius, filter_func)

        if not candidates:
            return None

        # Find closest candidate
        nearest = None
        nearest_dist_sq = max_radius * max_radius

        for entity in candidates:
            entity_pos = get_position_func(entity)
            dist_sq = glm.distance2(position, entity_pos)

            if dist_sq < nearest_dist_sq:
                nearest = entity
                nearest_dist_sq = dist_sq

        return nearest

    def clear(self) -> None:
        """Clear all entities from the grid."""
        self.grid.clear()
        self.entity_cells.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about the grid.

        Returns:
            Dict with statistics
        """
        return {
            'total_cells': len(self.grid),
            'total_entities': len(self.entity_cells),
            'avg_entities_per_cell': (
                len(self.entity_cells) / len(self.grid) if self.grid else 0
            ),
        }
