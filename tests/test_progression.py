"""Unit tests for character progression and leveling system."""
import unittest
from game.progression import (
    CharacterProgression,
    LEVEL_XP_THRESHOLDS,
    MAX_LEVEL,
    STATS_PER_LEVEL,
    XP_REWARDS,
    calculate_enemy_xp
)


class TestCharacterProgression(unittest.TestCase):
    """Test CharacterProgression class."""

    def test_initialization_default(self):
        """Test default initialization starts at level 1."""
        progression = CharacterProgression()

        self.assertEqual(progression.level, 1)
        self.assertEqual(progression.xp, 0)
        self.assertEqual(progression.total_xp, 0)

    def test_initialization_custom_level(self):
        """Test initialization with custom starting level."""
        progression = CharacterProgression(starting_level=5)

        self.assertEqual(progression.level, 5)
        self.assertEqual(progression.xp, LEVEL_XP_THRESHOLDS[4])  # Level 5 threshold

    def test_initialization_level_bounds(self):
        """Test level initialization is bounded."""
        # Too low
        progression_low = CharacterProgression(starting_level=0)
        self.assertEqual(progression_low.level, 1)

        # Too high
        progression_high = CharacterProgression(starting_level=999)
        self.assertEqual(progression_high.level, MAX_LEVEL)

    def test_xp_to_next_level(self):
        """Test XP required to next level calculation."""
        progression = CharacterProgression()

        # At level 1, need 100 XP to reach level 2
        self.assertEqual(progression.xp_to_next_level, 100)

        # Add 50 XP
        progression.add_xp(50)
        self.assertEqual(progression.xp_to_next_level, 50)

    def test_xp_to_next_level_max_level(self):
        """Test XP to next level returns 0 at max level."""
        progression = CharacterProgression(starting_level=MAX_LEVEL)
        self.assertEqual(progression.xp_to_next_level, 0)

    def test_xp_progress(self):
        """Test XP progress percentage calculation."""
        progression = CharacterProgression()

        # At 0 XP
        self.assertEqual(progression.xp_progress, 0.0)

        # At 50 XP (halfway to level 2 which needs 100)
        progression.add_xp(50)
        self.assertEqual(progression.xp_progress, 0.5)

        # At 75 XP (75% to level 2)
        progression.add_xp(25)
        self.assertEqual(progression.xp_progress, 0.75)

    def test_xp_progress_max_level(self):
        """Test XP progress returns 1.0 at max level."""
        progression = CharacterProgression(starting_level=MAX_LEVEL)
        self.assertEqual(progression.xp_progress, 1.0)

    def test_add_xp_no_level_up(self):
        """Test adding XP without leveling up."""
        progression = CharacterProgression()

        levels_gained = progression.add_xp(50)

        self.assertEqual(levels_gained, [])
        self.assertEqual(progression.level, 1)
        self.assertEqual(progression.xp, 50)
        self.assertEqual(progression.total_xp, 50)

    def test_add_xp_single_level_up(self):
        """Test single level up."""
        progression = CharacterProgression()

        levels_gained = progression.add_xp(100)

        self.assertEqual(levels_gained, [2])
        self.assertEqual(progression.level, 2)
        self.assertEqual(progression.xp, 100)
        self.assertEqual(progression.total_xp, 100)

    def test_add_xp_multiple_level_ups(self):
        """Test multiple level ups from single XP gain."""
        progression = CharacterProgression()

        # Add enough XP to reach level 5 (700 XP threshold)
        levels_gained = progression.add_xp(750)

        self.assertEqual(levels_gained, [2, 3, 4, 5])
        self.assertEqual(progression.level, 5)
        self.assertEqual(progression.xp, 750)

    def test_add_xp_zero(self):
        """Test adding zero XP does nothing."""
        progression = CharacterProgression()

        levels_gained = progression.add_xp(0)

        self.assertEqual(levels_gained, [])
        self.assertEqual(progression.level, 1)
        self.assertEqual(progression.xp, 0)

    def test_add_xp_negative(self):
        """Test adding negative XP does nothing."""
        progression = CharacterProgression()
        progression.add_xp(50)

        levels_gained = progression.add_xp(-25)

        self.assertEqual(levels_gained, [])
        self.assertEqual(progression.xp, 50)  # Unchanged

    def test_add_xp_at_max_level(self):
        """Test adding XP at max level does nothing."""
        progression = CharacterProgression(starting_level=MAX_LEVEL)
        old_xp = progression.xp

        levels_gained = progression.add_xp(1000)

        self.assertEqual(levels_gained, [])
        self.assertEqual(progression.level, MAX_LEVEL)
        self.assertEqual(progression.xp, old_xp)  # Unchanged

    def test_get_stat_bonus(self):
        """Test stat bonus calculation."""
        progression = CharacterProgression()

        # At level 1, all bonuses should be 0
        self.assertEqual(progression.get_stat_bonus("max_health"), 0)
        self.assertEqual(progression.get_stat_bonus("max_stamina"), 0)
        self.assertEqual(progression.get_stat_bonus("base_damage"), 0)

        # Level up to 5 (4 levels gained)
        progression.set_level(5)

        # Check bonuses (4 levels * stat_per_level)
        self.assertEqual(progression.get_stat_bonus("max_health"),
                        STATS_PER_LEVEL["max_health"] * 4)
        self.assertEqual(progression.get_stat_bonus("max_stamina"),
                        STATS_PER_LEVEL["max_stamina"] * 4)
        self.assertEqual(progression.get_stat_bonus("base_damage"),
                        STATS_PER_LEVEL["base_damage"] * 4)

    def test_get_stat_bonus_invalid_stat(self):
        """Test getting bonus for non-existent stat returns 0."""
        progression = CharacterProgression(starting_level=10)

        bonus = progression.get_stat_bonus("invalid_stat")

        self.assertEqual(bonus, 0)

    def test_get_all_stat_bonuses(self):
        """Test getting all stat bonuses at once."""
        progression = CharacterProgression(starting_level=3)

        bonuses = progression.get_all_stat_bonuses()

        self.assertIsInstance(bonuses, dict)
        self.assertIn("max_health", bonuses)
        self.assertIn("max_stamina", bonuses)
        self.assertIn("base_damage", bonuses)
        self.assertIn("defense", bonuses)

        # Level 3 = 2 levels gained
        self.assertEqual(bonuses["max_health"], STATS_PER_LEVEL["max_health"] * 2)

    def test_set_level(self):
        """Test manually setting level."""
        progression = CharacterProgression()

        progression.set_level(10)

        self.assertEqual(progression.level, 10)
        self.assertEqual(progression.xp, LEVEL_XP_THRESHOLDS[9])

    def test_set_level_bounds(self):
        """Test set_level respects bounds."""
        progression = CharacterProgression()

        # Too low
        progression.set_level(0)
        self.assertEqual(progression.level, 1)

        # Too high
        progression.set_level(999)
        self.assertEqual(progression.level, MAX_LEVEL)

    def test_get_level_info(self):
        """Test getting comprehensive level info."""
        progression = CharacterProgression(starting_level=5)
        progression.add_xp(50)

        info = progression.get_level_info()

        self.assertEqual(info["level"], 5)
        self.assertIn("xp", info)
        self.assertIn("total_xp", info)
        self.assertIn("xp_to_next", info)
        self.assertIn("xp_progress", info)
        self.assertIn("is_max_level", info)
        self.assertIn("stat_bonuses", info)
        self.assertIsInstance(info["stat_bonuses"], dict)

    def test_xp_gain_callback(self):
        """Test XP gain callback is triggered."""
        progression = CharacterProgression()

        callback_called = []
        def on_xp(amount, total):
            callback_called.append((amount, total))

        progression.on_xp_gain = on_xp
        progression.add_xp(50)

        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0], (50, 50))

    def test_level_up_callback(self):
        """Test level up callback is triggered."""
        progression = CharacterProgression()

        levels_called = []
        def on_level_up(level):
            levels_called.append(level)

        progression.on_level_up = on_level_up
        progression.add_xp(100)  # Level up to 2

        self.assertEqual(levels_called, [2])

    def test_level_up_callback_multiple_levels(self):
        """Test level up callback triggered for each level."""
        progression = CharacterProgression()

        levels_called = []
        progression.on_level_up = lambda level: levels_called.append(level)

        progression.add_xp(500)  # Multiple level ups

        # 500 XP reaches level 4 (threshold at 450), not level 5 (threshold at 700)
        self.assertEqual(len(levels_called), 3)  # Levels 2, 3, 4

    def test_total_xp_tracking(self):
        """Test total XP is correctly tracked."""
        progression = CharacterProgression()

        progression.add_xp(50)
        progression.add_xp(75)
        progression.add_xp(100)

        self.assertEqual(progression.total_xp, 225)


