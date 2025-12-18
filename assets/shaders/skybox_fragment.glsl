#version 330 core

// Input from vertex shader
in vec3 frag_position;

// Output color
out vec4 FragColor;

// Sky colors
uniform vec3 color_top;     // Zenith color (top of sky)
uniform vec3 color_bottom;  // Horizon color (bottom of sky)

void main()
{
    // Calculate gradient factor based on Y position
    // Y ranges from -1 (bottom) to +1 (top)
    float gradient_factor = (frag_position.y + 1.0) * 0.5;  // Map to [0, 1]

    // Smooth gradient for more natural sky
    gradient_factor = smoothstep(0.0, 1.0, gradient_factor);

    // Interpolate between horizon and zenith colors
    vec3 sky_color = mix(color_bottom, color_top, gradient_factor);

    // Output final color
    FragColor = vec4(sky_color, 1.0);
}
