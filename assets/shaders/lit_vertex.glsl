#version 330 core

// Input vertex attributes
in vec3 in_position;
in vec3 in_normal;
in vec2 in_texcoord;
in vec3 in_color;  // Vertex color for biome-specific coloring

// Output to fragment shader
out vec2 frag_texcoord;
out vec3 frag_normal;
out vec3 frag_position;
out vec3 frag_color;  // Pass vertex color to fragment shader
out vec4 frag_pos_light_space;  // Fragment position in light space for shadow mapping

// Transformation matrices
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat3 normal_matrix;  // Pre-computed transpose(inverse(model))
uniform mat4 light_space_matrix;  // For shadow mapping

void main()
{
    // Transform vertex position
    vec4 world_pos = model * vec4(in_position, 1.0);
    frag_position = world_pos.xyz;

    // Transform normal to world space
    frag_normal = normal_matrix * in_normal;

    // Pass texture coordinates
    frag_texcoord = in_texcoord;

    // Pass vertex color
    frag_color = in_color;

    // Transform to light space for shadow mapping
    frag_pos_light_space = light_space_matrix * world_pos;

    // Output clip-space position
    gl_Position = projection * view * world_pos;
}
