"""
Phase 5 Example: NPCs, Dialogue, Quests, and Pathfinding

This example demonstrates how to use all Phase 5 systems together.
"""
import glm
import numpy as np
from game.npc import NPC, NPCManager, NPCState, NPCBehavior
from game.dialogue import DialogueManager
from game.quests import Quest, QuestObjective, QuestManager, ObjectiveType
from game.pathfinding import NavigationGrid, PathFollower


def create_example_scene():
    """Create an example scene with NPCs, dialogues, and quests."""

    # === Setup Managers ===
    npc_manager = NPCManager()
    dialogue_manager = DialogueManager()
    quest_manager = QuestManager()
    nav_grid = NavigationGrid(width=100, height=100, cell_size=1.0)

    # Block some areas (walls, obstacles)
    nav_grid.block_rect(20, 20, 30, 30)  # Building
    nav_grid.block_rect(50, 10, 55, 40)  # Wall

    # === Create NPCs ===

    # 1. Village Guard (Patrols)
    guard = NPC(glm.vec3(10, 0, 10), name="Village Guard", npc_id="guard_1")
    guard.behavior = NPCBehavior.NEUTRAL
    guard.dialogue_id = "guard_greeting"
    guard.set_patrol_points([
        glm.vec3(10, 0, 10),
        glm.vec3(10, 0, 20),
        glm.vec3(20, 0, 20),
        glm.vec3(20, 0, 10)
    ])
    npc_manager.add_npc(guard)

    # 2. Traveling Merchant (Idle)
    merchant = NPC(glm.vec3(15, 0, 15), name="Traveling Merchant", npc_id="merchant")
    merchant.behavior = NPCBehavior.FRIENDLY
    merchant.dialogue_id = "merchant_greeting"
    npc_manager.add_npc(merchant)

    # 3. Village Elder (Quest Giver)
    elder = NPC(glm.vec3(25, 0, 15), name="Village Elder", npc_id="elder")
    elder.behavior = NPCBehavior.QUEST_GIVER
    elder.dialogue_id = "elder_quest"
    elder.quest_id = "investigate_ruins"
    npc_manager.add_npc(elder)

    # 4. Mysterious Stranger (Flees from player)
    stranger = NPC(glm.vec3(40, 0, 40), name="Mysterious Stranger", npc_id="stranger")
    stranger.behavior = NPCBehavior.HOSTILE
    stranger.state = NPCState.FLEE
    stranger.dialogue_id = "mysterious_stranger"
    npc_manager.add_npc(stranger)

    # === Load Dialogues ===

    # Load from JSON file
    count = dialogue_manager.load_dialogues_from_json("assets/dialogues.json")
    print(f"Loaded {count} dialogues from file")

    # Or create programmatically
    dialogue_manager.create_simple_dialogue(
        "test_dialogue",
        "Test NPC",
        [
            "Hello there!",
            "This is a test dialogue.",
            "Goodbye!"
        ]
    )

    # === Create Quests ===

    # Main quest: Investigate the Ruins
    investigate_quest = Quest(
        "investigate_ruins",
        "Investigate the Ancient Ruins",
        "The Village Elder has asked you to investigate strange activity at the northern ruins."
    )

    obj1 = QuestObjective("reach_ruins", "Travel to the ruins", ObjectiveType.REACH)
    obj2 = QuestObjective("explore_ruins", "Explore the ruins", ObjectiveType.DISCOVER)
    obj3 = QuestObjective("return_elder", "Return to the Village Elder", ObjectiveType.TALK_TO)

    investigate_quest.add_objective(obj1)
    investigate_quest.add_objective(obj2)
    investigate_quest.add_objective(obj3)
    investigate_quest.quest_giver_npc = "elder"
    investigate_quest.quest_complete_npc = "elder"
    investigate_quest.reward_text = "500 gold + Ancient Map"

    quest_manager.register_quest(investigate_quest)

    # Side quest: Collect Herbs
    collect_quest = quest_manager.create_simple_quest(
        "collect_herbs",
        "Gather Healing Herbs",
        "The merchant needs healing herbs.",
        [
            ("Collect Redleaf Herbs", 5),
            ("Collect Moonflower", 3),
            ("Return to merchant", 1)
        ]
    )

    return npc_manager, dialogue_manager, quest_manager, nav_grid


