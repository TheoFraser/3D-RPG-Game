"""Unit tests for critical bug fixes."""
import unittest
import glm
from game.puzzles import Button, PressurePlate
from game.sequence_puzzle import SequencePuzzle, ColoredButton


class TestPositionMutationFix(unittest.TestCase):
    """Test that position mutation bug is fixed."""

    def test_button_position_no_drift(self):
        """Test button position doesn't drift after multiple activations."""
        initial_pos = glm.vec3(0.0, 1.0, 0.0)
        button = Button(initial_pos, "Test Button")

        # Store initial position
        base_y = button.base_position.y

        # Activate and deactivate multiple times
        for _ in range(100):
            button.on_activate()
            button.on_deactivate()

        # Position should return to exactly the base position
        self.assertAlmostEqual(button.position.y, base_y, places=10,
                              msg="Button position drifted after multiple activations")

    def test_pressure_plate_position_no_drift(self):
        """Test pressure plate position doesn't drift after multiple activations."""
        initial_pos = glm.vec3(5.0, 0.0, 5.0)
        plate = PressurePlate(initial_pos, "Test Plate")

        # Store initial position
        base_y = plate.base_position.y

        # Activate and deactivate multiple times
        for _ in range(100):
            plate.on_activate()
            plate.on_deactivate()

        # Position should return to exactly the base position
        self.assertAlmostEqual(plate.position.y, base_y, places=10,
                              msg="Pressure plate position drifted after multiple activations")

    def test_colored_button_position_no_drift(self):
        """Test colored button position doesn't drift after multiple activations."""
        initial_pos = glm.vec3(2.0, 0.5, 3.0)
        button = ColoredButton(initial_pos, "Red", (1.0, 0.0, 0.0))

        # Store initial position
        base_y = button.base_position.y

        # Activate and deactivate multiple times
        for _ in range(100):
            button.on_activate()
            button.on_deactivate()

        # Position should return to exactly the base position
        self.assertAlmostEqual(button.position.y, base_y, places=10,
                              msg="Colored button position drifted after multiple activations")

    def test_button_pressed_position(self):
        """Test button moves to correct pressed position."""
        initial_pos = glm.vec3(0.0, 1.0, 0.0)
        button = Button(initial_pos, "Test Button")

        button.on_activate()

        # Should be pressed down by 0.1 (using 5 decimal places for floating point tolerance)
        self.assertAlmostEqual(button.position.y, 0.9, places=5)

    def test_button_released_position(self):
        """Test button returns to original position when released."""
        initial_pos = glm.vec3(0.0, 1.0, 0.0)
        button = Button(initial_pos, "Test Button")

        button.on_activate()
        button.on_deactivate()

        # Should be back at original position
        self.assertAlmostEqual(button.position.y, 1.0, places=10)


class TestLambdaClosureFix(unittest.TestCase):
    """Test that lambda closure bug is fixed."""

    def test_sequence_puzzle_correct_element_captured(self):
        """Test that each button in sequence captures correct element."""
        puzzle = SequencePuzzle("Test Sequence")

        # Create three buttons
        btn1 = ColoredButton(glm.vec3(0, 0, 0), "Red", (1.0, 0.0, 0.0))
        btn2 = ColoredButton(glm.vec3(1, 0, 0), "Green", (0.0, 1.0, 0.0))
        btn3 = ColoredButton(glm.vec3(2, 0, 0), "Blue", (0.0, 0.0, 1.0))

        # Add to sequence
        puzzle.add_to_sequence(btn1)
        puzzle.add_to_sequence(btn2)
        puzzle.add_to_sequence(btn3)

        # Test that pressing btn1 advances to index 1
        puzzle.current_index = 0
        btn1.interact()
        self.assertEqual(puzzle.current_index, 1,
                        "Button 1 should advance sequence to index 1")

        # Test that pressing btn2 advances to index 2
        btn2.interact()
        self.assertEqual(puzzle.current_index, 2,
                        "Button 2 should advance sequence to index 2")

        # Test that pressing btn3 completes the sequence
        btn3.interact()
        self.assertTrue(puzzle.completed,
                       "Button 3 should complete the sequence")

    def test_sequence_puzzle_wrong_order_resets(self):
        """Test that pressing buttons in wrong order resets sequence."""
        puzzle = SequencePuzzle("Test Sequence")

        # Create three buttons
        btn1 = ColoredButton(glm.vec3(0, 0, 0), "Red", (1.0, 0.0, 0.0))
        btn2 = ColoredButton(glm.vec3(1, 0, 0), "Green", (0.0, 1.0, 0.0))
        btn3 = ColoredButton(glm.vec3(2, 0, 0), "Blue", (0.0, 0.0, 1.0))

        puzzle.add_to_sequence(btn1)
        puzzle.add_to_sequence(btn2)
        puzzle.add_to_sequence(btn3)

        # Press first button correctly
        btn1.interact()
        self.assertEqual(puzzle.current_index, 1)

        # Press wrong button (btn3 instead of btn2)
        btn3.interact()

        # Should reset to 0
        self.assertEqual(puzzle.current_index, 0,
                        "Wrong button should reset sequence to 0")
        self.assertFalse(puzzle.completed,
                        "Wrong button should not complete sequence")

    def test_each_button_has_unique_closure(self):
        """Test that each button's interact method is unique."""
        puzzle = SequencePuzzle("Test Sequence")

        btn1 = ColoredButton(glm.vec3(0, 0, 0), "Red", (1.0, 0.0, 0.0))
        btn2 = ColoredButton(glm.vec3(1, 0, 0), "Green", (0.0, 1.0, 0.0))
        btn3 = ColoredButton(glm.vec3(2, 0, 0), "Blue", (0.0, 0.0, 1.0))

        puzzle.add_to_sequence(btn1)
        puzzle.add_to_sequence(btn2)
        puzzle.add_to_sequence(btn3)

        # Each button should call on_element_activated with itself
        # We verify this indirectly by checking the sequence works correctly

        # Reset and try different order
        puzzle.reset()

        # Press btn2 first (wrong)
        btn2.interact()
        self.assertEqual(puzzle.current_index, 0, "Should reset on wrong button")

        # Press btn1 (correct)
        btn1.interact()
        self.assertEqual(puzzle.current_index, 1, "Should advance on correct button")

        # This proves each button is calling with the correct element reference


if __name__ == '__main__':
    unittest.main()
