"""Journal and objectives tracking system."""
from enum import Enum
from typing import List, Dict, Optional
from game.logger import get_logger

logger = get_logger(__name__)


class ObjectiveStatus(Enum):
    """Status of an objective."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    HIDDEN = "hidden"


class Objective:
    """A single objective or quest."""

    def __init__(self, id: str, title: str, description: str, hidden: bool = False):
        """
        Initialize objective.

        Args:
            id: Unique identifier
            title: Short title
            description: Detailed description
            hidden: Whether objective is initially hidden
        """
        self.id = id
        self.title = title
        self.description = description
        self.status = ObjectiveStatus.HIDDEN if hidden else ObjectiveStatus.ACTIVE
        self.progress = 0
        self.progress_max = 1
        self.sub_tasks = []

    def add_sub_task(self, task: str, completed: bool = False):
        """Add a sub-task to the objective."""
        self.sub_tasks.append({"task": task, "completed": completed})
        self.progress_max = len(self.sub_tasks)
        self.update_progress()

    def complete_sub_task(self, index: int):
        """Mark a sub-task as completed."""
        if 0 <= index < len(self.sub_tasks):
            self.sub_tasks[index]["completed"] = True
            self.update_progress()

    def update_progress(self):
        """Update progress based on completed sub-tasks."""
        if self.sub_tasks:
            completed = sum(1 for task in self.sub_tasks if task["completed"])
            self.progress = completed
            if completed == len(self.sub_tasks):
                self.complete()

    def complete(self):
        """Mark objective as completed."""
        self.status = ObjectiveStatus.COMPLETED
        self.progress = self.progress_max

    def fail(self):
        """Mark objective as failed."""
        self.status = ObjectiveStatus.FAILED

    def reveal(self):
        """Reveal a hidden objective."""
        if self.status == ObjectiveStatus.HIDDEN:
            self.status = ObjectiveStatus.ACTIVE

    def is_active(self):
        """Check if objective is active."""
        return self.status == ObjectiveStatus.ACTIVE


class LoreEntry:
    """A piece of lore or discovery."""

    def __init__(self, id: str, title: str, content: str, category: str = "General"):
        """
        Initialize lore entry.

        Args:
            id: Unique identifier
            title: Entry title
            content: Full text
            category: Category (History, Puzzles, Locations, etc.)
        """
        self.id = id
        self.title = title
        self.content = content
        self.category = category
        self.discovered = False
        self.timestamp = None

    def discover(self):
        """Mark entry as discovered."""
        if not self.discovered:
            self.discovered = True
            import time
            self.timestamp = time.time()


class Journal:
    """Journal system for tracking objectives and lore."""

    def __init__(self):
        """Initialize journal."""
        self.objectives: Dict[str, Objective] = {}
        self.lore_entries: Dict[str, LoreEntry] = {}
        self.discoveries: List[str] = []  # Recently discovered items

    def add_objective(self, objective: Objective):
        """Add an objective to the journal."""
        self.objectives[objective.id] = objective
        if objective.is_active():
            logger.info(f"New Objective: {objective.title}")

    def get_objective(self, id: str) -> Optional[Objective]:
        """Get objective by ID."""
        return self.objectives.get(id)

    def complete_objective(self, id: str):
        """Complete an objective."""
        objective = self.get_objective(id)
        if objective:
            objective.complete()
            logger.info(f"Objective Complete: {objective.title}")

    def reveal_objective(self, id: str):
        """Reveal a hidden objective."""
        objective = self.get_objective(id)
        if objective:
            objective.reveal()
            logger.info(f"New Objective: {objective.title}")

    def get_active_objectives(self) -> List[Objective]:
        """Get all active objectives."""
        return [obj for obj in self.objectives.values() if obj.is_active()]

    def get_completed_objectives(self) -> List[Objective]:
        """Get all completed objectives."""
        return [obj for obj in self.objectives.values()
                if obj.status == ObjectiveStatus.COMPLETED]

    def add_lore_entry(self, entry: LoreEntry):
        """Add a lore entry to the journal."""
        self.lore_entries[entry.id] = entry

    def discover_lore(self, id: str):
        """Discover a lore entry."""
        entry = self.lore_entries.get(id)
        if entry and not entry.discovered:
            entry.discover()
            self.discoveries.append(id)
            logger.info(f"Discovery: {entry.title}")

    def get_discovered_lore(self) -> List[LoreEntry]:
        """Get all discovered lore entries."""
        return [entry for entry in self.lore_entries.values() if entry.discovered]

    def get_lore_by_category(self, category: str) -> List[LoreEntry]:
        """Get discovered lore entries by category."""
        return [entry for entry in self.get_discovered_lore()
                if entry.category == category]

    def get_lore_categories(self) -> List[str]:
        """Get all categories with discovered entries."""
        categories = set()
        for entry in self.get_discovered_lore():
            categories.add(entry.category)
        return sorted(list(categories))

    def clear_recent_discoveries(self):
        """Clear the recent discoveries list."""
        self.discoveries.clear()


def create_default_objectives():
    """Create the default objectives for the game."""
    objectives = []

    # Main exploration objective
    main_obj = Objective(
        "explore",
        "Explore the Ancient Ruins",
        "Discover the secrets hidden within these mysterious structures."
    )
    objectives.append(main_obj)

    # Puzzle objectives
    puzzle_obj = Objective(
        "solve_puzzles",
        "Solve the Ancient Puzzles",
        "The ancients left behind many puzzles. Solve them to unlock new areas."
    )
    puzzle_obj.add_sub_task("Open the Main Door")
    puzzle_obj.add_sub_task("Open the Side Door")
    puzzle_obj.add_sub_task("Open the Timed Door")
    puzzle_obj.add_sub_task("Unlock the Secret Door")
    objectives.append(puzzle_obj)

    # Collection objective
    collect_obj = Objective(
        "collect_gems",
        "Collect All Gems",
        "Find and collect all 3 ancient gems scattered throughout the ruins."
    )
    collect_obj.progress_max = 3
    objectives.append(collect_obj)

    return objectives


def create_default_lore():
    """Create the default lore entries for the game."""
    lore_entries = []

    # History entries
    lore_entries.append(LoreEntry(
        "ruins_history",
        "The Ancient Ruins",
        "These ruins date back thousands of years to a civilization long forgotten. "
        "The architecture suggests advanced knowledge of engineering and mathematics.",
        category="History"
    ))

    # Puzzle entries
    lore_entries.append(LoreEntry(
        "door_mechanisms",
        "Ancient Door Mechanisms",
        "The doors in these ruins are controlled by various mechanisms: levers, buttons, "
        "and pressure plates. Some doors are timed and will close after a short period.",
        category="Puzzles"
    ))

    lore_entries.append(LoreEntry(
        "sequence_puzzle",
        "The Color Sequence",
        "Inscriptions on the wall suggest a specific order: 'First the blood of war (Red), "
        "then the life of peace (Green), finally the calm of wisdom (Blue).'",
        category="Puzzles"
    ))

    # Collectibles
    lore_entries.append(LoreEntry(
        "golden_orb",
        "The Golden Orb",
        "A mysterious golden orb that glows with an inner light. Its purpose remains unknown, "
        "but it seems to resonate with the other artifacts.",
        category="Artifacts"
    ))

    lore_entries.append(LoreEntry(
        "crystal_shard",
        "Crystal Shard",
        "A fragment of a larger crystal formation. Ancient texts mention crystals that could "
        "store knowledge and energy.",
        category="Artifacts"
    ))

    lore_entries.append(LoreEntry(
        "secret_gem",
        "The Secret Gem",
        "Hidden behind the most difficult puzzle, this gem seems to be the most important "
        "artifact of all. It pulses with an otherworldly energy.",
        category="Artifacts"
    ))

    return lore_entries
