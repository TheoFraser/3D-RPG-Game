#version 330 core

// Input from vertex shader
in vec2 frag_texcoord;
in vec3 frag_normal;
in vec3 frag_position;
in vec3 frag_color;  // Vertex color for biome-specific coloring
in vec4 frag_pos_light_space;  // Fragment position in light space

// Output color
out vec4 FragColor;

// Material properties
uniform sampler2D texture0;
uniform sampler2D shadow_map;  // Shadow map texture
uniform vec3 view_pos;
uniform bool shadows_enabled;  // Toggle shadows on/off

// Fog uniforms (Phase 3.3)
uniform bool fog_enabled;
uniform vec3 fog_color;
uniform float fog_density;
uniform float fog_start;
uniform float fog_end;

// Light structure
struct Light {
    int type;            // 0 = directional, 1 = point, 2 = spot
    vec3 position;       // For point and spot lights
    vec3 direction;      // For directional and spot lights
    vec3 color;          // Light color * intensity

    // Attenuation (for point and spot lights)
    float constant;
    float linear;
    float quadratic;

    // Spot light properties
    float inner_cutoff;  // cos(inner angle)
    float outer_cutoff;  // cos(outer angle)
};

// Lighting uniforms
#define MAX_LIGHTS 8
uniform Light lights[MAX_LIGHTS];
uniform int num_lights;
uniform vec3 ambient_color;

// Material properties (hardcoded for now, can be uniforms later)
const float specular_strength = 0.5;
const float shininess = 32.0;

// Shadow mapping parameters
const float shadow_bias = 0.005;  // Bias to prevent shadow acne
const int pcf_samples = 2;         // PCF kernel size (2 = 5x5, 1 = 3x3, 0 = 1x1)

// Calculate shadow factor using PCF (Percentage Closer Filtering)
float calculate_shadow(vec4 frag_pos_light_space, vec3 normal, vec3 light_dir)
{
    if (!shadows_enabled) {
        return 0.0;  // No shadow
    }

    // Perspective divide to get normalized device coordinates
    vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;

    // Transform from [-1,1] to [0,1] range (texture coordinates)
    proj_coords = proj_coords * 0.5 + 0.5;

    // Outside shadow map frustum = no shadow
    if (proj_coords.z > 1.0 || proj_coords.x < 0.0 || proj_coords.x > 1.0 ||
        proj_coords.y < 0.0 || proj_coords.y > 1.0) {
        return 0.0;
    }

    // Get depth from shadow map
    float closest_depth = texture(shadow_map, proj_coords.xy).r;

    // Current fragment depth
    float current_depth = proj_coords.z;

    // Calculate bias based on surface angle to light
    float bias = max(shadow_bias * (1.0 - dot(normal, light_dir)), shadow_bias * 0.1);

    // PCF (Percentage Closer Filtering) for soft shadows
    float shadow = 0.0;
    vec2 texel_size = 1.0 / textureSize(shadow_map, 0);
    int samples = 0;

    for (int x = -pcf_samples; x <= pcf_samples; ++x) {
        for (int y = -pcf_samples; y <= pcf_samples; ++y) {
            float pcf_depth = texture(shadow_map, proj_coords.xy + vec2(x, y) * texel_size).r;
            shadow += current_depth - bias > pcf_depth ? 1.0 : 0.0;
            samples++;
        }
    }
    shadow /= float(samples);

    return shadow;
}

// Calculate lighting for a directional light
vec3 calc_directional_light(Light light, vec3 normal, vec3 view_dir, float shadow)
{
    vec3 light_dir = normalize(-light.direction);

    // Diffuse
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = diff * light.color;

    // Specular (Blinn-Phong)
    vec3 halfway_dir = normalize(light_dir + view_dir);
    float spec = pow(max(dot(normal, halfway_dir), 0.0), shininess);
    vec3 specular = specular_strength * spec * light.color;

    // Apply shadow (1.0 - shadow because shadow is 0.0 for lit, 1.0 for shadowed)
    return (diffuse + specular) * (1.0 - shadow);
}

