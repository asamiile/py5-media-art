#version 150

uniform vec2 resolution;
uniform float time;
uniform float n1;
uniform float m1;
uniform float n2;
uniform float m2;
uniform float mixA;
uniform float mixB;
uniform float phaseShift;

out vec4 fragColor;

const float PI = 3.14159265359;

float hash21(vec2 p) {
    p = fract(p * vec2(234.34, 435.345));
    p += dot(p, p + 34.23);
    return fract(p.x * p.y);
}

float chladni(vec2 p) {
    float w1 = cos(n1 * PI * p.x) * cos(m1 * PI * p.y)
             - mixA * cos(m1 * PI * p.x) * cos(n1 * PI * p.y);

    float w2 = cos(n2 * PI * p.x + phaseShift) * cos(m2 * PI * p.y - phaseShift * 0.7)
             + mixB * cos(m2 * PI * p.x - phaseShift * 0.5) * cos(n2 * PI * p.y + phaseShift);

    return 0.68 * w1 + 0.32 * w2;
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    // Match py5 screen coordinates where y=0 is top
    vec2 p = vec2(uv.x * 2.0 - 1.0, (1.0 - uv.y) * 2.0 - 1.0);

    float w = chladni(p);
    float abs_w = abs(w);

    // Compute finite-difference gradient for plate relief shading & nodal crispness
    float eps = 0.0025;
    float wx = chladni(p + vec2(eps, 0.0)) - w;
    float wy = chladni(p + vec2(0.0, eps)) - w;
    float grad_mag = max(length(vec2(wx, wy)) / eps, 0.35);

    // Distance to true nodal zero-crossing normalized by gradient magnitude
    float d_node = abs_w / grad_mag;

    // Deep nocturnal slate-obsidian plate base
    vec3 col_base = vec3(0.048, 0.062, 0.086);
    vec3 col_trough = vec3(0.075, 0.102, 0.142);
    vec3 col_crest = vec3(0.118, 0.158, 0.212);

    // Subtle brushed metal anisotropy on the vibrating plate
    float brush = sin(uv.x * 950.0 + sin(uv.y * 120.0) * 2.5) * 0.5 + 0.5;
    float micro = hash21(gl_FragCoord.xy * 0.5 + time * 0.1);

    // Standing wave acoustic pressure ripples (high-frequency carrier phase)
    float carrier = sin(w * 14.0 - time * 4.5) * 0.5 + 0.5;
    float antinode_energy = smoothstep(0.08, 0.95, abs_w);

    vec3 col = mix(col_base, col_trough, antinode_energy);
    col = mix(col, col_crest, antinode_energy * carrier * 0.45);
    col += (brush - 0.5) * 0.012;

    // Fine glowing acoustic nodal grooves where particles accumulate
    float nodal_halo = exp(-d_node * 28.0);
    float nodal_core = exp(-d_node * 95.0);
    float harmonic_node = exp(-abs(abs_w - 0.32) / grad_mag * 55.0);

    vec3 col_ivory = vec3(0.84, 0.87, 0.91);
    vec3 col_amber = vec3(0.92, 0.48, 0.24);

    col += col_amber * nodal_halo * 0.26;
    col += col_ivory * nodal_core * 0.34;
    col += col_amber * harmonic_node * 0.14;

    // Subtle edge acoustic transducer glow from the four boundary exciters
    float edge_dist = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
    float edge_pulse = exp(-edge_dist * 24.0) * (0.5 + 0.5 * sin(time * 2.5 + (uv.x + uv.y) * 8.0));
    col += col_amber * edge_pulse * 0.18;

    // Gentle corner vignette and fine tactile grain
    float r2 = dot(p * vec2(0.85, 0.95), p * vec2(0.85, 0.95));
    col *= 1.0 - 0.18 * smoothstep(0.65, 1.85, r2);
    col += (micro - 0.5) * 0.014;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
