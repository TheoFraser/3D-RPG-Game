"""Side quest content - Optional quests for exploration and rewards."""
from game.quests import Quest, QuestObjective, ObjectiveType
from game.quest_waypoints import create_waypoint_for_npc, create_waypoint_for_area, QuestWaypoint, WaypointType
from game.logger import get_logger

logger = get_logger(__name__)


def create_shrine_pilgrim_quest(quest_manager, player) -> Quest:
    """
    Side quest: Visit all shrines in the world.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_shrine_pilgrim",
        title="Shrine Pilgrim",
        description="Ancient shrines dot the landscape. Visit them all to gain their blessing."
    )

    obj1 = QuestObjective(
        objective_id="visit_shrines",
        description="Discover and activate 12 shrines",
        objective_type=ObjectiveType.DISCOVER
    )
    obj1.set_target(12)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="report_pilgrimage",
        description="Report your pilgrimage to the Wise Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "800 XP, 400 Gold, Traveler's Blessing (+10% movement speed)"

    def give_rewards():
        player.gain_xp(800)
        player.add_gold(400)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"

    return quest


def create_merchant_supplies_quest(quest_manager, player) -> Quest:
    """
    Side quest: Help the merchant gather supplies.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_merchant_supplies",
        title="Merchant's Request",
        description="The wandering merchant needs help gathering materials for his trade route."
    )

    obj1 = QuestObjective(
        objective_id="collect_materials",
        description="Collect materials from defeated enemies (defeat 20 enemies)",
        objective_type=ObjectiveType.DEFEAT
    )
    obj1.set_target(20)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="return_supplies",
        description="Return to the Wandering Merchant",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Wandering Merchant", (5.0, 0.0, 2.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "300 XP, 200 Gold, 10% Merchant Discount"

    def give_rewards():
        player.gain_xp(300)
        player.add_gold(200)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "merchant"
    quest.quest_complete_npc = "merchant"

    return quest


def create_ruin_explorer_quest(quest_manager, player) -> Quest:
    """
    Side quest: Explore all ruins and collect ancient lore.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_ruin_explorer",
        title="Ancient Ruins Explorer",
        description="Explore the ancient ruins scattered across the realm and uncover their secrets."
    )

    obj1 = QuestObjective(
        objective_id="discover_ruins",
        description="Discover 10 ancient ruins",
        objective_type=ObjectiveType.DISCOVER
    )
    obj1.set_target(10)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="report_findings",
        description="Share your findings with the Wise Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "600 XP, 350 Gold, Archaeologist's Map"

    def give_rewards():
        player.gain_xp(600)
        player.add_gold(350)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"

    return quest


def create_guard_patrol_quest(quest_manager, player) -> Quest:
    """
    Side quest: Help the guard clear nearby threats.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_guard_patrol",
        title="Patrol Assistance",
        description="The Village Guard needs help clearing enemies near the village."
    )

    obj1 = QuestObjective(
        objective_id="clear_enemies",
        description="Defeat enemies near the village (15 enemies)",
        objective_type=ObjectiveType.DEFEAT
    )
    obj1.set_target(15)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="report_guard",
        description="Report to the Village Guard",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Village Guard", (-6.0, 0.0, -8.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "400 XP, 250 Gold, Guard's Commendation"

    def give_rewards():
        player.gain_xp(400)
        player.add_gold(250)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "guard_1"
    quest.quest_complete_npc = "guard_1"

    return quest


