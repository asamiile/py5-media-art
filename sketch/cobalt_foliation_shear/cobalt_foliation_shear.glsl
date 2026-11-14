#version 150

uniform vec2 u_resolution;
uniform float u_phase;
uniform float u_act_fold;
uniform float u_act_shear;

out vec4 fragColor;

const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

float hash21(vec2 p) {
    p = fract(p * vec2(234.34, 435.345));
    p += dot(p, p + 34.23);
    return fract(p.x * p.y);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float aspect = u_resolution.x / u_resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    // 27-degree diagonal sweep coordinate system (s = along diagonal, n = across strata)
    float ang = 0.4712389; // ~27 deg
    float ca = cos(ang);
    float sa = sin(ang);
    vec2 q = vec2(ca * p.x + sa * p.y, -sa * p.x + ca * p.y);

    // Multi-act symplectic shear & homoclinic folding
    float band_raw = q.y * 6.5;
    float band_idx = floor(band_raw);
    float band_f = fract(band_raw) - 0.5;

    // Alternating shear velocity per stratum
    float dir = mod(band_idx, 2.0) * 2.0 - 1.0;
    float s_adv = q.x * 4.2 + dir * u_phase + 0.37 * band_idx;

    // Reeb foliation leaf function inside each diagonal stratum:
    // Asymptotic tangential clamping near stratum boundaries (+/- 0.5)
    // plus Act II homoclinic saddle-whorl perturbation
    float boundary_stretch = tan(clamp(band_f * 2.65, -1.32, 1.32));
    float saddle_whorl = u_act_fold * (
        0.85 * sin(s_adv * 2.0 - u_phase * 2.0) * cos(band_f * PI)
        + 0.42 * cos(s_adv * 3.0 + band_idx * 1.3 + u_phase)
    );
    float psi = boundary_stretch + 0.55 * sin(s_adv + saddle_whorl) + u_act_shear * 0.35 * cos(q.x * 7.0 - u_phase);

    // High-frequency foliation leaf contours
    float leaf_wave = 0.5 + 0.5 * cos(psi * 9.5 - dir * u_phase);
    float leaf_sharp = smoothstep(0.62, 0.96, leaf_wave);
    float sub_leaf = smoothstep(0.78, 0.98, 0.5 + 0.5 * sin(psi * 19.0 + u_phase));

    // Separatrix boundary ridge between adjacent diagonal strata
    float sep_dist = abs(abs(band_f) - 0.485);
    float sep_ridge = exp(-sep_dist * 68.0);

    // Rich Saturated Color Field Palette:
    // Deep forest viridian (#0a3830) <-> Deep cobalt ultramarine (#132c66) <-> Teal-emerald (#126862)
    // with luminous burnt sienna (#d94e28), cadmium gold (#f4b024), coral-vermilion (#f06438), and warm ivory (#f6efe2)
    vec3 viridian_deep = vec3(0.039, 0.220, 0.188);
    vec3 cobalt_deep   = vec3(0.075, 0.173, 0.400);
    vec3 emerald_mid   = vec3(0.071, 0.408, 0.384);
    vec3 burnt_sienna  = vec3(0.851, 0.306, 0.157);
    vec3 cadmium_gold  = vec3(0.957, 0.690, 0.141);
    vec3 coral_verm    = vec3(0.941, 0.392, 0.220);
    vec3 warm_ivory    = vec3(0.965, 0.937, 0.886);

    // Alternate base color field across strata with smooth internal gradients
    float stratum_tone = 0.5 + 0.5 * sin(band_idx * 1.15 + q.x * 1.4);
    vec3 base_col = mix(viridian_deep, cobalt_deep, stratum_tone);
    base_col = mix(base_col, emerald_mid, 0.42 * smoothstep(-0.4, 0.4, sin(psi * 1.8)));

    // Warm complementary foliation bands (burnt sienna & coral vermilion)
    float warm_zone = 0.5 + 0.5 * sin(psi * 2.4 + band_idx * 0.8 - u_phase);
    vec3 warm_band = mix(burnt_sienna, coral_verm, smoothstep(0.25, 0.85, warm_zone));
    vec3 col = mix(base_col, warm_band, (0.38 + 0.24 * u_act_fold) * smoothstep(0.25, 0.88, leaf_wave));

    // Crisp cadmium-gold foliation leaves
    col = mix(col, cadmium_gold, 0.68 * leaf_sharp);

    // Fine warm-ivory secondary holonomy filaments & separatrix ridges
    col = mix(col, warm_ivory, 0.48 * sub_leaf * (0.4 + 0.6 * warm_zone));
    col = mix(col, mix(cadmium_gold, warm_ivory, 0.55), 0.78 * sep_ridge);

    // Subtle mineral pigment micro-grain
    float grain = (hash21(gl_FragCoord.xy + vec2(u_phase * 19.0, u_phase * 31.0)) - 0.5) * 0.025;
    col = clamp(col + grain, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

