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
        p = rot * p * 2.02 + vec2(11.3, 6.9);
        a *= 0.5;
    }
    return v;
}

float screen_dot(vec2 px, float angle, float pitch, float density) {
    float c = cos(angle);
    float s = sin(angle);
    vec2 g = mat2(c, -s, s, c) * px / pitch;
    vec2 cell = fract(g) - 0.5;
    float r = length(cell) * 1.41421356;
    return smoothstep(density + 0.22, density - 0.18, r);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    float aspect = resolution.x / resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    float theta = u_loop * 6.28318530718;
    float c1 = cos(theta);
    float s1 = sin(theta);

    // Warm cream Risograph paper ground across 100% of the canvas
    vec3 paper_cream = vec3(0.941, 0.914, 0.863); // #f0e9dc
    vec3 paper_oat   = vec3(0.906, 0.875, 0.816); // #e7dfd0
    float paper_grain = (noise2d(gl_FragCoord.xy * 0.18) - 0.5) * 0.032;
    vec3 col = mix(paper_cream, paper_oat, 0.35 + 0.35 * fbm(p * 2.4)) + paper_grain;

    // 3 Translucent Spot-Ink Absorption Vectors (1 - InkRGB for subtractive overprint)
    vec3 ink_coral  = vec3(0.949, 0.322, 0.251); // Fluorescent Coral (#f25240)
    vec3 ink_teal   = vec3(0.063, 0.588, 0.549); // Peacock Teal (#10968c)
    vec3 ink_indigo = vec3(0.110, 0.165, 0.384); // Deep Federal Indigo (#1c2a62)

    // Diagonal sweep coordinate frame (-15 deg stratified tectonic-escarpment tilt)
    float tilt_ang = -0.26;
    mat2 tilt = mat2(cos(tilt_ang), -sin(tilt_ang), sin(tilt_ang), cos(tilt_ang));
    vec2 q = tilt * p;

    float coral_accum  = 0.0;
    float teal_accum   = 0.0;
    float indigo_accum = 0.0;

    // 9 Stratified escarpment horizons with cyclic camera depth traversal
    for (int i = 0; i < 9; i++) {
        float fi = float(i);
        // Seamless cyclic depth progression from distant upper horizon (d=0) to foreground (d=1)
        float d = fract((fi + u_loop) / 9.0);
        // Smooth boundary fade-in at top horizon & fade-out at foreground exit
        float fade = smoothstep(0.0, 0.14, d) * smoothstep(1.0, 0.86, d);

        // Perspective horizon height & spatial parallax scale
        float y_hor = mix(0.44, -0.48, pow(d, 1.15));
        float freq_x = mix(5.8, 2.2, d);
        float amp_y = mix(0.025, 0.088, d);
        float phase_i = fi * 2.0943951 + theta * ((i % 2 == 0) ? 1.0 : -1.0);

        // Slight Risograph drum registration offset between the 3 spot-ink channels
        vec2 reg_coral  = vec2(0.0045 * cos(theta + fi), 0.0035 * sin(theta + fi));
        vec2 reg_teal   = vec2(-0.0045 * sin(theta - fi), -0.0035 * cos(theta - fi));
        vec2 reg_indigo = vec2(0.0025 * sin(theta * 2.0), -0.0025 * cos(theta * 2.0));

        vec2 qc = q + reg_coral;
        vec2 qt = q + reg_teal;
        vec2 qi = q + reg_indigo;

        float ridge_base = amp_y * (
            0.60 * sin(q.x * freq_x + phase_i)
            + 0.30 * cos(q.x * freq_x * 1.85 - phase_i * 0.5)
            + 0.22 * (fbm(vec2(q.x * freq_x * 0.7, fi * 3.1 + c1 * 0.4)) - 0.5)
        );

        float dy_c = qc.y - (y_hor + ridge_base + 0.008 * sin(qc.x * 9.0 + theta));
        float dy_t = qt.y - (y_hor + ridge_base + 0.008 * cos(qt.x * 8.0 - theta));
        float dy_i = qi.y - (y_hor + ridge_base);

        // Stratified escarpment body + sunlit crest rim
        float body_c = smoothstep(0.012, -0.005, dy_c) * exp(max(dy_c, -0.24) * 11.0);
        float body_t = smoothstep(0.012, -0.005, dy_t) * exp(max(dy_t, -0.24) * 11.0);
        float crest_i = exp(-abs(dy_i) * 48.0) + 0.45 * smoothstep(0.008, -0.004, dy_i) * exp(max(dy_i, -0.16) * 16.0);

        // Role weight per stratum so coral, teal, and indigo interleave and overprint
        float w_coral  = (i % 3 == 0) ? 0.68 : ((i % 3 == 1) ? 0.28 : 0.14);
        float w_teal   = (i % 3 == 1) ? 0.68 : ((i % 3 == 2) ? 0.32 : 0.16);
        float w_indigo = (i % 3 == 2) ? 0.62 : 0.28;

        coral_accum  += body_c * w_coral * fade;
        teal_accum   += body_t * w_teal * fade;
        indigo_accum += crest_i * w_indigo * fade;
    }

    // Apply authentic Risograph stochastic + angled halftone screen modulation
    float ht_coral  = screen_dot(gl_FragCoord.xy, 0.2618, 6.5, clamp(coral_accum * 0.72, 0.0, 0.92));
    float ht_teal   = screen_dot(gl_FragCoord.xy, 1.3090, 6.5, clamp(teal_accum * 0.72, 0.0, 0.92));
    float ht_indigo = screen_dot(gl_FragCoord.xy, 0.7854, 5.5, clamp(indigo_accum * 0.68, 0.0, 0.90));

    float cov_coral  = mix(clamp(coral_accum * 0.62, 0.0, 0.85), ht_coral, 0.32);
    float cov_teal   = mix(clamp(teal_accum * 0.62, 0.0, 0.85), ht_teal, 0.32);
    float cov_indigo = mix(clamp(indigo_accum * 0.58, 0.0, 0.82), ht_indigo, 0.28);

    // Subtractive overprint ink multiplication on warm cream paper
    col *= mix(vec3(1.0), ink_coral,  cov_coral);
    col *= mix(vec3(1.0), ink_teal,   cov_teal);
    col *= mix(vec3(1.0), ink_indigo, cov_indigo);

    float dither = (hash12(gl_FragCoord.xy + vec2(c1 * 17.0, s1 * 23.0)) - 0.5) * 0.012;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

