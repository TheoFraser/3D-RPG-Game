"""Vegetation system for biome-specific trees and plants."""
import random
import glm
import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from game.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VegetationInstance:
    """A single vegetation instance (tree, plant, etc.)."""
    position: glm.vec3
    scale: float
    rotation_y: float
    vegetation_type: str


class VegetationType:
    """Types of vegetation that can be placed."""

    # Trees
    OAK_TREE = "oak_tree"
    PINE_TREE = "pine_tree"
    MAGIC_TREE = "magic_tree"
    CRYSTAL_TREE = "crystal_tree"
    DEAD_TREE = "dead_tree"

    # Plants
    GRASS = "grass"
    BUSH = "bush"
    MUSHROOM = "mushroom"
    CRYSTAL_CLUSTER = "crystal_cluster"
    RUINS_VINE = "ruins_vine"


# Biome vegetation configurations
BIOME_VEGETATION = {
    0: {  # Grasslands
        "trees": [
            (VegetationType.OAK_TREE, 0.7),
            (VegetationType.PINE_TREE, 0.3),
        ],
        "tree_density": 0.08,  # Reduced for better performance
        "plants": [
            (VegetationType.GRASS, 0.6),
            (VegetationType.BUSH, 0.4),
        ],
        "plant_density": 0.15,
    },
    1: {  # Enchanted Forest
        "trees": [
            (VegetationType.MAGIC_TREE, 0.8),
            (VegetationType.OAK_TREE, 0.2),
        ],
        "tree_density": 0.12,  # Reduced for better performance
        "plants": [
            (VegetationType.MUSHROOM, 0.5),
            (VegetationType.GRASS, 0.5),
        ],
        "plant_density": 0.20,
    },
    2: {  # Crystal Caves
        "trees": [
            (VegetationType.CRYSTAL_TREE, 1.0),
        ],
        "tree_density": 0.04,
        "plants": [
            (VegetationType.CRYSTAL_CLUSTER, 0.8),
            (VegetationType.MUSHROOM, 0.2),
        ],
        "plant_density": 0.12,
    },
    3: {  # Floating Islands
        "trees": [
            (VegetationType.PINE_TREE, 0.6),
            (VegetationType.MAGIC_TREE, 0.4),
        ],
        "tree_density": 0.06,
        "plants": [
            (VegetationType.GRASS, 0.7),
            (VegetationType.BUSH, 0.3),
        ],
        "plant_density": 0.15,
    },
    4: {  # Ancient Ruins
        "trees": [
            (VegetationType.DEAD_TREE, 0.7),
            (VegetationType.OAK_TREE, 0.3),
        ],
        "tree_density": 0.05,
        "plants": [
            (VegetationType.RUINS_VINE, 0.6),
            (VegetationType.GRASS, 0.4),
        ],
        "plant_density": 0.10,
    },
}


# Vegetation visual properties
VEGETATION_PROPERTIES = {
    VegetationType.OAK_TREE: {
        "scale_range": (3.0, 5.0),
        "color": (0.3, 0.5, 0.2),
        "height": 4.0,
    },
    VegetationType.PINE_TREE: {
        "scale_range": (4.0, 6.0),
        "color": (0.2, 0.4, 0.2),
        "height": 5.0,
    },
    VegetationType.MAGIC_TREE: {
        "scale_range": (3.5, 5.5),
        "color": (0.4, 0.3, 0.6),
        "height": 4.5,
    },
    VegetationType.CRYSTAL_TREE: {
        "scale_range": (2.0, 4.0),
        "color": (0.5, 0.7, 0.9),
        "height": 3.5,
    },
    VegetationType.DEAD_TREE: {
        "scale_range": (3.0, 4.5),
        "color": (0.3, 0.25, 0.2),
        "height": 4.0,
    },
    VegetationType.GRASS: {
        "scale_range": (0.3, 0.6),
        "color": (0.3, 0.6, 0.2),
        "height": 0.5,
    },
    VegetationType.BUSH: {
        "scale_range": (0.8, 1.5),
        "color": (0.25, 0.5, 0.2),
        "height": 1.2,
    },
    VegetationType.MUSHROOM: {
        "scale_range": (0.4, 0.8),
        "color": (0.8, 0.4, 0.3),
        "height": 0.6,
    },
    VegetationType.CRYSTAL_CLUSTER: {
        "scale_range": (0.5, 1.2),
        "color": (0.6, 0.8, 1.0),
        "height": 1.0,
    },
    VegetationType.RUINS_VINE: {
        "scale_range": (0.6, 1.0),
        "color": (0.2, 0.4, 0.15),
        "height": 0.8,
    },
}