class TestXPRewards(unittest.TestCase):
    """Test XP reward calculations."""

    def test_calculate_enemy_xp_weak(self):
        """Test XP calculation for weak enemies."""
        xp = calculate_enemy_xp("WEAK")
        self.assertEqual(xp, XP_REWARDS["WEAK"])

    def test_calculate_enemy_xp_normal(self):
        """Test XP calculation for normal enemies."""
        xp = calculate_enemy_xp("NORMAL")
        self.assertEqual(xp, XP_REWARDS["NORMAL"])

    def test_calculate_enemy_xp_tank(self):
        """Test XP calculation for tank enemies."""
        xp = calculate_enemy_xp("TANK")
        self.assertEqual(xp, XP_REWARDS["TANK"])

    def test_calculate_enemy_xp_fast(self):
        """Test XP calculation for fast enemies."""
        xp = calculate_enemy_xp("FAST")
        self.assertEqual(xp, XP_REWARDS["FAST"])

    def test_calculate_enemy_xp_unknown_type(self):
        """Test unknown enemy type returns default XP."""
        xp = calculate_enemy_xp("UNKNOWN_TYPE")
        self.assertEqual(xp, 50)  # Default value

    def test_calculate_enemy_xp_with_level(self):
        """Test XP calculation with enemy level (currently unused but future-proof)."""
        xp = calculate_enemy_xp("NORMAL", enemy_level=5)
        # Currently doesn't affect XP, but should not error
        self.assertEqual(xp, XP_REWARDS["NORMAL"])


