#version 330 core

// Input vertex position
in vec3 in_position;

// Output to fragment shader
out vec3 frag_position;

// Uniforms
uniform mat4 view;
uniform mat4 projection;

void main()
{
    // Pass position to fragment shader (used for gradient)
    frag_position = in_position;

    // Transform position
    // Note: view matrix has translation removed (only rotation)
    vec4 pos = projection * view * vec4(in_position, 1.0);

    // Set z = w to ensure depth = 1.0 (farthest possible)
    // This makes skybox always behind everything else
    gl_Position = pos.xyww;
}
