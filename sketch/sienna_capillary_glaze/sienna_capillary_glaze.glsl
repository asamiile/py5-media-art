#version 150

uniform vec2 u_resolution;
uniform float u_phase;
uniform float u_act_bloom;
uniform float u_act_front;

out vec4 fragColor;

const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

float hash21(vec2 p) {
    p = fract(p * vec2(127.1, 311.7));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise2d(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash21(i + vec2(0.0, 0.0)), hash21(i + vec2(1.0, 0.0)), u.x),
        mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), u.x),
        u.y
    );
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.80, -0.60, 0.60, 0.80);
    for (int i = 0; i < 5; i++) {
        v += a * noise2d(p);
        p = rot * p * 2.04 + vec2(1.7, 9.2);
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float aspect = u_resolution.x / u_resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    // Golden-ratio asymmetric focal anchor in the upper-left third:
    // screen uv ~ (0.31, 0.62) in bottom-up GLSL coords
    vec2 anchor1 = vec2(-0.34, 0.12) + 0.04 * vec2(cos(u_phase), sin(u_phase));
    // Secondary counter-weight satellite bloom in lower-left/mid zone
    vec2 anchor2 = vec2(-0.18, -0.22) + 0.05 * vec2(sin(u_phase * 2.0), -cos(u_phase));

    // Domain-warped painterly fluid coordinates
    vec2 flow_p = p * 2.2 + vec2(0.22 * cos(u_phase), 0.22 * sin(u_phase));
    float w1 = fbm(flow_p);
    float w2 = fbm(flow_p + vec2(3.4, -2.1) + 0.85 * w1);
    vec2 warp = vec2(w1 - 0.5, w2 - 0.5) * (0.36 + 0.22 * u_act_bloom);

    // Asymmetric anisotropic distance from the golden-ratio pigment core
    // Stretched toward the right-hand negative space so capillary plumes sweep rightward
    vec2 d1 = (p + warp) - anchor1;
    d1.x *= 0.72; // elongated horizontal reach
    float r1 = length(d1);
    float ang1 = atan(d1.y, d1.x);

    vec2 d2 = (p + warp * 0.85) - anchor2;
    d2.x *= 0.82;
    float r2 = length(d2);

    // Combined organic wet-on-wet pigment potential
    float lobe_mod = 0.08 * sin(ang1 * 5.0 - u_phase) + 0.05 * cos(ang1 * 9.0 + u_phase * 2.0);
    float a_r = r1 + lobe_mod;
    float b_r = r2 * 1.25 + 0.04 * cos(ang1 * 4.0 + u_phase);
    float h_k = clamp(0.5 + 0.5 * (b_r - a_r) / 0.28, 0.0, 1.0);
    float field = mix(b_r, a_r, h_k) - 0.28 * h_k * (1.0 - h_k);

    // Rich Saturated Color Field Palette:
    // Expansive right-side negative space: Deep Burnt Sienna (#701e12) -> Alizarin Madder (#a8281e) -> Raw Amber Glaze (#d66820)
    // Asymmetric left-third pigment mass: Lapis Ultramarine (#143474) -> Verdigris Turquoise (#189c90) -> Naples Gold (#f6c438)
    vec3 sienna_deep   = vec3(0.439, 0.118, 0.071);
    vec3 madder_crimson = vec3(0.659, 0.157, 0.118);
    vec3 raw_amber     = vec3(0.839, 0.408, 0.125);
    vec3 lapis_indigo  = vec3(0.078, 0.204, 0.455);
    vec3 verdigris     = vec3(0.094, 0.612, 0.565);
    vec3 naples_gold   = vec3(0.965, 0.769, 0.220);
    vec3 warm_cream    = vec3(0.976, 0.933, 0.855);

    // Rothko-scale atmospheric glaze gradient across the right-hand negative space
    float glaze_grad = smoothstep(-0.85, 0.85, p.x * 0.85 + p.y * 0.45 + 0.35 * (w2 - 0.5));
    vec3 bg_field = mix(sienna_deep, madder_crimson, smoothstep(0.0, 0.65, glaze_grad));
    bg_field = mix(bg_field, raw_amber, 0.58 * smoothstep(0.35, 1.0, glaze_grad) * (0.5 + 0.5 * w1));

    // Subtle horizontal painterly brush-wash strata in the negative space
    float wash_strata = 0.5 + 0.5 * sin(p.y * 14.0 + w1 * 5.5 - u_phase);
    bg_field = mix(bg_field, raw_amber * 1.12, 0.16 * wash_strata);

    // Expanding wet-on-wet pigment radius driven by Act II (u_act_bloom)
    float bloom_rad = 0.44 + 0.18 * u_act_bloom;
    float inside_core = 1.0 - smoothstep(0.06, bloom_rad, field);

    // Concentric wet-edge coffee-ring tide lines radiating asymmetrically from the core
    float tide_phase = field * 18.0 - u_phase * 2.0 + w2 * 3.2;
    float tide_ring = smoothstep(0.68, 0.97, 0.5 + 0.5 * cos(tide_phase)) * exp(-max(0.0, field - 0.15) * 1.85);

    // Sharp outer wet-edge granulation rim (classic watercolor capillary ring)
    float outer_rim = exp(-abs(field - bloom_rad * 0.88) * 26.0);
    float second_rim = exp(-abs(field - (bloom_rad + 0.19 + 0.06 * u_act_front)) * 22.0);

    // Compose asymmetric pigment bloom over the burnt-sienna/madder color field
    vec3 core_col = mix(lapis_indigo, verdigris, smoothstep(0.08, bloom_rad * 0.82, field + 0.12 * (w1 - 0.5)));
    vec3 col = mix(bg_field, core_col, inside_core * 0.92);

    // Luminous verdigris & Naples-gold wet-edge granulation rings
    col = mix(col, verdigris * 1.15, 0.55 * tide_ring);
    col = mix(col, naples_gold, 0.78 * outer_rim);
    col = mix(col, mix(naples_gold, warm_cream, 0.45), 0.68 * second_rim);

    // Fine mineral paper & pigment granulation texture
    float gran = (hash21(gl_FragCoord.xy * 0.75 + vec2(u_phase * 13.0, -u_phase * 17.0)) - 0.5) * 0.032;
    col = clamp(col + gran, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}
