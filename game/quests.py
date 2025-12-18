"""Quest system for tracking objectives and progression."""
from enum import Enum
from typing import Dict, List, Callable, Optional


class QuestStatus(Enum):
    """Quest completion status."""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ObjectiveType(Enum):
    """Types of quest objectives."""
    COLLECT = "collect"      # Collect X items
    REACH = "reach"          # Reach a location
    TALK_TO = "talk_to"      # Talk to an NPC
    DEFEAT = "defeat"        # Defeat enemies
    INTERACT = "interact"    # Interact with objects
    DISCOVER = "discover"    # Discover locations
    CUSTOM = "custom"        # Custom condition


class QuestObjective:
    """A single objective within a quest."""

    def __init__(self, objective_id, description, objective_type=ObjectiveType.CUSTOM):
        """
        Create a quest objective.

        Args:
            objective_id: Unique identifier
            description: Human-readable description
            objective_type: Type of objective
        """
        self.objective_id = objective_id
        self.description = description
        self.objective_type = objective_type

        # Progress tracking
        self.current = 0
        self.target = 1
        self.completed = False

        # Custom completion function
        self.completion_func = None  # Function that returns bool

        # Rewards
        self.on_complete = None  # Callback when objective completes

    def set_target(self, target):
        """
        Set the target count for this objective.

        Args:
            target: Number of times objective must be completed
        """
        self.target = target

    def set_completion_func(self, func):
        """
        Set a custom completion function.

        Args:
            func: Function that returns bool (True if objective is complete)
        """
        self.completion_func = func

    def progress(self, amount=1):
        """
        Progress the objective.

        Args:
            amount: Amount to progress by

        Returns:
            bool: True if objective just completed
        """
        if self.completed:
            return False

        old_current = self.current
        self.current = min(self.current + amount, self.target)

        if self.current >= self.target and not self.completed:
            self.completed = True
            if self.on_complete:
                self.on_complete()
            return True

        return False

    def check_completion(self):
        """
        Check if objective is complete.

        Returns:
            bool: True if complete
        """
        if self.completed:
            return True

        if self.completion_func:
            if self.completion_func():
                self.completed = True
                if self.on_complete:
                    self.on_complete()
                return True

        return False

    def get_progress_text(self):
        """
        Get progress as text.

        Returns:
            str: Progress string (e.g., "2/5")
        """
        if self.target > 1:
            return f"{self.current}/{self.target}"
        return "Complete" if self.completed else "Incomplete"

    def reset(self):
        """Reset objective progress."""
        self.current = 0
        self.completed = False


class Quest:
    """A quest with multiple objectives."""

    def __init__(self, quest_id, title, description=""):
        """
        Create a quest.

        Args:
            quest_id: Unique identifier
            title: Quest title
            description: Quest description
        """
        self.quest_id = quest_id
        self.title = title
        self.description = description
        self.status = QuestStatus.NOT_STARTED

        # Objectives
        self.objectives = []  # List of QuestObjective
        self.current_objective_index = 0

        # NPCs
        self.quest_giver_npc = None  # NPC who gives the quest
        self.quest_complete_npc = None  # NPC to return to

        # Rewards
        self.reward_text = ""
        self.reward_func = None  # Called when quest completes

        # Callbacks
        self.on_start = None
        self.on_complete = None
        self.on_fail = None

    def add_objective(self, objective):
        """
        Add an objective to the quest.

        Args:
            objective: QuestObjective instance

        Returns:
            int: Index of added objective
        """
        self.objectives.append(objective)
        return len(self.objectives) - 1

    def start(self):
        """Start the quest."""
        if self.status == QuestStatus.NOT_STARTED:
            self.status = QuestStatus.ACTIVE
            self.current_objective_index = 0
            if self.on_start:
                self.on_start()
            return True
        return False

    def get_current_objective(self):
        """
        Get the current active objective.

        Returns:
            QuestObjective or None
        """
        if 0 <= self.current_objective_index < len(self.objectives):
            return self.objectives[self.current_objective_index]
        return None

    def progress_objective(self, objective_id=None, amount=1):
        """
        Progress an objective.

        Args:
            objective_id: ID of objective to progress (None = current)
            amount: Amount to progress

        Returns:
            bool: True if quest completed
        """
        if self.status != QuestStatus.ACTIVE:
            return False

        # Find objective
        if objective_id:
            objective = None
            for obj in self.objectives:
                if obj.objective_id == objective_id:
                    objective = obj
                    break
            if not objective:
                return False
        else:
            objective = self.get_current_objective()
            if not objective:
                return False

        # Progress it
        just_completed = objective.progress(amount)

        # If current objective completed, move to next
        if just_completed and objective == self.get_current_objective():
            self.current_objective_index += 1

            # Check if all objectives complete
            if self.current_objective_index >= len(self.objectives):
                return self.complete()

        return False

    def check_completion(self):
        """
        Check if quest should be completed.

        Returns:
            bool: True if quest completed
        """
        if self.status != QuestStatus.ACTIVE:
            return False

        # Check all objectives
        all_complete = True
        for objective in self.objectives:
            if not objective.check_completion():
                all_complete = False
                break

        if all_complete:
            return self.complete()

        return False

    def complete(self):
        """
        Mark quest as completed.

        Returns:
            bool: True if successfully completed
        """
        if self.status != QuestStatus.ACTIVE:
            return False

        self.status = QuestStatus.COMPLETED

        # Apply rewards
        if self.reward_func:
            self.reward_func()

        # Callback
        if self.on_complete:
            self.on_complete()

        return True

    def fail(self):
        """
        Mark quest as failed.

        Returns:
            bool: True if successfully failed
        """
        if self.status != QuestStatus.ACTIVE:
            return False

        self.status = QuestStatus.FAILED

        if self.on_fail:
            self.on_fail()

        return True

    def reset(self):
        """Reset quest to initial state."""
        self.status = QuestStatus.NOT_STARTED
        self.current_objective_index = 0
        for objective in self.objectives:
            objective.reset()

    def get_progress_text(self):
        """
        Get overall progress text.

        Returns:
            str: Progress description
        """
        if self.status == QuestStatus.COMPLETED:
            return "Complete"
        elif self.status == QuestStatus.FAILED:
            return "Failed"
        elif self.status == QuestStatus.ACTIVE:
            completed = sum(1 for obj in self.objectives if obj.completed)
            return f"{completed}/{len(self.objectives)} objectives"
        else:
            return "Not started"


