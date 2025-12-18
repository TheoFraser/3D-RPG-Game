"""Camera system for 3D rendering."""
from typing import Optional
import glm
import math
import config
from engine.camera_shake import CameraShake


class Camera:
    """First-person camera with mouse look and WASD movement."""

    def __init__(self, position: Optional[glm.vec3] = None, yaw: float = -90.0, pitch: float = 0.0) -> None:
        """
        Initialize the camera.

        Args:
            position: Starting position (glm.vec3)
            yaw: Initial yaw angle in degrees
            pitch: Initial pitch angle in degrees
        """
        self.position = position or glm.vec3(0.0, 2.0, 5.0)
        self.yaw = yaw
        self.pitch = pitch

        # Camera vectors
        self.front = glm.vec3(0.0, 0.0, -1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.right = glm.vec3(1.0, 0.0, 0.0)
        self.world_up = glm.vec3(0.0, 1.0, 0.0)

        # Camera settings
        self.movement_speed = config.MOVEMENT_SPEED
        self.mouse_sensitivity = config.MOUSE_SENSITIVITY
        self.sprint_multiplier = config.SPRINT_MULTIPLIER

        # Projection settings
        self.fov = config.FOV
        self.near = config.NEAR_PLANE
        self.far = config.FAR_PLANE

        # Camera shake system
        self.shake = CameraShake()

        self.update_camera_vectors()

    def get_view_matrix(self) -> glm.mat4:
        """Get the view matrix for rendering with shake applied."""
        # Apply shake offset to position
        shake_offset = self.shake.get_shake_offset()
        shake_position = self.position + shake_offset

        # Apply shake rotation to view direction
        shake_rotation = self.shake.get_shake_rotation()
        shake_front = self.front

        if self.shake.is_shaking():
            # Apply pitch (X rotation)
            pitch_rad = glm.radians(shake_rotation.x)
            cos_pitch = math.cos(pitch_rad)
            sin_pitch = math.sin(pitch_rad)

            # Apply yaw (Y rotation)
            yaw_rad = glm.radians(shake_rotation.y)
            cos_yaw = math.cos(yaw_rad)
            sin_yaw = math.sin(yaw_rad)

            # Combine rotations (simplified)
            shake_front = glm.vec3(
                self.front.x + sin_yaw * 0.1,
                self.front.y + sin_pitch * 0.1,
                self.front.z
            )
            shake_front = glm.normalize(shake_front)

        return glm.lookAt(shake_position, shake_position + shake_front, self.up)

    def get_projection_matrix(self, aspect_ratio: float) -> glm.mat4:
        """Get the perspective projection matrix."""
        return glm.perspective(glm.radians(self.fov), aspect_ratio, self.near, self.far)

    def process_mouse_movement(self, xoffset: float, yoffset: float, constrain_pitch: bool = True) -> None:
        """
        Process mouse movement for camera rotation.

        Args:
            xoffset: Mouse movement in x direction
            yoffset: Mouse movement in y direction
            constrain_pitch: Whether to constrain pitch to prevent camera flipping
        """
        xoffset *= self.mouse_sensitivity
        yoffset *= self.mouse_sensitivity

        self.yaw += xoffset
        self.pitch += yoffset

        # Constrain pitch to prevent camera flipping
        if constrain_pitch:
            if self.pitch > 89.0:
                self.pitch = 89.0
            if self.pitch < -89.0:
                self.pitch = -89.0

        self.update_camera_vectors()

    def process_keyboard(self, direction: str, delta_time: float, sprinting: bool = False) -> None:
        """
        Process keyboard input for camera movement.

        Args:
            direction: Movement direction ('forward', 'backward', 'left', 'right', 'up', 'down')
            delta_time: Time since last frame
            sprinting: Whether sprint is active
        """
        velocity = self.movement_speed * delta_time
        if sprinting:
            velocity *= self.sprint_multiplier

        if direction == "forward":
            self.position += self.front * velocity
        elif direction == "backward":
            self.position -= self.front * velocity
        elif direction == "left":
            self.position -= self.right * velocity
        elif direction == "right":
            self.position += self.right * velocity
        elif direction == "up":
            self.position += self.world_up * velocity
        elif direction == "down":
            self.position -= self.world_up * velocity

    def update_camera_vectors(self) -> None:
        """Update camera direction vectors based on yaw and pitch."""
        # Calculate new front vector
        front = glm.vec3()
        front.x = math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        front.y = math.sin(glm.radians(self.pitch))
        front.z = math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        self.front = glm.normalize(front)

        # Recalculate right and up vectors
        self.right = glm.normalize(glm.cross(self.front, self.world_up))
        self.up = glm.normalize(glm.cross(self.right, self.front))
