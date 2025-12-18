"""Lighting system for 3D game engine."""
import glm
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Light:
    """Base class for all light types."""

    color: glm.vec3 = glm.vec3(1.0, 1.0, 1.0)  # White light by default
    intensity: float = 1.0

    def get_shader_data(self) -> dict:
        """Get light data to upload to shader."""
        raise NotImplementedError


@dataclass
class DirectionalLight(Light):
    """
    Directional light (sun, moon).

    Parallel rays from a direction at infinity.
    Best for simulating sun/moon lighting.
    """

    direction: glm.vec3 = glm.vec3(-0.3, -1.0, -0.3)  # Down and slightly angled

    def __post_init__(self):
        """Normalize direction vector."""
        self.direction = glm.normalize(self.direction)

    def get_shader_data(self) -> dict:
        """Get directional light data for shader."""
        return {
            'type': 0,  # Directional = 0
            'direction': self.direction,
            'color': self.color * self.intensity,
            'intensity': self.intensity
        }


@dataclass
class PointLight(Light):
    """
    Point light (torch, lamp, light bulb).

    Emits light in all directions from a point.
    Has distance-based attenuation.
    """

    position: glm.vec3 = glm.vec3(0.0, 0.0, 0.0)

    # Attenuation coefficients (constant, linear, quadratic)
    # For realistic falloff, use: constant=1.0, linear=0.09, quadratic=0.032 (range ~50 units)
    constant: float = 1.0
    linear: float = 0.09
    quadratic: float = 0.032

    def get_shader_data(self) -> dict:
        """Get point light data for shader."""
        return {
            'type': 1,  # Point = 1
            'position': self.position,
            'color': self.color * self.intensity,
            'intensity': self.intensity,
            'constant': self.constant,
            'linear': self.linear,
            'quadratic': self.quadratic
        }

    def get_effective_range(self) -> float:
        """Calculate effective range where light intensity > 0.01."""
        # Solve: intensity / (c + l*d + q*d^2) = 0.01
        # Approximate range calculation
        import math
        if self.quadratic > 0:
            range_val = (-self.linear + math.sqrt(
                self.linear**2 + 4 * self.quadratic * (self.intensity / 0.01 - self.constant)
            )) / (2 * self.quadratic)
            return max(0, range_val)
        elif self.linear > 0:
            return (self.intensity / 0.01 - self.constant) / self.linear
        else:
            return float('inf')


@dataclass
class SpotLight(Light):
    """
    Spot light (flashlight, searchlight).

    Emits light in a cone from a point.
    Has direction, cutoff angle, and attenuation.
    """

    position: glm.vec3 = glm.vec3(0.0, 0.0, 0.0)
    direction: glm.vec3 = glm.vec3(0.0, -1.0, 0.0)  # Pointing down

    # Cutoff angles in degrees
    inner_cutoff: float = 12.5  # Full brightness cone
    outer_cutoff: float = 17.5  # Edge falloff cone

    # Attenuation (same as point light)
    constant: float = 1.0
    linear: float = 0.09
    quadratic: float = 0.032

    def __post_init__(self):
        """Normalize direction and convert angles to cosines."""
        self.direction = glm.normalize(self.direction)
        import math
        self.inner_cutoff_cos = math.cos(math.radians(self.inner_cutoff))
        self.outer_cutoff_cos = math.cos(math.radians(self.outer_cutoff))

    def get_shader_data(self) -> dict:
        """Get spot light data for shader."""
        return {
            'type': 2,  # Spot = 2
            'position': self.position,
            'direction': self.direction,
            'color': self.color * self.intensity,
            'intensity': self.intensity,
            'constant': self.constant,
            'linear': self.linear,
            'quadratic': self.quadratic,
            'inner_cutoff': self.inner_cutoff_cos,
            'outer_cutoff': self.outer_cutoff_cos
        }


