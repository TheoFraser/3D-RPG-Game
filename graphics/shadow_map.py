"""Shadow mapping system for 3D game engine."""
import moderngl
import glm
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ShadowMap:
    """
    Shadow map for directional/point light shadows.

    Renders scene from light's perspective to a depth texture,
    which is then sampled during main rendering to determine shadows.
    """

    def __init__(self, ctx: moderngl.Context, resolution: int = 2048):
        """
        Initialize shadow map.

        Args:
            ctx: ModernGL context
            resolution: Shadow map resolution (power of 2, typically 1024-4096)
        """
        self.ctx = ctx
        self.resolution = resolution

        # Create depth texture for shadow map
        self.depth_texture = ctx.depth_texture((resolution, resolution))
        self.depth_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.depth_texture.compare_func = ''  # Disable comparison for manual sampling

        # Create framebuffer with depth attachment
        self.framebuffer = ctx.framebuffer(
            depth_attachment=self.depth_texture
        )

        # Light space matrices
        self.light_projection = glm.mat4(1.0)
        self.light_view = glm.mat4(1.0)
        self.light_space_matrix = glm.mat4(1.0)

        logger.info(f"Shadow map created: {resolution}x{resolution}")

    def setup_directional_light(self, light_direction: glm.vec3,
                                scene_center: glm.vec3 = glm.vec3(0, 0, 0),
                                scene_radius: float = 50.0) -> None:
        """
        Setup shadow map for directional light (sun/moon).

        Creates an orthographic projection that covers the scene.

        Args:
            light_direction: Direction of light (normalized)
            scene_center: Center of scene to cover
            scene_radius: Radius of scene to cover
        """
        # Create orthographic projection to cover scene
        # Use larger frustum to avoid edge clipping
        frustum_size = scene_radius * 1.5
        self.light_projection = glm.ortho(
            -frustum_size, frustum_size,  # left, right
            -frustum_size, frustum_size,  # bottom, top
            0.1, frustum_size * 3.0       # near, far
        )

        # Position light to look at scene center
        light_pos = scene_center - glm.normalize(light_direction) * frustum_size * 1.5
        self.light_view = glm.lookAt(
            light_pos,                    # eye
            scene_center,                 # center
            glm.vec3(0, 1, 0)            # up
        )

        # Combine into light space matrix
        self.light_space_matrix = self.light_projection * self.light_view

    def setup_point_light(self, light_position: glm.vec3, far_plane: float = 100.0) -> None:
        """
        Setup shadow map for point light (for cube shadow maps).

        Note: Basic point light shadows require 6 shadow maps (cube map).
        This is simplified - for full implementation, use cube map FBO.

        Args:
            light_position: Position of point light
            far_plane: Far plane distance
        """
        # Perspective projection for point light
        self.light_projection = glm.perspective(glm.radians(90.0), 1.0, 0.1, far_plane)

        # Look down -Z for simplified point shadows
        # (Full implementation would render 6 faces)
        self.light_view = glm.lookAt(
            light_position,
            light_position + glm.vec3(0, 0, -1),
            glm.vec3(0, 1, 0)
        )

        self.light_space_matrix = self.light_projection * self.light_view

    def begin_render(self) -> None:
        """
        Begin shadow map rendering pass.

        Binds shadow map framebuffer and clears depth buffer.
        Call this before rendering scene from light's perspective.
        """
        self.framebuffer.use()
        self.ctx.clear(depth=1.0)
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Set viewport to shadow map resolution
        self.ctx.viewport = (0, 0, self.resolution, self.resolution)

    def end_render(self) -> None:
        """
        End shadow map rendering pass.

        Releases framebuffer (return to screen).
        """
        # Framebuffer will be released when screen FBO is bound
        pass

    def bind_for_sampling(self, texture_unit: int = 1) -> None:
        """
        Bind shadow map texture for sampling in shaders.

        Args:
            texture_unit: Texture unit to bind to (default: 1, since 0 is usually base texture)
        """
        self.depth_texture.use(texture_unit)

    def get_light_space_matrix(self) -> glm.mat4:
        """Get combined light space transformation matrix."""
        return self.light_space_matrix

    def get_bias_matrix(self) -> glm.mat4:
        """
        Get bias matrix to transform clip space [-1,1] to texture space [0,1].

        Returns:
            4x4 bias matrix
        """
        return glm.mat4(
            0.5, 0.0, 0.0, 0.0,
            0.0, 0.5, 0.0, 0.0,
            0.0, 0.0, 0.5, 0.0,
            0.5, 0.5, 0.5, 1.0
        )

    def release(self) -> None:
        """Release OpenGL resources."""
        if self.framebuffer:
            self.framebuffer.release()
        if self.depth_texture:
            self.depth_texture.release()
        logger.info("Shadow map released")

    def __str__(self) -> str:
        """String representation."""
        return f"ShadowMap(resolution={self.resolution}x{self.resolution})"


class ShadowMapManager:
    """
    Manages multiple shadow maps for different lights.

    Handles shadow map creation, rendering, and binding.
    """

    def __init__(self, ctx: moderngl.Context, max_shadow_maps: int = 4):
        """
        Initialize shadow map manager.

        Args:
            ctx: ModernGL context
            max_shadow_maps: Maximum number of shadow-casting lights
        """
        self.ctx = ctx
        self.max_shadow_maps = max_shadow_maps
        self.shadow_maps = {}  # name -> ShadowMap

        logger.info(f"ShadowMapManager initialized (max: {max_shadow_maps})")

    def create_shadow_map(self, name: str, resolution: int = 2048) -> ShadowMap:
        """
        Create a new shadow map.

        Args:
            name: Identifier for this shadow map
            resolution: Shadow map resolution

        Returns:
            Created ShadowMap instance
        """
        if name in self.shadow_maps:
            logger.warning(f"Shadow map '{name}' already exists, returning existing")
            return self.shadow_maps[name]

        if len(self.shadow_maps) >= self.max_shadow_maps:
            logger.error(f"Maximum shadow maps ({self.max_shadow_maps}) reached")
            raise RuntimeError("Too many shadow maps")

        shadow_map = ShadowMap(self.ctx, resolution)
        self.shadow_maps[name] = shadow_map
        logger.info(f"Created shadow map '{name}': {shadow_map}")

        return shadow_map

    def get_shadow_map(self, name: str) -> Optional[ShadowMap]:
        """
        Get shadow map by name.

        Args:
            name: Shadow map identifier

        Returns:
            ShadowMap instance or None if not found
        """
        return self.shadow_maps.get(name)

    def remove_shadow_map(self, name: str) -> None:
        """
        Remove and release a shadow map.

        Args:
            name: Shadow map identifier
        """
        if name in self.shadow_maps:
            self.shadow_maps[name].release()
            del self.shadow_maps[name]
            logger.info(f"Removed shadow map '{name}'")

    def clear_all(self) -> None:
        """Release all shadow maps."""
        for shadow_map in self.shadow_maps.values():
            shadow_map.release()
        self.shadow_maps.clear()
        logger.info("All shadow maps cleared")

    def __str__(self) -> str:
        """String representation."""
        return f"ShadowMapManager({len(self.shadow_maps)}/{self.max_shadow_maps} maps)"
