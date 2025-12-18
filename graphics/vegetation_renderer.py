"""Optimized vegetation renderer using instanced rendering."""
import moderngl
import glm
import numpy as np
from typing import List, Dict
from world_gen.vegetation import VegetationInstance, VegetationType
from game.logger import get_logger

logger = get_logger(__name__)


# Colors for different vegetation types (R, G, B)
VEGETATION_COLORS = {
    VegetationType.OAK_TREE: (0.4, 0.3, 0.1),      # Brown trunk
    VegetationType.PINE_TREE: (0.2, 0.4, 0.2),     # Dark green
    VegetationType.MAGIC_TREE: (0.6, 0.3, 0.8),    # Purple
    VegetationType.CRYSTAL_TREE: (0.4, 0.6, 0.9),  # Light blue
    VegetationType.DEAD_TREE: (0.3, 0.3, 0.3),     # Gray
    VegetationType.GRASS: (0.3, 0.7, 0.3),         # Bright green
    VegetationType.BUSH: (0.2, 0.5, 0.2),          # Green
    VegetationType.MUSHROOM: (0.9, 0.3, 0.3),      # Red
    VegetationType.CRYSTAL_CLUSTER: (0.5, 0.8, 1.0), # Cyan
    VegetationType.RUINS_VINE: (0.2, 0.6, 0.2),    # Green
}


