#version 150

uniform vec2 resolution;
uniform float time;
uniform float u_loop;

out vec4 fragColor;

float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

float noise2d(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash12(i), hash12(i + vec2(1.0, 0.0)), u.x),
        mix(hash12(i + vec2(0.0, 1.0)), hash12(i + vec2(1.0, 1.0)), u.x),
        u.y
    );
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.866, 0.5, -0.5, 0.866);
    for (int i = 0; i < 4; i++) {
        v += a * noise2d(p);
        p = rot * p * 2.02 + vec2(15.7, 8.3);
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    float aspect = resolution.x / resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    float theta = u_loop * 6.28318530718;
    float c1 = cos(theta);
    float s1 = sin(theta);

    // High-Key Mineral & Washi Full-Canvas Light palette
    vec3 col_washi   = vec3(0.933, 0.910, 0.859); // #eee8db
    vec3 col_sand    = vec3(0.886, 0.855, 0.792); // #e2dac9
    vec3 col_slate   = vec3(0.141, 0.200, 0.239); // #24333d
    vec3 col_indigo  = vec3(0.196, 0.306, 0.384); // #324e62
    vec3 col_sienna  = vec3(0.737, 0.306, 0.188); // #bc4e30
    vec3 col_gold    = vec3(0.808, 0.557, 0.165); // #ce8e2a
    vec3 col_sage    = vec3(0.275, 0.451, 0.424); // #46736c

    // Full-canvas handmade kozo paper fiber texture
    float fiber = (noise2d(vec2(uv.x * 460.0, uv.y * 62.0)) * 0.65
                 + noise2d(vec2(uv.x * 75.0, uv.y * 410.0)) * 0.35) - 0.5;
    vec3 col = mix(col_washi, col_sand, 0.40 + 0.35 * fbm(p * 2.5 + vec2(c1 * 0.2, s1 * 0.2))) + fiber * 0.028;

    // Diagonally swept coordinate frame (-19 deg diagonal sweep)
    float ang = -0.3316125;
    mat2 rot = mat2(cos(ang), -sin(ang), sin(ang), cos(ang));
    vec2 q = rot * p;

    // Traveling wavefront coordinate (continuous advection from left to right along diagonal strata)
    float u_adv1 = q.x * 6.2831853 - theta * 1.0;
    float u_adv2 = q.x * 6.2831853 * 2.0 - theta * 2.0;

    // Warp threads (fine longitudinal silk filaments running along q.x)
    float warp_wave = q.y + 0.048 * sin(u_adv1 * 0.5 + q.y * 4.5) + 0.022 * cos(u_adv2 * 0.5 - q.y * 7.0);
    float warp_thread = smoothstep(0.65, 0.98, cos(warp_wave * 340.0));
    col = mix(col, col_sand * 0.90, warp_thread * 0.35);

    // 7 Stratified Kasuri (Ikat) Weft Bands with feathered resist-dyed edges & traveling shuttle wavefronts
    for (int i = 0; i < 7; i++) {
        float fi = float(i);
        float y_center = -0.45 + fi * 0.15;
        float dir = (i % 2 == 0) ? 1.0 : -1.0;

        // Traveling shed wavefront displacing the stratum
        float wave_y = y_center
            + 0.052 * sin(q.x * 3.8 - theta * dir + fi * 1.1)
            + 0.028 * cos(q.x * 7.2 - theta * 2.0 * dir + fi * 2.3);

        float dy = q.y - wave_y;

        // Kasuri ikat feathered step-shift along weft threads
        float weft_quant = floor((q.y + 0.6) * 85.0) / 85.0;
        float ikat_jitter = (hash12(vec2(weft_quant * 130.0, fi * 19.0)) - 0.5) * 0.036;
        float ikat_phase = q.x * (5.5 + mod(fi, 3.0) * 1.5) - theta * dir * 2.0 + dy * 8.0 + ikat_jitter * 6.28318;

        // Feathered resist-dye pattern block inside each band
        float ikat_motif = smoothstep(-0.15, 0.25, cos(ikat_phase) + 0.35 * sin(ikat_phase * 2.0));
        float band_env = smoothstep(0.068, 0.012, abs(dy + ikat_jitter * 0.45));

        // Fine weft-over-warp twill diagonal micro-ribbing
        float twill_rib = 0.72 + 0.28 * cos((q.x * 220.0 + q.y * 220.0 * dir) - theta * 4.0 * dir);

        vec3 dye_col;
        if (i % 4 == 0) {
            dye_col = mix(col_slate, col_indigo, ikat_motif);
        } else if (i % 4 == 1) {
            dye_col = mix(col_sienna, col_gold, ikat_motif);
        } else if (i % 4 == 2) {
            dye_col = mix(col_sage, col_slate, ikat_motif);
        } else {
            dye_col = mix(col_gold, col_sienna, ikat_motif);
        }

        float alpha = band_env * (0.42 + 0.46 * ikat_motif) * twill_rib;
        col = mix(col, dye_col, clamp(alpha, 0.0, 0.86));

        // Crisp selvedge cord lines along top and bottom of each woven band
        float selvedge = smoothstep(0.008, 0.001, abs(abs(dy) - 0.052));
        col = mix(col, col_slate, selvedge * 0.58);
    }

    float dither = (hash12(gl_FragCoord.xy + vec2(c1 * 17.0, s1 * 23.0)) - 0.5) * 0.012;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

