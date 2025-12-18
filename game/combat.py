"""Combat mechanics and damage calculation."""
import glm
import random
from typing import Optional, Tuple
from enum import Enum, auto
import config
from game.stats import CharacterStats


class AttackType(Enum):
    """Types of attacks."""
    LIGHT = auto()
    HEAVY = auto()
    RANGED = auto()


class CombatResult:
    """Result of a combat action."""

    def __init__(
        self,
        hit: bool,
        damage: float = 0.0,
        critical: bool = False,
        blocked: bool = False,
        dodged: bool = False
    ):
        """
        Initialize combat result.

        Args:
            hit: Whether the attack hit
            damage: Damage dealt
            critical: Whether it was a critical hit
            blocked: Whether it was blocked
            dodged: Whether it was dodged
        """
        self.hit = hit
        self.damage = damage
        self.critical = critical
        self.blocked = blocked
        self.dodged = dodged


class CombatSystem:
    """Handles combat calculations and mechanics."""

    @staticmethod
    def calculate_damage(
        attacker_stats: CharacterStats,
        defender_stats: CharacterStats,
        attack_type: AttackType = AttackType.LIGHT
    ) -> Tuple[float, bool]:
        """
        Calculate damage from an attack.

        Args:
            attacker_stats: Attacker's stats
            defender_stats: Defender's stats
            attack_type: Type of attack

        Returns:
            Tuple of (damage, is_critical)
        """
        base_damage = attacker_stats.base_damage

        # Modify based on attack type
        if attack_type == AttackType.HEAVY:
            base_damage *= 1.5
        elif attack_type == AttackType.RANGED:
            base_damage *= 0.8

        # Check for critical hit
        is_critical = random.random() < config.CRIT_CHANCE
        if is_critical:
            base_damage *= config.CRIT_MULTIPLIER

        return base_damage, is_critical

    @staticmethod
    def execute_attack(
        attacker_stats: CharacterStats,
        defender_stats: CharacterStats,
        attack_type: AttackType = AttackType.LIGHT,
        defender_is_blocking: bool = False
    ) -> CombatResult:
        """
        Execute an attack from attacker to defender.

        Args:
            attacker_stats: Attacker's stats
            defender_stats: Defender's stats
            attack_type: Type of attack
            defender_is_blocking: Whether defender is blocking

        Returns:
            CombatResult with attack outcome
        """
        # Calculate damage
        damage, is_critical = CombatSystem.calculate_damage(
            attacker_stats,
            defender_stats,
            attack_type
        )

        # Check if blocked
        if defender_is_blocking:
            damage *= 0.3  # Reduce damage by 70% when blocking
            result = CombatResult(
                hit=True,
                damage=defender_stats.take_damage(damage),
                critical=False,  # No crits on blocked attacks
                blocked=True
            )
            return result

        # Apply damage
        actual_damage = defender_stats.take_damage(damage)

        return CombatResult(
            hit=True,
            damage=actual_damage,
            critical=is_critical,
            blocked=False,
            dodged=False
        )

    @staticmethod
    def is_in_range(
        attacker_pos: glm.vec3,
        target_pos: glm.vec3,
        attack_range: float
    ) -> bool:
        """
        Check if target is in attack range.

        Args:
            attacker_pos: Attacker position
            target_pos: Target position
            attack_range: Maximum attack range

        Returns:
            True if in range
        """
        distance = glm.length(target_pos - attacker_pos)
        return distance <= attack_range

    @staticmethod
    def knockback(
        attacker_pos: glm.vec3,
        target_pos: glm.vec3,
        force: float = 5.0
    ) -> glm.vec3:
        """
        Calculate knockback vector.

        Args:
            attacker_pos: Attacker position
            target_pos: Target position
            force: Knockback force

        Returns:
            Knockback velocity vector
        """
        direction = glm.normalize(target_pos - attacker_pos)
        return direction * force


class CombatController:
    """Controls combat state for an entity."""

    def __init__(self, stats: CharacterStats):
        """
        Initialize combat controller.

        Args:
            stats: Character stats to control
        """
        self.stats = stats

        # Attack state
        self.attack_cooldown = 0.0
        self.is_attacking = False
        self.attack_timer = 0.0

        # Defense state
        self.is_blocking = False
        self.dodge_cooldown = 0.0
        self.is_dodging = False
        self.dodge_timer = 0.0
        self.is_invincible = False  # During dodge

    def update(self, delta_time: float) -> None:
        """
        Update combat state.

        Args:
            delta_time: Time since last update
        """
        # Update stats (stamina regen, etc.)
        self.stats.update(delta_time)

        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time

        # Update attack timer
        if self.is_attacking:
            self.attack_timer -= delta_time
            if self.attack_timer <= 0:
                self.is_attacking = False

        # Update dodge
        if self.is_dodging:
            self.dodge_timer -= delta_time
            if self.dodge_timer <= 0:
                self.is_dodging = False
                self.is_invincible = False

        # Update dodge cooldown
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= delta_time

    def can_attack(self) -> bool:
        """Check if can perform attack."""
        return (
            self.attack_cooldown <= 0 and
            not self.is_attacking and
            not self.is_dodging and
            not self.stats.is_stunned and
            self.stats.is_alive
        )

    def start_attack(self, attack_duration: float = 0.3) -> bool:
        """
        Start an attack.

        Args:
            attack_duration: How long the attack lasts

        Returns:
            True if attack started
        """
        if not self.can_attack():
            return False

        # Try to use stamina
        if not self.stats.use_stamina(config.STAMINA_ATTACK_COST):
            return False

        self.is_attacking = True
        self.attack_timer = attack_duration
        self.attack_cooldown = config.ATTACK_COOLDOWN
        return True

    def can_dodge(self) -> bool:
        """Check if can perform dodge."""
        return (
            self.dodge_cooldown <= 0 and
            not self.is_dodging and
            not self.is_attacking and
            not self.stats.is_stunned and
            self.stats.is_alive
        )

    def start_dodge(self) -> bool:
        """
        Start a dodge.

        Returns:
            True if dodge started
        """
        if not self.can_dodge():
            return False

        # Try to use stamina
        if not self.stats.use_stamina(config.STAMINA_DODGE_COST):
            return False

        self.is_dodging = True
        self.is_invincible = True
        self.dodge_timer = config.DODGE_DURATION
        self.dodge_cooldown = config.DODGE_COOLDOWN
        return True

    def start_block(self) -> bool:
        """
        Start blocking.

        Returns:
            True if started blocking
        """
        if self.stats.is_stunned or not self.stats.is_alive:
            return False

        self.is_blocking = True
        return True

    def stop_block(self) -> None:
        """Stop blocking."""
        self.is_blocking = False
