"""Character stats system for combat."""
from dataclasses import dataclass, field
from typing import Optional
import config


@dataclass
class CharacterStats:
    """Base stats for any character (player or enemy)."""

    # Core stats
    max_health: float
    max_stamina: float
    base_damage: float
    defense: float

    # Current values
    current_health: float = field(init=False)
    current_stamina: float = field(init=False)

    # Status
    is_alive: bool = field(init=False, default=True)
    is_stunned: bool = field(default=False)
    stun_timer: float = field(default=0.0)

    def __post_init__(self):
        """Initialize current values to max."""
        self.current_health = self.max_health
        self.current_stamina = self.max_stamina

    @property
    def health_percent(self) -> float:
        """Get health as a percentage (0.0 to 1.0)."""
        return self.current_health / self.max_health if self.max_health > 0 else 0.0

    @property
    def stamina_percent(self) -> float:
        """Get stamina as a percentage (0.0 to 1.0)."""
        return self.current_stamina / self.max_stamina if self.max_stamina > 0 else 0.0

    def take_damage(self, damage: float) -> float:
        """
        Take damage, applying defense.

        Args:
            damage: Raw damage amount

        Returns:
            Actual damage taken after defense
        """
        # Calculate actual damage (defense reduces damage)
        actual_damage = max(1.0, damage - self.defense)

        self.current_health = max(0.0, self.current_health - actual_damage)

        if self.current_health <= 0:
            self.is_alive = False

        return actual_damage

    def heal(self, amount: float) -> None:
        """
        Heal health.

        Args:
            amount: Amount to heal
        """
        self.current_health = min(self.max_health, self.current_health + amount)
        if self.current_health > 0:
            self.is_alive = True

    def use_stamina(self, amount: float) -> bool:
        """
        Try to use stamina.

        Args:
            amount: Stamina cost

        Returns:
            True if had enough stamina, False otherwise
        """
        if self.current_stamina >= amount:
            self.current_stamina -= amount
            return True
        return False

    def regen_stamina(self, amount: float) -> None:
        """
        Regenerate stamina.

        Args:
            amount: Amount to regenerate
        """
        self.current_stamina = min(self.max_stamina, self.current_stamina + amount)

    def update(self, delta_time: float) -> None:
        """
        Update stats (stamina regen, timers, etc.).

        Args:
            delta_time: Time since last update
        """
        # Regenerate stamina
        if self.current_stamina < self.max_stamina:
            self.regen_stamina(config.STAMINA_REGEN_RATE * delta_time)

        # Update stun timer
        if self.is_stunned:
            self.stun_timer -= delta_time
            if self.stun_timer <= 0:
                self.is_stunned = False
                self.stun_timer = 0.0

    def stun(self, duration: float) -> None:
        """
        Stun the character.

        Args:
            duration: Stun duration in seconds
        """
        self.is_stunned = True
        self.stun_timer = duration


def create_player_stats() -> CharacterStats:
    """Create default player stats from config."""
    return CharacterStats(
        max_health=config.PLAYER_MAX_HEALTH,
        max_stamina=config.PLAYER_MAX_STAMINA,
        base_damage=config.PLAYER_BASE_DAMAGE,
        defense=config.PLAYER_DEFENSE
    )


def create_enemy_stats(
    health: float,
    stamina: float,
    damage: float,
    defense: float
) -> CharacterStats:
    """
    Create enemy stats.

    Args:
        health: Max health
        stamina: Max stamina
        damage: Base damage
        defense: Defense value

    Returns:
        CharacterStats configured for enemy
    """
    return CharacterStats(
        max_health=health,
        max_stamina=stamina,
        base_damage=damage,
        defense=defense
    )
