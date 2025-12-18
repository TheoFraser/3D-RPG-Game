"""Unit tests for configuration validation."""
import unittest
import config


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation."""

    def test_default_config_is_valid(self):
        """Test that default configuration passes validation."""
        try:
            result = config.validate_config()
            self.assertTrue(result)
        except ValueError:
            self.fail("Default config should be valid")

    def test_invalid_window_size(self):
        """Test validation catches invalid window size."""
        original_width = config.WINDOW_WIDTH
        config.WINDOW_WIDTH = 0

        with self.assertRaises(ValueError) as context:
            config.validate_config()

        self.assertIn("Invalid window size", str(context.exception))

        # Restore original value
        config.WINDOW_WIDTH = original_width

    def test_invalid_fov(self):
        """Test validation catches invalid FOV."""
        original_fov = config.FOV
        config.FOV = 200  # Too high

        with self.assertRaises(ValueError) as context:
            config.validate_config()

        self.assertIn("Invalid FOV", str(context.exception))

        # Restore original value
        config.FOV = original_fov

    def test_invalid_near_far_plane(self):
        """Test validation catches invalid near/far plane relationship."""
        original_near = config.NEAR_PLANE
        original_far = config.FAR_PLANE

        config.NEAR_PLANE = 100.0
        config.FAR_PLANE = 50.0  # Far < Near (invalid)

        with self.assertRaises(ValueError) as context:
            config.validate_config()

        self.assertIn("Invalid FAR_PLANE", str(context.exception))

        # Restore original values
        config.NEAR_PLANE = original_near
        config.FAR_PLANE = original_far


if __name__ == '__main__':
    unittest.main()
