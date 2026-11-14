#version 150

uniform vec2 u_resolution;
uniform float u_phase;

out vec4 fragColor;

const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

float hash21(vec2 p) {
    p = fract(p * vec2(234.34, 435.345));
    p += dot(p, p + 34.23);
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

vec2 get_source_base(int idx, float hw, float hh) {
    if (idx < 5) {
        float t = float(idx) / 4.0;
        return vec2(mix(-hw * 0.88, hw * 0.88, t), hh);
    } else if (idx < 10) {
        float t = float(idx - 5) / 4.0;
        return vec2(mix(-hw * 0.88, hw * 0.88, t), -hh);
    } else if (idx < 13) {
        float t = float(idx - 10) / 2.0;
        return vec2(-hw, mix(-hh * 0.65, hh * 0.65, t));
    } else {
        float t = float(idx - 13) / 2.0;
        return vec2(hw, mix(-hh * 0.65, hh * 0.65, t));
    }
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float aspect = u_resolution.x / u_resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    float hw = aspect * 0.48;
    float hh = 0.47;

    // Subtle anisotropic mineral refraction in the raw linen medium
    float n1 = noise2d(p * 4.5 + vec2(cos(u_phase) * 0.25, sin(u_phase) * 0.25));
    float n2 = noise2d(p * 9.5 - vec2(sin(u_phase) * 0.35, cos(u_phase) * 0.35));
    vec2 p_warped = p + 0.034 * vec2(n1 - 0.5, n2 - 0.5);

    // Evaluate 1st, 2nd, and 3rd closest Eikonal arrival times from the 16 boundary perimeter sources
    float d1 = 1e5;
    float d2 = 1e5;
    float d3 = 1e5;
    int id1 = 0;
    int id2 = 0;

    for (int i = 0; i < 16; i++) {
        float fi = float(i);
        float s_phase = fi * 2.3999632; // Golden angle phase distribution
        vec2 base_p = get_source_base(i, hw, hh);
        vec2 src_p = base_p + vec2(
            0.085 * cos(u_phase + s_phase),
            0.075 * sin(u_phase * 2.0 + s_phase * 1.3)
        );
        float w_i = 0.045 * sin(u_phase - s_phase);

        vec2 diff = p_warped - src_p;
        float dist = length(diff) + w_i;
        if (dist < d1) {
            d3 = d2;
            d2 = d1;
            id2 = id1;
            d1 = dist;
            id1 = i;
        } else if (dist < d2) {
            d3 = d2;
            d2 = dist;
            id2 = i;
        } else if (dist < d3) {
            d3 = dist;
        }
    }

    // Medial-axis shock distance (Rankine-Hugoniot collision locus where d1 == d2)
    float shock_gap = d2 - d1;
    float triple_gap = d3 - d1;

    // Primary medial-axis shock network & secondary bisector veins
    float primary_shock = exp(-shock_gap * 68.0);
    float secondary_shock = exp(-abs(shock_gap - 0.065) * 85.0);
    float triple_node = exp(-triple_gap * 42.0);

    // Inward-traveling Eikonal wavefronts propagating from the boundary sources toward the interior shocks
    float wave_arg = d1 * 38.0 - u_phase * 3.0;
    float wave_crest = smoothstep(0.62, 0.96, 0.5 + 0.5 * cos(wave_arg));
    float harmonic_crest = smoothstep(0.78, 0.98, 0.5 + 0.5 * sin(d2 * 54.0 - u_phase * 2.0));

    // High-Key Mineral & Washi / Raw Linen Palette across 100% of the canvas:
    // Warm Linen Ground (#ede8dc - #e4ddd0)
    // Iron-Gall Slate (#243440), Burnt Terracotta (#b84a2e), Raw Gold Ochre (#c98826), Malachite Sage (#387268)
    vec3 linen_light = vec3(0.929, 0.910, 0.863); // #ede8dc
    vec3 linen_warm  = vec3(0.894, 0.867, 0.812); // #e4ddd0
    vec3 iron_slate  = vec3(0.141, 0.204, 0.251); // #243440
    vec3 terracotta  = vec3(0.722, 0.290, 0.180); // #b84a2e
    vec3 gold_ochre  = vec3(0.788, 0.533, 0.149); // #c98826
    vec3 malachite   = vec3(0.220, 0.447, 0.408); // #387268

    // Full-canvas high-key raw linen base with subtle cell-to-cell mineral tint
    float cell_parity = fract(float(id1) * 0.3183 + float(id2) * 0.173);
    vec3 paper = mix(linen_light, linen_warm, 0.45 * n1 + 0.35 * cell_parity);

    // Tint each Voronoi/Eikonal basin with delicate mineral washes near the shock front
    vec3 basin_tint = (mod(float(id1), 3.0) < 0.5)
        ? gold_ochre
        : ((mod(float(id1), 3.0) < 1.5) ? malachite : terracotta);
    vec3 col = mix(paper, basin_tint, 0.24 * exp(-shock_gap * 8.5));

    // Travelling Eikonal wavefront rings in raw gold ochre and malachite sage
    col = mix(col, gold_ochre, 0.46 * wave_crest);
    col = mix(col, malachite, 0.40 * harmonic_crest);

    // Secondary shock halo in burnt terracotta
    col = mix(col, terracotta, 0.74 * secondary_shock);

    // Crisp iron-slate medial-axis shock network & terracotta triple-junction cores
    col = mix(col, iron_slate, 0.92 * primary_shock);
    col = mix(col, terracotta, 0.68 * triple_node * (1.0 - 0.5 * primary_shock));

    // Fine linen weave & mineral paper grain
    float weave_x = sin(gl_FragCoord.x * 0.85) * sin(gl_FragCoord.y * 0.85);
    float grain = (hash21(gl_FragCoord.xy + vec2(u_phase * 17.0, u_phase * 29.0)) - 0.5) * 0.022;
    col = clamp(col + 0.008 * weave_x + grain, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}
