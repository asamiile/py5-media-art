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

vec2 hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
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
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 4; i++) {
        v += a * noise2d(p);
        p = rot * p * 2.02 + vec2(13.1, 7.7);
        a *= 0.5;
    }
    return v;
}

// Voronoi edge distance (returns vec2(nearest_dist, edge_ridge_dist))
vec2 voronoi_ridge(vec2 x, float phase) {
    vec2 n = floor(x);
    vec2 f = fract(x);

    vec2 mg, mr;
    float md = 8.0;
    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            vec2 g = vec2(float(i), float(j));
            vec2 o = hash22(n + g);
            o = 0.5 + 0.42 * sin(phase + 6.2831853 * o);
            vec2 r = g + o - f;
            float d = dot(r, r);
            if (d < md) {
                md = d;
                mr = r;
                mg = g;
            }
        }
    }

    float md2 = 8.0;
    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            vec2 g = mg + vec2(float(i), float(j));
            vec2 o = hash22(n + g);
            o = 0.5 + 0.42 * sin(phase + 6.2831853 * o);
            vec2 r = g + o - f;
            if (dot(mr - r, mr - r) > 0.00001) {
                md2 = min(md2, dot(0.5 * (mr + r), normalize(r - mr)));
            }
        }
    }
    return vec2(sqrt(md), md2);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    float aspect = resolution.x / resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    float theta = u_loop * 6.28318530718;
    float c1 = cos(theta);
    float s1 = sin(theta);

    // Deep Nocturnal Monochrome + Single Accent palette
    vec3 col_indigo   = vec3(0.039, 0.051, 0.078); // #0a0d14
    vec3 col_charcoal = vec3(0.086, 0.110, 0.157); // #161c28
    vec3 col_graphite = vec3(0.282, 0.341, 0.435); // #48576f
    vec3 col_silver   = vec3(0.761, 0.816, 0.894); // #c2d0e4
    vec3 col_frost    = vec3(0.925, 0.953, 0.988); // #ecf3fc
    vec3 col_amber    = vec3(0.961, 0.576, 0.196); // #f59332 (Single Accent)

    // Boundary-to-interior nucleation envelope (strongest near canvas edges & corners, sweeping inward)
    vec2 edge_d = abs(uv - 0.5) * 2.0;
    float boundary_dist = max(edge_d.x * 0.88, edge_d.y);
    float inward_front = 0.32 + 0.22 * sin(theta - length(p) * 3.2);
    float boundary_weight = smoothstep(0.18, 0.95, boundary_dist + 0.28 * fbm(p * 2.6 + vec2(c1 * 0.4, s1 * 0.4)));

    vec3 col = mix(col_indigo, col_charcoal, 0.35 + 0.65 * boundary_weight);

    // Spatial Camera / Depth Traversal across 3 parallax rime-crystal network planes
    vec2 cam_pan = vec2(0.22 * c1, 0.16 * s1);
    float total_vein = 0.0;
    float accent_spark = 0.0;

    for (int layer = 0; layer < 3; layer++) {
        float fl = float(layer);
        // Seamless cyclic depth zoom per layer
        float depth_phase = fract(u_loop + fl / 3.0);
        float z_angle = depth_phase * 6.28318530718;
        float scale = 3.2 + fl * 2.1 + 0.75 * sin(z_angle);
        vec2 parallax = cam_pan * (0.6 + fl * 0.45);

        vec2 q = p * scale + parallax;
        // Domain-warped organic dendrite coordinates
        vec2 warp = vec2(
            fbm(q * 0.85 + vec2(fl * 4.1 + c1 * 0.35, s1 * 0.35)),
            fbm(q * 0.85 + vec2(s1 * 0.35, fl * 7.3 - c1 * 0.35))
        ) - 0.5;
        q += warp * 1.15;

        vec2 vr = voronoi_ridge(q, theta + fl * 2.094);
        float ridge = vr.y;

        // Primary & secondary dendritic ice-vein filaments
        float vein_main = smoothstep(0.085, 0.006, ridge);
        float vein_halo = exp(-ridge * 14.0);
        float sub_branch = smoothstep(0.035, 0.002, abs(sin(vr.x * 18.0 - theta * 2.0)) * (ridge + 0.04));

        // Modulate growth from canvas boundary inward
        float growth_mask = smoothstep(0.10, 0.82, boundary_weight + 0.35 * (1.0 - fl * 0.25));
        float layer_intensity = (vein_main * 0.75 + sub_branch * 0.42 + vein_halo * 0.28) * growth_mask;

        vec3 layer_col = mix(col_graphite, col_silver, clamp(vein_main + sub_branch * 0.6, 0.0, 1.0));
        layer_col = mix(layer_col, col_frost, pow(vein_main, 2.2));

        float depth_alpha = (layer == 0) ? 0.52 : ((layer == 1) ? 0.68 : 0.82);
        col = mix(col, layer_col, clamp(layer_intensity * depth_alpha, 0.0, 0.88));

        // Single Accent ignition where boundary-grown filaments collide near triple junctions
        float triple_node = smoothstep(0.032, 0.002, ridge) * smoothstep(0.52, 0.22, vr.x);
        float front_wave = smoothstep(0.65, 0.96, sin(length(p) * 9.0 + theta * 2.0 - fl * 1.4));
        accent_spark += triple_node * (0.45 + 0.55 * front_wave) * growth_mask;
        total_vein += vein_main;
    }

    // Apply restrained warm amber gold single accent at filament collision nodes
    col = mix(col, col_amber, clamp(accent_spark * 1.15, 0.0, 0.92));

    // Soft nocturnal atmospheric mist veil
    float mist = fbm(p * 1.8 - cam_pan * 0.8);
    col += col_silver * (0.045 * mist * boundary_weight);

    float dither = (hash12(gl_FragCoord.xy + vec2(c1 * 19.0, s1 * 23.0)) - 0.5) * 0.014;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

