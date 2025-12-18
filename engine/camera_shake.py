"""Camera shake effect for combat feedback."""
import glm
import random
import math


class CameraShake:
    """Applies screen shake effects to the camera."""

    def __init__(self):
        """Initialize camera shake system."""
        self.trauma = 0.0  # Shake intensity (0-1)
        self.trauma_power = 2.0  # Exponential falloff power
        self.max_offset = 0.3  # Maximum position offset
        self.max_rotation = 2.0  # Maximum rotation in degrees

        # Shake decay
        self.decay_rate = 1.5  # Trauma loss per second

    def add_trauma(self, amount: float):
        """
        Add trauma to trigger shake.

        Args:
            amount: Amount of trauma to add (0-1)
        """
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, delta_time: float):
        """
        Update shake effect.

        Args:
            delta_time: Time since last frame
        """
        # Decay trauma over time
        if self.trauma > 0:
            self.trauma = max(0, self.trauma - self.decay_rate * delta_time)

    def get_shake_offset(self) -> glm.vec3:
        """
        Get current shake offset for camera position.

        Returns:
            Shake offset vector
        """
        if self.trauma <= 0:
            return glm.vec3(0, 0, 0)

        # Use power curve for trauma
        shake = pow(self.trauma, self.trauma_power)

        # Generate random offset
        offset_x = (random.random() * 2.0 - 1.0) * self.max_offset * shake
        offset_y = (random.random() * 2.0 - 1.0) * self.max_offset * shake
        offset_z = (random.random() * 2.0 - 1.0) * self.max_offset * shake

        return glm.vec3(offset_x, offset_y, offset_z)

    def get_shake_rotation(self) -> glm.vec3:
        """
        Get current shake rotation for camera.

        Returns:
            Shake rotation in degrees (pitch, yaw, roll)
        """
        if self.trauma <= 0:
            return glm.vec3(0, 0, 0)

        # Use power curve for trauma
        shake = pow(self.trauma, self.trauma_power)

        # Generate random rotation
        pitch = (random.random() * 2.0 - 1.0) * self.max_rotation * shake
        yaw = (random.random() * 2.0 - 1.0) * self.max_rotation * shake
        roll = (random.random() * 2.0 - 1.0) * self.max_rotation * shake

        return glm.vec3(pitch, yaw, roll)

    def is_shaking(self) -> bool:
        """Check if currently shaking."""
        return self.trauma > 0.01


# Trauma presets for different events
class ShakePresets:
    """Pre-defined shake intensities for different events."""

    LIGHT_HIT = 0.1      # Normal hit
    MEDIUM_HIT = 0.25    # Strong hit
    HEAVY_HIT = 0.4      # Critical hit
    PLAYER_HIT = 0.5     # Player takes damage
    EXPLOSION = 0.8      # Explosion nearby
    MASSIVE = 1.0        # Boss death, etc.
