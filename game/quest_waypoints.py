"""Quest waypoint system for navigation assistance."""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Tuple
import math
from game.logger import get_logger

logger = get_logger(__name__)


class WaypointType(Enum):
    """Types of quest waypoints."""
    LOCATION = auto()  # Go to a specific location
    NPC = auto()       # Talk to an NPC
    ENEMY = auto()     # Defeat an enemy
    ITEM = auto()      # Collect an item
    POI = auto()       # Visit a point of interest
    AREA = auto()      # Enter an area/radius


@dataclass
class QuestWaypoint:
    """
    A waypoint marker for quest objectives.

    Waypoints help players navigate to quest objectives by showing
    location markers on the map and directional indicators in the HUD.
    """
    # Location
    position: Tuple[float, float, float]  # (x, y, z) world position
    waypoint_type: WaypointType

    # Display
    name: str  # Display name for waypoint
    description: str = ""  # Additional info

    # Tracking
    radius: float = 5.0  # Completion radius in units
    show_distance: bool = True  # Show distance to player
    show_direction: bool = True  # Show directional arrow

    # Visual
    color: Tuple[int, int, int] = (255, 255, 100)  # RGB color for marker
    icon: str = "marker"  # Icon type ("marker", "npc", "enemy", "item", "poi")

    # State
    active: bool = True  # Whether to display this waypoint
    completed: bool = False  # Whether waypoint objective is complete

    def distance_to(self, player_x: float, player_z: float) -> float:
        """
        Calculate distance from player to waypoint (2D).

        Args:
            player_x, player_z: Player world position

        Returns:
            Distance in world units
        """
        wx, _, wz = self.position
        dx = player_x - wx
        dz = player_z - wz
        return math.sqrt(dx * dx + dz * dz)

    def direction_to(self, player_x: float, player_z: float) -> float:
        """
        Calculate angle from player to waypoint (radians).

        Args:
            player_x, player_z: Player world position

        Returns:
            Angle in radians (0 = north, clockwise)
        """
        wx, _, wz = self.position
        dx = wx - player_x
        dz = wz - player_z
        return math.atan2(dx, dz)

    def is_in_range(self, player_x: float, player_z: float) -> bool:
        """
        Check if player is within completion radius.

        Args:
            player_x, player_z: Player world position

        Returns:
            True if player is in range
        """
        distance = self.distance_to(player_x, player_z)
        return distance <= self.radius


class WaypointManager:
    """
    Manages quest waypoints for navigation.

    Provides methods to add, remove, and query waypoints for
    active quests, helping players navigate to objectives.
    """

    def __init__(self):
        """Initialize waypoint manager."""
        self.waypoints: List[QuestWaypoint] = []
        logger.info("WaypointManager initialized")

    def add_waypoint(self, waypoint: QuestWaypoint) -> None:
        """
        Add a waypoint.

        Args:
            waypoint: Waypoint to add
        """
        self.waypoints.append(waypoint)
        logger.debug(f"Added waypoint: {waypoint.name} at {waypoint.position}")

    def remove_waypoint(self, waypoint: QuestWaypoint) -> None:
        """
        Remove a waypoint.

        Args:
            waypoint: Waypoint to remove
        """
        if waypoint in self.waypoints:
            self.waypoints.remove(waypoint)
            logger.debug(f"Removed waypoint: {waypoint.name}")

    def clear_waypoints(self) -> None:
        """Clear all waypoints."""
        count = len(self.waypoints)
        self.waypoints.clear()
        if count > 0:
            logger.debug(f"Cleared {count} waypoints")

    def get_active_waypoints(self) -> List[QuestWaypoint]:
        """
        Get all active waypoints.

        Returns:
            List of active waypoints
        """
        return [w for w in self.waypoints if w.active and not w.completed]

    def get_nearest_waypoint(self, player_x: float, player_z: float) -> Optional[QuestWaypoint]:
        """
        Get the nearest active waypoint to player.

        Args:
            player_x, player_z: Player world position

        Returns:
            Nearest waypoint, or None if no active waypoints
        """
        active = self.get_active_waypoints()
        if not active:
            return None

        nearest = min(active, key=lambda w: w.distance_to(player_x, player_z))
        return nearest

    def get_waypoints_in_range(
        self,
        player_x: float,
        player_z: float,
        max_distance: float = 100.0
    ) -> List[QuestWaypoint]:
        """
        Get waypoints within a certain distance.

        Args:
            player_x, player_z: Player world position
            max_distance: Maximum distance to include

        Returns:
            List of waypoints within range
        """
        active = self.get_active_waypoints()
        return [
            w for w in active
            if w.distance_to(player_x, player_z) <= max_distance
        ]

    def update_waypoint_states(
        self,
        player_x: float,
        player_z: float
    ) -> List[QuestWaypoint]:
        """
        Update waypoint states and check for completion.

        Args:
            player_x, player_z: Player world position

        Returns:
            List of newly completed waypoints
        """
        completed = []

        for waypoint in self.waypoints:
            if waypoint.active and not waypoint.completed:
                if waypoint.is_in_range(player_x, player_z):
                    waypoint.completed = True
                    completed.append(waypoint)
                    logger.info(f"Waypoint reached: {waypoint.name}")

        return completed

    def mark_waypoint_complete(self, waypoint: QuestWaypoint) -> None:
        """
        Manually mark a waypoint as complete.

        Args:
            waypoint: Waypoint to complete
        """
        if waypoint in self.waypoints:
            waypoint.completed = True
            logger.debug(f"Marked waypoint complete: {waypoint.name}")

    def get_waypoint_count(self) -> Tuple[int, int]:
        """
        Get waypoint counts.

        Returns:
            Tuple of (active_count, total_count)
        """
        active = len(self.get_active_waypoints())
        total = len(self.waypoints)
        return (active, total)


def create_waypoint_for_poi(poi_name: str, poi_position: Tuple[float, float, float]) -> QuestWaypoint:
    """
    Create a waypoint for a POI.

    Args:
        poi_name: Name of the POI
        poi_position: World position of POI

    Returns:
        QuestWaypoint for the POI
    """
    return QuestWaypoint(
        position=poi_position,
        waypoint_type=WaypointType.POI,
        name=poi_name,
        description=f"Visit {poi_name}",
        radius=15.0,  # Larger radius for POIs
        color=(100, 200, 255),  # Light blue
        icon="poi"
    )


def create_waypoint_for_npc(npc_name: str, npc_position: Tuple[float, float, float]) -> QuestWaypoint:
    """
    Create a waypoint for an NPC.

    Args:
        npc_name: Name of the NPC
        npc_position: World position of NPC

    Returns:
        QuestWaypoint for the NPC
    """
    return QuestWaypoint(
        position=npc_position,
        waypoint_type=WaypointType.NPC,
        name=npc_name,
        description=f"Talk to {npc_name}",
        radius=5.0,
        color=(100, 255, 100),  # Green
        icon="npc"
    )


def create_waypoint_for_area(
    area_name: str,
    center_position: Tuple[float, float, float],
    radius: float = 10.0
) -> QuestWaypoint:
    """
    Create a waypoint for an area.

    Args:
        area_name: Name of the area
        center_position: Center of area
        radius: Radius of area

    Returns:
        QuestWaypoint for the area
    """
    return QuestWaypoint(
        position=center_position,
        waypoint_type=WaypointType.AREA,
        name=area_name,
        description=f"Reach {area_name}",
        radius=radius,
        color=(255, 200, 100),  # Orange
        icon="marker"
    )
