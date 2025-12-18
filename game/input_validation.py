"""Input validation utilities for the game."""
from pathlib import Path
from typing import Any, Optional, Union
from game.logger import get_logger

logger = get_logger(__name__)


class ValidationError(ValueError):
    """Exception raised when validation fails."""
    pass


def validate_file_path(path: Union[str, Path], must_exist: bool = False,
                       allowed_extensions: Optional[list] = None) -> Path:
    """
    Validate a file path.

    Args:
        path: Path to validate
        must_exist: If True, path must exist
        allowed_extensions: List of allowed file extensions (e.g., ['.json', '.txt'])

    Returns:
        Validated Path object

    Raises:
        ValidationError: If validation fails
    """
    if not path:
        raise ValidationError("Path cannot be empty")

    try:
        path_obj = Path(path)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid path format: {e}")

    # Check for path traversal attempts
    try:
        path_obj.resolve()
    except (OSError, RuntimeError) as e:
        raise ValidationError(f"Path resolution failed: {e}")

    # Check if file exists if required
    if must_exist and not path_obj.exists():
        raise ValidationError(f"Path does not exist: {path}")

    # Check file extension
    if allowed_extensions and path_obj.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
        raise ValidationError(
            f"Invalid file extension '{path_obj.suffix}'. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    return path_obj


def validate_numeric_range(value: Union[int, float], min_value: Optional[Union[int, float]] = None,
                           max_value: Optional[Union[int, float]] = None,
                           name: str = "value") -> Union[int, float]:
    """
    Validate a numeric value is within a range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        name: Name of the value for error messages

    Returns:
        Validated value

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")

    if min_value is not None and value < min_value:
        raise ValidationError(f"{name} must be >= {min_value}, got {value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"{name} must be <= {max_value}, got {value}")

    return value


def validate_string(value: Any, min_length: int = 0, max_length: Optional[int] = None,
                   allowed_chars: Optional[str] = None, name: str = "string") -> str:
    """
    Validate a string value.

    Args:
        value: Value to validate
        min_length: Minimum string length
        max_length: Maximum string length
        allowed_chars: String of allowed characters (if None, all chars allowed)
        name: Name of the value for error messages

    Returns:
        Validated string

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string, got {type(value).__name__}")

    if len(value) < min_length:
        raise ValidationError(f"{name} must be at least {min_length} characters, got {len(value)}")

    if max_length and len(value) > max_length:
        raise ValidationError(f"{name} must be at most {max_length} characters, got {len(value)}")

    if allowed_chars:
        invalid_chars = set(value) - set(allowed_chars)
        if invalid_chars:
            raise ValidationError(
                f"{name} contains invalid characters: {', '.join(sorted(invalid_chars))}"
            )

    return value


def validate_slot_number(slot: int) -> int:
    """
    Validate a save slot number.

    Args:
        slot: Slot number to validate

    Returns:
        Validated slot number

    Raises:
        ValidationError: If slot is invalid
    """
    if not isinstance(slot, int):
        raise ValidationError(f"Slot must be an integer, got {type(slot).__name__}")

    if slot < 1 or slot > 5:
        raise ValidationError(f"Slot must be between 1 and 5, got {slot}")

    return slot


def validate_coordinates(x: Union[int, float], z: Union[int, float],
                        world_size: int = 2000) -> tuple[float, float]:
    """
    Validate world coordinates.

    Args:
        x: X coordinate
        z: Z coordinate
        world_size: Size of the world (coordinates must be within ±world_size/2)

    Returns:
        Tuple of validated (x, z) coordinates

    Raises:
        ValidationError: If coordinates are invalid
    """
    if not isinstance(x, (int, float)):
        raise ValidationError(f"X coordinate must be numeric, got {type(x).__name__}")

    if not isinstance(z, (int, float)):
        raise ValidationError(f"Z coordinate must be numeric, got {type(z).__name__}")

    half_world = world_size / 2
    if abs(x) > half_world or abs(z) > half_world:
        raise ValidationError(
            f"Coordinates ({x}, {z}) outside world bounds (±{half_world})"
        )

    return float(x), float(z)


def validate_color(color: tuple) -> tuple:
    """
    Validate an RGB(A) color tuple.

    Args:
        color: Color tuple (3 or 4 values between 0 and 1)

    Returns:
        Validated color tuple

    Raises:
        ValidationError: If color is invalid
    """
    if not isinstance(color, (tuple, list)):
        raise ValidationError(f"Color must be a tuple/list, got {type(color).__name__}")

    if len(color) not in (3, 4):
        raise ValidationError(f"Color must have 3 or 4 components, got {len(color)}")

    for i, component in enumerate(color):
        if not isinstance(component, (int, float)):
            raise ValidationError(
                f"Color component {i} must be numeric, got {type(component).__name__}"
            )
        if not (0.0 <= component <= 1.0):
            raise ValidationError(
                f"Color component {i} must be between 0 and 1, got {component}"
            )

    return tuple(color)


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename by removing invalid characters.

    Args:
        filename: Filename to sanitize
        max_length: Maximum filename length

    Returns:
        Sanitized filename

    Raises:
        ValidationError: If filename is empty after sanitization
    """
    if not isinstance(filename, str):
        raise ValidationError(f"Filename must be a string, got {type(filename).__name__}")

    # Remove invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    sanitized = ''.join(c for c in filename if c not in invalid_chars)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')

    # Truncate if too long
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        sanitized = f"{name[:max_name_length]}.{ext}" if ext else name[:max_length]

    if not sanitized:
        raise ValidationError("Filename is empty after sanitization")

    return sanitized