class VegetationRenderer:
    """Renders vegetation instances using efficient instanced rendering."""

    def __init__(self, ctx: moderngl.Context):
        """
        Initialize vegetation renderer.

        Args:
            ctx: ModernGL context
        """
        self.ctx = ctx
        self.cube_vbo = None
        self.cube_ibo = None
        self.vertex_count = 0

        # Instance VAOs for each vegetation type
        self.instance_vaos: Dict[str, moderngl.VertexArray] = {}
        self.instance_vbos: Dict[str, moderngl.Buffer] = {}

        # Instanced shader program
        self.shader_program = None

        self._create_cube_mesh()
        self._create_instanced_shader()

        logger.info("VegetationRenderer initialized with instanced rendering")

    def _create_cube_mesh(self):
        """Create a simple cube mesh for rendering vegetation."""
        # Cube vertices (position + normal)
        vertices = np.array([
            # Front face
            -0.5, -0.5,  0.5,  0, 0, 1,
             0.5, -0.5,  0.5,  0, 0, 1,
             0.5,  0.5,  0.5,  0, 0, 1,
            -0.5,  0.5,  0.5,  0, 0, 1,
            # Back face
            -0.5, -0.5, -0.5,  0, 0, -1,
             0.5, -0.5, -0.5,  0, 0, -1,
             0.5,  0.5, -0.5,  0, 0, -1,
            -0.5,  0.5, -0.5,  0, 0, -1,
            # Top face
            -0.5,  0.5, -0.5,  0, 1, 0,
             0.5,  0.5, -0.5,  0, 1, 0,
             0.5,  0.5,  0.5,  0, 1, 0,
            -0.5,  0.5,  0.5,  0, 1, 0,
            # Bottom face
            -0.5, -0.5, -0.5,  0, -1, 0,
             0.5, -0.5, -0.5,  0, -1, 0,
             0.5, -0.5,  0.5,  0, -1, 0,
            -0.5, -0.5,  0.5,  0, -1, 0,
            # Right face
             0.5, -0.5, -0.5,  1, 0, 0,
             0.5,  0.5, -0.5,  1, 0, 0,
             0.5,  0.5,  0.5,  1, 0, 0,
             0.5, -0.5,  0.5,  1, 0, 0,
            # Left face
            -0.5, -0.5, -0.5,  -1, 0, 0,
            -0.5,  0.5, -0.5,  -1, 0, 0,
            -0.5,  0.5,  0.5,  -1, 0, 0,
            -0.5, -0.5,  0.5,  -1, 0, 0,
        ], dtype=np.float32)

        # Cube indices
        indices = np.array([
            0, 1, 2, 2, 3, 0,    # Front
            4, 6, 5, 6, 4, 7,    # Back
            8, 9, 10, 10, 11, 8, # Top
            12, 14, 13, 14, 12, 15, # Bottom
            16, 17, 18, 18, 19, 16, # Right
            20, 22, 21, 22, 20, 23, # Left
        ], dtype=np.uint32)

        self.cube_vbo = self.ctx.buffer(vertices.tobytes())
        self.cube_ibo = self.ctx.buffer(indices.tobytes())
        self.vertex_count = len(indices)

    def _create_instanced_shader(self):
        """Create shader program for instanced rendering."""
        # Instanced vertex shader
        vertex_shader = """
        #version 330 core

        // Per-vertex attributes
        in vec3 in_position;
        in vec3 in_normal;

        // Per-instance attributes
        in vec3 instance_position;
        in vec3 instance_scale;
        in vec3 instance_color;

        // Output to fragment shader
        out vec3 frag_normal;
        out vec3 frag_position;
        out vec3 frag_color;
        out vec4 frag_pos_light_space;

        // Transformation matrices
        uniform mat4 view;
        uniform mat4 projection;
        uniform mat4 light_space_matrix;

        void main()
        {
            // Build per-instance model matrix
            mat4 model = mat4(1.0);
            model[0][0] = instance_scale.x;
            model[1][1] = instance_scale.y;
            model[2][2] = instance_scale.z;
            model[3][0] = instance_position.x;
            model[3][1] = instance_position.y;
            model[3][2] = instance_position.z;

            // Transform vertex position
            vec4 world_pos = model * vec4(in_position, 1.0);
            frag_position = world_pos.xyz;

            // Transform normal to world space
            frag_normal = mat3(model) * in_normal;

            // Pass instance color
            frag_color = instance_color;

            // Transform to light space
            frag_pos_light_space = light_space_matrix * world_pos;

            // Output position
            gl_Position = projection * view * world_pos;
        }
        """

        # Simple fragment shader for vegetation
        fragment_shader = """
        #version 330 core

        in vec3 frag_normal;
        in vec3 frag_position;
        in vec3 frag_color;
        in vec4 frag_pos_light_space;

        out vec4 FragColor;

        uniform vec3 view_pos;
        uniform vec3 light_direction;
        uniform vec3 light_color;
        uniform vec3 ambient_color;

        void main()
        {
            vec3 norm = normalize(frag_normal);
            vec3 light_dir = normalize(-light_direction);

            // Diffuse lighting
            float diff = max(dot(norm, light_dir), 0.0);
            vec3 diffuse = diff * light_color;

            // Simple ambient
            vec3 ambient = ambient_color;

            // Combine lighting
            vec3 result = (ambient + diffuse) * frag_color;

            FragColor = vec4(result, 1.0);
        }
        """

        try:
            self.shader_program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )

            # Set default uniforms
            if 'light_space_matrix' in self.shader_program:
                self.shader_program['light_space_matrix'].write(glm.mat4(1.0))
            if 'light_direction' in self.shader_program:
                self.shader_program['light_direction'].write(glm.vec3(0.3, -1.0, 0.5))
            if 'light_color' in self.shader_program:
                self.shader_program['light_color'].write(glm.vec3(1.0, 1.0, 1.0))
            if 'ambient_color' in self.shader_program:
                self.shader_program['ambient_color'].write(glm.vec3(0.4, 0.4, 0.4))

        except Exception as e:
            logger.error(f"Failed to create instanced shader: {e}")
            self.shader_program = None

    def render(self, instances: List[VegetationInstance], shader, view_matrix, projection_matrix):
        """
        Render vegetation instances using instanced rendering.

        Args:
            instances: List of vegetation instances to render
            shader: Shader to use (ignored, we use our own instanced shader)
            view_matrix: View matrix
            projection_matrix: Projection matrix
        """
        if not instances or self.shader_program is None:
            return

        # Group instances by vegetation type
        grouped_instances: Dict[str, List[VegetationInstance]] = {}
        for instance in instances:
            veg_type = instance.vegetation_type
            if veg_type not in grouped_instances:
                grouped_instances[veg_type] = []
            grouped_instances[veg_type].append(instance)

        # Set shader uniforms (shared across all instances)
        self.shader_program['view'].write(view_matrix)
        self.shader_program['projection'].write(projection_matrix)

        # Enable depth testing
        self.ctx.enable(moderngl.DEPTH_TEST)

        # Render each vegetation type with instancing
        for veg_type, type_instances in grouped_instances.items():
            self._render_instances(veg_type, type_instances)

    def _render_instances(self, veg_type: str, instances: List[VegetationInstance]):
        """
        Render all instances of a specific vegetation type in one draw call.

        Args:
            veg_type: Vegetation type
            instances: List of instances of this type
        """
        if not instances:
            return

        # Build instance data array (position, scale, color for each instance)
        instance_data = []
        color = VEGETATION_COLORS.get(veg_type, (0.5, 0.5, 0.5))

        for instance in instances:
            # Position
            instance_data.extend([instance.position.x, instance.position.y, instance.position.z])

            # Scale (trees are taller)
            scale = instance.scale
            if veg_type.endswith('_tree'):
                instance_data.extend([scale * 0.5, scale * 3.0, scale * 0.5])
            else:
                instance_data.extend([scale, scale * 0.5, scale])

            # Color
            instance_data.extend(color)

        # Convert to numpy array
        instance_array = np.array(instance_data, dtype=np.float32)

        # Create or update instance buffer
        if veg_type in self.instance_vbos:
            # Update existing buffer
            self.instance_vbos[veg_type].orphan(size=instance_array.nbytes)
            self.instance_vbos[veg_type].write(instance_array.tobytes())
        else:
            # Create new buffer
            self.instance_vbos[veg_type] = self.ctx.buffer(instance_array.tobytes())

        # Create or get VAO
        if veg_type not in self.instance_vaos:
            self.instance_vaos[veg_type] = self.ctx.vertex_array(
                self.shader_program,
                [
                    # Per-vertex data (cube mesh)
                    (self.cube_vbo, '3f 3f', 'in_position', 'in_normal'),
                    # Per-instance data (divisor=1 means one per instance)
                    (self.instance_vbos[veg_type], '3f 3f 3f/i', 'instance_position', 'instance_scale', 'instance_color'),
                ],
                self.cube_ibo
            )

        # Render all instances in one draw call
        self.instance_vaos[veg_type].render(instances=len(instances))

    def release(self):
        """Release GPU resources."""
        # Release instance buffers and VAOs
        for vao in self.instance_vaos.values():
            vao.release()
        for vbo in self.instance_vbos.values():
            vbo.release()

        if self.cube_vbo:
            self.cube_vbo.release()
        if self.cube_ibo:
            self.cube_ibo.release()
        if self.shader_program:
            self.shader_program.release()

        logger.info("VegetationRenderer released")
