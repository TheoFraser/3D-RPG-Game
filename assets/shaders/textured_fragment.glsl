#version 330 core

in vec2 frag_texcoord;
in vec3 frag_normal;
in vec3 frag_position;

out vec4 FragColor;

uniform sampler2D texture0;
uniform vec3 light_pos;
uniform vec3 view_pos;

void main()
{
    // Ambient lighting
    float ambient_strength = 0.3;
    vec3 ambient = ambient_strength * vec3(1.0);

    // Diffuse lighting
    vec3 norm = normalize(frag_normal);
    vec3 light_dir = normalize(light_pos - frag_position);
    float diff = max(dot(norm, light_dir), 0.0);
    vec3 diffuse = diff * vec3(1.0);

    // Specular lighting
    float specular_strength = 0.5;
    vec3 view_dir = normalize(view_pos - frag_position);
    vec3 reflect_dir = reflect(-light_dir, norm);
    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32);
    vec3 specular = specular_strength * spec * vec3(1.0);

    vec3 result = (ambient + diffuse + specular) * texture(texture0, frag_texcoord).rgb;
    FragColor = vec4(result, 1.0);
}
