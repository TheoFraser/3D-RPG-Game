"""Texture loading and management."""
import moderngl
from PIL import Image
import numpy as np
from pathlib import Path


class Texture:
    """Manages texture loading and binding."""

    def __init__(self, ctx: moderngl.Context, texture: moderngl.Texture):
        """
        Initialize texture wrapper.

        Args:
            ctx: ModernGL context
            texture: ModernGL texture object
        """
        self.ctx = ctx
        self.texture = texture
        self.texture.build_mipmaps()

    @classmethod
    def from_file(cls, ctx: moderngl.Context, path: str, flip=True):
        """
        Load texture from image file.

        Args:
            ctx: ModernGL context
            path: Path to image file
            flip: Whether to flip image vertically (OpenGL convention)

        Raises:
            FileNotFoundError: If texture file doesn't exist
            ValueError: If image format is unsupported
        """
        path_obj = Path(path)

        # Check if file exists
        if not path_obj.exists():
            raise FileNotFoundError(
                f"Texture file not found: {path}\n"
                f"Please ensure the texture file exists at the specified path."
            )

        try:
            img = Image.open(path).convert('RGBA')
        except (IOError, OSError) as e:
            raise ValueError(
                f"Failed to load texture: {path}\n"
                f"Error: {e}\n"
                f"Ensure the file is a valid image format (PNG, JPG, etc.)"
            )
        except Image.UnidentifiedImageError as e:
            raise ValueError(
                f"Invalid image format: {path}\n"
                f"Error: {e}\n"
                f"Ensure the file is a valid image format (PNG, JPG, etc.)"
            )

        if flip:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)

        texture = ctx.texture(img.size, 4, img.tobytes())
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        texture.anisotropy = 32.0  # Enable anisotropic filtering

        return cls(ctx, texture)

    @classmethod
    def from_array(cls, ctx: moderngl.Context, data: np.ndarray):
        """
        Create texture from numpy array.

        Args:
            ctx: ModernGL context
            data: Numpy array of shape (height, width, channels)
        """
        height, width = data.shape[:2]
        channels = data.shape[2] if len(data.shape) > 2 else 1

        # Ensure data is in the right format
        if data.dtype != np.uint8:
            data = (data * 255).astype(np.uint8)

        texture = ctx.texture((width, height), channels, data.tobytes())
        texture.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)

        return cls(ctx, texture)

    @classmethod
    def create_checkerboard(cls, ctx: moderngl.Context, size=256, tile_size=32):
        """
        Create a checkerboard texture procedurally.

        Args:
            ctx: ModernGL context
            size: Texture size in pixels
            tile_size: Size of each checkerboard tile
        """
        data = np.zeros((size, size, 3), dtype=np.uint8)

        for y in range(size):
            for x in range(size):
                # Determine if this pixel is in a white or black tile
                tile_x = (x // tile_size) % 2
                tile_y = (y // tile_size) % 2

                if tile_x == tile_y:
                    data[y, x] = [200, 200, 200]  # Light gray
                else:
                    data[y, x] = [100, 100, 100]  # Dark gray

        return cls.from_array(ctx, data)

    @classmethod
    def create_grid(cls, ctx: moderngl.Context, size=256, grid_size=32, line_width=2):
        """
        Create a grid texture procedurally.

        Args:
            ctx: ModernGL context
            size: Texture size in pixels
            grid_size: Size of each grid cell
            line_width: Width of grid lines in pixels
        """
        data = np.ones((size, size, 3), dtype=np.uint8) * 180  # Light background

        for y in range(size):
            for x in range(size):
                # Draw grid lines
                if (x % grid_size < line_width) or (y % grid_size < line_width):
                    data[y, x] = [60, 60, 60]  # Dark grid lines

        return cls.from_array(ctx, data)

    def use(self, location=0):
        """
        Bind texture to a texture unit.

        Args:
            location: Texture unit number (0-31)
        """
        self.texture.use(location)

    def release(self):
        """Release texture resources."""
        self.texture.release()
