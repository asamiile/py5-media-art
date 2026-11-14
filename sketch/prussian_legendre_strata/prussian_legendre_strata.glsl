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

    // Rich Saturated Color Field palette (Prussian Blue / Malachite -> Burnt Sienna / Cadmium Gold)
    vec3 col_prussian  = vec3(0.039, 0.118, 0.251); // #0a1e40
    vec3 col_malachite = vec3(0.055, 0.341, 0.314); // #0e5750
    vec3 col_turquoise = vec3(0.141, 0.659, 0.620); // #24a89e
    vec3 col_sienna    = vec3(0.753, 0.267, 0.141); // #c04424
    vec3 col_cadmium   = vec3(0.957, 0.675, 0.141); // #f4ac24
    vec3 col_ivory     = vec3(0.988, 0.945, 0.855); // #fcf1da

    // Diagonally swept coordinate frame (18 deg sweep)
    float ang = 0.314159;
    mat2 rot = mat2(cos(ang), -sin(ang), sin(ang), cos(ang));
    vec2 q = rot * p;

    // Rich saturated background gradient across diagonal horizon
    float bg_t = clamp(0.5 + 0.65 * q.y + 0.15 * sin(q.x * 2.2 + theta), 0.0, 1.0);
    vec3 col = mix(col_prussian, col_malachite, smoothstep(0.0, 0.65, bg_t));
    col = mix(col, col_sienna * 0.65, smoothstep(0.45, 1.0, 1.0 - bg_t));

    // Stratified Legendre-Chebyshev Polynomial Foliation
    // Map q into [-1, 1] domain with poly-rhythmic harmonic phase modulation
    float x = clamp(q.x * 0.92, -0.98, 0.98);
    float y = q.y * 1.45;

    // Chebyshev T_n(x) = cos(n * acos(x)) evaluated via trigonometric identity on u
    float u_arg = q.x * 2.35;
    float T2 = cos(2.0 * u_arg + theta * 1.0);
    float T3 = cos(3.0 * u_arg - theta * 2.0);
    float T4 = cos(4.0 * u_arg + theta * 3.0);
    float T5 = cos(5.0 * u_arg - theta * 1.0);
    float T7 = cos(7.0 * u_arg + theta * 2.0);

    // 7 Stratified algebraic horizon bands with poly-rhythmic phase interference
    for (int i = 0; i < 7; i++) {
        float fi = float(i);
        float y_center = -0.45 + fi * 0.15;
        float dir = (i % 2 == 0) ? 1.0 : -1.0;

        float poly_curve = y_center
            + 0.065 * cos((2.0 + fi * 0.5) * u_arg + theta * dir + fi * 0.9)
            + 0.042 * sin((4.0 + fi * 0.4) * u_arg - theta * 2.0 * dir + fi * 1.7)
            + 0.024 * cos((7.0 - fi * 0.3) * u_arg + theta * 3.0 + fi * 2.5);

        float dy = q.y - poly_curve;
        float band_glow = exp(-abs(dy) * 28.0);
        float band_sheet = smoothstep(0.028, -0.008, dy) * exp(max(dy, -0.22) * 10.0);

        vec3 band_col;
        if (i % 3 == 0) {
            band_col = mix(col_sienna, col_cadmium, 0.5 + 0.5 * T3);
        } else if (i % 3 == 1) {
            band_col = mix(col_malachite, col_turquoise, 0.5 + 0.5 * T4);
        } else {
            band_col = mix(col_cadmium, col_sienna, 0.5 + 0.5 * T2);
        }

        col = mix(col, band_col, clamp(band_sheet * 0.52 + band_glow * 0.38, 0.0, 0.84));
    }

    // Fine Lissajous-Chebyshev caustic foliation contours across the entire field
    float psi = y * 18.0 + 1.45 * T2 + 1.05 * T3 + 0.72 * T5 + 0.45 * T7;
    float caustic_line = smoothstep(0.88, 0.995, cos(psi));
    float caustic_sub  = smoothstep(0.90, 0.995, sin(psi * 0.5 - u_arg * 6.0 + theta * 2.0));

    col = mix(col, col_cadmium, caustic_line * 0.62);
    col = mix(col, col_turquoise, caustic_sub * 0.45);
    col = mix(col, col_ivory, pow(caustic_line * caustic_sub, 0.75) * 0.85);

    float dither = (hash12(gl_FragCoord.xy + vec2(c2 * 13.0, s3 * 19.0)) - 0.5) * 0.014;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

