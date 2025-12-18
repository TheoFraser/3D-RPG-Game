"""Unit tests for weather system."""
import unittest
import glm
import moderngl
from graphics.weather import WeatherType, WeatherSystem
from graphics.particles import ParticleSystem, ParticleType


class TestWeatherSystem(unittest.TestCase):
    """Test WeatherSystem class."""

    @classmethod
    def setUpClass(cls):
        """Create a ModernGL context for tests."""
        cls.ctx = moderngl.create_standalone_context()

    @classmethod
    def tearDownClass(cls):
        """Release the ModernGL context."""
        cls.ctx.release()

    def setUp(self):
        """Create fresh particle system and weather system for each test."""
        self.particle_system = ParticleSystem(self.ctx)
        self.weather_system = WeatherSystem(self.particle_system)

    def test_weather_system_creation(self):
        """Test weather system initializes correctly."""
        self.assertIsNotNone(self.weather_system)
        self.assertEqual(self.weather_system.current_weather, WeatherType.CLEAR)
        self.assertEqual(self.weather_system.target_weather, WeatherType.CLEAR)
        self.assertEqual(self.weather_system.transition_progress, 1.0)
        self.assertTrue(self.weather_system.enabled)

    def test_initial_weather_is_clear(self):
        """Test weather starts as clear."""
        self.assertEqual(self.weather_system.current_weather, WeatherType.CLEAR)

    def test_change_weather(self):
        """Test changing weather type."""
        self.weather_system.change_weather(WeatherType.RAIN)

        self.assertEqual(self.weather_system.target_weather, WeatherType.RAIN)
        self.assertEqual(self.weather_system.transition_progress, 0.0)

    def test_weather_transition(self):
        """Test weather transitions over time."""
        self.weather_system.change_weather(WeatherType.SNOW)

        # Initially transitioning
        self.assertLess(self.weather_system.transition_progress, 1.0)

        # Update for long enough to complete transition
        player_pos = glm.vec3(0.0, 0.0, 0.0)
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        # Transition should be complete
        self.assertEqual(self.weather_system.transition_progress, 1.0)
        self.assertEqual(self.weather_system.current_weather, WeatherType.SNOW)

    def test_weather_duration_triggers_change(self):
        """Test weather changes automatically after duration."""
        self.weather_system.weather_duration = 1.0  # 1 second duration

        player_pos = glm.vec3(0.0, 0.0, 0.0)

        # Wait beyond weather duration (transition_progress should reset to 0.0)
        self.weather_system.update(1.5, player_pos)

        # Should have started transitioning (progress < 1.0 or time_in_weather reset)
        # Either transition started or weather changed
        self.assertTrue(
            self.weather_system.transition_progress < 1.0 or
            self.weather_system.time_in_weather < 1.0
        )

    def test_change_weather_random(self):
        """Test random weather changes."""
        initial_weather = self.weather_system.current_weather

        # Try multiple random changes (one should be different)
        changed = False
        for _ in range(10):
            self.weather_system.change_weather_random()
            if self.weather_system.target_weather != initial_weather:
                changed = True
                break

        # With probability > 0, should eventually change
        self.assertTrue(changed)

    def test_rain_creates_rain_particles(self):
        """Test rain weather creates rain particle emitters."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        self.weather_system.change_weather(WeatherType.RAIN)

        # Complete transition
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        # Should have created rain emitters
        self.assertGreater(len(self.weather_system.weather_emitters), 0)

        # Emitters should be creating rain particles
        has_rain = False
        for emitter in self.weather_system.weather_emitters:
            if emitter.particle_type == ParticleType.RAIN:
                has_rain = True
                break

        self.assertTrue(has_rain)

    def test_snow_creates_snow_particles(self):
        """Test snow weather creates snow particle emitters."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        self.weather_system.change_weather(WeatherType.SNOW)

        # Complete transition
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        # Should have created snow emitters
        self.assertGreater(len(self.weather_system.weather_emitters), 0)

        has_snow = False
        for emitter in self.weather_system.weather_emitters:
            if emitter.particle_type == ParticleType.SNOW:
                has_snow = True
                break

        self.assertTrue(has_snow)

    def test_storm_creates_heavy_rain(self):
        """Test storm weather creates more rain emitters than normal rain."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        # Test rain
        self.weather_system.change_weather(WeatherType.RAIN)
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)
        rain_emitter_count = len(self.weather_system.weather_emitters)

        # Reset and test storm
        self.weather_system._clear_weather_effects()
        self.weather_system.change_weather(WeatherType.STORM)
        self.weather_system.transition_progress = 0.0  # Reset transition
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)
        storm_emitter_count = len(self.weather_system.weather_emitters)

        # Storm should have more emitters than rain
        self.assertGreater(storm_emitter_count, rain_emitter_count)

    def test_clear_weather_no_particles(self):
        """Test clear weather doesn't create particle emitters."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        self.weather_system.change_weather(WeatherType.CLEAR)

        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        # Clear weather shouldn't create emitters
        self.assertEqual(len(self.weather_system.weather_emitters), 0)

    def test_fog_weather_no_particles(self):
        """Test fog weather doesn't create particle emitters (visual effect only)."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        self.weather_system.change_weather(WeatherType.FOG)

        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        # Fog is visual effect, not particles
        self.assertEqual(len(self.weather_system.weather_emitters), 0)

    def test_update_weather_emitter_positions(self):
        """Test weather emitters follow player position."""
        player_pos_1 = glm.vec3(0.0, 0.0, 0.0)
        player_pos_2 = glm.vec3(100.0, 0.0, 100.0)

        # Create rain weather
        self.weather_system.change_weather(WeatherType.RAIN)
        for _ in range(100):
            self.weather_system.update(0.1, player_pos_1)

        # Get initial emitter position
        initial_pos = self.weather_system.weather_emitters[0].position

        # Move player and update emitter positions
        self.weather_system.update_weather_emitter_positions(player_pos_2)

        # Emitter should have moved
        new_pos = self.weather_system.weather_emitters[0].position
        self.assertNotEqual(initial_pos, new_pos)

    def test_get_fog_density_multiplier(self):
        """Test fog density changes with weather."""
        # Clear weather should have normal fog
        self.weather_system.current_weather = WeatherType.CLEAR
        clear_fog = self.weather_system.get_fog_density_multiplier()
        self.assertEqual(clear_fog, 1.0)

        # Fog weather should have high fog density
        self.weather_system.current_weather = WeatherType.FOG
        fog_fog = self.weather_system.get_fog_density_multiplier()
        self.assertGreater(fog_fog, clear_fog)

        # Storm should have more fog than clear
        self.weather_system.current_weather = WeatherType.STORM
        storm_fog = self.weather_system.get_fog_density_multiplier()
        self.assertGreater(storm_fog, clear_fog)

    def test_get_ambient_light_multiplier(self):
        """Test ambient light changes with weather."""
        # Clear weather should have full light
        self.weather_system.current_weather = WeatherType.CLEAR
        clear_light = self.weather_system.get_ambient_light_multiplier()
        self.assertEqual(clear_light, 1.0)

        # Storm should have reduced light
        self.weather_system.current_weather = WeatherType.STORM
        storm_light = self.weather_system.get_ambient_light_multiplier()
        self.assertLess(storm_light, clear_light)

        # Cloudy should be darker than clear but lighter than storm
        self.weather_system.current_weather = WeatherType.CLOUDY
        cloudy_light = self.weather_system.get_ambient_light_multiplier()
        self.assertLess(cloudy_light, clear_light)
        self.assertGreater(cloudy_light, storm_light)

    def test_transition_interpolates_fog(self):
        """Test fog density interpolates during weather transition."""
        self.weather_system.current_weather = WeatherType.CLEAR
        self.weather_system.target_weather = WeatherType.FOG
        self.weather_system.transition_progress = 0.5  # Halfway

        fog_density = self.weather_system.get_fog_density_multiplier()

        # Should be between clear (1.0) and fog (3.0)
        self.assertGreater(fog_density, 1.0)
        self.assertLess(fog_density, 3.0)

    def test_transition_interpolates_light(self):
        """Test ambient light interpolates during transition."""
        self.weather_system.current_weather = WeatherType.CLEAR
        self.weather_system.target_weather = WeatherType.STORM
        self.weather_system.transition_progress = 0.5

        light = self.weather_system.get_ambient_light_multiplier()

        # Should be between clear (1.0) and storm (0.5)
        self.assertGreater(light, 0.5)
        self.assertLess(light, 1.0)

    def test_get_weather_name(self):
        """Test getting weather name as string."""
        self.weather_system.current_weather = WeatherType.RAIN
        name = self.weather_system.get_weather_name()

        self.assertEqual(name, "Rain")
        self.assertIsInstance(name, str)

    def test_is_raining(self):
        """Test checking if it's raining."""
        # Clear weather
        self.weather_system.current_weather = WeatherType.CLEAR
        self.assertFalse(self.weather_system.is_raining())

        # Rain weather
        self.weather_system.current_weather = WeatherType.RAIN
        self.assertTrue(self.weather_system.is_raining())

        # Storm weather (also counts as raining)
        self.weather_system.current_weather = WeatherType.STORM
        self.assertTrue(self.weather_system.is_raining())

        # Snow weather (not raining)
        self.weather_system.current_weather = WeatherType.SNOW
        self.assertFalse(self.weather_system.is_raining())

    def test_is_snowing(self):
        """Test checking if it's snowing."""
        # Clear weather
        self.weather_system.current_weather = WeatherType.CLEAR
        self.assertFalse(self.weather_system.is_snowing())

        # Snow weather
        self.weather_system.current_weather = WeatherType.SNOW
        self.assertTrue(self.weather_system.is_snowing())

        # Rain weather (not snowing)
        self.weather_system.current_weather = WeatherType.RAIN
        self.assertFalse(self.weather_system.is_snowing())

    def test_weather_disabled(self):
        """Test disabled weather system doesn't update."""
        self.weather_system.enabled = False
        self.weather_system.change_weather(WeatherType.RAIN)

        initial_progress = self.weather_system.transition_progress

        # Update
        player_pos = glm.vec3(0.0, 0.0, 0.0)
        self.weather_system.update(1.0, player_pos)

        # Progress shouldn't change when disabled
        self.assertEqual(self.weather_system.transition_progress, initial_progress)

    def test_weather_probabilities_sum_to_one(self):
        """Test weather probabilities add up to 1.0."""
        total_prob = sum(self.weather_system.weather_probabilities.values())
        self.assertAlmostEqual(total_prob, 1.0, places=5)

    def test_clear_weather_effects(self):
        """Test clearing weather effects removes emitters."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        # Create rain
        self.weather_system.change_weather(WeatherType.RAIN)
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        self.assertGreater(len(self.weather_system.weather_emitters), 0)

        # Clear effects
        self.weather_system._clear_weather_effects()

        self.assertEqual(len(self.weather_system.weather_emitters), 0)

    def test_changing_weather_clears_previous_effects(self):
        """Test changing weather clears previous weather's effects."""
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        # Start with rain
        self.weather_system.change_weather(WeatherType.RAIN)
        for _ in range(100):
            self.weather_system.update(0.1, player_pos)

        rain_emitters = len(self.weather_system.weather_emitters)
        self.assertGreater(rain_emitters, 0)

        # Change to clear
        self.weather_system.change_weather(WeatherType.CLEAR)

        # Old emitters should be cleared
        self.assertEqual(len(self.weather_system.weather_emitters), 0)


