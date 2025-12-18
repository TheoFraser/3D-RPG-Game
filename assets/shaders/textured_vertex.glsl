#version 330 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec2 in_texcoord;
layout (location = 2) in vec3 in_normal;

out vec2 frag_texcoord;
out vec3 frag_normal;
out vec3 frag_position;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat3 normal_matrix;  // Pre-computed normal matrix from CPU

void main()
{
    vec4 world_pos = model * vec4(in_position, 1.0);
    gl_Position = projection * view * world_pos;

    frag_texcoord = in_texcoord;
    frag_normal = normal_matrix * in_normal;  // Use pre-computed normal matrix
    frag_position = world_pos.xyz;
}