class QuestManager:
    """Manages all quests in the game."""

    def __init__(self):
        """Initialize quest manager."""
        self.quests = {}  # quest_id -> Quest
        self.active_quests = []  # List of active quest IDs
        self.completed_quests = []  # List of completed quest IDs

    def register_quest(self, quest):
        """
        Register a quest.

        Args:
            quest: Quest instance

        Returns:
            str: Quest ID
        """
        self.quests[quest.quest_id] = quest
        return quest.quest_id

    def start_quest(self, quest_id):
        """
        Start a quest.

        Args:
            quest_id: ID of quest to start

        Returns:
            bool: True if started successfully
        """
        if quest_id not in self.quests:
            return False

        quest = self.quests[quest_id]
        if quest.start():
            self.active_quests.append(quest_id)
            return True

        return False

    def complete_quest(self, quest_id):
        """
        Complete a quest.

        Args:
            quest_id: ID of quest to complete

        Returns:
            bool: True if completed successfully
        """
        if quest_id not in self.quests:
            return False

        quest = self.quests[quest_id]
        if quest.complete():
            if quest_id in self.active_quests:
                self.active_quests.remove(quest_id)
            if quest_id not in self.completed_quests:
                self.completed_quests.append(quest_id)
            return True

        return False

    def progress_quest(self, quest_id, objective_id=None, amount=1):
        """
        Progress a quest objective.

        Args:
            quest_id: Quest ID
            objective_id: Objective ID (None = current)
            amount: Amount to progress

        Returns:
            bool: True if quest completed
        """
        if quest_id not in self.quests:
            return False

        quest = self.quests[quest_id]
        completed = quest.progress_objective(objective_id, amount)

        # If quest just completed, update tracking
        if completed:
            if quest_id in self.active_quests:
                self.active_quests.remove(quest_id)
            if quest_id not in self.completed_quests:
                self.completed_quests.append(quest_id)

        return completed

    def get_quest(self, quest_id):
        """
        Get a quest by ID.

        Args:
            quest_id: Quest ID

        Returns:
            Quest or None
        """
        return self.quests.get(quest_id)

    def get_active_quests(self):
        """
        Get all active quests.

        Returns:
            List of Quest objects
        """
        return [self.quests[qid] for qid in self.active_quests if qid in self.quests]

    def get_completed_quests(self):
        """
        Get all completed quests.

        Returns:
            List of Quest objects
        """
        return [self.quests[qid] for qid in self.completed_quests if qid in self.quests]

    def is_quest_active(self, quest_id):
        """Check if a quest is active."""
        return quest_id in self.active_quests

    def is_quest_completed(self, quest_id):
        """Check if a quest is completed."""
        return quest_id in self.completed_quests

    def create_simple_quest(self, quest_id, title, description, objectives_list):
        """
        Create a simple quest with multiple objectives.

        Args:
            quest_id: Unique ID
            title: Quest title
            description: Quest description
            objectives_list: List of (description, target_count) tuples

        Returns:
            Quest
        """
        quest = Quest(quest_id, title, description)

        for i, (obj_desc, target) in enumerate(objectives_list):
            objective = QuestObjective(
                objective_id=f"{quest_id}_obj_{i}",
                description=obj_desc,
                objective_type=ObjectiveType.CUSTOM
            )
            objective.set_target(target)
            quest.add_objective(objective)

        self.register_quest(quest)
        return quest

    def update(self):
        """Update all active quests (check for completion)."""
        for quest_id in self.active_quests[:]:  # Copy list to allow modification
            quest = self.quests.get(quest_id)
            if quest and quest.check_completion():
                self.active_quests.remove(quest_id)
                if quest_id not in self.completed_quests:
                    self.completed_quests.append(quest_id)
