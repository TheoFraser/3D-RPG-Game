"""Points of Interest (POI) generator for world population."""
import random
import glm
import config
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from game.logger import get_logger

logger = get_logger(__name__)


class POIType(Enum):
    """Types of points of interest."""
    VILLAGE = "village"
    SHRINE = "shrine"
    RUIN = "ruin"
    DUNGEON = "dungeon"


@dataclass
class POI:
    """Point of Interest data structure."""
    poi_type: POIType
    position: glm.vec3
    name: str
    radius: float = 10.0
    discovered: bool = False
    data: Dict = None  # Additional type-specific data

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class POIGenerator:
    """Generates and manages Points of Interest across the world."""

    def __init__(self, world_size: int, seed: int = 42):
        """
        Initialize POI generator.

        Args:
            world_size: Size of the world (e.g., 2000)
            seed: Random seed for deterministic generation
        """
        self.world_size = world_size
        self.seed = seed
        self.pois: List[POI] = []
        self.rng = random.Random(seed)

        # POI counts from config
        self.poi_counts = {
            POIType.VILLAGE: 4,
            POIType.SHRINE: 12,
            POIType.RUIN: 20,
            POIType.DUNGEON: 6,
        }

        # Minimum distances between POIs
        self.min_distances = {
            POIType.VILLAGE: 200.0,  # Villages well separated
            POIType.SHRINE: 100.0,   # Shrines moderately separated
            POIType.RUIN: 50.0,      # Ruins can be closer
            POIType.DUNGEON: 150.0,  # Dungeons well separated
        }

    def generate_all_pois(self, chunk_manager=None) -> List[POI]:
        """
        Generate all POIs for the world.

        Args:
            chunk_manager: Optional chunk manager to get terrain height

        Returns:
            List of generated POIs
        """
        logger.info(f"Generating POIs for {self.world_size}x{self.world_size} world...")

        # Generate each type of POI
        for poi_type, count in self.poi_counts.items():
            self._generate_poi_type(poi_type, count, chunk_manager)

        logger.info(f"Generated {len(self.pois)} total POIs:")
        for poi_type in POIType:
            type_count = sum(1 for poi in self.pois if poi.poi_type == poi_type)
            logger.info(f"  - {poi_type.value}: {type_count}")

        return self.pois

    def _generate_poi_type(self, poi_type: POIType, count: int, chunk_manager=None):
        """Generate POIs of a specific type."""
        min_dist = self.min_distances[poi_type]
        max_attempts = count * 50  # Prevent infinite loops

        for i in range(count):
            poi = self._try_place_poi(poi_type, i, min_dist, chunk_manager, max_attempts)
            if poi:
                self.pois.append(poi)

    def _try_place_poi(self, poi_type: POIType, index: int, min_dist: float,
                       chunk_manager=None, max_attempts: int = 100) -> Optional[POI]:
        """
        Try to place a POI with minimum distance constraints.

        Args:
            poi_type: Type of POI to place
            index: Index of this POI (for naming)
            min_dist: Minimum distance from other POIs
            chunk_manager: Optional chunk manager for terrain height
            max_attempts: Maximum placement attempts

        Returns:
            POI if successfully placed, None otherwise
        """
        for attempt in range(max_attempts):
            # Generate random position (avoid edges)
            margin = 100.0  # Stay away from world edges
            x = self.rng.uniform(-self.world_size/2 + margin, self.world_size/2 - margin)
            z = self.rng.uniform(-self.world_size/2 + margin, self.world_size/2 - margin)

            # Check distance from existing POIs
            pos_2d = glm.vec2(x, z)
            too_close = False

            for existing_poi in self.pois:
                existing_pos_2d = glm.vec2(existing_poi.position.x, existing_poi.position.z)
                dist = glm.length(pos_2d - existing_pos_2d)
                if dist < min_dist:
                    too_close = True
                    break

            if too_close:
                continue

            # Get terrain height
            if chunk_manager:
                y = chunk_manager.get_height_at(x, z) + 0.5
            else:
                y = 1.0  # Default height

            position = glm.vec3(x, y, z)

            # Create POI with type-specific data
            name = self._generate_poi_name(poi_type, index)
            poi = POI(
                poi_type=poi_type,
                position=position,
                name=name,
                radius=self._get_poi_radius(poi_type),
                data=self._generate_poi_data(poi_type)
            )

            return poi

        logger.warning(f"Failed to place {poi_type.value} #{index} after {max_attempts} attempts")
        return None

    def _generate_poi_name(self, poi_type: POIType, index: int) -> str:
        """Generate a name for a POI."""
        if poi_type == POIType.VILLAGE:
            village_names = ["Riverwood", "Whiterun", "Solitude", "Windhelm", "Dawnstar"]
            return village_names[index % len(village_names)]

        elif poi_type == POIType.SHRINE:
            return f"Shrine of the {['North', 'South', 'East', 'West', 'Center', 'Moon', 'Sun', 'Stars', 'Winds', 'Waters', 'Earth', 'Fire'][index % 12]}"

        elif poi_type == POIType.RUIN:
            ruin_types = ["Ancient Temple", "Forgotten Fort", "Old Cathedral", "Ruined Keep"]
            return f"{ruin_types[index % len(ruin_types)]} #{index // len(ruin_types) + 1}"

        elif poi_type == POIType.DUNGEON:
            dungeon_names = ["Dark Cavern", "Shadow Depths", "Crystal Grotto", "Cursed Tomb", "Dragon's Lair", "Necromancer's Den"]
            return dungeon_names[index % len(dungeon_names)]

        return f"{poi_type.value.title()} #{index}"

    def _get_poi_radius(self, poi_type: POIType) -> float:
        """Get the radius/size of a POI type."""
        radii = {
            POIType.VILLAGE: 30.0,
            POIType.SHRINE: 5.0,
            POIType.RUIN: 15.0,
            POIType.DUNGEON: 20.0,
        }
        return radii.get(poi_type, 10.0)

    def _generate_poi_data(self, poi_type: POIType) -> Dict:
        """Generate type-specific data for a POI."""
        if poi_type == POIType.VILLAGE:
            return {
                "npc_count": self.rng.randint(config.VILLAGE_NPC_COUNT_MIN, config.VILLAGE_NPC_COUNT_MAX),
                "has_merchant": True,
                "has_inn": True,
            }

        elif poi_type == POIType.SHRINE:
            return {
                "unlocked": False,  # Fast travel unlocked when discovered
                "blessing": self.rng.choice(["health", "stamina", "damage", "defense"]),
            }

        elif poi_type == POIType.RUIN:
            return {
                "loot_quality": self.rng.choice(["common", "uncommon", "rare"]),
                "has_lore": self.rng.random() > 0.5,
                "enemy_count": self.rng.randint(2, 5),
            }

        elif poi_type == POIType.DUNGEON:
            return {
                "difficulty": self.rng.randint(1, 5),
                "has_boss": True,
                "loot_quality": "rare",
                "enemy_count": self.rng.randint(10, 20),
            }

        return {}

    def get_nearby_poi(self, position: glm.vec3, poi_type: Optional[POIType] = None,
                       max_distance: float = 50.0) -> Optional[POI]:
        """
        Find the nearest POI to a position.

        Args:
            position: Position to search from
            poi_type: Optional filter by POI type
            max_distance: Maximum search distance

        Returns:
            Nearest POI or None
        """
        nearest = None
        nearest_dist = max_distance

        for poi in self.pois:
            if poi_type and poi.poi_type != poi_type:
                continue

            dist = glm.length(glm.vec2(poi.position.x - position.x, poi.position.z - position.z))
            if dist < nearest_dist:
                nearest = poi
                nearest_dist = dist

        return nearest

    def discover_poi(self, position: glm.vec3, discovery_radius: float = 20.0) -> Optional[POI]:
        """
        Discover a POI if player is close enough.

        Args:
            position: Player position
            discovery_radius: Radius to discover POIs

        Returns:
            Newly discovered POI or None
        """
        for poi in self.pois:
            if poi.discovered:
                continue

            dist = glm.length(glm.vec2(poi.position.x - position.x, poi.position.z - position.z))
            if dist < discovery_radius:
                poi.discovered = True
                return poi

        return None

    def get_discovered_pois(self, poi_type: Optional[POIType] = None) -> List[POI]:
        """Get all discovered POIs, optionally filtered by type."""
        pois = [poi for poi in self.pois if poi.discovered]
        if poi_type:
            pois = [poi for poi in pois if poi.poi_type == poi_type]
        return pois

    def get_all_pois(self, poi_type: Optional[POIType] = None) -> List[POI]:
        """Get all POIs, optionally filtered by type."""
        if poi_type:
            return [poi for poi in self.pois if poi.poi_type == poi_type]
        return self.pois.copy()
