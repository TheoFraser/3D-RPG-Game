"""Fast travel system for shrine teleportation."""
import glm
from typing import List, Dict, Optional
from world_gen.poi_generator import POI, POIType


class FastTravelPoint:
    """Represents a fast travel destination."""

    def __init__(self, poi: POI):
        """
        Initialize fast travel point from a shrine POI.

        Args:
            poi: The shrine POI
        """
        self.poi = poi
        self.name = poi.name
        self.position = poi.position
        self.unlocked = poi.discovered  # Can only fast travel to discovered shrines
        self.last_visited = 0.0  # Game time of last visit

    def unlock(self):
        """Unlock this fast travel point."""
        self.unlocked = True
        self.poi.discovered = True
        self.poi.data["unlocked"] = True


class FastTravelSystem:
    """Manages fast travel between discovered shrines."""

    def __init__(self):
        """Initialize fast travel system."""
        self.travel_points: Dict[str, FastTravelPoint] = {}
        self.cooldown_time = 5.0  # Seconds between fast travels
        self.last_travel_time = -999.0  # Time of last fast travel

    def register_shrine(self, shrine_poi: POI) -> FastTravelPoint:
        """
        Register a shrine as a potential fast travel point.

        Args:
            shrine_poi: The shrine POI to register

        Returns:
            The created fast travel point
        """
        travel_point = FastTravelPoint(shrine_poi)
        self.travel_points[shrine_poi.name] = travel_point
        return travel_point

    def unlock_shrine(self, shrine_name: str):
        """
        Unlock a shrine for fast travel.

        Args:
            shrine_name: Name of the shrine to unlock
        """
        if shrine_name in self.travel_points:
            self.travel_points[shrine_name].unlock()

    def get_unlocked_shrines(self) -> List[FastTravelPoint]:
        """
        Get all unlocked shrines.

        Returns:
            List of unlocked fast travel points
        """
        return [point for point in self.travel_points.values() if point.unlocked]

    def can_fast_travel(self, current_time: float) -> tuple[bool, str]:
        """
        Check if fast travel is available.

        Args:
            current_time: Current game time

        Returns:
            Tuple of (can_travel, reason)
        """
        # Check cooldown
        time_since_last = current_time - self.last_travel_time
        if time_since_last < self.cooldown_time:
            cooldown_left = self.cooldown_time - time_since_last
            return False, f"Fast travel on cooldown ({cooldown_left:.1f}s remaining)"

        # Check if any shrines are unlocked
        if not self.get_unlocked_shrines():
            return False, "No shrines discovered yet"

        return True, "Ready to travel"

    def fast_travel(self, destination_name: str, current_time: float) -> tuple[bool, str, Optional[glm.vec3]]:
        """
        Attempt to fast travel to a destination.

        Args:
            destination_name: Name of the destination shrine
            current_time: Current game time

        Returns:
            Tuple of (success, message, destination_position)
        """
        # Check if can travel
        can_travel, reason = self.can_fast_travel(current_time)
        if not can_travel:
            return False, reason, None

        # Check if destination exists and is unlocked
        if destination_name not in self.travel_points:
            return False, f"Unknown destination: {destination_name}", None

        destination = self.travel_points[destination_name]
        if not destination.unlocked:
            return False, f"{destination_name} has not been discovered yet", None

        # Perform travel
        self.last_travel_time = current_time
        destination.last_visited = current_time

        # Return position slightly above shrine to avoid being stuck in ground
        travel_position = glm.vec3(
            destination.position.x,
            destination.position.y + 2.0,
            destination.position.z
        )

        return True, f"Traveled to {destination_name}", travel_position

    def get_nearest_shrine(self, position: glm.vec3) -> Optional[FastTravelPoint]:
        """
        Get the nearest shrine to a position.

        Args:
            position: Position to check from

        Returns:
            Nearest shrine, or None if no shrines exist
        """
        if not self.travel_points:
            return None

        nearest = None
        nearest_dist = float('inf')

        for point in self.travel_points.values():
            dist = glm.length(position - point.position)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = point

        return nearest

    def discover_nearby_shrine(self, position: glm.vec3, discovery_radius: float = 20.0) -> Optional[FastTravelPoint]:
        """
        Discover and unlock shrines within radius.

        Args:
            position: Player position
            discovery_radius: Radius to search for shrines

        Returns:
            Newly discovered shrine, or None
        """
        for point in self.travel_points.values():
            if not point.unlocked:
                dist = glm.length(position - point.position)
                if dist <= discovery_radius:
                    point.unlock()
                    return point

        return None

    def get_shrine_count(self) -> tuple[int, int]:
        """
        Get shrine counts.

        Returns:
            Tuple of (unlocked_count, total_count)
        """
        total = len(self.travel_points)
        unlocked = len(self.get_unlocked_shrines())
        return unlocked, total
