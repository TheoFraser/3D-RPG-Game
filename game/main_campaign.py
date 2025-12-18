"""Main quest campaign - The Awakening of the Ancient Guardians.

This campaign tells the story of an ancient threat awakening in the world,
and the player's journey to stop it.
"""
from game.quests import Quest, QuestObjective, ObjectiveType, QuestStatus
from game.logger import get_logger

logger = get_logger(__name__)


class MainCampaign:
    """
    Main story campaign manager.

    Story Summary:
    The player awakens in a peaceful world, but strange disturbances have been
    occurring. Ancient guardians that once protected the land have become corrupted
    by a dark force. The player must journey through different biomes, gathering
    power and allies, to confront the source of the corruption and restore balance.
    """

    def __init__(self, quest_manager, player):
        """
        Initialize the main campaign.

        Args:
            quest_manager: QuestManager instance
            player: Player instance
        """
        self.quest_manager = quest_manager
        self.player = player
        self.campaign_quests = []

        # Create all campaign quests
        self._create_campaign_quests()

        logger.info("Main campaign initialized with 8 quests")

    def _create_campaign_quests(self):
        """Create all main campaign quests."""
        # Quest 1: The Awakening
        q1 = self._create_quest_awakening()
        self.campaign_quests.append(q1.quest_id)

        # Quest 2: First Blood
        q2 = self._create_quest_first_blood()
        self.campaign_quests.append(q2.quest_id)

        # Quest 3: The Village Elder
        q3 = self._create_quest_village_elder()
        self.campaign_quests.append(q3.quest_id)

        # Quest 4: Gathering Strength
        q4 = self._create_quest_gathering_strength()
        self.campaign_quests.append(q4.quest_id)

        # Quest 5: The Corrupted Woods
        q5 = self._create_quest_corrupted_woods()
        self.campaign_quests.append(q5.quest_id)

        # Quest 6: Crystal Caves Expedition
        q6 = self._create_quest_crystal_caves()
        self.campaign_quests.append(q6.quest_id)

        # Quest 7: The Ancient Shrine
        q7 = self._create_quest_ancient_shrine()
        self.campaign_quests.append(q7.quest_id)

        # Quest 8: Final Confrontation
        q8 = self._create_quest_final_boss()
        self.campaign_quests.append(q8.quest_id)

    def _create_quest_awakening(self) -> Quest:
        """Quest 1: The Awakening - Tutorial quest."""
        quest = Quest(
            "main_1_awakening",
            "The Awakening",
            "You awaken in an unfamiliar land. Explore your surroundings and learn the basics of survival."
        )

        # Objective 1: Move around
        obj1 = QuestObjective(
            "awakening_move",
            "Explore the area (Move with WASD)",
            ObjectiveType.CUSTOM
        )
        obj1.set_target(1)
        obj1.set_completion_func(lambda: True)  # Auto-complete for tutorial

        # Objective 2: Look around
        obj2 = QuestObjective(
            "awakening_look",
            "Look around (Move mouse to look)",
            ObjectiveType.CUSTOM
        )
        obj2.set_target(1)
        obj2.set_completion_func(lambda: True)  # Auto-complete

        # Objective 3: Find the village
        obj3 = QuestObjective(
            "awakening_village",
            "Find the nearby village",
            ObjectiveType.DISCOVER
        )
        obj3.set_target(1)

        quest.add_objective(obj1)
        quest.add_objective(obj2)
        quest.add_objective(obj3)

        quest.reward_text = "50 XP, Basic Supplies"
        quest.reward_func = lambda: self._reward_awakening()
        quest.on_complete = lambda: self._on_awakening_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_first_blood(self) -> Quest:
        """Quest 2: First Blood - Combat introduction."""
        quest = Quest(
            "main_2_first_blood",
            "First Blood",
            "The village guard mentions that hostile creatures have been spotted nearby. Prove your combat skills."
        )

        # Objective 1: Defeat enemies
        obj1 = QuestObjective(
            "first_blood_defeat",
            "Defeat 3 hostile creatures",
            ObjectiveType.DEFEAT
        )
        obj1.set_target(3)

        # Objective 2: Collect loot
        obj2 = QuestObjective(
            "first_blood_loot",
            "Collect materials from defeated enemies",
            ObjectiveType.COLLECT
        )
        obj2.set_target(5)

        quest.add_objective(obj1)
        quest.add_objective(obj2)

        quest.reward_text = "100 XP, Iron Sword, Leather Armor"
        quest.reward_func = lambda: self._reward_first_blood()
        quest.on_complete = lambda: self._on_first_blood_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_village_elder(self) -> Quest:
        """Quest 3: The Village Elder - Story progression."""
        quest = Quest(
            "main_3_village_elder",
            "The Village Elder",
            "Seek out the Wise Elder in the village. He may know about the strange disturbances."
        )

        # Objective 1: Find the elder
        obj1 = QuestObjective(
            "elder_find",
            "Locate the Wise Elder in the village",
            ObjectiveType.DISCOVER
        )
        obj1.set_target(1)

        # Objective 2: Talk to the elder
        obj2 = QuestObjective(
            "elder_talk",
            "Speak with the Wise Elder",
            ObjectiveType.TALK_TO
        )
        obj2.set_target(1)

        quest.add_objective(obj1)
        quest.add_objective(obj2)

        quest.reward_text = "150 XP, Elder's Blessing (+10 Max Health)"
        quest.reward_func = lambda: self._reward_village_elder()
        quest.on_complete = lambda: self._on_village_elder_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_gathering_strength(self) -> Quest:
        """Quest 4: Gathering Strength - Progression and crafting."""
        quest = Quest(
            "main_4_gathering_strength",
            "Gathering Strength",
            "The Elder warns of greater threats ahead. Gather materials and craft better equipment."
        )

        # Objective 1: Collect materials
        obj1 = QuestObjective(
            "gather_materials",
            "Collect 10 wolf pelts and 5 iron ingots",
            ObjectiveType.COLLECT
        )
        obj1.set_target(15)

        # Objective 2: Craft equipment
        obj2 = QuestObjective(
            "craft_equipment",
            "Craft a steel sword or chainmail armor",
            ObjectiveType.CUSTOM
        )
        obj2.set_target(1)

        # Objective 3: Reach level 5
        obj3 = QuestObjective(
            "reach_level_5",
            "Reach character level 5",
            ObjectiveType.CUSTOM
        )
        obj3.set_target(1)
        obj3.set_completion_func(lambda: self.player.progression.level >= 5)

        quest.add_objective(obj1)
        quest.add_objective(obj2)
        quest.add_objective(obj3)

        quest.reward_text = "250 XP, 100 Gold, Crafting Recipe: Steel Blade"
        quest.reward_func = lambda: self._reward_gathering_strength()
        quest.on_complete = lambda: self._on_gathering_strength_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_corrupted_woods(self) -> Quest:
        """Quest 5: The Corrupted Woods - First major challenge."""
        quest = Quest(
            "main_5_corrupted_woods",
            "The Corrupted Woods",
            "The forest to the north has been corrupted by dark energy. Investigate and defeat the Forest Guardian."
        )

        # Objective 1: Travel to corrupted woods
        obj1 = QuestObjective(
            "woods_travel",
            "Journey to the Corrupted Woods (Forest biome)",
            ObjectiveType.DISCOVER
        )
        obj1.set_target(1)

        # Objective 2: Defeat corrupted creatures
        obj2 = QuestObjective(
            "woods_defeat",
            "Defeat 15 corrupted creatures in the woods",
            ObjectiveType.DEFEAT
        )
        obj2.set_target(15)

        # Objective 3: Defeat Forest Guardian boss
        obj3 = QuestObjective(
            "woods_boss",
            "Defeat the Corrupted Forest Guardian",
            ObjectiveType.DEFEAT
        )
        obj3.set_target(1)

        quest.add_objective(obj1)
        quest.add_objective(obj2)
        quest.add_objective(obj3)

        quest.reward_text = "500 XP, Forest Blade (Legendary), Guardian's Heart"
        quest.reward_func = lambda: self._reward_corrupted_woods()
        quest.on_complete = lambda: self._on_corrupted_woods_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_crystal_caves(self) -> Quest:
        """Quest 6: Crystal Caves Expedition - Exploration and resource gathering."""
        quest = Quest(
            "main_6_crystal_caves",
            "Crystal Caves Expedition",
            "The Elder speaks of ancient caves filled with magical crystals. Find them and harness their power."
        )

        # Objective 1: Discover crystal caves
        obj1 = QuestObjective(
            "caves_discover",
            "Discover the Crystal Caves (Tundra/Mountain biome)",
            ObjectiveType.DISCOVER
        )
        obj1.set_target(1)

        # Objective 2: Collect crystal shards
        obj2 = QuestObjective(
            "caves_crystals",
            "Collect 20 crystal shards",
            ObjectiveType.COLLECT
        )
        obj2.set_target(20)

        # Objective 3: Defeat Crystal Golem
        obj3 = QuestObjective(
            "caves_golem",
            "Defeat the Crystal Golem guardian",
            ObjectiveType.DEFEAT
        )
        obj3.set_target(1)

        quest.add_objective(obj1)
        quest.add_objective(obj2)
        quest.add_objective(obj3)

        quest.reward_text = "400 XP, Crystal Plate Armor (Epic), Recipe: Crystal Weapons"
        quest.reward_func = lambda: self._reward_crystal_caves()
        quest.on_complete = lambda: self._on_crystal_caves_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_ancient_shrine(self) -> Quest:
        """Quest 7: The Ancient Shrine - Unlocking fast travel and lore."""
        quest = Quest(
            "main_7_ancient_shrine",
            "The Ancient Shrine",
            "Discover the ancient shrines scattered across the land and unlock their power."
        )

        # Objective 1: Find shrines
        obj1 = QuestObjective(
            "shrine_find",
            "Discover 3 ancient shrines",
            ObjectiveType.DISCOVER
        )
        obj1.set_target(3)

        # Objective 2: Activate shrines
        obj2 = QuestObjective(
            "shrine_activate",
            "Activate all discovered shrines",
            ObjectiveType.INTERACT
        )
        obj2.set_target(3)

        quest.add_objective(obj1)
        quest.add_objective(obj2)

        quest.reward_text = "300 XP, Fast Travel Unlocked, Ancient Amulet (+20 Max Health)"
        quest.reward_func = lambda: self._reward_ancient_shrine()
        quest.on_complete = lambda: self._on_ancient_shrine_complete()

        self.quest_manager.register_quest(quest)
        return quest

    def _create_quest_final_boss(self) -> Quest:
        """Quest 8: Final Confrontation - Campaign finale."""
        quest = Quest(
            "main_8_final_boss",
            "The Final Confrontation",
            "The source of the corruption has been revealed - an ancient entity awakened from its slumber. End this threat once and for all."
        )

        # Objective 1: Prepare for battle
        obj1 = QuestObjective(
            "final_prepare",
            "Reach level 15 and craft legendary equipment",
            ObjectiveType.CUSTOM
        )
        obj1.set_target(1)
        obj1.set_completion_func(lambda: self.player.progression.level >= 15)

        # Objective 2: Journey to the source
        obj2 = QuestObjective(
            "final_journey",
            "Travel to the Corrupted Shrine at the world's center",
            ObjectiveType.DISCOVER
        )
        obj2.set_target(1)

        # Objective 3: Final boss
        obj3 = QuestObjective(
            "final_boss",
            "Defeat the Ancient Corruption",
            ObjectiveType.DEFEAT
        )
        obj3.set_target(1)

        quest.add_objective(obj1)
        quest.add_objective(obj2)
        quest.add_objective(obj3)

        quest.reward_text = "2000 XP, Legendary Equipment Set, World Peace Restored"
        quest.reward_func = lambda: self._reward_final_boss()
        quest.on_complete = lambda: self._on_campaign_complete()

        self.quest_manager.register_quest(quest)
        return quest

    # ===== Reward Functions =====

    def _reward_awakening(self):
        """Reward for completing The Awakening."""
        self.player.gain_xp(50)
        # Add some basic starting materials
        self.player.inventory.add_material("wooden_stick", 5)
        self.player.inventory.add_material("red_herb", 3)
        logger.info("Received starting supplies!")

    def _reward_first_blood(self):
        """Reward for completing First Blood."""
        self.player.gain_xp(100)
        self.player.add_gold(50)
        # Add equipment would require item creation
        logger.info("Received combat rewards!")

    def _reward_village_elder(self):
        """Reward for completing The Village Elder."""
        self.player.gain_xp(150)
        # Elder's blessing: +10 max health
        self.player.stats.max_health += 10
        self.player.stats.current_health = self.player.stats.max_health
        logger.info("Received Elder's Blessing! +10 Max Health")

    def _reward_gathering_strength(self):
        """Reward for completing Gathering Strength."""
        self.player.gain_xp(250)
        self.player.add_gold(100)
        # Unlock steel blade recipe
        from game.crafting import get_crafting_manager
        crafting = get_crafting_manager()
        crafting.discover_recipe("craft_steel_sword")
        logger.info("Learned new crafting recipe: Steel Sword!")

    def _reward_corrupted_woods(self):
        """Reward for completing The Corrupted Woods."""
        self.player.gain_xp(500)
        self.player.add_gold(200)
        self.player.inventory.add_material("guardian_heart", 1)
        logger.info("Forest Guardian defeated! Received Guardian's Heart")

    def _reward_crystal_caves(self):
        """Reward for completing Crystal Caves Expedition."""
        self.player.gain_xp(400)
        self.player.add_gold(300)
        # Unlock crystal weapon recipes
        from game.crafting import get_crafting_manager
        crafting = get_crafting_manager()
        crafting.discover_recipe("craft_crystal_blade")
        logger.info("Learned new crafting recipe: Crystal Blade!")

    def _reward_ancient_shrine(self):
        """Reward for completing The Ancient Shrine."""
        self.player.gain_xp(300)
        # Ancient amulet: +20 max health
        self.player.stats.max_health += 20
        self.player.stats.current_health = self.player.stats.max_health
        logger.info("Received Ancient Amulet! +20 Max Health")

    def _reward_final_boss(self):
        """Reward for completing the campaign."""
        self.player.gain_xp(2000)
        self.player.add_gold(1000)
        logger.info("CAMPAIGN COMPLETE! You have restored peace to the land!")

    # ===== Completion Callbacks =====

    def _on_awakening_complete(self):
        """Called when The Awakening completes."""
        logger.info("Quest Complete: The Awakening")
        # Auto-start next quest
        self.quest_manager.start_quest("main_2_first_blood")

    def _on_first_blood_complete(self):
        """Called when First Blood completes."""
        logger.info("Quest Complete: First Blood")
        # Auto-start next quest
        self.quest_manager.start_quest("main_3_village_elder")

    def _on_village_elder_complete(self):
        """Called when The Village Elder completes."""
        logger.info("Quest Complete: The Village Elder")
        logger.info("The Elder tells you of ancient guardians corrupted by darkness...")
        # Auto-start next quest
        self.quest_manager.start_quest("main_4_gathering_strength")

    def _on_gathering_strength_complete(self):
        """Called when Gathering Strength completes."""
        logger.info("Quest Complete: Gathering Strength")
        logger.info("You are ready to face greater challenges!")
        # Auto-start next quest
        self.quest_manager.start_quest("main_5_corrupted_woods")

    def _on_corrupted_woods_complete(self):
        """Called when The Corrupted Woods completes."""
        logger.info("Quest Complete: The Corrupted Woods")
        logger.info("The forest begins to heal, but more corruption remains...")
        # Make both cave and shrine quests available
        self.quest_manager.start_quest("main_6_crystal_caves")
        self.quest_manager.start_quest("main_7_ancient_shrine")

    def _on_crystal_caves_complete(self):
        """Called when Crystal Caves Expedition completes."""
        logger.info("Quest Complete: Crystal Caves Expedition")
        logger.info("You have harnessed the power of ancient crystals!")
        self._check_final_quest_unlock()

    def _on_ancient_shrine_complete(self):
        """Called when The Ancient Shrine completes."""
        logger.info("Quest Complete: The Ancient Shrine")
        logger.info("The shrines reveal the location of the corruption's source...")
        self._check_final_quest_unlock()

    def _check_final_quest_unlock(self):
        """Check if both prerequisite quests are done to unlock final quest."""
        if (self.quest_manager.is_quest_completed("main_6_crystal_caves") and
            self.quest_manager.is_quest_completed("main_7_ancient_shrine")):
            logger.info("You are ready for the final confrontation!")
            self.quest_manager.start_quest("main_8_final_boss")

    def _on_campaign_complete(self):
        """Called when the entire campaign completes."""
        logger.info("=" * 60)
        logger.info("CONGRATULATIONS!")
        logger.info("You have completed the main campaign!")
        logger.info("The Awakening of the Ancient Guardians")
        logger.info("=" * 60)
        logger.info("Continue exploring to find hidden secrets and challenges!")

    # ===== Campaign Management =====

    def start_campaign(self):
        """Start the main campaign."""
        logger.info("Starting Main Campaign: The Awakening of the Ancient Guardians")
        self.quest_manager.start_quest("main_1_awakening")

    def get_campaign_progress(self) -> dict:
        """
        Get campaign progress statistics.

        Returns:
            dict: Progress information
        """
        total_quests = len(self.campaign_quests)
        completed_count = sum(
            1 for qid in self.campaign_quests
            if self.quest_manager.is_quest_completed(qid)
        )
        active_count = sum(
            1 for qid in self.campaign_quests
            if self.quest_manager.is_quest_active(qid)
        )

        return {
            "total_quests": total_quests,
            "completed": completed_count,
            "active": active_count,
            "progress_percent": (completed_count / total_quests) * 100,
            "is_complete": completed_count == total_quests
        }

    def is_campaign_complete(self) -> bool:
        """Check if the entire campaign is complete."""
        return all(
            self.quest_manager.is_quest_completed(qid)
            for qid in self.campaign_quests
        )
