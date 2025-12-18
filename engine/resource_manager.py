"""Resource manager for loading and caching game assets."""
from typing import Dict, Optional, Any
from pathlib import Path
import logging
import os
from graphics.shader import Shader
from graphics.texture import Texture
from graphics.mesh import Mesh
import pywavefront
import moderngl
import numpy as np

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Centralized asset loading and caching system.

    Implements reference counting and lazy loading for efficient
    memory management. Caches loaded assets to avoid redundant I/O.
    """

    def __init__(self, ctx: moderngl.Context, base_path: Optional[str] = None):
        """
        Initialize resource manager.

        Args:
            ctx: ModernGL rendering context
            base_path: Base directory for assets (defaults to current working directory)
        """
        self.ctx = ctx

        # Set and validate base path for security
        if base_path is None:
            self.base_path = Path.cwd()
        else:
            self.base_path = Path(base_path).resolve()

        logger.info(f"ResourceManager initialized with base path: {self.base_path}")

        # Asset caches
        self._shaders: Dict[str, Shader] = {}
        self._textures: Dict[str, Texture] = {}
        self._meshes: Dict[str, Mesh] = {}
        self._models: Dict[str, Any] = {}

        # Reference counting for cleanup
        self._shader_refs: Dict[str, int] = {}
        self._texture_refs: Dict[str, int] = {}
        self._mesh_refs: Dict[str, int] = {}
        self._model_refs: Dict[str, int] = {}

    def _validate_path(self, file_path: str) -> Path:
        """
        Validate that a file path is safe and within the base directory.

        Args:
            file_path: Path to validate

        Returns:
            Path: Resolved absolute path

        Raises:
            ValueError: If path attempts directory traversal or is outside base path
        """
        try:
            # Resolve the full path
            full_path = Path(file_path).resolve()

            # Check if the path is within base_path
            # This prevents directory traversal attacks like ../../../../etc/passwd
            try:
                full_path.relative_to(self.base_path)
            except ValueError:
                raise ValueError(
                    f"Security: Path '{file_path}' is outside allowed directory '{self.base_path}'"
                )

            return full_path

        except Exception as e:
            logger.error(f"Path validation failed for '{file_path}': {e}")
            raise

    def load_shader(self, name: str, vertex_path: str, fragment_path: str) -> Shader:
        """
        Load and cache a shader program.

        Args:
            name: Unique identifier for this shader
            vertex_path: Path to vertex shader
            fragment_path: Path to fragment shader

        Returns:
            Shader: Compiled shader program
        """
        if name in self._shaders:
            self._shader_refs[name] += 1
            logger.debug(f"Shader '{name}' found in cache (refs: {self._shader_refs[name]})")
            return self._shaders[name]

        logger.info(f"Loading shader '{name}' from {vertex_path}, {fragment_path}")

        try:
            # Validate paths for security
            validated_vertex = str(self._validate_path(vertex_path))
            validated_fragment = str(self._validate_path(fragment_path))

            shader = Shader.from_files(self.ctx, validated_vertex, validated_fragment)
            self._shaders[name] = shader
            self._shader_refs[name] = 1
            logger.info(f"Shader '{name}' loaded successfully")
            return shader
        except Exception as e:
            logger.error(f"Failed to load shader '{name}': {e}")
            logger.warning(f"Using fallback shader for '{name}'")
            # Return fallback shader instead of crashing
            fallback = self._get_fallback_shader()
            self._shaders[name] = fallback
            self._shader_refs[name] = 1
            return fallback

    def load_texture(self, name: str, path: str, flip: bool = True) -> Texture:
        """
        Load and cache a texture.

        Args:
            name: Unique identifier for this texture
            path: Path to texture file
            flip: Whether to flip vertically for OpenGL

        Returns:
            Texture: Loaded texture
        """
        if name in self._textures:
            self._texture_refs[name] += 1
            logger.debug(f"Texture '{name}' found in cache (refs: {self._texture_refs[name]})")
            return self._textures[name]

        logger.info(f"Loading texture '{name}' from {path}")

        try:
            # Validate path for security
            validated_path = str(self._validate_path(path))

            texture = Texture.from_file(self.ctx, validated_path, flip)
            self._textures[name] = texture
            self._texture_refs[name] = 1
            logger.info(f"Texture '{name}' loaded successfully")
            return texture
        except Exception as e:
            logger.error(f"Failed to load texture '{name}': {e}")
            raise

    def create_procedural_texture(self, name: str, texture_type: str, **kwargs) -> Texture:
        """
        Create and cache a procedural texture.

        Args:
            name: Unique identifier
            texture_type: Type ('checkerboard' or 'grid')
            **kwargs: Parameters for texture generation

        Returns:
            Texture: Generated texture
        """
        if name in self._textures:
            self._texture_refs[name] += 1
            return self._textures[name]

        logger.info(f"Creating procedural texture '{name}' (type: {texture_type})")

        if texture_type == 'checkerboard':
            texture = Texture.create_checkerboard(self.ctx, **kwargs)
        elif texture_type == 'grid':
            texture = Texture.create_grid(self.ctx, **kwargs)
        else:
            raise ValueError(f"Unknown procedural texture type: {texture_type}")

        self._textures[name] = texture
        self._texture_refs[name] = 1
        return texture

    def load_obj_model(self, name: str, path: str, shader: Shader) -> Dict[str, Mesh]:
        """
        Load OBJ model and create meshes.

        Args:
            name: Unique identifier for this model
            path: Path to OBJ file
            shader: Shader to use with this model

        Returns:
            Dict[str, Mesh]: Dictionary of mesh name to Mesh object
        """
        if name in self._models:
            self._model_refs[name] += 1
            logger.debug(f"Model '{name}' found in cache (refs: {self._model_refs[name]})")
            return self._models[name]

        logger.info(f"Loading OBJ model '{name}' from {path}")

        try:
            # Validate path for security
            validated_path = str(self._validate_path(path))

            # Load with PyWavefront
            scene = pywavefront.Wavefront(validated_path, collect_faces=True, create_materials=True)

            meshes = {}
            for mesh_name, mesh_data in scene.meshes.items():
                logger.debug(f"Processing mesh '{mesh_name}' from model '{name}'")

                # Get vertex data
                vertices = []
                indices = []

                # mesh_data.materials contains Material objects directly
                for material in mesh_data.materials:
                    # Extract vertex data (positions, texcoords, normals)
                    # PyWavefront format: [x, y, z, nx, ny, nz, u, v, ...]
                    vertex_format = material.vertex_format
                    vertex_data = np.array(material.vertices, dtype='f4')

                    # Build indices (simple sequential for now)
                    num_vertices = len(vertex_data) // len(vertex_format.split())
                    indices.extend(range(len(vertices), len(vertices) + num_vertices))

                    vertices.extend(vertex_data.tolist())

                # Create mesh
                if vertices and indices:
                    vertices_array = np.array(vertices, dtype='f4')
                    indices_array = np.array(indices, dtype='i4')

                    # PyWavefront uses T2F_N3F_V3F format: texcoord (2f) + normal (3f) + position (3f)
                    mesh = Mesh(
                        self.ctx,
                        vertices_array,
                        indices_array,
                        shader,
                        '2f 3f 3f',
                        ['in_texcoord', 'in_normal', 'in_position']
                    )

                    meshes[mesh_name] = mesh
                    logger.debug(f"Created mesh '{mesh_name}' with {len(indices)} indices")

            if not meshes:
                logger.warning(f"No meshes found in model '{name}'")

            self._models[name] = meshes
            self._model_refs[name] = 1
            logger.info(f"Model '{name}' loaded successfully with {len(meshes)} mesh(es)")
            return meshes

        except Exception as e:
            logger.error(f"Failed to load OBJ model '{name}': {e}")
            raise

    def get_shader(self, name: str) -> Optional[Shader]:
        """Get cached shader by name."""
        return self._shaders.get(name)

    def get_texture(self, name: str) -> Optional[Texture]:
        """Get cached texture by name."""
        return self._textures.get(name)

    def get_model(self, name: str) -> Optional[Dict[str, Mesh]]:
        """Get cached model by name."""
        return self._models.get(name)

    def release_shader(self, name: str) -> None:
        """
        Decrease reference count for shader.
        Releases GPU resources when count reaches 0.
        """
        if name not in self._shader_refs:
            logger.warning(f"Attempted to release unknown shader '{name}'")
            return

        self._shader_refs[name] -= 1

        if self._shader_refs[name] <= 0:
            logger.info(f"Releasing shader '{name}' (refs reached 0)")
            shader = self._shaders.pop(name)
            shader.release()
            del self._shader_refs[name]

    def release_texture(self, name: str) -> None:
        """
        Decrease reference count for texture.
        Releases GPU resources when count reaches 0.
        """
        if name not in self._texture_refs:
            logger.warning(f"Attempted to release unknown texture '{name}'")
            return

        self._texture_refs[name] -= 1

        if self._texture_refs[name] <= 0:
            logger.info(f"Releasing texture '{name}' (refs reached 0)")
            texture = self._textures.pop(name)
            texture.release()
            del self._texture_refs[name]

    def release_model(self, name: str) -> None:
        """
        Decrease reference count for model.
        Releases GPU resources when count reaches 0.
        """
        if name not in self._model_refs:
            logger.warning(f"Attempted to release unknown model '{name}'")
            return

        self._model_refs[name] -= 1

        if self._model_refs[name] <= 0:
            logger.info(f"Releasing model '{name}' (refs reached 0)")
            meshes = self._models.pop(name)
            for mesh in meshes.values():
                mesh.release()
            del self._model_refs[name]

    def clear_cache(self) -> None:
        """Release all cached resources."""
        logger.info("Clearing resource cache...")

        # Release all shaders
        for shader in self._shaders.values():
            shader.release()
        self._shaders.clear()
        self._shader_refs.clear()

        # Release all textures
        for texture in self._textures.values():
            texture.release()
        self._textures.clear()
        self._texture_refs.clear()

        # Release all models
        for meshes in self._models.values():
            for mesh in meshes.values():
                mesh.release()
        self._models.clear()
        self._model_refs.clear()

        logger.info("Resource cache cleared")

    def _get_fallback_shader(self):
        """
        Get a simple fallback shader for when shader loading fails.

        Returns:
            Shader: Simple fallback shader that renders with solid color
        """
        # Check if fallback already exists
        if '_fallback' in self._shaders:
            return self._shaders['_fallback']

        # Create simple fallback shader
        vertex_shader = """
        #version 330 core
        layout (location = 0) in vec3 in_position;
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        void main() {
            gl_Position = projection * view * model * vec4(in_position, 1.0);
        }
        """

        fragment_shader = """
        #version 330 core
        out vec4 FragColor;
        void main() {
            FragColor = vec4(1.0, 0.0, 1.0, 1.0);  // Magenta to indicate missing shader
        }
        """

        try:
            from graphics.shader import Shader
            fallback = Shader(self.ctx, vertex_shader, fragment_shader)
            self._shaders['_fallback'] = fallback
            logger.info("Created fallback shader")
            return fallback
        except Exception as e:
            logger.critical(f"Failed to create fallback shader: {e}")
            raise  # This is critical - if fallback fails, we must crash

    def get_stats(self) -> Dict[str, int]:
        """Get resource manager statistics."""
        return {
            'shaders_loaded': len(self._shaders),
            'textures_loaded': len(self._textures),
            'models_loaded': len(self._models),
            'total_shader_refs': sum(self._shader_refs.values()),
            'total_texture_refs': sum(self._texture_refs.values()),
            'total_model_refs': sum(self._model_refs.values()),
        }

    def __str__(self) -> str:
        """String representation of resource manager state."""
        stats = self.get_stats()
        return (
            f"ResourceManager("
            f"shaders={stats['shaders_loaded']}, "
            f"textures={stats['textures_loaded']}, "
            f"models={stats['models_loaded']})"
        )

    def __enter__(self):
        """Enter context manager - return self for use in 'with' statements."""
        logger.debug("ResourceManager context entered")
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
        logger.debug("ResourceManager context exiting - cleaning up resources")
        try:
            self.clear_cache()
        except Exception as e:
            logger.error(f"Error during ResourceManager cleanup: {e}", exc_info=True)
        return False  # Don't suppress exceptions
