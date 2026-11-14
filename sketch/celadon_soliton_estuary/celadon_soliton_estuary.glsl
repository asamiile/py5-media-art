#version 150

uniform vec2 resolution;
uniform float time;
uniform float seed;

out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(127.1, 311.7) + seed * 0.01);
    p += dot(p, p + 34.5);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p = rot * p * 2.03 + vec2(2.1, 7.4);
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    float aspect = resolution.x / resolution.y;

    // Match py5 screen coordinates where y=0 is top; off-center tidal mouth at (0.26, 0.68)
    vec2 p = vec2((uv.x - 0.26) * aspect, (1.0 - uv.y) - 0.68);
    float r = length(p);

    // Smooth non-singular directional cosine toward upper-right (-0.42 rad): avoid atan2 branch cut!
    vec2 dir_unit = p / sqrt(r * r + 0.045);
    vec2 axis_main = vec2(cos(-0.42), sin(-0.42));
    vec2 axis_perp = vec2(-axis_main.y, axis_main.x);
    float proj_main = dot(dir_unit, axis_main);
    float proj_perp = dot(dir_unit, axis_perp);

    // Domain-warped advection coordinates
    vec2 flow_uv = p * 2.4 - axis_main * (time * 0.14);
    float warp1 = fbm(flow_uv);
    float warp2 = fbm(flow_uv * 1.9 + vec2(warp1 * 1.35, -time * 0.12));

    // Propagating Korteweg-de Vries (KdV) soliton wave packet train radiating from (0.26, 0.68)
    float r_warped = r + (warp2 - 0.5) * 0.11 + 0.045 * sin(proj_perp * 3.5 + warp1 * 2.2);
    float phase1 = r_warped * 18.0 - time * 3.2;
    float phase2 = (r_warped + 0.08 * proj_perp) * 34.0 - time * 5.2;

    // Crisp soliton crests and dark trough shadows
    float crest1 = pow(0.5 + 0.5 * cos(phase1), 9.0);
    float trough1 = pow(0.5 - 0.5 * cos(phase1), 3.0);
    float crest2 = pow(0.5 + 0.5 * cos(phase2), 11.0);
    float packet_env = exp(-r * 0.48) * (0.68 + 0.32 * sin(r * 4.2 - time * 0.8));

    // Mid-Tone Atmospheric Dusk / Celadon Slate palette
    vec3 col_deep_trough = vec3(0.125, 0.165, 0.192); // #202a31
    vec3 col_slate       = vec3(0.173, 0.220, 0.251); // #2c3840
    vec3 col_celadon     = vec3(0.239, 0.314, 0.294); // #3d504b
    vec3 col_mist        = vec3(0.460, 0.580, 0.588); // #759496
    vec3 col_chalk       = vec3(0.920, 0.898, 0.855); // #ebe5da
    vec3 col_amber       = vec3(0.902, 0.573, 0.196); // #e69232

    // Base atmospheric gradient with organic silt texture
    vec3 col = mix(col_slate, col_celadon, smoothstep(0.0, 1.5, r + (warp1 - 0.5) * 0.35));
    col = mix(col, col_deep_trough, trough1 * packet_env * 0.55);
    col = mix(col, col_mist, warp2 * 0.32 * exp(-r * 0.35));

    // Luminous traveling soliton wavefronts
    float dir_focus = 0.42 + 0.58 * smoothstep(-0.6, 0.85, proj_main);
    float wave_strength = (crest1 * 0.78 + crest2 * 0.42) * packet_env * dir_focus;

    col = mix(col, col_mist, smoothstep(0.04, 0.38, wave_strength) * 0.58);
    col += col_chalk * pow(wave_strength, 1.35) * 0.52;

    // Warm amber mineral silt ribbon along the leading shear edge of each soliton crest
    float leading_edge = pow(max(0.0, sin(phase1 + 0.55)), 6.0) * (0.4 + 0.6 * crest1);
    col += col_amber * leading_edge * packet_env * dir_focus * (0.45 + 0.55 * warp2) * 0.68;

    // Soft warm estuary core glow near (0.26, 0.68) without any angular pinch
    float core_glow = exp(-r * r * 14.0);
    col += mix(col_amber, col_chalk, 0.45) * core_glow * 0.26;

    // Subtle tactile grain
    float g = hash21(gl_FragCoord.xy * 0.5 + time) - 0.5;
    col += g * 0.015;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