class VegetationManager:
    """Manages vegetation placement across chunks."""

    def __init__(self, seed: int = 42):
        """
        Initialize vegetation manager.

        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        self.vegetation_instances: Dict[Tuple[int, int], List[VegetationInstance]] = {}

        logger.info(f"VegetationManager initialized (seed={seed})")

    def generate_vegetation_for_chunk(
        self,
        chunk_x: int,
        chunk_z: int,
        chunk_size: float,
        biome_manager,
        get_height_func
    ) -> List[VegetationInstance]:
        """
        Generate vegetation for a chunk.

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
            chunk_size: Size of the chunk in world units
            biome_manager: BiomeManager to query biomes
            get_height_func: Function to get terrain height at (x, z)

        Returns:
            List of vegetation instances for this chunk
        """
        chunk_key = (chunk_x, chunk_z)

        # Return cached if already generated
        if chunk_key in self.vegetation_instances:
            return self.vegetation_instances[chunk_key]

        # Create deterministic random generator for this chunk
        chunk_seed = (self.seed + chunk_x * 73856093 + chunk_z * 19349663) % (2**32)
        rng = random.Random(chunk_seed)
        np_rng = np.random.RandomState(chunk_seed)

        instances = []

        # Calculate world position of chunk
        world_x = chunk_x * chunk_size
        world_z = chunk_z * chunk_size

        # Grid-based placement (divide chunk into cells)
        grid_size = 4.0  # Place vegetation in 4x4 unit cells
        cells_per_side = int(chunk_size / grid_size)

        for i in range(cells_per_side):
            for j in range(cells_per_side):
                # Cell center in world coordinates
                cell_x = world_x + i * grid_size + grid_size / 2
                cell_z = world_z + j * grid_size + grid_size / 2

                # Get biome at this position
                biome_id = biome_manager.get_biome_at(cell_x, cell_z)

                # Get biome vegetation config
                if biome_id not in BIOME_VEGETATION:
                    continue

                biome_config = BIOME_VEGETATION[biome_id]

                # Try to place a tree
                if rng.random() < biome_config["tree_density"]:
                    tree_type = self._choose_weighted(
                        biome_config["trees"],
                        rng
                    )

                    if tree_type:
                        # Random offset within cell
                        offset_x = rng.uniform(-grid_size/2, grid_size/2)
                        offset_z = rng.uniform(-grid_size/2, grid_size/2)

                        pos_x = cell_x + offset_x
                        pos_z = cell_z + offset_z
                        pos_y = get_height_func(pos_x, pos_z)

                        # Get properties
                        props = VEGETATION_PROPERTIES[tree_type]
                        scale = rng.uniform(*props["scale_range"])
                        rotation = rng.uniform(0, 360)

                        instance = VegetationInstance(
                            position=glm.vec3(pos_x, pos_y, pos_z),
                            scale=scale,
                            rotation_y=rotation,
                            vegetation_type=tree_type
                        )
                        instances.append(instance)

                # Try to place plants (can have both trees and plants)
                if rng.random() < biome_config["plant_density"]:
                    plant_type = self._choose_weighted(
                        biome_config["plants"],
                        rng
                    )

                    if plant_type:
                        # Random offset within cell
                        offset_x = rng.uniform(-grid_size/2, grid_size/2)
                        offset_z = rng.uniform(-grid_size/2, grid_size/2)

                        pos_x = cell_x + offset_x
                        pos_z = cell_z + offset_z
                        pos_y = get_height_func(pos_x, pos_z)

                        # Get properties
                        props = VEGETATION_PROPERTIES[plant_type]
                        scale = rng.uniform(*props["scale_range"])
                        rotation = rng.uniform(0, 360)

                        instance = VegetationInstance(
                            position=glm.vec3(pos_x, pos_y, pos_z),
                            scale=scale,
                            rotation_y=rotation,
                            vegetation_type=plant_type
                        )
                        instances.append(instance)

        # Cache the instances
        self.vegetation_instances[chunk_key] = instances

        logger.debug(f"Generated {len(instances)} vegetation instances for chunk ({chunk_x}, {chunk_z})")

        return instances

    def _choose_weighted(
        self,
        choices: List[Tuple[str, float]],
        rng: random.Random
    ) -> str:
        """
        Choose a random item from weighted choices.

        Args:
            choices: List of (item, weight) tuples
            rng: Random generator

        Returns:
            Chosen item
        """
        if not choices:
            return None

        total_weight = sum(weight for _, weight in choices)
        r = rng.uniform(0, total_weight)

        cumulative = 0.0
        for item, weight in choices:
            cumulative += weight
            if r <= cumulative:
                return item

        return choices[-1][0]  # Fallback

    def get_vegetation_for_chunk(
        self,
        chunk_x: int,
        chunk_z: int
    ) -> List[VegetationInstance]:
        """
        Get vegetation instances for a chunk (if generated).

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate

        Returns:
            List of vegetation instances or empty list
        """
        return self.vegetation_instances.get((chunk_x, chunk_z), [])

    def clear_chunk(self, chunk_x: int, chunk_z: int):
        """
        Clear vegetation for a chunk (when unloading).

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate
        """
        chunk_key = (chunk_x, chunk_z)
        if chunk_key in self.vegetation_instances:
            del self.vegetation_instances[chunk_key]
            logger.debug(f"Cleared vegetation for chunk ({chunk_x}, {chunk_z})")

    def get_total_instances(self) -> int:
        """Get total number of vegetation instances loaded."""
        return sum(len(instances) for instances in self.vegetation_instances.values())

    def get_stats(self) -> Dict[str, int]:
        """Get vegetation statistics."""
        stats = {
            "total_instances": self.get_total_instances(),
            "loaded_chunks": len(self.vegetation_instances),
        }

        # Count by type
        type_counts = {}
        for instances in self.vegetation_instances.values():
            for instance in instances:
                veg_type = instance.vegetation_type
                type_counts[veg_type] = type_counts.get(veg_type, 0) + 1

        stats.update(type_counts)
        return stats
