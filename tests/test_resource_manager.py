"""Unit tests for ResourceManager."""
import unittest
import moderngl
import tempfile
import os
from engine.resource_manager import ResourceManager


class TestResourceManager(unittest.TestCase):
    """Test ResourceManager asset loading and caching."""

    @classmethod
    def setUpClass(cls):
        """Create a ModernGL context for all tests."""
        cls.ctx = moderngl.create_standalone_context()

    @classmethod
    def tearDownClass(cls):
        """Release the ModernGL context."""
        cls.ctx.release()

    def setUp(self):
        """Create a fresh ResourceManager for each test."""
        self.resource_manager = ResourceManager(self.ctx)

    def tearDown(self):
        """Clean up resources after each test."""
        self.resource_manager.clear_cache()

    def test_resource_manager_initialization(self):
        """Test ResourceManager initializes correctly."""
        self.assertIsNotNone(self.resource_manager)
        self.assertEqual(self.resource_manager.ctx, self.ctx)
        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['shaders_loaded'], 0)
        self.assertEqual(stats['textures_loaded'], 0)
        self.assertEqual(stats['models_loaded'], 0)

    def test_load_shader_caching(self):
        """Test shader loading and caching."""
        # Create temporary shader files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ResourceManager with temp directory as base path for testing
            test_resource_manager = ResourceManager(self.ctx, base_path=tmpdir)

            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            # Write minimal valid shaders
            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec3 in_position;
void main() {
    gl_Position = vec4(in_position, 1.0);
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            # Load shader first time
            shader1 = test_resource_manager.load_shader("test_shader", vertex_path, fragment_path)
            self.assertIsNotNone(shader1)

            # Verify it's cached
            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['shaders_loaded'], 1)
            self.assertEqual(stats['total_shader_refs'], 1)

            # Load same shader again - should return cached version
            shader2 = test_resource_manager.load_shader("test_shader", vertex_path, fragment_path)
            self.assertIs(shader1, shader2, "Should return same cached shader instance")

            # Verify reference count increased
            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['shaders_loaded'], 1)
            self.assertEqual(stats['total_shader_refs'], 2)

    def test_get_cached_shader(self):
        """Test retrieving cached shader by name."""
        # Create temporary shader files
        with tempfile.TemporaryDirectory() as tmpdir:
            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec3 in_position;
void main() {
    gl_Position = vec4(in_position, 1.0);
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            # Load shader
            shader = self.resource_manager.load_shader("test_shader", vertex_path, fragment_path)

            # Get cached shader
            cached_shader = self.resource_manager.get_shader("test_shader")
            self.assertIs(shader, cached_shader)

            # Try to get non-existent shader
            missing_shader = self.resource_manager.get_shader("nonexistent")
            self.assertIsNone(missing_shader)

    def test_create_procedural_texture_checkerboard(self):
        """Test creating procedural checkerboard texture."""
        texture = self.resource_manager.create_procedural_texture(
            "test_checkerboard", "checkerboard", size=256, tile_size=32
        )
        self.assertIsNotNone(texture)

        # Verify it's cached
        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['textures_loaded'], 1)
        self.assertEqual(stats['total_texture_refs'], 1)

        # Request same texture again
        texture2 = self.resource_manager.create_procedural_texture(
            "test_checkerboard", "checkerboard", size=256, tile_size=32
        )
        self.assertIs(texture, texture2)

        # Verify reference count increased
        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['textures_loaded'], 1)
        self.assertEqual(stats['total_texture_refs'], 2)

    def test_create_procedural_texture_grid(self):
        """Test creating procedural grid texture."""
        texture = self.resource_manager.create_procedural_texture(
            "test_grid", "grid", size=512, grid_size=64, line_width=3
        )
        self.assertIsNotNone(texture)

        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['textures_loaded'], 1)

    def test_create_procedural_texture_invalid_type(self):
        """Test creating procedural texture with invalid type raises error."""
        with self.assertRaises(ValueError):
            self.resource_manager.create_procedural_texture(
                "invalid", "invalid_type"
            )

    def test_get_cached_texture(self):
        """Test retrieving cached texture by name."""
        texture = self.resource_manager.create_procedural_texture(
            "test_texture", "checkerboard", size=128
        )

        cached_texture = self.resource_manager.get_texture("test_texture")
        self.assertIs(texture, cached_texture)

        missing_texture = self.resource_manager.get_texture("nonexistent")
        self.assertIsNone(missing_texture)

    def test_release_shader(self):
        """Test shader reference counting and release."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ResourceManager with temp directory as base path for testing
            test_resource_manager = ResourceManager(self.ctx, base_path=tmpdir)

            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec3 in_position;
void main() {
    gl_Position = vec4(in_position, 1.0);
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            # Load shader twice (ref count = 2)
            test_resource_manager.load_shader("test_shader", vertex_path, fragment_path)
            test_resource_manager.load_shader("test_shader", vertex_path, fragment_path)

            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['total_shader_refs'], 2)

            # Release once (ref count = 1)
            test_resource_manager.release_shader("test_shader")
            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['total_shader_refs'], 1)
            self.assertEqual(stats['shaders_loaded'], 1)

            # Release again (ref count = 0, should be removed)
            test_resource_manager.release_shader("test_shader")
            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['total_shader_refs'], 0)
            self.assertEqual(stats['shaders_loaded'], 0)

    def test_release_texture(self):
        """Test texture reference counting and release."""
        # Load texture twice (ref count = 2)
        self.resource_manager.create_procedural_texture("test_texture", "checkerboard")
        self.resource_manager.create_procedural_texture("test_texture", "checkerboard")

        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['total_texture_refs'], 2)

        # Release once (ref count = 1)
        self.resource_manager.release_texture("test_texture")
        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['total_texture_refs'], 1)

        # Release again (ref count = 0, should be removed)
        self.resource_manager.release_texture("test_texture")
        stats = self.resource_manager.get_stats()
        self.assertEqual(stats['total_texture_refs'], 0)
        self.assertEqual(stats['textures_loaded'], 0)

    def test_clear_cache(self):
        """Test clearing all cached resources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ResourceManager with temp directory as base path for testing
            test_resource_manager = ResourceManager(self.ctx, base_path=tmpdir)

            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec3 in_position;
