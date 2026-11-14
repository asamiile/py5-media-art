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
    float a = hash12(i);
    float b = hash12(i + vec2(1.0, 0.0));
    float c = hash12(i + vec2(0.0, 1.0));
    float d = hash12(i + vec2(1.0, 1.0));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.866, 0.5, -0.5, 0.866);
    for (int i = 0; i < 4; i++) {
        v += a * noise2d(p);
        p = rot * p * 2.04 + vec2(17.3, 9.2);
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
    float c2 = cos(theta * 2.0);
    float s2 = sin(theta * 2.0);
    float c3 = cos(theta * 3.0);
    float s3 = sin(theta * 3.0);

    // High-Key Mineral & Washi Full-Canvas Light palette
    vec3 col_alabaster  = vec3(0.929, 0.910, 0.863); // #ede8dc
    vec3 col_linen      = vec3(0.898, 0.875, 0.820); // #e5dfcf
    vec3 col_ochre      = vec3(0.792, 0.541, 0.165); // #ca8a2a
    vec3 col_sienna     = vec3(0.722, 0.298, 0.192); // #b84c31
    vec3 col_sage       = vec3(0.282, 0.455, 0.431); // #48746e
    vec3 col_slate      = vec3(0.149, 0.212, 0.251); // #263640

    // Paper fiber grain across 100% of the canvas
    float fiber_h = noise2d(vec2(uv.x * 420.0, uv.y * 55.0));
    float fiber_v = noise2d(vec2(uv.x * 65.0, uv.y * 380.0));
    float paper_tex = (fiber_h * 0.6 + fiber_v * 0.4) - 0.5;
    vec3 col = mix(col_alabaster, col_linen, 0.45 + 0.35 * fbm(p * 2.8 + vec2(c1 * 0.25, s1 * 0.25)));
    col += paper_tex * 0.028;

    // Stratified Horizon / Diagonal Sweep coordinate frame (-12 deg gentle atmospheric tilt)
    float ang = -0.21;
    mat2 tilt = mat2(cos(ang), -sin(ang), sin(ang), cos(ang));
    vec2 q = tilt * p;

    // Poly-rhythmic phase interference across 8 stratified pigment horizons
    for (int i = 0; i < 8; i++) {
        float fi = float(i);
        float y_center = -0.46 + fi * 0.132;
        float dir = (i % 2 == 0) ? 1.0 : -1.0;

        // Three harmonic spatial waves drifting at different phase velocities
        float w1 = 0.055 * sin(q.x * (2.6 + fi * 0.35) + theta * dir + fi * 1.1);
        float w2 = 0.034 * cos(q.x * (5.2 - fi * 0.22) - theta * 2.0 * dir + fi * 2.3);
        float w3 = 0.021 * sin(q.x * 8.4 + theta * 3.0 + fi * 0.7);
        float warp = 0.042 * (fbm(vec2(q.x * 2.4 + c1 * 0.6 * dir, fi * 3.7 + s1 * 0.6)) - 0.5);

        float ridge_y = y_center + w1 + w2 + w3 + warp;
        float dy = q.y - ridge_y;

        // Wet pigment diffusion veil below each ridge + crisp capillary tide line at crest
        float crest = exp(-abs(dy) * 42.0);
        float body = smoothstep(0.018, -0.004, dy) * exp(max(dy, -0.26) * 9.5);
        float tide_ring = smoothstep(0.007, 0.001, abs(dy + 0.004 * sin(q.x * 16.0 + theta * 2.0)));

        // Alternate mineral pigment families per stratum
        vec3 pigment;
        if (i % 4 == 0) {
            pigment = mix(col_ochre, col_sienna, 0.35 + 0.35 * sin(q.x * 2.5 + theta));
        } else if (i % 4 == 1) {
            pigment = mix(col_slate, col_sage, 0.45 + 0.35 * cos(q.x * 2.0 - theta));
        } else if (i % 4 == 2) {
            pigment = mix(col_sienna, col_ochre, 0.30 + 0.40 * cos(q.x * 3.1 + theta * 2.0));
        } else {
            pigment = mix(col_sage, col_slate, 0.40 + 0.40 * sin(q.x * 2.2 - theta));
        }

        // Granulation texture inside pigment wash
        float gran = 0.78 + 0.44 * fbm(q * 18.0 + vec2(fi * 5.1 + c2 * 0.3, s2 * 0.3));
        float wash_alpha = clamp((body * 0.46 + crest * 0.32) * gran, 0.0, 0.78);

        // Subtractive glaze blending on high-key washi paper
        col = mix(col, pigment, wash_alpha);
        // Darkened mineral capillary edge (wet-into-wet water-line)
        col = mix(col, mix(pigment, col_slate, 0.55), tide_ring * 0.52);
    }

    // Fine poly-rhythmic interference contour threads across the whole field
    float moire_phase = (q.y * 28.0)
                      + 1.6 * sin(q.x * 4.5 + theta)
                      + 1.1 * cos(q.x * 7.8 - theta * 2.0)
                      + 0.7 * sin((q.x + q.y) * 11.0 + theta * 3.0);
    float contour_line = smoothstep(0.92, 0.995, cos(moire_phase));
    col = mix(col, col_slate, contour_line * 0.22);

    float dither = (hash12(gl_FragCoord.xy + vec2(c3 * 11.0, s3 * 17.0)) - 0.5) * 0.012;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