class TestLevelThresholds(unittest.TestCase):
    """Test level threshold configuration."""

    def test_level_thresholds_start_at_zero(self):
        """Test first level threshold is 0."""
        self.assertEqual(LEVEL_XP_THRESHOLDS[0], 0)

    def test_level_thresholds_increasing(self):
        """Test thresholds are strictly increasing."""
        for i in range(1, len(LEVEL_XP_THRESHOLDS)):
            self.assertGreater(LEVEL_XP_THRESHOLDS[i], LEVEL_XP_THRESHOLDS[i-1])

    def test_max_level_matches_thresholds(self):
        """Test MAX_LEVEL matches threshold array length."""
        self.assertEqual(MAX_LEVEL, len(LEVEL_XP_THRESHOLDS))

    def test_stats_per_level_all_positive(self):
        """Test all stat bonuses are positive."""
        for stat, value in STATS_PER_LEVEL.items():
            self.assertGreater(value, 0, f"{stat} should have positive bonus")

    def test_xp_rewards_all_positive(self):
        """Test all XP rewards are positive."""
        for enemy_type, xp in XP_REWARDS.items():
            self.assertGreater(xp, 0, f"{enemy_type} should have positive XP reward")


class TestProgressionIntegration(unittest.TestCase):
    """Test progression system integration scenarios."""

    def test_level_1_to_max_level(self):
        """Test leveling from 1 to max level."""
        progression = CharacterProgression()

        # Add enough XP to reach max level
        max_xp = LEVEL_XP_THRESHOLDS[-1] + 1000
        progression.add_xp(max_xp)

        self.assertEqual(progression.level, MAX_LEVEL)
        self.assertTrue(progression.get_level_info()["is_max_level"])

    def test_gradual_progression(self):
        """Test gradual progression through levels."""
        progression = CharacterProgression()

        # Gradually add XP
        for _ in range(50):
            old_level = progression.level
            progression.add_xp(50)

            # Level should never decrease
            self.assertGreaterEqual(progression.level, old_level)

    def test_stat_scaling(self):
        """Test stat bonuses scale correctly with level."""
        low_level = CharacterProgression(starting_level=5)
        high_level = CharacterProgression(starting_level=20)

        low_health = low_level.get_stat_bonus("max_health")
        high_health = high_level.get_stat_bonus("max_health")

        # Higher level should have more bonus
        self.assertGreater(high_health, low_health)

        # Difference should be proportional to level difference
        level_diff = high_level.level - low_level.level
        health_diff = high_health - low_health
        expected_diff = STATS_PER_LEVEL["max_health"] * level_diff
        self.assertEqual(health_diff, expected_diff)

    def test_xp_required_increases_with_level(self):
        """Test XP required to level up increases."""
        progression = CharacterProgression()

        xp_required_at_1 = progression.xp_to_next_level

        # Level up a few times
        progression.add_xp(1000)

        # XP to next level should be higher now
        xp_required_later = progression.xp_to_next_level
        if progression.level < MAX_LEVEL:
            self.assertGreater(xp_required_later, xp_required_at_1)


if __name__ == '__main__':
    unittest.main()
