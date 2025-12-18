"""Tests for Phase 5: Game Logic & NPCs (NPCs, Dialogue, Quests, Pathfinding)."""
import pytest
import numpy as np
import glm
from game.npc import NPC, NPCManager, NPCState, NPCBehavior
from game.dialogue import (
    DialogueNode, DialogueTree, DialogueManager,
    DialogueNodeType
)
from game.quests import (
    Quest, QuestObjective, QuestManager,
    QuestStatus, ObjectiveType
)
from game.pathfinding import (
    NavigationGrid, PathFollower,
    astar_search, heuristic
)


class TestNPC:
    """Test NPC system."""

    def test_npc_creation(self):
        """Test creating an NPC."""
        npc = NPC(glm.vec3(0, 0, 0), name="Test NPC")

        assert npc.name == "Test NPC"
        assert npc.npc_id == "test_npc"
        assert npc.state == NPCState.IDLE
        assert npc.behavior == NPCBehavior.FRIENDLY
        assert npc.interactable == True

    def test_npc_patrol(self):
        """Test NPC patrol behavior."""
        npc = NPC(glm.vec3(0, 0, 0), name="Guard")

        # Set patrol points
        patrol_points = [
            glm.vec3(0, 0, 0),
            glm.vec3(10, 0, 0),
            glm.vec3(10, 0, 10)
        ]
        npc.set_patrol_points(patrol_points)

        assert npc.state == NPCState.PATROL
        assert len(npc.patrol_points) == 3

        # Update NPC (should move towards first patrol point)
        for _ in range(100):  # Simulate movement
            npc.update(0.016)  # 60 FPS

        # Should have moved
        assert glm.length(npc.position) > 0

    def test_npc_interaction(self):
        """Test NPC interaction."""
        npc = NPC(glm.vec3(0, 0, 0), name="Merchant")
        player_pos = glm.vec3(2, 0, 0)
        current_time = 0.0

        # Should be able to interact (within range)
        assert npc.can_interact(player_pos, current_time) == True

        # Start interaction
        npc.start_interaction(current_time)
        assert npc.state == NPCState.INTERACT
        assert npc.has_talked == True

        # Can't interact immediately (cooldown)
        assert npc.can_interact(player_pos, current_time) == False

        # Can interact after cooldown
        assert npc.can_interact(player_pos, current_time + 2.0) == True

    def test_npc_manager(self):
        """Test NPC manager."""
        manager = NPCManager()

        # Add NPCs
        npc1 = NPC(glm.vec3(0, 0, 0), name="NPC1")
        npc2 = NPC(glm.vec3(10, 0, 0), name="NPC2")

        manager.add_npc(npc1)
        manager.add_npc(npc2)

        assert len(manager) == 2
        assert manager.get_npc("npc1") == npc1
        assert manager.get_npc("npc2") == npc2

        # Update all NPCs
        manager.update_all(0.016, player_position=glm.vec3(5, 0, 0))

        # Get interactable NPC
        player_pos = glm.vec3(1, 0, 0)
        nearby = manager.get_interactable_npc(player_pos, 0.0)
        assert nearby == npc1  # Closest to player


class TestDialogue:
    """Test dialogue system."""

    def test_dialogue_node(self):
        """Test dialogue node creation."""
        node = DialogueNode(
            node_id="greeting",
            node_type=DialogueNodeType.TEXT,
            text="Hello, traveler!",
            speaker="Guard"
        )

        assert node.node_id == "greeting"
        assert node.text == "Hello, traveler!"
        assert node.speaker == "Guard"

    def test_dialogue_tree_linear(self):
        """Test linear dialogue tree."""
        tree = DialogueTree("test_dialogue", "Merchant")

        # Create nodes
        node1 = DialogueNode("node1", DialogueNodeType.TEXT, "Welcome to my shop!", "Merchant")
        node1.next_node = "node2"

        node2 = DialogueNode("node2", DialogueNodeType.TEXT, "What can I get you?", "Merchant")
        node2.next_node = "node3"

        node3 = DialogueNode("node3", DialogueNodeType.END, "Come back soon!", "Merchant")

        tree.add_node(node1)
        tree.add_node(node2)
        tree.add_node(node3)

        # Start dialogue
        current = tree.start()
        assert current.text == "Welcome to my shop!"

        # Advance
        current = tree.advance()
        assert current.text == "What can I get you?"

        current = tree.advance()
        assert current.text == "Come back soon!"

        # End of dialogue
        current = tree.advance()
        assert current is None

    def test_dialogue_tree_choices(self):
        """Test dialogue with choices."""
        tree = DialogueTree("choice_dialogue", "Elder")

        # Greeting node
        greeting = DialogueNode("greeting", DialogueNodeType.TEXT, "Greetings, adventurer.", "Elder")
        greeting.next_node = "choice"

        # Choice node
        choice = DialogueNode("choice", DialogueNodeType.CHOICE, "What do you ask?", "Player")
        choice.add_choice("Tell me about this place.", "about_place")
        choice.add_choice("Do you have any quests?", "quest")
        choice.add_choice("Goodbye.", "goodbye")

        # Response nodes
        about = DialogueNode("about_place", DialogueNodeType.END, "This village is ancient...", "Elder")
        quest = DialogueNode("quest", DialogueNodeType.END, "I need help finding...", "Elder")
        goodbye = DialogueNode("goodbye", DialogueNodeType.END, "Farewell.", "Elder")

        tree.add_node(greeting)
        tree.add_node(choice)
        tree.add_node(about)
        tree.add_node(quest)
        tree.add_node(goodbye)

        # Start and navigate
        tree.start()
        tree.advance()  # Move to choice

        current = tree.get_current_node()
        assert current.node_type == DialogueNodeType.CHOICE
        assert len(current.choices) == 3

        # Choose first option
        result = tree.advance(choice_index=0)
        assert result.text == "This village is ancient..."

    def test_dialogue_manager(self):
        """Test dialogue manager."""
        manager = DialogueManager()

        # Create simple dialogue
        tree = manager.create_simple_dialogue(
            "test_dlg",
            "Guard",
            ["Stop right there!", "This area is restricted."]
        )

        assert tree.dialogue_id == "test_dlg"
        assert len(tree.nodes) == 2

        # Start dialogue
        node = manager.start_dialogue("test_dlg")
        assert node is not None
        assert node.text == "Stop right there!"
        assert manager.is_dialogue_active() == True

        # Advance
        node = manager.advance_dialogue()
        assert node.text == "This area is restricted."

        # End
        node = manager.advance_dialogue()
        assert node is None
        assert manager.is_dialogue_active() == False


