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

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    float aspect = resolution.x / resolution.y;
    vec2 p = (uv - 0.5) * vec2(aspect, 1.0);

    float theta = u_loop * 6.28318530718;
    float c1 = cos(theta);
    float s1 = sin(theta);
    float c2 = cos(theta * 2.0);
    float s2 = sin(theta * 2.0);

    // Mid-Tone Atmospheric Dusk / Celadon Slate palette
    vec3 col_dusk_slate = vec3(0.173, 0.220, 0.251); // #2c3840
    vec3 col_sage_slate = vec3(0.239, 0.306, 0.282); // #3d4e48
    vec3 col_mist_teal  = vec3(0.510, 0.659, 0.667); // #82a8aa
    vec3 col_soft_chalk = vec3(0.922, 0.902, 0.855); // #ebe6da
    vec3 col_ochre_gold = vec3(0.894, 0.588, 0.212); // #e49636
    vec3 col_terracotta = vec3(0.808, 0.369, 0.251); // #ce5e40

    // 5x3 Full-Canvas Rhythmic Matrix
    vec2 grid_dim = vec2(5.0, 3.0);
    vec2 g_pos = uv * grid_dim;
    vec2 cell_id = floor(g_pos);
    vec2 cell_uv = fract(g_pos) - 0.5;
    vec2 q = cell_uv * vec2(aspect * 3.0 / 5.0, 1.0);

    float cell_idx = cell_id.y * 5.0 + cell_id.x;
    float cell_phase = cell_idx * 0.418879;

    // Directional advection wave vector per cell (propagating across the matrix)
    float flow_ang = 0.35 * sin(cell_idx * 1.1) + 0.22 * cell_id.y - 0.18 * cell_id.x;
    vec2 flow_dir = vec2(cos(flow_ang), sin(flow_ang));
    vec2 ortho_dir = vec2(-flow_dir.y, flow_dir.x);

    float u_flow = dot(q, flow_dir);
    float v_ortho = dot(q, ortho_dir);

    // Global traveling wavefront sweeping diagonally across all 15 cells
    float global_front = sin(p.x * 5.5 - p.y * 3.5 - theta * 2.0);

    // Cell-specific morphogenetic reaction-diffusion wavenumber & anisotropy
    float k_main = 16.0 + mod(cell_idx * 3.0, 9.0) * 2.2;
    float k_sub  = 11.0 + mod(cell_idx * 5.0, 7.0) * 1.8;

    // Traveling Turing stripe + labyrinthine reaction-diffusion wavefronts
    float shear_warp = 0.14 * sin(v_ortho * k_sub - theta + cell_phase)
                     + 0.08 * cos(u_flow * (k_sub * 0.7) - theta * 2.0);

    float rd_u = sin((u_flow + shear_warp) * k_main - theta * 2.0 + cell_phase);
    float rd_v = cos((v_ortho * 0.85 - shear_warp * 0.7) * k_sub + sin(u_flow * k_main * 0.5 - theta));
    float activator = 0.58 * rd_u + 0.42 * rd_v + 0.22 * global_front;

    // Inhibitor lateral inhibition halo & sharp reaction front
    float morph_ridge = smoothstep(-0.12, 0.38, activator) * smoothstep(0.95, 0.42, activator);
    float morph_core  = smoothstep(0.32, 0.76, activator);
    float front_crest = smoothstep(0.86, 0.99, cos((u_flow + shear_warp) * k_main - theta * 2.0 + cell_phase));

    // Mid-tone atmospheric dusk base inside tile
    vec3 tile_base = mix(col_dusk_slate, col_sage_slate, 0.5 + 0.5 * sin(cell_idx * 0.9 + v_ortho * 3.0));
    vec3 tile_col = mix(tile_base, col_mist_teal, morph_ridge * 0.78);
    tile_col = mix(tile_col, col_soft_chalk, morph_core * 0.74);

    // Warm ochre-amber & terracotta reaction catalyst along traveling wavefront crests
    float catalyst = front_crest * (0.55 + 0.45 * sin(v_ortho * 12.0 - theta * 2.0 + cell_phase));
    vec3 warm_accent = mix(col_ochre_gold, col_terracotta, 0.5 + 0.5 * cos(cell_idx + u_flow * 8.0));
    tile_col = mix(tile_col, warm_accent, clamp(catalyst * 0.85, 0.0, 0.88));

    // Clean cellular framing & subtle slate gutter
    vec2 border_d = abs(cell_uv) - vec2(0.478, 0.470);
    float in_tile = 1.0 - smoothstep(-0.006, 0.003, max(border_d.x, border_d.y));
    float rim_line = smoothstep(-0.012, -0.004, max(border_d.x, border_d.y)) * in_tile;

    tile_col = mix(tile_col, col_mist_teal * 0.82, rim_line * 0.55);
    vec3 gutter_col = col_dusk_slate * 0.84;
    vec3 col = mix(gutter_col, tile_col, in_tile);

    float dither = (hash12(gl_FragCoord.xy + vec2(c1 * 13.0, s2 * 19.0)) - 0.5) * 0.014;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}