void main() {
    gl_Position = vec4(in_position, 1.0);
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            # Load some resources
            test_resource_manager.load_shader("test_shader", vertex_path, fragment_path)
            test_resource_manager.create_procedural_texture("test_texture", "checkerboard")

            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['shaders_loaded'], 1)
            self.assertEqual(stats['textures_loaded'], 1)

            # Clear cache
            test_resource_manager.clear_cache()

            # Verify all resources released
            stats = test_resource_manager.get_stats()
            self.assertEqual(stats['shaders_loaded'], 0)
            self.assertEqual(stats['textures_loaded'], 0)
            self.assertEqual(stats['models_loaded'], 0)
            self.assertEqual(stats['total_shader_refs'], 0)
            self.assertEqual(stats['total_texture_refs'], 0)
            self.assertEqual(stats['total_model_refs'], 0)

    def test_get_stats(self):
        """Test get_stats returns correct information."""
        stats = self.resource_manager.get_stats()

        # Check all expected keys exist
        self.assertIn('shaders_loaded', stats)
        self.assertIn('textures_loaded', stats)
        self.assertIn('models_loaded', stats)
        self.assertIn('total_shader_refs', stats)
        self.assertIn('total_texture_refs', stats)
        self.assertIn('total_model_refs', stats)

        # All should be 0 initially
        self.assertEqual(stats['shaders_loaded'], 0)
        self.assertEqual(stats['textures_loaded'], 0)
        self.assertEqual(stats['models_loaded'], 0)

    def test_string_representation(self):
        """Test string representation of ResourceManager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create ResourceManager with temp directory as base path for testing
            test_resource_manager = ResourceManager(self.ctx, base_path=tmpdir)

            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec3 in_position;
void main() {
    gl_Position = vec4(in_position, 1.0);
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            test_resource_manager.load_shader("test_shader", vertex_path, fragment_path)
            test_resource_manager.create_procedural_texture("test_texture", "checkerboard")

            str_repr = str(test_resource_manager)
            self.assertIn("ResourceManager", str_repr)
            self.assertIn("shaders=1", str_repr)
            self.assertIn("textures=1", str_repr)
            self.assertIn("models=0", str_repr)

    @unittest.skip("OBJ loading needs integration testing with real game shaders")
    def test_load_obj_model(self):
        """Test loading OBJ model from file."""
        # Create shader for the model
        with tempfile.TemporaryDirectory() as tmpdir:
            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec2 in_texcoord;
in vec3 in_normal;
in vec3 in_position;
out vec2 frag_texcoord;
out vec3 frag_normal;
void main() {
    gl_Position = vec4(in_position, 1.0);
    frag_texcoord = in_texcoord;
    frag_normal = in_normal;
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
in vec2 frag_texcoord;
in vec3 frag_normal;
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            shader = self.resource_manager.load_shader("model_shader", vertex_path, fragment_path)

            # Load the test cube model
            model_path = os.path.join(os.path.dirname(__file__), "..", "assets", "models", "test_cube.obj")
            model_path = os.path.normpath(model_path)

            if os.path.exists(model_path):
                meshes = self.resource_manager.load_obj_model("test_cube", model_path, shader)

                # Verify model was loaded
                self.assertIsNotNone(meshes)
                self.assertIsInstance(meshes, dict)
                self.assertGreater(len(meshes), 0, "Model should have at least one mesh")

                # Verify it's cached
                stats = self.resource_manager.get_stats()
                self.assertEqual(stats['models_loaded'], 1)
                self.assertEqual(stats['total_model_refs'], 1)

                # Load same model again - should return cached version
                meshes2 = self.resource_manager.load_obj_model("test_cube", model_path, shader)
                self.assertIs(meshes, meshes2)

                # Verify reference count increased
                stats = self.resource_manager.get_stats()
                self.assertEqual(stats['models_loaded'], 1)
                self.assertEqual(stats['total_model_refs'], 2)
            else:
                self.skipTest(f"Test model not found at {model_path}")

    @unittest.skip("OBJ loading needs integration testing with real game shaders")
    def test_get_cached_model(self):
        """Test retrieving cached model by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec2 in_texcoord;
