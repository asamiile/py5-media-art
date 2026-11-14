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

    // 4x3 full-canvas rhythmic subband grid
    vec2 grid_dim = vec2(4.0, 3.0);
    vec2 g_pos = uv * grid_dim;
    vec2 cell_id = floor(g_pos);
    vec2 cell_uv = fract(g_pos) - 0.5;

    float cell_idx = cell_id.y * 4.0 + cell_id.x;
    float cell_phase = cell_idx * 0.52359877;

    // Camera depth traversal through frequency subbands
    float depth_zoom = 1.0 + 0.28 * sin(theta + cell_phase);
    vec2 q = cell_uv * depth_zoom;

    // Walsh-Hadamard & Cosine Packet basis frequencies per tile
    float kx = (2.0 + mod(cell_idx * 3.0, 7.0)) * 3.14159265;
    float ky = (2.0 + mod(cell_idx * 5.0 + 1.0, 6.0)) * 3.14159265;

    // Phase-locked horizontal packet slip (quantized step shear)
    float row_quant = floor((cell_uv.y + 0.5) * 16.0) / 16.0;
    float slip = 0.085 * sign(sin(row_quant * 12.566 + theta + cell_phase))
               * pow(abs(sin(theta * 2.0 + cell_phase * 1.5)), 3.0);
    q.x += slip;

    // 2D Wavelet / DCT interference packet
    float wave_u = cos(q.x * kx + s1 * 2.4 + cell_phase) * cos(q.y * ky - c1 * 2.0);
    float wave_v = sin((q.x + q.y) * (kx * 0.65) - c2 * 2.2) * cos((q.x - q.y) * (ky * 0.65) + s2 * 1.8);

    // Walsh square-wave sign quantization
    float walsh_x = sign(sin(q.x * kx * 0.5 + c1 * 1.4));
    float walsh_y = sign(cos(q.y * ky * 0.5 + s1 * 1.4));
    float walsh = walsh_x * walsh_y;

    // Bit-quantizer staircase (dead-zone uniform quantizer)
    float raw_signal = 0.55 * wave_u + 0.35 * wave_v + 0.22 * walsh;
    float quant_levels = 5.0 + 3.0 * sin(theta + cell_id.x * 0.9 - cell_id.y * 1.1);
    float quantized = floor(raw_signal * quant_levels + 0.5) / quant_levels;
    float quant_error = (raw_signal - quantized) * quant_levels;

    // Global cross-tile carrier harmonic sweep
    float global_carrier = sin(p.x * 18.0 - p.y * 12.0 + c3 * 2.5 + s1 * 3.0);
    float global_packet = smoothstep(0.15, 0.85, 0.5 + 0.5 * sin(quant_error * 3.14159 + global_carrier * 0.8));

    // Chroma subsampling block pattern (4:2:0 / 4:1:1 macroblock quantization)
    vec2 macro_uv = floor((cell_uv + 0.5) * vec2(24.0, 18.0)) / vec2(24.0, 18.0);
    float macro_hash = hash12(macro_uv * 100.0 + cell_id * 17.0);
    float bit_gate = step(0.58, fract(macro_hash + 0.25 * c1 - 0.18 * s2));

    // Cell border crisp gutters
    vec2 border_d = abs(cell_uv) - vec2(0.476, 0.468);
    float in_tile = 1.0 - smoothstep(-0.006, 0.003, max(border_d.x, border_d.y));
    float frame_line = smoothstep(-0.012, -0.004, max(border_d.x, border_d.y)) * in_tile;

    // Deep Nocturnal Monochrome + Single Accent palette
    vec3 col_obsidian = vec3(0.039, 0.047, 0.067); // #0a0c11
    vec3 col_slate    = vec3(0.094, 0.118, 0.165); // #181e2a
    vec3 col_silver   = vec3(0.560, 0.620, 0.710); // #8f9eb5
    vec3 col_ice      = vec3(0.902, 0.929, 0.969); // #e6edf7
    vec3 col_amber    = vec3(1.000, 0.369, 0.141); // #ff5e24 (Single Accent)

    // Compose luminance & quantized contours
    float contour = smoothstep(0.42, 0.04, abs(quant_error));
    float fine_grid = smoothstep(0.92, 0.99, cos((cell_uv.x + 0.5) * 96.0 * 3.14159))
                    + smoothstep(0.92, 0.99, cos((cell_uv.y + 0.5) * 72.0 * 3.14159));

    vec3 tile_col = mix(col_obsidian, col_slate, 0.35 + 0.65 * clamp(quantized + 0.5, 0.0, 1.0));
    tile_col = mix(tile_col, col_silver, 0.55 * global_packet * (0.4 + 0.6 * bit_gate));
    tile_col = mix(tile_col, col_ice, 0.78 * contour);

    // Single Accent activation on high-frequency quantization residual spikes
    float spike_mask = smoothstep(0.68, 0.92, abs(raw_signal)) * smoothstep(0.25, 0.85, bit_gate + 0.5 * contour);
    float pulse_band = smoothstep(0.76, 0.96, sin(cell_uv.y * 18.85 - theta * 2.0 + cell_phase));
    float accent_amt = clamp(spike_mask * 0.85 + pulse_band * contour * 0.75, 0.0, 1.0);
    tile_col = mix(tile_col, col_amber, accent_amt);

    // Subtle scanline micro-texture & border framing
    tile_col += col_silver * (0.07 * clamp(fine_grid, 0.0, 1.0));
    tile_col = mix(tile_col, col_silver * 0.65, frame_line * 0.7);

    vec3 bg_col = col_obsidian * (0.82 + 0.18 * cos(uv.y * 3.14159));
    vec3 col = mix(bg_col, tile_col, in_tile);

    // Outer margin subtle ticks styling via pure geometry
    float dither = (hash12(gl_FragCoord.xy + vec2(c1 * 13.0, s1 * 19.0)) - 0.5) * 0.018;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