def simulate_player_interaction():
    """Simulate player interactions with the scene."""

    npc_manager, dialogue_manager, quest_manager, nav_grid = create_example_scene()

    # Player state
    player_pos = glm.vec3(10, 0, 10)
    current_time = 0.0

    print("\n=== Phase 5 Example: NPC Interaction ===\n")

    # === Scenario 1: Talk to Guard ===
    print("--- Talking to Guard ---")
    guard = npc_manager.get_npc("guard_1")

    if guard.can_interact(player_pos, current_time):
        guard.start_interaction(current_time)

        # Start dialogue
        node = dialogue_manager.start_dialogue(guard.dialogue_id)
        print(f"{node.speaker}: {node.text}")

        # Advance through dialogue
        node = dialogue_manager.advance_dialogue()
        print(f"{node.speaker}: {node.text}")

        # Make a choice (option 2: looking for work)
        node = dialogue_manager.advance_dialogue(choice_index=1)
        print(f"{node.speaker}: {node.text}")

        dialogue_manager.end_dialogue()
        guard.end_interaction()

    # === Scenario 2: Get Quest from Elder ===
    print("\n--- Getting Quest from Elder ---")
    player_pos = glm.vec3(25, 0, 15)
    current_time += 5.0

    elder = npc_manager.get_npc("elder")
    if elder.can_interact(player_pos, current_time):
        elder.start_interaction(current_time)

        # Start quest dialogue
        node = dialogue_manager.start_dialogue(elder.dialogue_id)
        print(f"{node.speaker}: {node.text}")

        # Go through quest offer
        while node:
            node = dialogue_manager.advance_dialogue(choice_index=0)  # Always choose first option
            if node:
                print(f"{node.speaker}: {node.text}")

        # Start the quest
        quest_manager.start_quest(elder.quest_id)
        print(f"\n[Quest Started: {quest_manager.get_quest(elder.quest_id).title}]")

        elder.end_interaction()

    # === Scenario 3: Progress Quest ===
    print("\n--- Progressing Quest ---")
    quest = quest_manager.get_quest("investigate_ruins")

    # Complete objective 1: Reach ruins
    print(f"Objective: {quest.get_current_objective().description}")
    quest_manager.progress_quest("investigate_ruins")
    print("[Objective Complete]")

    # Complete objective 2: Explore
    print(f"Objective: {quest.get_current_objective().description}")
    quest_manager.progress_quest("investigate_ruins")
    print("[Objective Complete]")

    # Complete objective 3: Return
    print(f"Objective: {quest.get_current_objective().description}")
    quest_manager.progress_quest("investigate_ruins")
    print("[Quest Complete!]")
    print(f"Reward: {quest.reward_text}")

    # === Scenario 4: NPC Pathfinding ===
    print("\n--- NPC Pathfinding ---")

    # Have merchant path to player
    merchant = npc_manager.get_npc("merchant")
    merchant_start = merchant.position
    merchant_goal = glm.vec3(50, 0, 50)

    path = nav_grid.find_path(merchant_start, merchant_goal)
    print(f"Merchant pathfinding: {len(path)} waypoints")
    print(f"Start: {merchant_start}")
    print(f"Goal: {merchant_goal}")
    print(f"First waypoints: {path[:3]}")

    # Simulate merchant following path
    follower = PathFollower(path)
    for i in range(100):
        velocity = follower.update(merchant.position, merchant.speed, 0.016)
        merchant.position += velocity * 0.016

        if follower.is_complete():
            print(f"Merchant reached destination in {i} steps!")
            break

    # === Scenario 5: Update NPCs ===
    print("\n--- Simulating NPC AI ---")

    # Reset NPCs
    npc_manager, dialogue_manager, quest_manager, nav_grid = create_example_scene()

    # Simulate 10 seconds
    for frame in range(600):  # 60 FPS * 10 seconds
        dt = 1.0 / 60.0
        player_pos = glm.vec3(15 + frame * 0.01, 0, 15)  # Player moving

        # Update all NPCs
        npc_manager.update_all(dt, player_pos)

    # Check NPC states
    guard = npc_manager.get_npc("guard_1")
    print(f"Guard state after 10s: {guard.state.value}")
    print(f"Guard position: {guard.position}")

    stranger = npc_manager.get_npc("stranger")
    print(f"Stranger state: {stranger.state.value}")
    print(f"Stranger position: {stranger.position}")

    print("\n=== Example Complete ===")


def main():
    """Run the Phase 5 example."""
    print("Phase 5: Game Logic & NPCs Example")
    print("===================================")
    print()
    print("This example demonstrates:")
    print("  1. NPCs with AI behaviors (patrol, idle, flee)")
    print("  2. Dialogue system with choices")
    print("  3. Quest system with objectives")
    print("  4. A* pathfinding with navigation grid")
    print("  5. Integration of all systems")
    print()

    simulate_player_interaction()


if __name__ == "__main__":
    main()