in vec3 in_normal;
in vec3 in_position;
out vec2 frag_texcoord;
out vec3 frag_normal;
void main() {
    gl_Position = vec4(in_position, 1.0);
    frag_texcoord = in_texcoord;
    frag_normal = in_normal;
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
in vec2 frag_texcoord;
in vec3 frag_normal;
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            shader = self.resource_manager.load_shader("model_shader", vertex_path, fragment_path)

            model_path = os.path.join(os.path.dirname(__file__), "..", "assets", "models", "test_cube.obj")
            model_path = os.path.normpath(model_path)

            if os.path.exists(model_path):
                # Load model
                meshes = self.resource_manager.load_obj_model("test_cube", model_path, shader)

                # Get cached model
                cached_model = self.resource_manager.get_model("test_cube")
                self.assertIs(meshes, cached_model)

                # Try to get non-existent model
                missing_model = self.resource_manager.get_model("nonexistent")
                self.assertIsNone(missing_model)
            else:
                self.skipTest(f"Test model not found at {model_path}")

    @unittest.skip("OBJ loading needs integration testing with real game shaders")
    def test_release_model(self):
        """Test model reference counting and release."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vertex_path = os.path.join(tmpdir, "test_vertex.glsl")
            fragment_path = os.path.join(tmpdir, "test_fragment.glsl")

            with open(vertex_path, 'w') as f:
                f.write("""
#version 330 core
in vec2 in_texcoord;
in vec3 in_normal;
in vec3 in_position;
out vec2 frag_texcoord;
out vec3 frag_normal;
void main() {
    gl_Position = vec4(in_position, 1.0);
    frag_texcoord = in_texcoord;
    frag_normal = in_normal;
}
""")
            with open(fragment_path, 'w') as f:
                f.write("""
#version 330 core
in vec2 frag_texcoord;
in vec3 frag_normal;
out vec4 fragColor;
void main() {
    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
""")

            shader = self.resource_manager.load_shader("model_shader", vertex_path, fragment_path)

            model_path = os.path.join(os.path.dirname(__file__), "..", "assets", "models", "test_cube.obj")
            model_path = os.path.normpath(model_path)

            if os.path.exists(model_path):
                # Load model twice (ref count = 2)
                self.resource_manager.load_obj_model("test_cube", model_path, shader)
                self.resource_manager.load_obj_model("test_cube", model_path, shader)

                stats = self.resource_manager.get_stats()
                self.assertEqual(stats['total_model_refs'], 2)

                # Release once (ref count = 1)
                self.resource_manager.release_model("test_cube")
                stats = self.resource_manager.get_stats()
                self.assertEqual(stats['total_model_refs'], 1)
                self.assertEqual(stats['models_loaded'], 1)

                # Release again (ref count = 0, should be removed)
                self.resource_manager.release_model("test_cube")
                stats = self.resource_manager.get_stats()
                self.assertEqual(stats['total_model_refs'], 0)
                self.assertEqual(stats['models_loaded'], 0)
            else:
                self.skipTest(f"Test model not found at {model_path}")


if __name__ == '__main__':
    unittest.main()