class TestQuests:
    """Test quest system."""

    def test_quest_objective(self):
        """Test quest objective."""
        objective = QuestObjective(
            "collect_gems",
            "Collect 5 gems",
            ObjectiveType.COLLECT
        )
        objective.set_target(5)

        assert objective.completed == False
        assert objective.current == 0
        assert objective.target == 5

        # Progress objective
        objective.progress(2)
        assert objective.current == 2
        assert objective.get_progress_text() == "2/5"

        objective.progress(3)
        assert objective.completed == True
        assert objective.get_progress_text() == "5/5"

    def test_quest_creation(self):
        """Test quest creation."""
        quest = Quest("find_artifact", "Find the Ancient Artifact", "Search the ruins...")

        assert quest.quest_id == "find_artifact"
        assert quest.title == "Find the Ancient Artifact"
        assert quest.status == QuestStatus.NOT_STARTED

        # Add objectives
        obj1 = QuestObjective("reach_ruins", "Reach the ruins")
        obj2 = QuestObjective("find_key", "Find the key")
        obj3 = QuestObjective("open_door", "Open the sealed door")

        quest.add_objective(obj1)
        quest.add_objective(obj2)
        quest.add_objective(obj3)

        assert len(quest.objectives) == 3

    def test_quest_progression(self):
        """Test quest progression."""
        quest = Quest("test_quest", "Test Quest")

        obj1 = QuestObjective("obj1", "First objective")
        obj2 = QuestObjective("obj2", "Second objective")

        quest.add_objective(obj1)
        quest.add_objective(obj2)

        # Start quest
        quest.start()
        assert quest.status == QuestStatus.ACTIVE
        assert quest.current_objective_index == 0

        # Progress first objective
        quest.progress_objective()
        assert obj1.completed == True
        assert quest.current_objective_index == 1

        # Progress second objective
        completed = quest.progress_objective()
        assert obj2.completed == True
        assert completed == True
        assert quest.status == QuestStatus.COMPLETED

    def test_quest_manager(self):
        """Test quest manager."""
        manager = QuestManager()

        # Create quest
        quest = manager.create_simple_quest(
            "tutorial",
            "Tutorial Quest",
            "Learn the basics",
            [("Move around", 1), ("Collect an item", 1)]
        )

        assert manager.get_quest("tutorial") == quest

        # Start quest
        manager.start_quest("tutorial")
        assert manager.is_quest_active("tutorial") == True

        # Progress
        manager.progress_quest("tutorial")  # Complete first objective
        manager.progress_quest("tutorial")  # Complete second objective

        assert manager.is_quest_completed("tutorial") == True


