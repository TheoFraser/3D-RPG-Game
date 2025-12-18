"""AI pathfinding using A* algorithm (Numba-optimized for performance)."""
import numpy as np
from numba import njit
import glm
from typing import List, Tuple, Optional


@njit(fastmath=True)
def heuristic(a_x, a_z, b_x, b_z):
    """
    Calculate heuristic (Manhattan distance).

    Args:
        a_x, a_z: Position A
        b_x, b_z: Position B

    Returns:
        float: Estimated distance
    """
    return abs(a_x - b_x) + abs(a_z - b_z)


@njit(fastmath=True)
def get_neighbors(x, z, width, height):
    """
    Get valid neighbor cells (8-directional movement).

    Args:
        x, z: Current cell position
        width, height: Grid dimensions

    Returns:
        Array of neighbor positions (Nx2)
    """
    neighbors = []

    # 8 directions (N, S, E, W, NE, NW, SE, SW)
    for dx in range(-1, 2):
        for dz in range(-1, 2):
            if dx == 0 and dz == 0:
                continue

            nx = x + dx
            nz = z + dz

            if 0 <= nx < width and 0 <= nz < height:
                neighbors.append((nx, nz))

    return neighbors


@njit(fastmath=True)
def reconstruct_path(came_from, current_x, current_z, max_length=1000):
    """
    Reconstruct path from came_from dictionary.

    Args:
        came_from: 2D array storing parent cells
        current_x, current_z: Goal position
        max_length: Maximum path length

    Returns:
        Array of path positions (Nx2)
    """
    path = np.empty((max_length, 2), dtype=np.int32)
    path_length = 0

    x, z = current_x, current_z
    path[path_length] = (x, z)
    path_length += 1

    # Trace back through parents
    while path_length < max_length:
        parent_x = came_from[x, z, 0]
        parent_z = came_from[x, z, 1]

        # Reached start (no parent)
        if parent_x == -1 and parent_z == -1:
            break

        x, z = parent_x, parent_z
        path[path_length] = (x, z)
        path_length += 1

    # Reverse path (currently goes from goal to start)
    result = np.empty((path_length, 2), dtype=np.int32)
    for i in range(path_length):
        result[i] = path[path_length - 1 - i]

    return result


@njit(fastmath=True)
def astar_search(grid, start_x, start_z, goal_x, goal_z):
    """
    A* pathfinding algorithm (Numba-optimized).

    Args:
        grid: 2D array (0 = walkable, 1 = blocked)
        start_x, start_z: Start position
        goal_x, goal_z: Goal position

    Returns:
        Array of path positions (Nx2), or empty array if no path found
    """
    height, width = grid.shape

    # Validate positions
    if not (0 <= start_x < width and 0 <= start_z < height):
        return np.empty((0, 2), dtype=np.int32)
    if not (0 <= goal_x < width and 0 <= goal_z < height):
        return np.empty((0, 2), dtype=np.int32)
    if grid[start_z, start_x] != 0 or grid[goal_z, goal_x] != 0:
        return np.empty((0, 2), dtype=np.int32)

    # Initialize data structures
    open_set = np.zeros((width * height, 3), dtype=np.float32)  # (x, z, f_score)
    open_set_size = 1
    open_set[0, 0] = start_x
    open_set[0, 1] = start_z
    open_set[0, 2] = heuristic(start_x, start_z, goal_x, goal_z)

    came_from = np.full((width, height, 2), -1, dtype=np.int32)  # Parent positions

    g_score = np.full((width, height), np.inf, dtype=np.float32)
    g_score[start_x, start_z] = 0.0

    closed_set = np.zeros((width, height), dtype=np.bool_)

    # A* main loop
    iterations = 0
    max_iterations = width * height

    while open_set_size > 0 and iterations < max_iterations:
        iterations += 1

        # Find node with lowest f_score in open set
        min_idx = 0
        min_f = open_set[0, 2]
        for i in range(1, open_set_size):
            if open_set[i, 2] < min_f:
                min_f = open_set[i, 2]
                min_idx = i

        # Get current node
        current_x = int(open_set[min_idx, 0])
        current_z = int(open_set[min_idx, 1])

        # Remove from open set (swap with last and decrease size)
        open_set[min_idx] = open_set[open_set_size - 1]
        open_set_size -= 1

        # Goal reached
        if current_x == goal_x and current_z == goal_z:
            return reconstruct_path(came_from, goal_x, goal_z)

        # Mark as closed
        closed_set[current_x, current_z] = True

        # Check neighbors
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    continue

                nx = current_x + dx
                nz = current_z + dz

                # Check bounds
                if not (0 <= nx < width and 0 <= nz < height):
                    continue

                # Skip if blocked or already closed
                if grid[nz, nx] != 0 or closed_set[nx, nz]:
                    continue

                # Calculate movement cost (diagonal = 1.4, straight = 1.0)
                if dx != 0 and dz != 0:
                    move_cost = 1.414  # sqrt(2)
                else:
                    move_cost = 1.0

                tentative_g = g_score[current_x, current_z] + move_cost

                # Better path found
                if tentative_g < g_score[nx, nz]:
                    came_from[nx, nz, 0] = current_x
                    came_from[nx, nz, 1] = current_z
                    g_score[nx, nz] = tentative_g
                    f_score = tentative_g + heuristic(nx, nz, goal_x, goal_z)

                    # Add to open set if not already there
                    in_open_set = False
                    for i in range(open_set_size):
                        if int(open_set[i, 0]) == nx and int(open_set[i, 1]) == nz:
                            open_set[i, 2] = f_score
                            in_open_set = True
                            break

                    if not in_open_set and open_set_size < len(open_set):
                        open_set[open_set_size, 0] = nx
                        open_set[open_set_size, 1] = nz
                        open_set[open_set_size, 2] = f_score
                        open_set_size += 1

    # No path found
    return np.empty((0, 2), dtype=np.int32)


