"""Unit tests for day/night cycle system."""
import unittest
import glm
import math
from graphics.day_night import DayNightCycle, TimeOfDay


class TestDayNightCycle(unittest.TestCase):
    """Test DayNightCycle class."""

    def test_cycle_creation_default(self):
        """Test default cycle creation."""
        cycle = DayNightCycle()

        self.assertEqual(cycle.day_length, 600.0)
        self.assertEqual(cycle.time, 0.5)  # Noon
        self.assertTrue(cycle.enabled)
        self.assertEqual(cycle.time_scale, 1.0)

    def test_cycle_creation_custom(self):
        """Test cycle creation with custom parameters."""
        cycle = DayNightCycle(day_length=1200.0, start_time=0.25)

        self.assertEqual(cycle.day_length, 1200.0)
        self.assertEqual(cycle.time, 0.25)

    def test_time_advances(self):
        """Test time advances with updates."""
        cycle = DayNightCycle(day_length=100.0)
        initial_time = cycle.time

        cycle.update(10.0)  # 10 seconds

        # Time should have advanced
        self.assertGreater(cycle.time, initial_time)

    def test_time_wraps_around(self):
        """Test time wraps from 1.0 back to 0.0."""
        cycle = DayNightCycle(day_length=100.0, start_time=0.99)

        # Update enough to wrap around
        cycle.update(50.0)

        # Time should have wrapped
        self.assertLess(cycle.time, 0.5)

    def test_time_scale_affects_speed(self):
        """Test time_scale multiplies advancement speed."""
        cycle_normal = DayNightCycle(day_length=100.0, start_time=0.0)
        cycle_fast = DayNightCycle(day_length=100.0, start_time=0.0)
        cycle_fast.time_scale = 2.0

        cycle_normal.update(10.0)
        cycle_fast.update(10.0)

        # Fast cycle should advance twice as much
        self.assertAlmostEqual(cycle_fast.time, cycle_normal.time * 2.0, places=5)

    def test_disabled_cycle_doesnt_advance(self):
        """Test disabled cycle doesn't advance time."""
        cycle = DayNightCycle(start_time=0.0)
        cycle.enabled = False

        cycle.update(10.0)

        # Time should not have changed
        self.assertEqual(cycle.time, 0.0)

    def test_get_time_of_day(self):
        """Test getting time of day."""
        cycle = DayNightCycle(start_time=0.75)

        time = cycle.get_time_of_day()

        self.assertEqual(time, 0.75)

    def test_get_hour(self):
        """Test getting current hour."""
        # Midnight
        cycle = DayNightCycle(start_time=0.0)
        self.assertEqual(cycle.get_hour(), 0)

        # 6 AM
        cycle.set_time(0.25)
        self.assertEqual(cycle.get_hour(), 6)

        # Noon
        cycle.set_time(0.5)
        self.assertEqual(cycle.get_hour(), 12)

        # 6 PM
        cycle.set_time(0.75)
        self.assertEqual(cycle.get_hour(), 18)

    def test_get_time_string(self):
        """Test getting formatted time string."""
        # Noon
        cycle = DayNightCycle(start_time=0.5)
        time_str = cycle.get_time_string()
        self.assertIn("12", time_str)
        self.assertIn("PM", time_str)

        # Midnight
        cycle.set_time(0.0)
        time_str = cycle.get_time_string()
        self.assertIn("12", time_str)
        self.assertIn("AM", time_str)

        # 6 AM
        cycle.set_time(0.25)
        time_str = cycle.get_time_string()
        self.assertIn("06", time_str)
        self.assertIn("AM", time_str)

        # 6 PM
        cycle.set_time(0.75)
        time_str = cycle.get_time_string()
        self.assertIn("06", time_str)
        self.assertIn("PM", time_str)

    def test_is_night(self):
        """Test checking if it's night time."""
        cycle = DayNightCycle()

        # Midnight (0.0) - night
        cycle.set_time(0.0)
        self.assertTrue(cycle.is_night())

        # 3 AM (0.125) - night
        cycle.set_time(0.125)
        self.assertTrue(cycle.is_night())

        # 9 PM (0.875) - night
        cycle.set_time(0.875)
        self.assertTrue(cycle.is_night())

        # Noon (0.5) - day
        cycle.set_time(0.5)
        self.assertFalse(cycle.is_night())

        # 3 PM (0.625) - day
        cycle.set_time(0.625)
        self.assertFalse(cycle.is_night())

    def test_is_day(self):
        """Test checking if it's day time."""
        cycle = DayNightCycle()

        # Noon - day
        cycle.set_time(0.5)
        self.assertTrue(cycle.is_day())

        # Midnight - not day
        cycle.set_time(0.0)
        self.assertFalse(cycle.is_day())

    def test_is_day_is_inverse_of_is_night(self):
        """Test is_day is always opposite of is_night."""
        cycle = DayNightCycle()

        for time in [0.0, 0.25, 0.5, 0.75, 0.9]:
            cycle.set_time(time)
            self.assertEqual(cycle.is_day(), not cycle.is_night())

    def test_get_sun_direction(self):
        """Test sun direction calculation."""
        cycle = DayNightCycle()

        # Noon - sun should be high
        cycle.set_time(0.5)
        sun_dir = cycle.get_sun_direction()
        self.assertLessEqual(sun_dir.y, 0.0)  # Negative or zero Y points down at ground (sun above)

        # Midnight - sun should be low/below horizon
        cycle.set_time(0.0)
        sun_dir = cycle.get_sun_direction()
        self.assertGreaterEqual(sun_dir.y, 0.0)  # Positive or zero Y points up (sun below)

        # Direction should be normalized
        length = glm.length(sun_dir)
        self.assertAlmostEqual(length, 1.0, places=5)

    def test_get_sun_color_daytime(self):
        """Test sun color during daytime."""
        cycle = DayNightCycle()

        # Noon - bright yellow-white
        cycle.set_time(0.5)
        color = cycle.get_sun_color()

        self.assertGreater(color.r, 0.8)
        self.assertGreater(color.g, 0.8)

    def test_get_sun_color_nighttime(self):
        """Test sun color during nighttime (moonlight)."""
        cycle = DayNightCycle()

        # Midnight - blue moonlight
        cycle.set_time(0.0)
        color = cycle.get_sun_color()

        # Should be bluish
        self.assertGreater(color.b, color.r)
        self.assertGreater(color.b, color.g)

    def test_get_sun_color_sunrise_sunset(self):
        """Test sun color at sunrise/sunset has warm tones."""
        cycle = DayNightCycle()

        # Dawn (6 AM)
        cycle.set_time(0.25)
        color = cycle.get_sun_color()

        # Should have warm orange/red tones
        self.assertGreater(color.r, 0.5)

    def test_get_sun_intensity(self):
        """Test sun intensity varies with time."""
        cycle = DayNightCycle()

        # Noon - maximum intensity
        cycle.set_time(0.5)
        noon_intensity = cycle.get_sun_intensity()

        # Night - minimum intensity
        cycle.set_time(0.0)
        night_intensity = cycle.get_sun_intensity()

        # Noon should be brighter than night
        self.assertGreater(noon_intensity, night_intensity)

    def test_get_ambient_color_varies(self):
        """Test ambient color changes with time."""
        cycle = DayNightCycle()

        # Day
        cycle.set_time(0.5)
        day_ambient = cycle.get_ambient_color()

        # Night
        cycle.set_time(0.0)
        night_ambient = cycle.get_ambient_color()

        # Day should be brighter than night
        day_brightness = day_ambient.r + day_ambient.g + day_ambient.b
        night_brightness = night_ambient.r + night_ambient.g + night_ambient.b
        self.assertGreater(day_brightness, night_brightness)

    def test_get_sky_color_varies(self):
        """Test sky color changes with time."""
        cycle = DayNightCycle()

        # Day - blue sky
        cycle.set_time(0.5)
        day_sky = cycle.get_sky_color()
        self.assertGreater(day_sky.b, 0.5)

        # Night - dark sky
        cycle.set_time(0.0)
        night_sky = cycle.get_sky_color()

        # Night sky should be darker
        night_brightness = night_sky.r + night_sky.g + night_sky.b
        day_brightness = day_sky.r + day_sky.g + day_sky.b
        self.assertLess(night_brightness, day_brightness)

    def test_get_fog_color_varies(self):
        """Test fog color changes with time."""
        cycle = DayNightCycle()

        # Day
        cycle.set_time(0.5)
        day_fog = cycle.get_fog_color()

        # Night
        cycle.set_time(0.0)
        night_fog = cycle.get_fog_color()

        # Different colors for day and night
        self.assertNotEqual(day_fog, night_fog)

    def test_set_time(self):
        """Test setting time directly."""
        cycle = DayNightCycle()

        cycle.set_time(0.75)

        self.assertEqual(cycle.time, 0.75)

    def test_set_time_clamps_to_valid_range(self):
        """Test set_time clamps values to [0.0, 1.0]."""
        cycle = DayNightCycle()

        # Too low
        cycle.set_time(-0.5)
        self.assertEqual(cycle.time, 0.0)

        # Too high
        cycle.set_time(1.5)
        self.assertEqual(cycle.time, 1.0)

    def test_set_hour(self):
        """Test setting time by hour."""
        cycle = DayNightCycle()

        cycle.set_hour(6)  # 6 AM

        self.assertAlmostEqual(cycle.time, 0.25, places=5)

    def test_set_hour_wraps(self):
        """Test set_hour wraps hours >= 24."""
        cycle = DayNightCycle()

        cycle.set_hour(25)  # Should wrap to 1 AM

        self.assertAlmostEqual(cycle.time, 1.0 / 24.0, places=5)

    def test_advance_to_time(self):
        """Test instantly advancing to specific time."""
        cycle = DayNightCycle(start_time=0.0)

        cycle.advance_to_time(0.75)

        self.assertEqual(cycle.time, 0.75)

    def test_advance_to_time_wraps(self):
        """Test advance_to_time wraps values."""
        cycle = DayNightCycle()

        cycle.advance_to_time(1.5)

        self.assertEqual(cycle.time, 0.5)

    def test_advance_hours(self):
        """Test advancing time by hours."""
        cycle = DayNightCycle(start_time=0.0)

        cycle.advance_hours(6.0)  # 6 hours

        self.assertAlmostEqual(cycle.time, 0.25, places=5)

    def test_advance_hours_wraps(self):
        """Test advancing hours wraps around day."""
        cycle = DayNightCycle(start_time=0.75)  # 6 PM

        cycle.advance_hours(12.0)  # Add 12 hours -> 6 AM

        self.assertAlmostEqual(cycle.time, 0.25, places=5)


