"""Main quest storyline - 3 Act campaign."""
from game.quests import Quest, QuestObjective, ObjectiveType
from game.quest_waypoints import create_waypoint_for_npc, create_waypoint_for_area, QuestWaypoint, WaypointType
from game.logger import get_logger

logger = get_logger(__name__)


def create_prologue_quest(quest_manager, player) -> Quest:
    """
    Act 0: Awakening - Introduction to the world.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="main_prologue",
        title="Awakening",
        description="You wake in an ancient land, with no memory of how you arrived. The Wise Elder may have answers."
    )

    # Objective 1: Talk to the Wise Elder
    obj1 = QuestObjective(
        objective_id="speak_elder",
        description="Speak with the Wise Elder in the village",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint1 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj1.set_waypoint(waypoint1)
    quest.add_objective(obj1)

    # Objective 2: Explore the immediate area
    obj2 = QuestObjective(
        objective_id="explore_village",
        description="Explore the village area (walk 100 units from spawn)",
        objective_type=ObjectiveType.REACH
    )
    waypoint2 = create_waypoint_for_area("Village Area", (0.0, 0.0, -100.0), radius=20.0)
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    # Objective 3: Return to Elder
    obj3 = QuestObjective(
        objective_id="return_elder",
        description="Return to the Wise Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint3 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj3.set_waypoint(waypoint3)
    quest.add_objective(obj3)

    # Quest rewards
    quest.reward_text = "100 XP, Basic Sword, 50 Gold"

    def give_rewards():
        player.gain_xp(100)
        player.add_gold(50)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"

    return quest


def create_act1_quest(quest_manager, player) -> Quest:
    """
    Act 1: The Corruption - Investigate the spreading darkness.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="main_act1",
        title="The Spreading Corruption",
        description="Dark magic spreads from the Enchanted Forest. Investigate its source and stop the corruption."
    )

    # Objective 1: Travel to Enchanted Forest
    obj1 = QuestObjective(
        objective_id="reach_forest",
        description="Travel to the Enchanted Forest",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    # Objective 2: Defeat corrupted creatures
    obj2 = QuestObjective(
        objective_id="defeat_corrupted",
        description="Defeat 10 corrupted enemies",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(10)
    quest.add_objective(obj2)

    # Objective 3: Find the corruption source
    obj3 = QuestObjective(
        objective_id="find_source",
        description="Locate the source of corruption (discover a dungeon in the forest)",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj3)

    # Objective 4: Defeat the Corrupted Guardian (boss)
    obj4 = QuestObjective(
        objective_id="defeat_forest_boss",
        description="Defeat the Corrupted Forest Guardian",
        objective_type=ObjectiveType.DEFEAT
    )
    obj4.set_target(1)
    quest.add_objective(obj4)

    # Objective 5: Report to Elder
    obj5 = QuestObjective(
        objective_id="report_corruption",
        description="Report your findings to the Wise Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint5 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj5.set_waypoint(waypoint5)
    quest.add_objective(obj5)

    # Quest rewards
    quest.reward_text = "500 XP, 300 Gold, Forest Amulet"

    def give_rewards():
        player.gain_xp(500)
        player.add_gold(300)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"
    quest.prerequisites = ["main_prologue"]  # Requires prologue completion

    return quest


def create_act2_quest(quest_manager, player) -> Quest:
    """
    Act 2: The Gathering Storm - Collect ancient artifacts to combat the darkness.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="main_act2",
        title="The Gathering Storm",
        description="The corruption was only a symptom. Ancient artifacts scattered across the realm hold the key to stopping a greater threat."
    )

    # Objective 1: Speak with the Mysterious Figure
    obj1 = QuestObjective(
        objective_id="speak_stranger",
        description="Seek out the Mysterious Figure for guidance",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint1 = create_waypoint_for_npc("Mysterious Figure", (-6.0, 0.0, 5.0))
    obj1.set_waypoint(waypoint1)
    quest.add_objective(obj1)

    # Objective 2: Retrieve the Crystal Shard
    obj2 = QuestObjective(
        objective_id="get_crystal",
        description="Obtain the Crystal Shard from the Crystal Caves",
        objective_type=ObjectiveType.COLLECT
    )
    quest.add_objective(obj2)

    # Objective 3: Retrieve the Ancient Artifact
    obj3 = QuestObjective(
        objective_id="get_artifact",
        description="Claim the Ancient Artifact from the ruins",
        objective_type=ObjectiveType.COLLECT
    )
    quest.add_objective(obj3)

    # Objective 4: Discover the Sky Islands
    obj4 = QuestObjective(
        objective_id="reach_sky",
        description="Find a way to the Floating Islands",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj4)

    # Objective 5: Defeat the Sky Serpent
    obj5 = QuestObjective(
        objective_id="defeat_serpent",
        description="Defeat the Elder Sky Serpent guardian",
        objective_type=ObjectiveType.DEFEAT
    )
    obj5.set_target(1)
    quest.add_objective(obj5)

    # Objective 6: Return with the artifacts
    obj6 = QuestObjective(
        objective_id="return_artifacts",
        description="Bring the artifacts to the Mysterious Figure",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint6 = create_waypoint_for_npc("Mysterious Figure", (-6.0, 0.0, 5.0))
    obj6.set_waypoint(waypoint6)
    quest.add_objective(obj6)

    # Quest rewards
    quest.reward_text = "1000 XP, 500 Gold, Ancient Power"

    def give_rewards():
        player.gain_xp(1000)
        player.add_gold(500)
        # Could grant special ability or stat boost here
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "stranger"
    quest.prerequisites = ["main_act1"]  # Requires Act 1 completion

    return quest


def create_act3_quest(quest_manager, player) -> Quest:
    """
    Act 3: Into the Void - Final confrontation with the darkness.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="main_act3",
        title="Into the Void",
        description="The artifacts reveal a portal to the Void. Only by entering the cursed dungeon and defeating the Void Knight can the realm be saved."
    )

    # Objective 1: Prepare for battle
    obj1 = QuestObjective(
        objective_id="gear_up",
        description="Ensure you have strong equipment (reach level 10)",
        objective_type=ObjectiveType.CUSTOM
    )
    quest.add_objective(obj1)

    # Objective 2: Locate the Cursed Dungeon
    obj2 = QuestObjective(
        objective_id="find_void",
        description="Locate the entrance to the Cursed Dungeon",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj2)

    # Objective 3: Clear the dungeon
    obj3 = QuestObjective(
        objective_id="clear_dungeon",
        description="Defeat the dungeon's guardians (10 enemies)",
        objective_type=ObjectiveType.DEFEAT
    )
    obj3.set_target(10)
    quest.add_objective(obj3)

    # Objective 4: Face the Void Knight
    obj4 = QuestObjective(
        objective_id="defeat_void_knight",
        description="Defeat the Void Knight",
        objective_type=ObjectiveType.DEFEAT
    )
    obj4.set_target(1)
    quest.add_objective(obj4)

    # Objective 5: Seal the portal
    obj5 = QuestObjective(
        objective_id="seal_portal",
        description="Use the artifacts to seal the Void portal",
        objective_type=ObjectiveType.INTERACT
    )
    quest.add_objective(obj5)

    # Objective 6: Return victorious
    obj6 = QuestObjective(
        objective_id="victory",
        description="Return to the Wise Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint6 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj6.set_waypoint(waypoint6)
    quest.add_objective(obj6)

    # Quest rewards
    quest.reward_text = "2000 XP, 1000 Gold, Hero's Title"

    def give_rewards():
        player.gain_xp(2000)
        player.add_gold(1000)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")
        logger.info("=== CONGRATULATIONS! You have completed the main storyline! ===")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "stranger"
    quest.quest_complete_npc = "elder"
    quest.prerequisites = ["main_act2"]  # Requires Act 2 completion

    return quest


def register_main_quest_line(quest_manager, player):
    """
    Register all main quest line quests.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        List of main quest IDs
    """
    quest_ids = []

    # Create and register main quests in order
    quests = [
        create_prologue_quest(quest_manager, player),
        create_act1_quest(quest_manager, player),
        create_act2_quest(quest_manager, player),
        create_act3_quest(quest_manager, player),
    ]

    for quest in quests:
        quest_manager.register_quest(quest)
        quest_ids.append(quest.quest_id)
        logger.info(f"Registered main quest: {quest.title}")

    return quest_ids
