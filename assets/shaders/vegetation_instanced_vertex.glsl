#version 330 core

// Per-vertex attributes
in vec3 in_position;
in vec3 in_normal;

// Per-instance attributes
in vec3 instance_position;    // Instance world position
in vec3 instance_scale;       // Instance scale (x, y, z)
in vec3 instance_color;       // Instance color

// Output to fragment shader
out vec3 frag_normal;
out vec3 frag_position;
out vec3 frag_color;
out vec4 frag_pos_light_space;

// Transformation matrices (shared across all instances)
uniform mat4 view;
uniform mat4 projection;
uniform mat4 light_space_matrix;

void main()
{
    // Build per-instance model matrix
    mat4 model = mat4(1.0);

    // Apply scale
    model[0][0] = instance_scale.x;
    model[1][1] = instance_scale.y;
    model[2][2] = instance_scale.z;

    // Apply translation
    model[3][0] = instance_position.x;
    model[3][1] = instance_position.y;
    model[3][2] = instance_position.z;

    // Transform vertex position
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_position = world_pos.xyz;

    // Transform normal to world space (simplified for uniform scaling)
    // For non-uniform scaling, we'd need the full normal matrix
    frag_normal = mat3(model) * in_normal;

    // Pass instance color
    frag_color = instance_color;

    // Transform to light space for shadow mapping
    frag_pos_light_space = light_space_matrix * world_pos;

    // Output clip-space position
    gl_Position = projection * view * world_pos;
}
