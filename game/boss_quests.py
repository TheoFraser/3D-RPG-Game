"""Boss encounter quest chains."""
from game.quests import Quest, QuestObjective, ObjectiveType, QuestStatus
from game.quest_waypoints import create_waypoint_for_npc
from game.logger import get_logger

logger = get_logger(__name__)


def create_corrupted_forest_quest(quest_manager, player) -> Quest:
    """
    Create the Corrupted Forest Guardian quest chain.

    Args:
        quest_manager: QuestManager instance
        player: Player instance for rewards

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="corrupted_forest_boss",
        title="The Corrupted Guardian",
        description="Dark magic has corrupted the ancient forest guardian. Defeat it to restore balance."
    )

    # Objective 1: Discover the corrupted forest area
    obj1 = QuestObjective(
        objective_id="find_corruption",
        description="Investigate reports of corruption in the enchanted forest",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    # Objective 2: Defeat the Corrupted Guardian boss
    obj2 = QuestObjective(
        objective_id="defeat_guardian",
        description="Defeat the Corrupted Forest Guardian",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(1)
    quest.add_objective(obj2)

    # Objective 3: Report back
    obj3 = QuestObjective(
        objective_id="report_victory",
        description="Report your victory to the Elder",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint3 = create_waypoint_for_npc("Wise Elder", (-5.0, 0.0, 1.0))
    obj3.set_waypoint(waypoint3)
    quest.add_objective(obj3)

    # Quest rewards
    quest.reward_text = "500 XP, 200 Gold, Ancient Forest Medallion"

    def give_rewards():
        """Give quest rewards to player."""
        # XP already given from boss kill, add bonus gold
        player.add_gold(200)
        # Could add unique quest item here
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"

    return quest


def create_crystal_tyrant_quest(quest_manager, player) -> Quest:
    """
    Create the Crystal Tyrant quest chain.

    Args:
        quest_manager: QuestManager instance
        player: Player instance for rewards

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="crystal_tyrant_boss",
        title="The Crystal Tyrant",
        description="A massive crystal golem threatens the cave miners. Help them by defeating the tyrant."
    )

    # Objective 1: Find the crystal caves
    obj1 = QuestObjective(
        objective_id="find_caves",
        description="Locate the Crystal Caves",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    # Objective 2: Defeat the Crystal Tyrant
    obj2 = QuestObjective(
        objective_id="defeat_tyrant",
        description="Defeat the Crystal Tyrant",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(1)
    quest.add_objective(obj2)

    # Objective 3: Collect crystal shard
    obj3 = QuestObjective(
        objective_id="collect_shard",
        description="Collect the Tyrant's Crystal Shard",
        objective_type=ObjectiveType.COLLECT
    )
    quest.add_objective(obj3)

    # Quest rewards
    quest.reward_text = "600 XP, 250 Gold, Crystal-Infused Armor"

    def give_rewards():
        """Give quest rewards to player."""
        player.add_gold(250)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "merchant"
    quest.quest_complete_npc = "merchant"

    return quest


def create_ancient_warden_quest(quest_manager, player) -> Quest:
    """
    Create the Ancient Warden quest chain.

    Args:
        quest_manager: QuestManager instance
        player: Player instance for rewards

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="ancient_warden_boss",
        title="Awakening of the Warden",
        description="Ancient ruins have awoken their protector. Defeat the Ancient Warden to claim the ruins' secrets."
    )

    # Objective 1: Explore the ancient ruins
    obj1 = QuestObjective(
        objective_id="explore_ruins",
        description="Explore the Ancient Ruins",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    # Objective 2: Defeat the Ancient Warden
    obj2 = QuestObjective(
        objective_id="defeat_warden",
        description="Defeat the Ancient Warden",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(1)
    quest.add_objective(obj2)

    # Objective 3: Claim the ancient artifact
    obj3 = QuestObjective(
        objective_id="claim_artifact",
        description="Claim the Ancient Artifact",
        objective_type=ObjectiveType.COLLECT
    )
    quest.add_objective(obj3)

    # Quest rewards
    quest.reward_text = "700 XP, 300 Gold, Ancient Warden's Blade"

    def give_rewards():
        """Give quest rewards to player."""
        player.add_gold(300)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "elder"
    quest.quest_complete_npc = "elder"

    return quest


def create_void_knight_quest(quest_manager, player) -> Quest:
    """
    Create the Void Knight quest chain.

    Args:
        quest_manager: QuestManager instance
        player: Player instance for rewards

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="void_knight_boss",
        title="Knight of the Void",
        description="A dark knight from the void realm guards a cursed dungeon. Only the bravest can face him."
    )

    # Objective 1: Find the cursed dungeon
    obj1 = QuestObjective(
        objective_id="find_dungeon",
        description="Locate the Cursed Dungeon",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    # Objective 2: Survive the dungeon challenges
    obj2 = QuestObjective(
        objective_id="survive_dungeon",
        description="Defeat 5 dungeon enemies",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(5)
    quest.add_objective(obj2)

    # Objective 3: Defeat the Void Knight
    obj3 = QuestObjective(
        objective_id="defeat_void_knight",
        description="Defeat the Void Knight",
        objective_type=ObjectiveType.DEFEAT
    )
    obj3.set_target(1)
    quest.add_objective(obj3)

    # Quest rewards
    quest.reward_text = "800 XP, 400 Gold, Void Knight's Armor"

    def give_rewards():
        """Give quest rewards to player."""
        player.add_gold(400)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "stranger"
    quest.quest_complete_npc = "stranger"

    return quest


def create_sky_serpent_quest(quest_manager, player) -> Quest:
    """
    Create the Sky Serpent quest chain.

    Args:
        quest_manager: QuestManager instance
        player: Player instance for rewards

    Returns:
        Quest instance
    """
    quest = Quest(
        quest_id="sky_serpent_boss",
        title="Terror of the Skies",
        description="A massive sky serpent terrorizes the floating islands. Defeat it to save the realm."
    )

    # Objective 1: Reach the floating islands
    obj1 = QuestObjective(
        objective_id="reach_islands",
        description="Reach the Floating Islands",
        objective_type=ObjectiveType.DISCOVER
    )
    quest.add_objective(obj1)

    # Objective 2: Defeat the Elder Sky Serpent
    obj2 = QuestObjective(
        objective_id="defeat_serpent",
        description="Defeat the Elder Sky Serpent",
        objective_type=ObjectiveType.DEFEAT
    )
    obj2.set_target(1)
    quest.add_objective(obj2)

    # Objective 3: Return with proof
    obj3 = QuestObjective(
        objective_id="return_proof",
        description="Return to the Village Guard with proof of victory",
        objective_type=ObjectiveType.TALK_TO
    )
    waypoint3 = create_waypoint_for_npc("Village Guard", (-6.0, 0.0, -8.0))
    obj3.set_waypoint(waypoint3)
    quest.add_objective(obj3)

    # Quest rewards
    quest.reward_text = "650 XP, 350 Gold, Serpent Scale Shield"

    def give_rewards():
        """Give quest rewards to player."""
        player.add_gold(350)
        logger.info(f"Quest '{quest.title}' completed! Received: {quest.reward_text}")

    quest.reward_func = give_rewards
    quest.quest_giver_npc = "guard_1"
    quest.quest_complete_npc = "guard_1"

    return quest


def register_all_boss_quests(quest_manager, player):
    """
    Register all boss encounter quests with the quest manager.

    Args:
        quest_manager: QuestManager instance
        player: Player instance

    Returns:
        List of created quest IDs
    """
    quest_ids = []

    # Create and register all boss quests
    quests = [
        create_corrupted_forest_quest(quest_manager, player),
        create_crystal_tyrant_quest(quest_manager, player),
        create_ancient_warden_quest(quest_manager, player),
        create_void_knight_quest(quest_manager, player),
        create_sky_serpent_quest(quest_manager, player),
    ]

    for quest in quests:
        quest_manager.register_quest(quest)
        quest_ids.append(quest.quest_id)
        logger.info(f"Registered boss quest: {quest.title}")

    return quest_ids
