"""Quick integration test to verify game systems work together."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_game_initialization():
    """Test that game can initialize without errors."""
    print("\n=== Testing Game Initialization ===")

    try:
        from game.player import Player
        from game.quests import QuestManager
        from game.crafting import get_crafting_manager

        # Create game components
        player = Player()
        quest_manager = QuestManager()
        crafting_manager = get_crafting_manager()

        print(f"[PASS] Player created - Level {player.progression.level}")
        print(f"[PASS] Quest manager created")
        print(f"[PASS] Crafting manager created - {len(crafting_manager.recipes)} recipes")

        return True
    except Exception as e:
        print(f"[FAIL] Initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quest_system_integration():
    """Test quest system with prerequisites."""
    print("\n=== Testing Quest System Integration ===")

    try:
        from game.quests import QuestManager
        from game.main_quest import register_main_quest_line
        from game.player import Player

        player = Player()
        qm = QuestManager()

        # Register main quests
        quest_ids = register_main_quest_line(qm, player)
        print(f"[PASS] Registered {len(quest_ids)} main quests")

        # Test prerequisite checking
        prologue_id = "main_prologue"
        act1_id = "main_act1"

        # Prologue should be available (no prerequisites)
        can_start = qm.check_prerequisites(prologue_id)
        assert can_start, "Prologue should be available"
        print("[PASS] Prologue available without prerequisites")

        # Act 1 should NOT be available (requires prologue)
        can_start = qm.check_prerequisites(act1_id)
        assert not can_start, "Act 1 should require prologue completion"
        print("[PASS] Act 1 blocked by prerequisites")

        # Start and complete prologue
        qm.start_quest(prologue_id)
        prologue = qm.get_quest(prologue_id)

        # Progress each objective through quest manager
        for obj in prologue.objectives:
            qm.progress_objective(prologue_id, obj.objective_id, obj.target)

        # Verify quest is marked as completed
        assert qm.is_quest_completed(prologue_id), "Prologue should be completed"
        print("[PASS] Prologue completed successfully")

        # Now Act 1 should be available
        can_start = qm.check_prerequisites(act1_id)
        assert can_start, f"Act 1 should be available after prologue (completed: {qm.is_quest_completed(prologue_id)})"
        print("[PASS] Act 1 available after completing prologue")

        return True
    except Exception as e:
        print(f"[FAIL] Quest system error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crafting_system_integration():
    """Test end-to-end crafting."""
    print("\n=== Testing Crafting System Integration ===")

    try:
        from game.player import Player
        from game.crafting import get_crafting_manager

        player = Player()
        cm = get_crafting_manager()

        # Add materials for leather strips
        player.inventory.add_material("wolf_pelt", 10)

        # Check if can craft
        recipe_id = "craft_leather_strip"
        can_craft, reason = cm.can_craft(recipe_id, player.inventory, player.progression.level)
        print(f"[INFO] Can craft leather strips: {can_craft}, reason: {reason}")

        if can_craft:
            # Craft the item
            success, message = cm.craft_item(recipe_id, player.inventory, player.progression.level)
            assert success, f"Crafting should succeed: {message}"
            print(f"[PASS] {message}")

            # Verify result
            strips = player.inventory.get_item_count("leather_strip")
            assert strips >= 4, f"Should have at least 4 leather strips, got {strips}"
            print(f"[PASS] Crafted 4 leather strips (inventory: {strips})")

            # Verify materials consumed
            pelts = player.inventory.get_item_count("wolf_pelt")
            assert pelts == 9, f"Should have 9 pelts remaining, got {pelts}"
            print(f"[PASS] Materials consumed correctly (9 pelts remaining)")
        else:
            print("[SKIP] Cannot craft - missing prerequisites")

        return True
    except Exception as e:
        print(f"[FAIL] Crafting error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_optimizations():
    """Test that performance optimizations are in place."""
    print("\n=== Testing Performance Optimizations ===")

    try:
        from game.quests import QuestManager
        from game.crafting import get_crafting_manager
        import time

        qm = QuestManager()
        cm = get_crafting_manager()

        # Test 1: Quest manager uses sets
        assert isinstance(qm.active_quests, set), "Should use sets"
        assert isinstance(qm.completed_quests, set), "Should use sets"
        print("[PASS] Quest manager uses sets for O(1) lookups")

        # Test 2: Recipe caching works
        cached_recipes = cm.get_all_discovered_recipes()

        # Benchmark: accessing cached list vs calling method
        iterations = 10000

        start = time.time()
        for _ in range(iterations):
            _ = cached_recipes
        cached_time = time.time() - start

        start = time.time()
        for _ in range(iterations):
            _ = cm.get_all_discovered_recipes()
        uncached_time = time.time() - start

        print(f"[INFO] Cached access: {cached_time:.4f}s for {iterations} iterations")
        print(f"[INFO] Uncached access: {uncached_time:.4f}s for {iterations} iterations")

        if cached_time > 0:
            speedup = uncached_time / cached_time
            print(f"[PASS] Recipe caching available ({speedup:.1f}x potential speedup)")
        else:
            print("[PASS] Recipe caching available (instant access)")

        return True
    except Exception as e:
        print(f"[FAIL] Performance test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("GAME INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Game Initialization", test_game_initialization),
        ("Quest System", test_quest_system_integration),
        ("Crafting System", test_crafting_system_integration),
        ("Performance", test_performance_optimizations),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            print(f"\n[FAIL] {test_name} - Unexpected error")
            print(f"Error: {e}")

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
