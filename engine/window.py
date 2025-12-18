"""Window and OpenGL context management."""
from typing import Tuple
import pygame
import moderngl
from pygame.locals import DOUBLEBUF, OPENGL, FULLSCREEN
import config
from game.logger import get_logger

logger = get_logger(__name__)


class Window:
    """Manages the game window and OpenGL context."""

    def __init__(self) -> None:
        """Initialize the window and ModernGL context."""
        pygame.init()

        # Set OpenGL attributes before creating window
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK,
                                       pygame.GL_CONTEXT_PROFILE_CORE)

        # Disable VSync for maximum FPS (0 = off, 1 = on)
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 0)

        # Create window
        flags = DOUBLEBUF | OPENGL
        if config.FULLSCREEN:
            flags |= FULLSCREEN

        self.screen = pygame.display.set_mode(
            (config.WINDOW_WIDTH, config.WINDOW_HEIGHT),
            flags
        )
        pygame.display.set_caption(config.WINDOW_TITLE)

        # Create ModernGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)

        # Mouse capture for FPS controls
        self.mouse_captured = False

        # Window properties
        self.width = config.WINDOW_WIDTH
        self.height = config.WINDOW_HEIGHT
        self.aspect_ratio = self.width / self.height

        logger.info(f"OpenGL Version: {self.ctx.info['GL_VERSION']}")
        logger.info(f"Window created: {self.width}x{self.height}")

    def capture_mouse(self) -> None:
        """Capture the mouse for FPS-style camera control."""
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        self.mouse_captured = True

    def release_mouse(self) -> None:
        """Release the mouse cursor."""
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        self.mouse_captured = False

    def toggle_mouse_capture(self) -> None:
        """Toggle mouse capture state."""
        if self.mouse_captured:
            self.release_mouse()
        else:
            self.capture_mouse()

    def swap_buffers(self) -> None:
        """Swap the display buffers."""
        pygame.display.flip()

    def cleanup(self) -> None:
        """Clean up resources."""
        self.ctx.release()
        pygame.quit()

    def __enter__(self):
        """Enter context manager - return self for use in 'with' statements."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager - automatically clean up resources.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred

        Returns:
            False to propagate any exception that occurred
        """
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error during Window cleanup: {e}")
        return False  # Don't suppress exceptions
