"""Weather system for dynamic atmospheric effects."""
import glm
import random
from enum import Enum, auto
from graphics.particles import ParticleSystem, ParticleType


class WeatherType(Enum):
    """Types of weather conditions."""
    CLEAR = auto()
    CLOUDY = auto()
    RAIN = auto()
    SNOW = auto()
    FOG = auto()
    STORM = auto()


class WeatherSystem:
    """Manages dynamic weather changes and effects."""

    def __init__(self, particle_system: ParticleSystem):
        """
        Initialize weather system.

        Args:
            particle_system: Particle system for weather effects
        """
        self.particle_system = particle_system
        self.current_weather = WeatherType.CLEAR
        self.target_weather = WeatherType.CLEAR
        self.transition_progress = 1.0  # 0.0 to 1.0
        self.transition_speed = 0.1  # How fast weather changes
        self.weather_duration = 300.0  # Seconds before random weather change
        self.time_in_weather = 0.0
        self.enabled = True
        self.weather_emitters = []

        # Weather probabilities (must sum to 1.0)
        self.weather_probabilities = {
            WeatherType.CLEAR: 0.5,
            WeatherType.CLOUDY: 0.2,
            WeatherType.RAIN: 0.15,
            WeatherType.SNOW: 0.05,
            WeatherType.FOG: 0.08,
            WeatherType.STORM: 0.02,
        }

    def update(self, delta_time: float, player_position: glm.vec3):
        """
        Update weather system.

        Args:
            delta_time: Time since last frame
            player_position: Current player position
        """
        if not self.enabled:
            return

        # Update transition
        if self.transition_progress < 1.0:
            self.transition_progress = min(1.0, self.transition_progress + delta_time * self.transition_speed)

            # When transition complete, apply new weather
            if self.transition_progress >= 1.0:
                self.current_weather = self.target_weather
                self._apply_weather_effects(player_position)

        # Track time in current weather
        self.time_in_weather += delta_time

        # Random weather changes
        if self.time_in_weather >= self.weather_duration:
            self.change_weather_random()

    def change_weather(self, new_weather: WeatherType):
        """
        Begin transition to new weather.

        Args:
            new_weather: Weather type to transition to
        """
        if new_weather != self.target_weather:
            self.target_weather = new_weather
            self.transition_progress = 0.0
            self.time_in_weather = 0.0
            self._clear_weather_effects()

    def change_weather_random(self):
        """Change to a random weather type based on probabilities."""
        # Choose random weather
        weather_types = list(self.weather_probabilities.keys())
        probabilities = list(self.weather_probabilities.values())
        new_weather = random.choices(weather_types, weights=probabilities, k=1)[0]

        self.change_weather(new_weather)

    def _clear_weather_effects(self):
        """Clear current weather particle emitters."""
        for emitter in self.weather_emitters:
            if emitter in self.particle_system.emitters:
                self.particle_system.emitters.remove(emitter)
        self.weather_emitters.clear()

    def _apply_weather_effects(self, player_position: glm.vec3):
        """
        Apply particle effects for current weather.

        Args:
            player_position: Player position to center effects
        """
        self._clear_weather_effects()

        if self.current_weather == WeatherType.RAIN:
            # Create rain emitters around player
            for i in range(4):
                angle = (i / 4.0) * 3.14159 * 2.0
                offset_x = glm.cos(angle) * 30.0
                offset_z = glm.sin(angle) * 30.0

                emitter = self.particle_system.create_emitter(
                    position=player_position + glm.vec3(offset_x, 20.0, offset_z),
                    particle_type=ParticleType.RAIN,
                    emission_rate=100.0,
                    area_size=40.0
                )
                self.weather_emitters.append(emitter)

        elif self.current_weather == WeatherType.SNOW:
            # Create snow emitters
            for i in range(4):
                angle = (i / 4.0) * 3.14159 * 2.0
                offset_x = glm.cos(angle) * 30.0
                offset_z = glm.sin(angle) * 30.0

                emitter = self.particle_system.create_emitter(
                    position=player_position + glm.vec3(offset_x, 15.0, offset_z),
                    particle_type=ParticleType.SNOW,
                    emission_rate=50.0,
                    area_size=40.0
                )
                self.weather_emitters.append(emitter)

        elif self.current_weather == WeatherType.STORM:
            # Heavy rain for storms
            for i in range(6):
                angle = (i / 6.0) * 3.14159 * 2.0
                offset_x = glm.cos(angle) * 30.0
                offset_z = glm.sin(angle) * 30.0

                emitter = self.particle_system.create_emitter(
                    position=player_position + glm.vec3(offset_x, 20.0, offset_z),
                    particle_type=ParticleType.RAIN,
                    emission_rate=200.0,
                    area_size=50.0
                )
                self.weather_emitters.append(emitter)

    def update_weather_emitter_positions(self, player_position: glm.vec3):
        """
        Update weather emitter positions to follow player.

        Args:
            player_position: Current player position
        """
        if not self.weather_emitters:
            return

        # Reposition emitters around player
        for i, emitter in enumerate(self.weather_emitters):
            if self.current_weather in [WeatherType.RAIN, WeatherType.STORM]:
                angle = (i / len(self.weather_emitters)) * 3.14159 * 2.0
                offset_x = glm.cos(angle) * 30.0
                offset_z = glm.sin(angle) * 30.0
                emitter.position = player_position + glm.vec3(offset_x, 20.0, offset_z)

            elif self.current_weather == WeatherType.SNOW:
                angle = (i / len(self.weather_emitters)) * 3.14159 * 2.0
                offset_x = glm.cos(angle) * 30.0
                offset_z = glm.sin(angle) * 30.0
                emitter.position = player_position + glm.vec3(offset_x, 15.0, offset_z)

    def get_fog_density_multiplier(self) -> float:
        """
        Get fog density multiplier based on weather.

        Returns:
            Fog density multiplier (1.0 = normal, higher = more fog)
        """
        fog_multipliers = {
            WeatherType.CLEAR: 1.0,
            WeatherType.CLOUDY: 1.2,
            WeatherType.RAIN: 1.5,
            WeatherType.SNOW: 1.8,
            WeatherType.FOG: 3.0,
            WeatherType.STORM: 2.0,
        }

        # Interpolate during transition
        current_mult = fog_multipliers[self.current_weather]
        if self.transition_progress < 1.0:
            target_mult = fog_multipliers[self.target_weather]
            return current_mult + (target_mult - current_mult) * self.transition_progress

        return current_mult

    def get_ambient_light_multiplier(self) -> float:
        """
        Get ambient light multiplier based on weather.

        Returns:
            Light multiplier (1.0 = normal, lower = darker)
        """
        light_multipliers = {
            WeatherType.CLEAR: 1.0,
            WeatherType.CLOUDY: 0.8,
            WeatherType.RAIN: 0.7,
            WeatherType.SNOW: 0.9,
            WeatherType.FOG: 0.6,
            WeatherType.STORM: 0.5,
        }

        current_mult = light_multipliers[self.current_weather]
        if self.transition_progress < 1.0:
            target_mult = light_multipliers[self.target_weather]
            return current_mult + (target_mult - current_mult) * self.transition_progress

        return current_mult

    def get_weather_name(self) -> str:
        """Get current weather name as string."""
        return self.current_weather.name.title()

    def is_raining(self) -> bool:
        """Check if it's currently raining."""
        return self.current_weather in [WeatherType.RAIN, WeatherType.STORM]

    def is_snowing(self) -> bool:
        """Check if it's currently snowing."""
        return self.current_weather == WeatherType.SNOW