class TestWeatherTypes(unittest.TestCase):
    """Test weather type enumeration."""

    def test_all_weather_types_exist(self):
        """Test all expected weather types are defined."""
        expected_types = ['CLEAR', 'CLOUDY', 'RAIN', 'SNOW', 'FOG', 'STORM']

        for weather_name in expected_types:
            self.assertTrue(hasattr(WeatherType, weather_name))

    def test_weather_types_are_unique(self):
        """Test all weather types have unique values."""
        weather_values = [w.value for w in WeatherType]
        self.assertEqual(len(weather_values), len(set(weather_values)))


class TestWeatherIntegration(unittest.TestCase):
    """Test weather system integration scenarios."""

    @classmethod
    def setUpClass(cls):
        """Create a ModernGL context for tests."""
        cls.ctx = moderngl.create_standalone_context()

    @classmethod
    def tearDownClass(cls):
        """Release the ModernGL context."""
        cls.ctx.release()

    def test_weather_cycle(self):
        """Test cycling through different weather types."""
        particle_system = ParticleSystem(self.ctx)
        weather_system = WeatherSystem(particle_system)
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        weather_types = [WeatherType.CLEAR, WeatherType.RAIN, WeatherType.SNOW, WeatherType.FOG]

        for weather in weather_types:
            weather_system.change_weather(weather)

            # Complete transition
            for _ in range(100):
                weather_system.update(0.1, player_pos)

            self.assertEqual(weather_system.current_weather, weather)

    def test_weather_effects_integrate_with_particle_system(self):
        """Test weather effects properly add emitters to particle system."""
        particle_system = ParticleSystem(self.ctx)
        weather_system = WeatherSystem(particle_system)
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        initial_emitters = len(particle_system.emitters)

        # Create rain weather
        weather_system.change_weather(WeatherType.RAIN)
        for _ in range(100):
            weather_system.update(0.1, player_pos)

        # Particle system should have new emitters
        self.assertGreater(len(particle_system.emitters), initial_emitters)

    def test_long_running_weather_simulation(self):
        """Test weather system over extended simulation."""
        particle_system = ParticleSystem(self.ctx)
        weather_system = WeatherSystem(particle_system)
        player_pos = glm.vec3(0.0, 0.0, 0.0)

        weather_system.weather_duration = 2.0  # 2 second weather duration

        weather_changes = []
        current_weather = weather_system.current_weather

        # Run for 30 seconds to ensure multiple weather cycles
        for _ in range(300):
            weather_system.update(0.1, player_pos)

            # Track when transition starts (not just completed changes)
            if weather_system.transition_progress < 1.0:
                if len(weather_changes) == 0 or weather_changes[-1] != weather_system.target_weather:
                    weather_changes.append(weather_system.target_weather)

        # Should have started at least one transition in 30 seconds with 2s duration
        self.assertGreater(len(weather_changes), 0)


if __name__ == '__main__':
    unittest.main()
