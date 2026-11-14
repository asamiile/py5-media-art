#version 150

uniform vec2 resolution;
uniform float time;
uniform float seed;
uniform float strataAngle;

out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(127.1, 311.7) + seed * 0.01);
    p += dot(p, p + 34.5);
    return fract(p.x * p.y);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    float aspect = resolution.x / resolution.y;
    // Match py5 screen coordinates (y=0 top)
    vec2 p = vec2((uv.x - 0.5) * aspect, (1.0 - uv.y) - 0.5);

    // Rotate into diagonal strata coordinate frame (u along sweep, v across strata)
    float ca = cos(-strataAngle);
    float sa = sin(-strataAngle);
    vec2 q = vec2(p.x * ca - p.y * sa, p.x * sa + p.y * ca);

    // Propagating transverse fault displacement along u
    float fault_wave = 0.042 * tanh(3.5 * sin(q.x * 4.5 - time * 1.4 + floor(q.y * 12.0) * 0.5));
    float v_warped = q.y - fault_wave;

    // 22 stratified tectonic horizons
    float band_coord = (v_warped + 0.92) / 1.84 * 22.0;
    float band_id = floor(band_coord);
    float band_f = fract(band_coord);

    float dir = (mod(band_id, 2.0) < 0.5) ? 1.0 : -1.0;
    float speed = dir * (0.20 + 0.18 * hash21(vec2(band_id, 7.0)));
    float u_adv = q.x - time * speed;

    // Columnar basalt jointing ribs inside each stratum
    float col_freq = 14.0 + floor(hash21(vec2(band_id, 19.0)) * 22.0);
    float col_id = floor(u_adv * col_freq);
    float col_f = fract(u_adv * col_freq);
    float cell_rnd = hash21(vec2(col_id, band_id));

    // Stark Constructivist High-Contrast Palette
    vec3 col_carbon      = vec3(0.059, 0.067, 0.086); // #0f1116
    vec3 col_basalt      = vec3(0.118, 0.133, 0.165); // #1e222a
    vec3 col_bone        = vec3(0.953, 0.941, 0.910); // #f3f0e8
    vec3 col_vermilion   = vec3(0.910, 0.204, 0.141); // #e83424
    vec3 col_ultramarine = vec3(0.110, 0.243, 0.839); // #1c3ed6
    vec3 col_ochre       = vec3(0.949, 0.698, 0.094); // #f2b218

    // Base stratum shading with crisp columnar joints
    float joint_mask = smoothstep(0.04, 0.09, col_f) * smoothstep(0.04, 0.09, 1.0 - col_f)
                     * smoothstep(0.06, 0.12, band_f) * smoothstep(0.06, 0.12, 1.0 - band_f);

    vec3 cell_col = col_basalt;
    if (cell_rnd > 0.86) {
        cell_col = col_bone * 0.88;
    } else if (cell_rnd > 0.74) {
        cell_col = col_ultramarine * 0.85;
    } else if (cell_rnd > 0.64) {
        cell_col = col_vermilion * 0.88;
    } else if (cell_rnd > 0.56) {
        cell_col = col_ochre * 0.88;
    } else {
        // Striated basalt micro-fluting inside dark columns
        float flute = sin(col_f * 31.4159) * 0.5 + 0.5;
        cell_col = mix(col_carbon, col_basalt * 1.35, 0.35 + 0.65 * flute * cell_rnd);
    }

    vec3 col = mix(col_carbon, cell_col, joint_mask);

    // Luminous slip-plane hairline along each tectonic horizon boundary
    float slip_line = exp(-abs(band_f - 0.5) * 38.0);
    float pulse = 0.5 + 0.5 * sin(u_adv * 8.0 + band_id * 1.7);
    col += mix(col_bone, col_vermilion, step(0.5, fract(band_id * 0.37))) * slip_line * pulse * 0.16;

    // Fine tactile grain
    float g = hash21(gl_FragCoord.xy * 0.5 + time) - 0.5;
    col += g * 0.015;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}