// Calculate lighting for a point light
vec3 calc_point_light(Light light, vec3 normal, vec3 frag_pos, vec3 view_dir)
{
    vec3 light_dir = normalize(light.position - frag_pos);

    // Diffuse
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = diff * light.color;

    // Specular (Blinn-Phong)
    vec3 halfway_dir = normalize(light_dir + view_dir);
    float spec = pow(max(dot(normal, halfway_dir), 0.0), shininess);
    vec3 specular = specular_strength * spec * light.color;

    // Attenuation
    float distance = length(light.position - frag_pos);
    float attenuation = 1.0 / (light.constant + light.linear * distance +
                               light.quadratic * distance * distance);

    diffuse *= attenuation;
    specular *= attenuation;

    return diffuse + specular;
}

// Calculate lighting for a spot light
vec3 calc_spot_light(Light light, vec3 normal, vec3 frag_pos, vec3 view_dir)
{
    vec3 light_dir = normalize(light.position - frag_pos);

    // Check if inside spotlight cone
    float theta = dot(light_dir, normalize(-light.direction));
    float epsilon = light.inner_cutoff - light.outer_cutoff;
    float intensity = clamp((theta - light.outer_cutoff) / epsilon, 0.0, 1.0);

    // Diffuse
    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = diff * light.color * intensity;

    // Specular (Blinn-Phong)
    vec3 halfway_dir = normalize(light_dir + view_dir);
    float spec = pow(max(dot(normal, halfway_dir), 0.0), shininess);
    vec3 specular = specular_strength * spec * light.color * intensity;

    // Attenuation
    float distance = length(light.position - frag_pos);
    float attenuation = 1.0 / (light.constant + light.linear * distance +
                               light.quadratic * distance * distance);

    diffuse *= attenuation;
    specular *= attenuation;

    return diffuse + specular;
}

void main()
{
    // Normalize interpolated normal
    vec3 norm = normalize(frag_normal);
    vec3 view_dir = normalize(view_pos - frag_position);

    // Sample base texture
    vec3 texture_color = texture(texture0, frag_texcoord).rgb;

    // Blend texture with vertex color for biome-specific coloring
    vec3 base_color = texture_color * frag_color;

    // Start with ambient light
    vec3 result = ambient_color * base_color;

    // Calculate shadow for directional light (only first directional light casts shadows)
    float shadow = 0.0;

    // Calculate contribution from each light
    for (int i = 0; i < num_lights && i < MAX_LIGHTS; i++)
    {
        vec3 light_contribution = vec3(0.0);

        if (lights[i].type == 0) {
            // Directional light - calculate shadow for first one only
            if (i == 0 && shadows_enabled) {
                vec3 light_dir = normalize(-lights[i].direction);
                shadow = calculate_shadow(frag_pos_light_space, norm, light_dir);
            }
            light_contribution = calc_directional_light(lights[i], norm, view_dir, shadow);
            shadow = 0.0;  // Reset for next lights
        }
        else if (lights[i].type == 1) {
            // Point light
            light_contribution = calc_point_light(lights[i], norm, frag_position, view_dir);
        }
        else if (lights[i].type == 2) {
            // Spot light
            light_contribution = calc_spot_light(lights[i], norm, frag_position, view_dir);
        }

        result += light_contribution * base_color;
    }

    // Apply fog (Phase 3.3)
    if (fog_enabled) {
        // Calculate distance from camera
        float distance = length(view_pos - frag_position);

        // Linear fog: fog factor = (end - distance) / (end - start)
        float fog_factor = (fog_end - distance) / (fog_end - fog_start);
        fog_factor = clamp(fog_factor, 0.0, 1.0);

        // Optionally use exponential fog for more realistic results
        // fog_factor = exp(-fog_density * distance);

        // Mix scene color with fog color
        result = mix(fog_color, result, fog_factor);
    }

    // Output final color
    FragColor = vec4(result, 1.0);
}