class LightManager:
    """
    Manages all lights in the scene.

    Handles:
    - Adding/removing lights
    - Culling lights outside view frustum
    - Sorting lights by importance
    - Uploading light data to shaders
    """

    def __init__(self, max_lights: int = 8):
        """
        Initialize light manager.

        Args:
            max_lights: Maximum number of lights per shader (default: 8)
        """
        self.max_lights = max_lights

        # Light storage
        self.directional_lights: List[DirectionalLight] = []
        self.point_lights: List[PointLight] = []
        self.spot_lights: List[SpotLight] = []

        # Global ambient light (simulates indirect lighting)
        self.ambient_color = glm.vec3(0.2, 0.2, 0.25)  # Slightly blue ambient
        self.ambient_intensity = 0.3

    def add_directional_light(self, light: DirectionalLight) -> None:
        """Add a directional light to the scene."""
        if light not in self.directional_lights:
            self.directional_lights.append(light)

    def add_point_light(self, light: PointLight) -> None:
        """Add a point light to the scene."""
        if light not in self.point_lights:
            self.point_lights.append(light)

    def add_spot_light(self, light: SpotLight) -> None:
        """Add a spot light to the scene."""
        if light not in self.spot_lights:
            self.spot_lights.append(light)

    def remove_light(self, light: Light) -> None:
        """Remove a light from the scene."""
        if isinstance(light, DirectionalLight):
            self.directional_lights.remove(light)
        elif isinstance(light, PointLight):
            self.point_lights.remove(light)
        elif isinstance(light, SpotLight):
            self.spot_lights.remove(light)

    def clear_lights(self) -> None:
        """Remove all lights from the scene."""
        self.directional_lights.clear()
        self.point_lights.clear()
        self.spot_lights.clear()

    def get_active_lights(self, camera_pos: Optional[glm.vec3] = None,
                         max_distance: float = 100.0) -> List[Light]:
        """
        Get list of active lights, sorted by importance.

        Args:
            camera_pos: Camera position for distance culling
            max_distance: Maximum distance for point/spot lights

        Returns:
            List of lights (directional always included, point/spot sorted by distance)
        """
        active_lights = []

        # Always include directional lights
        active_lights.extend(self.directional_lights)

        # Add point lights (sorted by distance if camera_pos provided)
        if camera_pos is not None:
            # Sort point lights by distance to camera
            sorted_point = sorted(
                self.point_lights,
                key=lambda l: glm.length(l.position - camera_pos)
            )
            # Include lights within range
            for light in sorted_point:
                if glm.length(light.position - camera_pos) <= max_distance:
                    active_lights.append(light)
                    if len(active_lights) >= self.max_lights:
                        break
        else:
            active_lights.extend(self.point_lights[:self.max_lights - len(active_lights)])

        # Add spot lights (sorted by distance if camera_pos provided)
        if len(active_lights) < self.max_lights:
            if camera_pos is not None:
                sorted_spot = sorted(
                    self.spot_lights,
                    key=lambda l: glm.length(l.position - camera_pos)
                )
                for light in sorted_spot:
                    if glm.length(light.position - camera_pos) <= max_distance:
                        active_lights.append(light)
                        if len(active_lights) >= self.max_lights:
                            break
            else:
                remaining = self.max_lights - len(active_lights)
                active_lights.extend(self.spot_lights[:remaining])

        return active_lights[:self.max_lights]

    def get_light_count(self) -> int:
        """Get total number of lights in the scene."""
        return (len(self.directional_lights) +
                len(self.point_lights) +
                len(self.spot_lights))

    def upload_to_shader(self, shader_program, camera_pos: Optional[glm.vec3] = None) -> None:
        """
        Upload light data to shader uniforms.

        Args:
            shader_program: ModernGL shader program
            camera_pos: Camera position for light culling
        """
        # Get active lights
        active_lights = self.get_active_lights(camera_pos)

        # Upload ambient light
        if 'ambient_color' in shader_program:
            shader_program['ambient_color'].write(
                self.ambient_color * self.ambient_intensity
            )

        # Upload number of lights
        if 'num_lights' in shader_program:
            shader_program['num_lights'] = len(active_lights)

        # Upload individual light data
        for i, light in enumerate(active_lights):
            prefix = f'lights[{i}]'
            light_data = light.get_shader_data()

            # Upload light type
            if f'{prefix}.type' in shader_program:
                shader_program[f'{prefix}.type'] = light_data['type']

            # Upload common properties
            if f'{prefix}.color' in shader_program:
                shader_program[f'{prefix}.color'].write(light_data['color'])

            # Upload type-specific properties
            if isinstance(light, DirectionalLight):
                if f'{prefix}.direction' in shader_program:
                    shader_program[f'{prefix}.direction'].write(light_data['direction'])

            elif isinstance(light, (PointLight, SpotLight)):
                if f'{prefix}.position' in shader_program:
                    shader_program[f'{prefix}.position'].write(light_data['position'])
                if f'{prefix}.constant' in shader_program:
                    shader_program[f'{prefix}.constant'] = light_data['constant']
                if f'{prefix}.linear' in shader_program:
                    shader_program[f'{prefix}.linear'] = light_data['linear']
                if f'{prefix}.quadratic' in shader_program:
                    shader_program[f'{prefix}.quadratic'] = light_data['quadratic']

                if isinstance(light, SpotLight):
                    if f'{prefix}.direction' in shader_program:
                        shader_program[f'{prefix}.direction'].write(light_data['direction'])
                    if f'{prefix}.inner_cutoff' in shader_program:
                        shader_program[f'{prefix}.inner_cutoff'] = light_data['inner_cutoff']
                    if f'{prefix}.outer_cutoff' in shader_program:
                        shader_program[f'{prefix}.outer_cutoff'] = light_data['outer_cutoff']

    def __str__(self) -> str:
        """String representation of light manager."""
        return (f"LightManager("
                f"directional={len(self.directional_lights)}, "
                f"point={len(self.point_lights)}, "
                f"spot={len(self.spot_lights)})")