class TestPathfinding:
    """Test pathfinding system."""

    def test_heuristic(self):
        """Test heuristic function."""
        dist = heuristic(0, 0, 10, 5)
        assert dist == 15  # Manhattan distance

    def test_astar_simple(self):
        """Test A* with simple grid."""
        # Create a 10x10 grid with no obstacles
        grid = np.zeros((10, 10), dtype=np.int32)

        # Find path from (0,0) to (9,9)
        path = astar_search(grid, 0, 0, 9, 9)

        assert len(path) > 0
        assert path[0][0] == 0 and path[0][1] == 0  # Start
        assert path[-1][0] == 9 and path[-1][1] == 9  # Goal

    def test_astar_with_obstacles(self):
        """Test A* with obstacles."""
        # Create grid with wall
        grid = np.zeros((10, 10), dtype=np.int32)

        # Add vertical wall at x=5
        for z in range(3, 8):
            grid[z, 5] = 1

        # Find path that must go around wall
        path = astar_search(grid, 0, 5, 9, 5)

        assert len(path) > 0
        # Path should not go through wall
        for i in range(len(path)):
            x, z = path[i]
            assert grid[z, x] == 0  # All path cells should be walkable

    def test_astar_no_path(self):
        """Test A* when no path exists."""
        # Create grid with complete wall
        grid = np.zeros((10, 10), dtype=np.int32)

        # Wall blocking entire middle
        for z in range(10):
            grid[z, 5] = 1

        # Try to find path (should fail)
        path = astar_search(grid, 0, 0, 9, 0)

        assert len(path) == 0  # No path found

    def test_navigation_grid(self):
        """Test navigation grid."""
        nav_grid = NavigationGrid(width=50, height=50, cell_size=1.0)

        assert nav_grid.width == 50
        assert nav_grid.height == 50

        # Block some cells
        nav_grid.set_blocked(25, 25, True)
        assert nav_grid.is_walkable(25, 25) == False
        assert nav_grid.is_walkable(24, 24) == True

        # World to grid conversion
        gx, gz = nav_grid.world_to_grid(25.5, 25.5)
        assert gx == 25 and gz == 25

        # Grid to world conversion
        wx, wz = nav_grid.grid_to_world(10, 10)
        assert abs(wx - 10.5) < 0.01
        assert abs(wz - 10.5) < 0.01

    def test_find_path(self):
        """Test finding path with navigation grid."""
        nav_grid = NavigationGrid(width=20, height=20, cell_size=1.0)

        # Block a rectangular area
        nav_grid.block_rect(5, 5, 10, 10)

        # Find path around obstacle
        start = glm.vec3(0, 0, 0)
        goal = glm.vec3(15, 0, 15)

        path = nav_grid.find_path(start, goal)

        assert len(path) > 0
        assert isinstance(path[0], glm.vec3)

        # Path should go around blocked area
        for waypoint in path:
            gx, gz = nav_grid.world_to_grid(waypoint.x, waypoint.z)
            assert nav_grid.is_walkable(gx, gz)

    def test_path_follower(self):
        """Test path follower."""
        # Create simple path
        path = [
            glm.vec3(0, 0, 0),
            glm.vec3(10, 0, 0),
            glm.vec3(10, 0, 10)
        ]

        follower = PathFollower(path)
        current_pos = glm.vec3(0, 0, 0)

        assert follower.is_complete() == False

        # Simulate movement
        for _ in range(1000):
            velocity = follower.update(current_pos, speed=5.0, delta_time=0.016)
            current_pos += velocity * 0.016

            if follower.is_complete():
                break

        # Should reach end
        distance_to_goal = glm.length(current_pos - path[-1])
        assert distance_to_goal < 1.0


class TestIntegration:
    """Integration tests for Phase 5 systems."""

    def test_npc_with_dialogue(self):
        """Test NPC with dialogue system."""
        # Create NPC
        npc = NPC(glm.vec3(0, 0, 0), name="Quest Giver")
        npc.dialogue_id = "quest_intro"

        # Create dialogue
        dialogue_mgr = DialogueManager()
        dialogue_mgr.create_simple_dialogue(
            "quest_intro",
            "Quest Giver",
            ["I have a task for you.", "Will you help me?"]
        )

        # Start dialogue
        node = dialogue_mgr.start_dialogue(npc.dialogue_id)
        assert node is not None
        assert node.speaker == "Quest Giver"

    def test_quest_with_npc(self):
        """Test quest given by NPC."""
        # Create quest manager
        quest_mgr = QuestManager()

        # Create quest
        quest = quest_mgr.create_simple_quest(
            "help_merchant",
            "Help the Merchant",
            "The merchant needs assistance",
            [("Talk to the merchant", 1), ("Collect supplies", 5)]
        )

        # Create NPC
        npc = NPC(glm.vec3(0, 0, 0), name="Merchant")
        npc.quest_id = "help_merchant"

        # Start quest
        quest_mgr.start_quest(npc.quest_id)
        assert quest_mgr.is_quest_active(npc.quest_id)

        # Progress quest
        quest_mgr.progress_quest(npc.quest_id)  # Talk to merchant
        quest_mgr.progress_quest(npc.quest_id, amount=5)  # Collect all supplies

        assert quest_mgr.is_quest_completed(npc.quest_id)

    def test_npc_pathfinding(self):
        """Test NPC using pathfinding."""
        # Create navigation grid
        nav_grid = NavigationGrid(width=30, height=30, cell_size=1.0)

        # Create NPC
        npc = NPC(glm.vec3(0, 0, 0), name="Wanderer")

        # Find path to destination
        destination = glm.vec3(20, 0, 20)
        path = nav_grid.find_path(npc.position, destination)

        assert len(path) > 0

        # NPC could follow this path
        follower = PathFollower(path)

        # Simulate a few steps
        for _ in range(10):
            velocity = follower.update(npc.position, npc.speed, 0.016)
            npc.position += velocity * 0.016

        # NPC should have moved
        assert glm.length(npc.position) > 0


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