def create_crystal_collector_quest(quest_manager, player) -> Quest:
    """
    Side quest: Collect crystals from the Crystal Caves.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_crystal_collector",
        title="Crystal Collector",
        description="The merchant seeks rare crystals from the caves. Defeat crystal enemies to gather them."
    )

    obj1 = QuestObjective(
        objective_id="collect_crystals",
        description="Collect crystals (defeat 10 enemies in Crystal Caves biome)",
        objective_type=ObjectiveType.DEFEAT
    )
    obj1.set_target(10)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="deliver_crystals",
        description="Deliver the crystals to the Wandering Merchant",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Wandering Merchant", (5.0, 0.0, 2.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "350 XP, 300 Gold, Crystal Pendant"

    def give_rewards():
        player.gain_xp(350)
        player.add_gold(300)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "merchant"
    quest.quest_complete_npc = "merchant"

    return quest


def create_biome_explorer_quest(quest_manager, player) -> Quest:
    """
    Side quest: Discover all biome types.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_biome_explorer",
        title="World Explorer",
        description="Travel to each unique biome in the realm and witness its wonders."
    )

    obj1 = QuestObjective(
        objective_id="visit_grasslands",
        description="Visit the Grasslands biome",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="visit_forest",
        description="Visit the Enchanted Forest biome",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj2)

    obj3 = QuestObjective(
        objective_id="visit_caves",
        description="Visit the Crystal Caves biome",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj3)

    obj4 = QuestObjective(
        objective_id="visit_islands",
        description="Visit the Floating Islands biome",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj4)

    obj5 = QuestObjective(
        objective_id="visit_ruins",
        description="Visit the Ancient Ruins biome",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj5)

    obj6 = QuestObjective(
        objective_id="report_travels",
        description="Share your travels with the Wise Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint6 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj6.set_waypoint(waypoint6)
    quest.add_objective(obj6)

    quest.reward_text = "700 XP, 450 Gold, Explorer's Compass"

    def give_rewards():
        player.gain_xp(700)
        player.add_gold(450)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"

    return quest


def create_dungeon_delver_quest(quest_manager, player) -> Quest:
    """
    Side quest: Clear all dungeons in the world.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_dungeon_delver",
        title="Dungeon Delver",
        description="Prove your worth by conquering every dungeon in the realm."
    )

    obj1 = QuestObjective(
        objective_id="clear_dungeons",
        description="Discover and clear 6 dungeons (defeat their bosses)",
        objective_type=ObjectiveType.DEFEAT
    )
    obj1.set_target(6)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="report_conquest",
        description="Report your conquests to the Mysterious Figure",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Mysterious Figure", (-6.0, 0.0, 5.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "1200 XP, 800 Gold, Dungeon Master's Key"

    def give_rewards():
        player.gain_xp(1200)
        player.add_gold(800)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "stranger"
    quest.quest_complete_npc = "stranger"

    return quest


def create_village_finder_quest(quest_manager, player) -> Quest:
    """
    Side quest: Find all villages.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_village_finder",
        title="Village Finder",
        description="Locate all villages scattered across the realm and meet their inhabitants."
    )

    obj1 = QuestObjective(
        objective_id="find_villages",
        description="Discover 4 villages",
        objective_type=ObjectiveType.DISCOVER
    )
    obj1.set_target(4)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="report_villages",
        description="Report back to the Village Guard",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Village Guard", (-6.0, 0.0, -8.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "500 XP, 300 Gold, Traveler's Charm"

    def give_rewards():
        player.gain_xp(500)
        player.add_gold(300)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "guard_1"
    quest.quest_complete_npc = "guard_1"

    return quest


def create_seasoned_warrior_quest(quest_manager, player) -> Quest:
    """
    Side quest: Become a seasoned warrior through combat.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_seasoned_warrior",
        title="Seasoned Warrior",
        description="Prove yourself in combat by defeating many foes."
    )

    obj1 = QuestObjective(
        objective_id="defeat_many",
        description="Defeat 50 enemies",
        objective_type=ObjectiveType.DEFEAT
    )
    obj1.set_target(50)
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="warrior_recognition",
        description="Speak with the Village Guard for recognition",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint2 = create_waypoint_for_npc("Village Guard", (-6.0, 0.0, -8.0))
    obj2.set_waypoint(waypoint2)
    quest.add_objective(obj2)

    quest.reward_text = "900 XP, 600 Gold, Warrior's Mark (+5% damage)"

    def give_rewards():
        player.gain_xp(900)
        player.add_gold(600)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "guard_1"
    quest.quest_complete_npc = "guard_1"

    return quest


def create_mysterious_task_quest(quest_manager, player) -> Quest:
    """
    Side quest: A mysterious task from the stranger.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="side_mysterious_task",
        title="The Stranger's Task",
        description="The Mysterious Figure has a cryptic request. What could they want?"
    )

    obj1 = QuestObjective(
        objective_id="explore_far",
        description="Travel to the edge of the known world (1000 units from spawn)",
        objective_type=ObjectiveType.REACH
    )
    quest.add_objective(obj1)

    obj2 = QuestObjective(
        objective_id="prove_strength",
        description="Defeat a powerful foe (defeat any boss)",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(1)
    quest.add_objective(obj2)

    obj3 = QuestObjective(
        objective_id="return_stranger",
        description="Return to the Mysterious Figure",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint3 = create_waypoint_for_npc("Mysterious Figure", (-6.0, 0.0, 5.0))
    obj3.set_waypoint(waypoint3)
    quest.add_objective(obj3)

    quest.reward_text = "750 XP, 500 Gold, ???"

    def give_rewards():
        player.gain_xp(750)
        player.add_gold(500)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")
        logger.info("The stranger nods approvingly. You feel... different.")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "stranger"
    quest.quest_complete_npc = "stranger"

    return quest


def register_all_side_quests(quest_manager, player):
    """
    Register all side quests with the quest manager.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        List of created quest IDs
    """
    quest_ids = []

    # Create and register all side quests
    quests = [
        create_shrine_pilgrim_quest(quest_manager, player),
        create_merchant_supplies_quest(quest_manager, player),
        create_ruin_explorer_quest(quest_manager, player),
        create_guard_patrol_quest(quest_manager, player),
        create_crystal_collector_quest(quest_manager, player),
        create_biome_explorer_quest(quest_manager, player),
        create_dungeon_delver_quest(quest_manager, player),
        create_village_finder_quest(quest_manager, player),
        create_seasoned_warrior_quest(quest_manager, player),
        create_mysterious_task_quest(quest_manager, player),
    ]

    for quest in quests:
        quest_manager.register_quest(quest)
        quest_ids.append(quest.quest_id)
        logger.info(f"Registered side quest: {quest.title}")

    return quest_ids