class NavigationGrid:
    """Navigation grid for pathfinding."""

    def __init__(self, width, height, cell_size=1.0):
        """
        Create a navigation grid.

        Args:
            width: Grid width (number of cells)
            height: Grid height (number of cells)
            cell_size: Size of each cell in world units

        Raises:
            ValueError: If width, height, or cell_size are invalid
        """
        # Validate inputs
        if width <= 0:
            raise ValueError(f"Grid width must be > 0, got {width}")
        if height <= 0:
            raise ValueError(f"Grid height must be > 0, got {height}")
        if cell_size <= 0:
            raise ValueError(f"Cell size must be > 0, got {cell_size}")

        self.width = width
        self.height = height
        self.cell_size = cell_size

        # Grid (0 = walkable, 1 = blocked)
        self.grid = np.zeros((height, width), dtype=np.int32)

        # World bounds
        self.min_x = 0.0
        self.min_z = 0.0
        self.max_x = width * cell_size
        self.max_z = height * cell_size

    def world_to_grid(self, x, z):
        """
        Convert world position to grid coordinates.

        Args:
            x, z: World position

        Returns:
            Tuple[int, int]: Grid coordinates (gx, gz)
        """
        gx = int((x - self.min_x) / self.cell_size)
        gz = int((z - self.min_z) / self.cell_size)
        return gx, gz

    def grid_to_world(self, gx, gz):
        """
        Convert grid coordinates to world position.

        Args:
            gx, gz: Grid coordinates

        Returns:
            Tuple[float, float]: World position (x, z)
        """
        x = self.min_x + (gx + 0.5) * self.cell_size
        z = self.min_z + (gz + 0.5) * self.cell_size
        return x, z

    def set_blocked(self, gx, gz, blocked=True):
        """
        Mark a cell as blocked or walkable.

        Args:
            gx, gz: Grid coordinates
            blocked: True to block, False to unblock
        """
        if 0 <= gx < self.width and 0 <= gz < self.height:
            self.grid[gz, gx] = 1 if blocked else 0

    def is_walkable(self, gx, gz):
        """
        Check if a cell is walkable.

        Args:
            gx, gz: Grid coordinates

        Returns:
            bool: True if walkable
        """
        if 0 <= gx < self.width and 0 <= gz < self.height:
            return self.grid[gz, gx] == 0
        return False

    def find_path(self, start_pos, goal_pos):
        """
        Find a path from start to goal using A*.

        Args:
            start_pos: Start world position (glm.vec3 or tuple)
            goal_pos: Goal world position (glm.vec3 or tuple)

        Returns:
            List of glm.vec3 waypoints, or empty list if no path
        """
        # Convert to grid coordinates
        if isinstance(start_pos, glm.vec3):
            start_x, start_z = self.world_to_grid(start_pos.x, start_pos.z)
        else:
            start_x, start_z = self.world_to_grid(start_pos[0], start_pos[2] if len(start_pos) > 2 else start_pos[1])

        if isinstance(goal_pos, glm.vec3):
            goal_x, goal_z = self.world_to_grid(goal_pos.x, goal_pos.z)
        else:
            goal_x, goal_z = self.world_to_grid(goal_pos[0], goal_pos[2] if len(goal_pos) > 2 else goal_pos[1])

        # Run A*
        path_grid = astar_search(self.grid, start_x, start_z, goal_x, goal_z)

        # Convert to world coordinates
        path_world = []
        for i in range(len(path_grid)):
            gx, gz = path_grid[i]
            wx, wz = self.grid_to_world(gx, gz)

            # Use Y from start position (assume flat navigation for now)
            if isinstance(start_pos, glm.vec3):
                y = start_pos.y
            else:
                y = start_pos[1] if len(start_pos) > 1 else 0.0

            path_world.append(glm.vec3(wx, y, wz))

        return path_world

    def block_circle(self, center_x, center_z, radius):
        """
        Block a circular area.

        Args:
            center_x, center_z: Center world position
            radius: Radius in world units
        """
        gx, gz = self.world_to_grid(center_x, center_z)
        grid_radius = int(radius / self.cell_size) + 1

        for dx in range(-grid_radius, grid_radius + 1):
            for dz in range(-grid_radius, grid_radius + 1):
                if dx*dx + dz*dz <= grid_radius*grid_radius:
                    self.set_blocked(gx + dx, gz + dz, True)

    def block_rect(self, min_x, min_z, max_x, max_z):
        """
        Block a rectangular area.

        Args:
            min_x, min_z: Minimum corner world position
            max_x, max_z: Maximum corner world position
        """
        gx1, gz1 = self.world_to_grid(min_x, min_z)
        gx2, gz2 = self.world_to_grid(max_x, max_z)

        for gx in range(min(gx1, gx2), max(gx1, gx2) + 1):
            for gz in range(min(gz1, gz2), max(gz1, gz2) + 1):
                self.set_blocked(gx, gz, True)


