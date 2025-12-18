"""Character progression and leveling system."""
from typing import Callable, Optional


# XP thresholds for each level (cumulative)
LEVEL_XP_THRESHOLDS = [
    0,      # Level 1
    100,    # Level 2
    250,    # Level 3
    450,    # Level 4
    700,    # Level 5
    1000,   # Level 6
    1350,   # Level 7
    1750,   # Level 8
    2200,   # Level 9
    2700,   # Level 10
    3250,   # Level 11
    3850,   # Level 12
    4500,   # Level 13
    5200,   # Level 14
    5950,   # Level 15
    6750,   # Level 16
    7600,   # Level 17
    8500,   # Level 18
    9450,   # Level 19
    10450,  # Level 20
    11500,  # Level 21
    12600,  # Level 22
    13750,  # Level 23
    14950,  # Level 24
    16200,  # Level 25
    17500,  # Level 26
    18850,  # Level 27
    20250,  # Level 28
    21700,  # Level 29
    23200,  # Level 30 (max)
]

MAX_LEVEL = len(LEVEL_XP_THRESHOLDS)

# Stat increases per level
STATS_PER_LEVEL = {
    "max_health": 10,
    "max_stamina": 5,
    "base_damage": 2,
    "defense": 1,
}


class CharacterProgression:
    """Manages character level and XP progression."""

    def __init__(self, starting_level: int = 1):
        """
        Initialize character progression.

        Args:
            starting_level: Starting level (default 1)
        """
        self.level = max(1, min(starting_level, MAX_LEVEL))
        self.xp = LEVEL_XP_THRESHOLDS[self.level - 1]
        self.total_xp = self.xp

        # Callbacks for level-up events
        self.on_level_up: Optional[Callable[[int], None]] = None
        self.on_xp_gain: Optional[Callable[[int, int], None]] = None  # (xp_gained, new_total)

    @property
    def xp_to_next_level(self) -> int:
        """Get XP needed to reach next level."""
        if self.level >= MAX_LEVEL:
            return 0
        return LEVEL_XP_THRESHOLDS[self.level] - self.xp

    @property
    def xp_progress(self) -> float:
        """Get progress to next level as a percentage (0.0 to 1.0)."""
        if self.level >= MAX_LEVEL:
            return 1.0

        current_level_xp = LEVEL_XP_THRESHOLDS[self.level - 1]
        next_level_xp = LEVEL_XP_THRESHOLDS[self.level]
        level_range = next_level_xp - current_level_xp

        if level_range <= 0:
            return 1.0

        progress = (self.xp - current_level_xp) / level_range
        return max(0.0, min(1.0, progress))

    def add_xp(self, amount: int) -> list:
        """
        Add XP and check for level ups.

        Args:
            amount: Amount of XP to add

        Returns:
            List of levels gained (empty if no level up)
        """
        if amount <= 0 or self.level >= MAX_LEVEL:
            return []

        old_xp = self.xp
        self.xp += amount
        self.total_xp += amount

        # Trigger XP gain callback
        if self.on_xp_gain:
            self.on_xp_gain(amount, self.xp)

        # Check for level ups
        levels_gained = []
        while self.level < MAX_LEVEL and self.xp >= LEVEL_XP_THRESHOLDS[self.level]:
            self.level += 1
            levels_gained.append(self.level)

            # Trigger level up callback
            if self.on_level_up:
                self.on_level_up(self.level)

        return levels_gained

    def get_stat_bonus(self, stat_name: str) -> int:
        """
        Get total stat bonus from levels.

        Args:
            stat_name: Name of stat (e.g., 'max_health')

        Returns:
            Total bonus for that stat
        """
        if stat_name not in STATS_PER_LEVEL:
            return 0

        # Bonus is per_level * (level - 1) since level 1 is base
        return STATS_PER_LEVEL[stat_name] * (self.level - 1)

    def get_all_stat_bonuses(self) -> dict:
        """Get all stat bonuses from levels."""
        return {
            stat: self.get_stat_bonus(stat)
            for stat in STATS_PER_LEVEL.keys()
        }

    def set_level(self, level: int) -> None:
        """
        Set character level directly (for debugging/testing).

        Args:
            level: Level to set (1 to MAX_LEVEL)
        """
        self.level = max(1, min(level, MAX_LEVEL))
        self.xp = LEVEL_XP_THRESHOLDS[self.level - 1]

    def get_level_info(self) -> dict:
        """Get detailed level information."""
        return {
            "level": self.level,
            "xp": self.xp,
            "total_xp": self.total_xp,
            "xp_to_next": self.xp_to_next_level,
            "xp_progress": self.xp_progress,
            "is_max_level": self.level >= MAX_LEVEL,
            "stat_bonuses": self.get_all_stat_bonuses()
        }


# XP rewards for killing enemies (by enemy type)
XP_REWARDS = {
    "WEAK": 25,
    "NORMAL": 50,
    "TANK": 75,
    "FAST": 60,
    # Boss rewards
    "BOSS_CORRUPTED_GUARDIAN": 500,
    "BOSS_CRYSTAL_TYRANT": 600,
    "BOSS_ANCIENT_WARDEN": 700,
    "BOSS_VOID_KNIGHT": 800,
    "BOSS_SKY_SERPENT": 650,
}


def calculate_enemy_xp(enemy_type: str, enemy_level: int = 1) -> int:
    """
    Calculate XP reward for defeating an enemy.

    Args:
        enemy_type: Enemy type (WEAK, NORMAL, TANK, FAST, or boss type)
        enemy_level: Enemy level (currently unused, for future scaling)

    Returns:
        XP amount
    """
    base_xp = XP_REWARDS.get(enemy_type, 50)
    # Bosses give massive XP rewards
    if enemy_type.startswith("BOSS_"):
        base_xp = XP_REWARDS.get(enemy_type, 500)
    # Could add level scaling here in the future
    return base_xp
