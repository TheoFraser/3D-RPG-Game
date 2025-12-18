"""Shader compilation and management."""
import moderngl
from pathlib import Path
from game.logger import get_logger

logger = get_logger(__name__)


class Shader:
    """Manages shader programs."""

    def __init__(self, ctx: moderngl.Context, vertex_source: str, fragment_source: str):
        """
        Create a shader program from source code.

        Args:
            ctx: ModernGL context
            vertex_source: Vertex shader GLSL source code
            fragment_source: Fragment shader GLSL source code
        """
        self.ctx = ctx
        try:
            self.program = ctx.program(
                vertex_shader=vertex_source,
                fragment_shader=fragment_source
            )
        except Exception as e:
            logger.error(f"Shader compilation error:\n{e}")
            raise

    @classmethod
    def from_files(cls, ctx: moderngl.Context, vertex_path: str, fragment_path: str):
        """
        Load shader from files.

        Args:
            ctx: ModernGL context
            vertex_path: Path to vertex shader file
            fragment_path: Path to fragment shader file

        Raises:
            FileNotFoundError: If shader files don't exist
            IOError: If shader files can't be read
        """
        vertex_path_obj = Path(vertex_path)
        fragment_path_obj = Path(fragment_path)

        # Check if files exist
        if not vertex_path_obj.exists():
            raise FileNotFoundError(
                f"Vertex shader not found: {vertex_path}\n"
                f"Please ensure the shader file exists at the specified path."
            )
        if not fragment_path_obj.exists():
            raise FileNotFoundError(
                f"Fragment shader not found: {fragment_path}\n"
                f"Please ensure the shader file exists at the specified path."
            )

        try:
            vertex_source = vertex_path_obj.read_text()
            fragment_source = fragment_path_obj.read_text()
        except IOError as e:
            raise IOError(
                f"Failed to read shader files:\n"
                f"  Vertex: {vertex_path}\n"
                f"  Fragment: {fragment_path}\n"
                f"Error: {e}"
            )

        return cls(ctx, vertex_source, fragment_source)

    def __getitem__(self, name: str):
        """Get uniform location by name."""
        return self.program[name]

    def use(self):
        """Bind this shader program for rendering."""
        # ModernGL programs are automatically used when accessed
        pass

    def release(self):
        """Release shader resources."""
        self.program.release()