class PathFollower:
    """Helper class for following a path."""

    def __init__(self, path: List[glm.vec3]):
        """
        Create a path follower.

        Args:
            path: List of waypoints (glm.vec3)
        """
        self.path = path
        self.current_waypoint = 0
        self.completed = False

    def update(self, current_position, speed, delta_time):
        """
        Update path following.

        Args:
            current_position: Current position (glm.vec3)
            speed: Movement speed
            delta_time: Time since last frame

        Returns:
            glm.vec3: Velocity to move towards next waypoint
        """
        if self.completed or not self.path:
            return glm.vec3(0.0, 0.0, 0.0)

        # Get current target
        target = self.path[self.current_waypoint]
        direction = target - current_position
        distance = glm.length(glm.vec2(direction.x, direction.z))

        # Reached waypoint
        if distance < 0.5:
            self.current_waypoint += 1
            if self.current_waypoint >= len(self.path):
                self.completed = True
                return glm.vec3(0.0, 0.0, 0.0)

            # Move to next waypoint
            target = self.path[self.current_waypoint]
            direction = target - current_position

        # Move towards target
        if glm.length(direction) > 0.01:
            direction = glm.normalize(direction)
            return direction * speed
        else:
            return glm.vec3(0.0, 0.0, 0.0)

    def is_complete(self):
        """Check if path is complete."""
        return self.completed

    def get_progress(self):
        """
        Get progress along path.

        Returns:
            float: Progress from 0.0 to 1.0
        """
        if not self.path:
            return 1.0
        return self.current_waypoint / len(self.path)
