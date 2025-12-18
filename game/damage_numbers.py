"""Damage number display system for combat feedback."""
import glm
from typing import List
import time


class DamageNumber:
    """Floating damage number that appears when entities take damage."""

    def __init__(self, damage: float, position: glm.vec3, critical: bool = False):
        """
        Create a damage number.

        Args:
            damage: Amount of damage dealt
            position: World position where damage occurred
            critical: Whether this was a critical hit
        """
        self.damage = int(damage)
        self.position = glm.vec3(position)
        self.start_position = glm.vec3(position)
        self.critical = critical

        # Animation properties
        self.lifetime = 1.5 if critical else 1.0  # Seconds
        self.elapsed = 0.0
        self.rise_speed = 2.0 if critical else 1.5  # Units per second
        self.fade_start = 0.5  # Start fading after this time

        # Visual properties
        self.scale = 1.5 if critical else 1.0
        self.color = (1.0, 0.3, 0.3) if critical else (1.0, 1.0, 1.0)  # Red for crit, white for normal

    def update(self, delta_time: float) -> bool:
        """
        Update the damage number animation.

        Args:
            delta_time: Time since last frame

        Returns:
            True if still alive, False if should be removed
        """
        self.elapsed += delta_time

        # Rise upward
        self.position.y = self.start_position.y + (self.rise_speed * self.elapsed)

        # Check if lifetime expired
        return self.elapsed < self.lifetime

    def get_alpha(self) -> float:
        """Get current alpha value for fading."""
        if self.elapsed < self.fade_start:
            return 1.0

        # Fade out after fade_start
        fade_duration = self.lifetime - self.fade_start
        fade_progress = (self.elapsed - self.fade_start) / fade_duration
        return max(0.0, 1.0 - fade_progress)

    def get_text(self) -> str:
        """Get the text to display."""
        if self.critical:
            return f"{self.damage}!"
        return str(self.damage)


class DamageNumberManager:
    """Manages all active damage numbers."""

    def __init__(self):
        """Initialize the damage number manager."""
        self.damage_numbers: List[DamageNumber] = []

    def add_damage_number(self, damage: float, position: glm.vec3, critical: bool = False):
        """
        Add a new damage number to display.

        Args:
            damage: Amount of damage dealt
            position: World position where damage occurred
            critical: Whether this was a critical hit
        """
        # Offset position slightly to avoid z-fighting
        offset_position = position + glm.vec3(0, 1.0, 0)
        number = DamageNumber(damage, offset_position, critical)
        self.damage_numbers.append(number)

    def update(self, delta_time: float):
        """
        Update all damage numbers.

        Args:
            delta_time: Time since last frame
        """
        # Update all damage numbers and remove expired ones
        self.damage_numbers = [
            num for num in self.damage_numbers
            if num.update(delta_time)
        ]

    def get_active_numbers(self) -> List[DamageNumber]:
        """Get all active damage numbers for rendering."""
        return self.damage_numbers.copy()

    def clear(self):
        """Remove all damage numbers."""
        self.damage_numbers.clear()