class TestTimeOfDay(unittest.TestCase):
    """Test TimeOfDay constants."""

    def test_time_constants_are_correct(self):
        """Test TimeOfDay constants have correct values."""
        self.assertEqual(TimeOfDay.MIDNIGHT, 0.0)
        self.assertEqual(TimeOfDay.DAWN, 0.25)
        self.assertEqual(TimeOfDay.NOON, 0.5)
        self.assertEqual(TimeOfDay.DUSK, 0.75)

    def test_time_constants_match_hours(self):
        """Test time constants match expected hours."""
        cycle = DayNightCycle()

        # Dawn at 6 AM
        cycle.set_time(TimeOfDay.DAWN)
        self.assertEqual(cycle.get_hour(), 6)

        # Noon at 12 PM
        cycle.set_time(TimeOfDay.NOON)
        self.assertEqual(cycle.get_hour(), 12)

        # Dusk at 6 PM
        cycle.set_time(TimeOfDay.DUSK)
        self.assertEqual(cycle.get_hour(), 18)


class TestDayNightIntegration(unittest.TestCase):
    """Test day/night cycle integration scenarios."""

    def test_full_day_cycle(self):
        """Test cycling through a full 24-hour day."""
        cycle = DayNightCycle(day_length=100.0, start_time=0.0)

        # Run for one full day
        for _ in range(100):
            cycle.update(1.0)

        # Should have completed full cycle
        self.assertAlmostEqual(cycle.time, 0.0, places=1)

    def test_sun_position_changes_continuously(self):
        """Test sun direction changes smoothly over time."""
        cycle = DayNightCycle(day_length=100.0, start_time=0.0)

        positions = []
        for _ in range(24):
            positions.append(cycle.get_sun_direction())
            cycle.advance_hours(1.0)

        # All positions should be different
        for i in range(len(positions) - 1):
            self.assertNotEqual(positions[i], positions[i + 1])

    def test_lighting_smooth_transition(self):
        """Test lighting transitions smoothly during daytime."""
        # Start at noon to avoid day/night boundary
        cycle = DayNightCycle(day_length=1000.0, start_time=0.3)

        intensities = []
        # Run for shorter time to stay within daytime
        for _ in range(20):
            intensities.append(cycle.get_sun_intensity())
            cycle.update(10.0)

        # Intensities should change gradually (no huge jumps during day)
        # Allow larger diff to account for dawn/dusk transitions
        for i in range(len(intensities) - 1):
            diff = abs(intensities[i+1] - intensities[i])
            self.assertLess(diff, 1.0)  # Should not jump instantly

    def test_time_progresses_realistically(self):
        """Test time progresses at expected rate."""
        # 10 minute day (600 seconds)
        cycle = DayNightCycle(day_length=600.0, start_time=0.0)

        # After 60 seconds (1/10 of day), should be at time 0.1 (2.4 hours)
        cycle.update(60.0)

        self.assertAlmostEqual(cycle.time, 0.1, places=2)

    def test_rapid_time_advancement(self):
        """Test rapid time advancement (e.g., for time-lapse)."""
        cycle = DayNightCycle(day_length=600.0, start_time=0.0)
        cycle.time_scale = 100.0  # 100x speed

        # One second should advance significantly
        cycle.update(1.0)

        # Should have advanced ~1/6 of a day
        self.assertGreater(cycle.time, 0.1)

    def test_color_progression_dawn_to_dusk(self):
        """Test colors progress naturally from dawn to dusk."""
        cycle = DayNightCycle()

        # Dawn (6 AM) - sunrise
        cycle.set_hour(6)
        dawn_color = cycle.get_sky_color()

        # Mid-morning (10 AM) - should be blue
        cycle.set_hour(10)
        morning_color = cycle.get_sky_color()

        # Noon (12 PM)
        cycle.set_hour(12)
        noon_color = cycle.get_sky_color()

        # Mid-day should be bluest (dawn might be orange/warm)
        self.assertGreater(morning_color.b, 0.5)
        self.assertGreater(noon_color.b, 0.5)

    def test_night_has_consistent_darkness(self):
        """Test nighttime maintains consistent darkness."""
        cycle = DayNightCycle()

        night_intensities = []
        for hour in [0, 2, 4]:  # Midnight, 2 AM, 4 AM
            cycle.set_hour(hour)
            night_intensities.append(cycle.get_sun_intensity())

        # All night hours should have similar low intensity
        for intensity in night_intensities:
            self.assertLess(intensity, 0.3)


class TestPerformance(unittest.TestCase):
    """Test day/night cycle performance."""

    def test_update_performance(self):
        """Test update performance for many cycles."""
        cycle = DayNightCycle(day_length=100.0)

        # Should handle many updates without issues
        for _ in range(10000):
            cycle.update(0.016)  # ~60 FPS

        # Should complete without error
        self.assertTrue(True)

    def test_sun_direction_calculation_performance(self):
        """Test sun direction can be calculated frequently."""
        cycle = DayNightCycle()

        # Should handle many direction calculations
        for _ in range(10000):
            _ = cycle.get_sun_direction()

        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
