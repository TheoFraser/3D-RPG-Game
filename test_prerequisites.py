"""Test script for quest prerequisite system."""
from game.quests import Quest, QuestManager, QuestObjective, ObjectiveType
from game.player import Player
import glm


def test_quest_prerequisites():
    """Test that quest prerequisites are properly enforced."""
    print("\n=== Testing Quest Prerequisites ===\n")

    # Create quest manager and player
    quest_manager = QuestManager()
    player = Player(position=glm.vec3(0, 0, 0))

    # Create quest chain with prerequisites
    # Quest 1: No prerequisites
    quest1 = Quest("test_quest_1", "First Quest", "The beginning")
    obj1 = QuestObjective("obj1", "Do something", ObjectiveType.CUSTOM)
    quest1.add_objective(obj1)
    quest1.reward_func = lambda: print("Quest 1 completed!")
    quest_manager.register_quest(quest1)

    # Quest 2: Requires Quest 1
    quest2 = Quest("test_quest_2", "Second Quest", "The continuation")
    quest2.prerequisites = ["test_quest_1"]
    obj2 = QuestObjective("obj2", "Do another thing", ObjectiveType.CUSTOM)
    quest2.add_objective(obj2)
    quest2.reward_func = lambda: print("Quest 2 completed!")
    quest_manager.register_quest(quest2)

    # Quest 3: Requires Quest 2
    quest3 = Quest("test_quest_3", "Third Quest", "The finale")
    quest3.prerequisites = ["test_quest_2"]
    obj3 = QuestObjective("obj3", "Do final thing", ObjectiveType.CUSTOM)
    quest3.add_objective(obj3)
    quest3.reward_func = lambda: print("Quest 3 completed!")
    quest_manager.register_quest(quest3)

    # Test 1: Try to start Quest 2 without completing Quest 1 (should fail)
    print("Test 1: Try to start Quest 2 before Quest 1")
    result = quest_manager.start_quest("test_quest_2")
    if not result:
        print("[PASS] Quest 2 correctly blocked (Quest 1 not completed)\n")
    else:
        print("[FAIL] Quest 2 should not start without prerequisite\n")
        return False

    # Test 2: Check prerequisites
    print("Test 2: Check Quest 2 prerequisites")
    missing = quest_manager.get_missing_prerequisites("test_quest_2")
    if missing == ["test_quest_1"]:
        print(f"[PASS] Missing prerequisites correctly identified: {missing}\n")
    else:
        print(f"[FAIL] Expected ['test_quest_1'], got {missing}\n")
        return False

    # Test 3: Start Quest 1 (should succeed)
    print("Test 3: Start Quest 1 (no prerequisites)")
    result = quest_manager.start_quest("test_quest_1")
    if result and quest_manager.is_quest_active("test_quest_1"):
        print("[PASS] Quest 1 started successfully\n")
    else:
        print("[FAIL] Quest 1 should start\n")
        return False

    # Test 4: Try to start Quest 2 while Quest 1 is active (should still fail)
    print("Test 4: Try to start Quest 2 while Quest 1 is active")
    result = quest_manager.start_quest("test_quest_2")
    if not result:
        print("[PASS] Quest 2 correctly blocked (Quest 1 not completed, only active)\n")
    else:
        print("[FAIL] Quest 2 should wait for Quest 1 completion\n")
        return False

    # Test 5: Complete Quest 1
    print("Test 5: Complete Quest 1")
    quest_manager.progress_objective("test_quest_1", "obj1", 1)
    if quest_manager.is_quest_completed("test_quest_1"):
        print("[PASS] Quest 1 completed\n")
    else:
        print("[FAIL] Quest 1 should be completed\n")
        return False

    # Test 6: Check if Quest 2 is now available
    print("Test 6: Check if Quest 2 is now available")
    available = quest_manager.is_quest_available("test_quest_2")
    if available:
        print("[PASS] Quest 2 is now available\n")
    else:
        print("[FAIL] Quest 2 should be available\n")
        return False

    # Test 7: Start Quest 2 (should succeed now)
    print("Test 7: Start Quest 2 after Quest 1 completion")
    result = quest_manager.start_quest("test_quest_2")
    if result and quest_manager.is_quest_active("test_quest_2"):
        print("[PASS] Quest 2 started successfully\n")
    else:
        print("[FAIL] Quest 2 should start now\n")
        return False

    # Test 8: Complete Quest 2 and start Quest 3
    print("Test 8: Complete Quest 2 and verify Quest 3 becomes available")
    quest_manager.progress_objective("test_quest_2", "obj2", 1)
    if quest_manager.is_quest_completed("test_quest_2"):
        print("[PASS] Quest 2 completed\n")
    else:
        print("[FAIL] Quest 2 should be completed\n")
        return False

    # Test 9: Start Quest 3
    print("Test 9: Start Quest 3 after Quest 2 completion")
    result = quest_manager.start_quest("test_quest_3")
    if result and quest_manager.is_quest_active("test_quest_3"):
        print("[PASS] Quest 3 started successfully\n")
    else:
        print("[FAIL] Quest 3 should start now\n")
        return False

    # Test 10: Check available quests
    print("Test 10: Check get_available_quests()")
    quest4 = Quest("test_quest_4", "Fourth Quest", "No prereqs")
    obj4 = QuestObjective("obj4", "Something", ObjectiveType.CUSTOM)
    quest4.add_objective(obj4)
    quest_manager.register_quest(quest4)

    available_quests = quest_manager.get_available_quests()
    available_ids = [q.quest_id for q in available_quests]
    if "test_quest_4" in available_ids and len(available_ids) == 1:
        print(f"[PASS] get_available_quests() returns correct quests: {available_ids}\n")
    else:
        print(f"[FAIL] Expected ['test_quest_4'], got {available_ids}\n")
        return False

    print("=== All Tests Passed! ===\n")
    return True


if __name__ == "__main__":
    success = test_quest_prerequisites()
    exit(0 if success else 1)
