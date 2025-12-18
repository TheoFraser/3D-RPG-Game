"""Day/night cycle system for dynamic lighting and atmosphere."""
import glm
import math


class TimeOfDay:
    """Represents the current time of day."""

    DAWN = 0.25       # 6 AM
    NOON = 0.5        # 12 PM
    DUSK = 0.75       # 6 PM
    MIDNIGHT = 0.0    # 12 AM


class DayNightCycle:
    """Manages the day/night cycle and associated lighting changes."""

    def __init__(self, day_length: float = 600.0, start_time: float = 0.5):
        """
        Initialize day/night cycle.

        Args:
            day_length: Length of a full day in seconds (default: 10 minutes)
            start_time: Starting time (0.0 = midnight, 0.5 = noon, 1.0 = midnight)
        """
        self.day_length = day_length
        self.time = start_time  # 0.0 to 1.0 (represents 24 hours)
        self.enabled = True
        self.time_scale = 1.0  # Speed multiplier

    def update(self, delta_time: float):
        """
        Update the time of day.

        Args:
            delta_time: Time since last frame in seconds
        """
        if not self.enabled:
            return

        # Advance time
        time_advance = (delta_time * self.time_scale) / self.day_length
        self.time = (self.time + time_advance) % 1.0

    def get_time_of_day(self) -> float:
        """
        Get current time of day.

        Returns:
            Time as 0.0 to 1.0 (0.0 = midnight, 0.5 = noon)
        """
        return self.time

    def get_hour(self) -> int:
        """
        Get current hour (0-23).

        Returns:
            Hour of the day
        """
        return int(self.time * 24) % 24

    def get_time_string(self) -> str:
        """
        Get formatted time string.

        Returns:
            Time as "HH:MM AM/PM"
        """
        hour = self.get_hour()
        minute = int((self.time * 24 * 60) % 60)

        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        period = "AM" if hour < 12 else "PM"

        return f"{display_hour:02d}:{minute:02d} {period}"

    def is_night(self) -> bool:
        """Check if it's currently night time."""
        # Night is from 8 PM (0.833) to 6 AM (0.25)
        return self.time < 0.25 or self.time > 0.833

    def is_day(self) -> bool:
        """Check if it's currently day time."""
        return not self.is_night()

    def get_sun_direction(self) -> glm.vec3:
        """
        Calculate sun direction based on time of day.

        Returns:
            Normalized sun direction vector
        """
        # Sun moves in an arc across the sky
        # At noon (0.5), sun is at highest point
        # At midnight (0.0/1.0), sun is below horizon

        angle = (self.time - 0.5) * math.pi * 2.0  # -PI to PI

        # Sun height (y) follows sine wave
        sun_height = math.sin(angle)

        # Sun moves east to west
        sun_x = math.cos(angle)

        direction = glm.vec3(sun_x, -sun_height, 0.3)
        return glm.normalize(direction)

    def get_sun_color(self) -> glm.vec3:
        """
        Get sun color based on time of day.

        Returns:
            RGB color for the sun
        """
        # Sunrise/sunset: orange/red
        # Noon: bright white/yellow
        # Night: dark blue

        if self.is_night():
            # Moon light - pale blue
            return glm.vec3(0.2, 0.3, 0.5)

        # Calculate how close to noon (0.5)
        noon_distance = abs(self.time - 0.5) * 2.0  # 0.0 at noon, 1.0 at dawn/dusk

        if noon_distance > 0.7:  # Sunrise/sunset
            # Orange/red tint
            return glm.vec3(1.0, 0.6 + (1.0 - noon_distance) * 0.3, 0.3)
        else:  # Daytime
            # Bright yellow-white
            return glm.vec3(1.0, 1.0, 0.9)

    def get_sun_intensity(self) -> float:
        """
        Get sun light intensity.

        Returns:
            Intensity multiplier (0.0 to 1.5+)
        """
        if self.is_night():
            return 0.2  # Dim moonlight

        # Full brightness at noon, dimmer at sunrise/sunset
        # Increased base from 0.4 to 0.7 and max from 1.0 to 1.5 for brighter scenes
        noon_distance = abs(self.time - 0.5) * 2.0
        return 0.7 + (1.0 - noon_distance) * 0.8

    def get_ambient_color(self) -> glm.vec3:
        """
        Get ambient light color.

        Returns:
            RGB ambient color
        """
        if self.is_night():
            # Dark blue ambient at night
            return glm.vec3(0.1, 0.12, 0.2)

        noon_distance = abs(self.time - 0.5) * 2.0

        if noon_distance > 0.7:  # Sunrise/sunset
            # Warm ambient
            return glm.vec3(0.5, 0.45, 0.4)
        else:  # Daytime
            # Bright neutral ambient (increased from 0.3 to make scenes brighter)
            return glm.vec3(0.6, 0.6, 0.65)

    def get_sky_color(self) -> glm.vec3:
        """
        Get sky color for skybox tinting.

        Returns:
            RGB sky color
        """
        if self.is_night():
            # Dark blue/purple night sky
            return glm.vec3(0.02, 0.05, 0.15)

        noon_distance = abs(self.time - 0.5) * 2.0

        if noon_distance > 0.7:  # Sunrise/sunset
            # Orange/pink sky
            return glm.vec3(0.8, 0.5, 0.4)
        else:  # Daytime
            # Bright blue sky
            return glm.vec3(0.4, 0.6, 0.9)

    def get_fog_color(self) -> glm.vec3:
        """
        Get fog color based on time of day.

        Returns:
            RGB fog color
        """
        if self.is_night():
            # Dark blue fog at night
            return glm.vec3(0.1, 0.15, 0.25)

        noon_distance = abs(self.time - 0.5) * 2.0

        if noon_distance > 0.7:  # Sunrise/sunset
            # Warm orange fog
            return glm.vec3(0.7, 0.6, 0.5)
        else:  # Daytime
            # Light blue-gray fog
            return glm.vec3(0.7, 0.8, 0.9)

    def set_time(self, time: float):
        """
        Set the current time.

        Args:
            time: Time to set (0.0 to 1.0)
        """
        self.time = max(0.0, min(1.0, time))

    def set_hour(self, hour: int):
        """
        Set time by hour.

        Args:
            hour: Hour to set (0-23)
        """
        self.time = (hour % 24) / 24.0

    def advance_to_time(self, target_time: float):
        """
        Instantly advance to a specific time.

        Args:
            target_time: Target time (0.0 to 1.0)
        """
        self.time = target_time % 1.0

    def advance_hours(self, hours: float):
        """
        Advance time by a number of hours.

        Args:
            hours: Hours to advance
        """
        self.time = (self.time + hours / 24.0) % 1.0
