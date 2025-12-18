#version 330 core

// Input vertex attributes
in vec3 in_position;

// Transformation matrices
uniform mat4 light_space_matrix;  // Combined projection * view from light
uniform mat4 model;

void main()
{
    // Transform vertex to light's clip space
    gl_Position = light_space_matrix * model * vec4(in_position, 1.0);
}
