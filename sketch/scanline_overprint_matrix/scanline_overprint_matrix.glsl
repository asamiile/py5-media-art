#version 150

uniform vec2 resolution;
uniform float time;
uniform float seed;
uniform float camX;
uniform float camY;
uniform float camZoom;

out vec4 fragColor;

const float PI = 3.14159265359;

float hash21(vec2 p) {
    p = fract(p * vec2(127.1, 311.7) + seed * 0.01);
    p += dot(p, p + 34.5);
    return fract(p.x * p.y);
}

// Evaluates one cellular signal polyptych layer at a given parallax depth
float eval_signal_layer(vec2 uv_centered, float depth_scale, float ch_offset, float t) {
    // Parallax translation + camera zoom
    vec2 p = uv_centered / (camZoom * mix(0.75, 1.35, depth_scale * 0.5))
           + vec2(camX, camY) * depth_scale
           + vec2(ch_offset * 0.008, -ch_offset * 0.005);

    // Primary cellular matrix (e.g., 7x4 scale) with hierarchical sub-cells
    vec2 grid_p = p * 3.6;
    vec2 cell_id = floor(grid_p);
    vec2 cell_uv = fract(grid_p);

    float h = hash21(cell_id + depth_scale * 13.0);
    // Subdivide ~45% of cells into 2x2 sub-registers
    if (h > 0.55) {
        grid_p *= 2.0;
        cell_id = floor(grid_p);
        cell_uv = fract(grid_p);
        h = hash21(cell_id + depth_scale * 29.0);
    }

    // Crisp margin between polyptych cells
    vec2 margin = smoothstep(0.03, 0.06, cell_uv) * smoothstep(0.03, 0.06, 1.0 - cell_uv);
    float mask = margin.x * margin.y;

    // Analog horizontal scanline phase-slip displacement inside each cell
    float scan_row = floor(cell_uv.y * (16.0 + floor(h * 24.0)));
    float row_rnd = hash21(vec2(scan_row, h * 97.0));
    float slip = 0.14 * sin(t * (1.8 + row_rnd * 3.0) + scan_row * 0.7) * step(0.45, row_rnd);

    vec2 q = cell_uv - 0.5;
    q.x += slip;

    // 4 distinct analog signal waveform archetypes per cell
    float pattern = 0.0;
    float mode = floor(fract(h * 7.13) * 4.0);

    if (mode < 1.0) {
        // Archetype 0: High-frequency FM modulated horizontal scanlines
        float freq = 18.0 + floor(h * 28.0);
        float fm = sin(q.x * (6.0 + h * 10.0) + t * 2.4) * 0.22;
        pattern = smoothstep(-0.15, 0.25, sin((q.y + fm) * freq * PI));
    } else if (mode < 2.0) {
        // Archetype 1: Quantized Risograph halftone dot matrix with traveling wave envelope
        float dots = 10.0 + floor(h * 12.0);
        vec2 d_uv = fract(q * dots) - 0.5;
        float wave = 0.5 + 0.42 * sin(length(q) * 14.0 - t * 3.2 + h * 6.28);
        pattern = 1.0 - smoothstep(wave * 0.42 - 0.06, wave * 0.42 + 0.06, length(d_uv));
    } else if (mode < 3.0) {
        // Archetype 2: Diagonal stepped bit-shift raster bars
        float quant_y = floor((q.y + 0.5) * 12.0) / 12.0;
        float stripes = sin((q.x + quant_y * 0.65) * 28.0 + t * 3.0);
        pattern = smoothstep(0.0, 0.2, stripes);
    } else {
        // Archetype 3: Crossed linear frequency grating interference
        float g1 = sin((q.x * cos(h * 3.14) + q.y * sin(h * 3.14)) * 32.0 - t * 2.5);
        float g2 = cos((q.x - q.y * 0.8) * 24.0 + t * 1.8);
        pattern = smoothstep(0.1, 0.45, g1 * g2);
    }

    // Thin crisp register frame around active cells
    float border = (1.0 - (smoothstep(0.06, 0.085, cell_uv.x) * smoothstep(0.06, 0.085, 1.0 - cell_uv.x)
                         * smoothstep(0.06, 0.085, cell_uv.y) * smoothstep(0.06, 0.085, 1.0 - cell_uv.y))) * mask;

    return clamp(pattern * mask * 0.85 + border * 0.55, 0.0, 1.0);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    float aspect = resolution.x / resolution.y;
    // Match py5 screen coordinates (y=0 top)
    vec2 p = vec2((uv.x - 0.5) * aspect, (1.0 - uv.y) - 0.5);

    // Warm cream Risograph paper ground (#efe9dc) with tactile fiber grain
    vec3 paper = vec3(0.937, 0.914, 0.863);
    float fiber = hash21(gl_FragCoord.xy * 0.35) * 0.5 + hash21(gl_FragCoord.xy * 0.12) * 0.5;
    paper -= (fiber - 0.5) * 0.032;

    // Evaluate 3 parallax depth planes for the 3 Risograph spot inks:
    // Plane 1 (Deep): Peacock Teal Ink (#14968c)
    // Plane 2 (Mid):  Fluorescent Coral Ink (#f05442)
    // Plane 3 (Near): Deep Indigo Ink (#1c2a5e)
    float ink_teal   = eval_signal_layer(p, 0.72, -1.0, time);
    float ink_coral  = eval_signal_layer(p + vec2(0.09, 0.05), 1.12, 0.0, time * 1.05);
    float ink_indigo = eval_signal_layer(p - vec2(0.06, 0.08), 1.55, 1.0, time * 0.95);

    // Subtractive Risograph ink transmittance colors (where 1.0 = no absorption, ink_col = full spot ink)
    vec3 trans_teal   = vec3(0.08, 0.62, 0.58);
    vec3 trans_coral  = vec3(0.95, 0.33, 0.26);
    vec3 trans_indigo = vec3(0.14, 0.20, 0.44);

    // Multiplicative overprint blending so overlapping coral + teal + indigo produce authentic rich overprint darks
    vec3 col = paper;
    col *= mix(vec3(1.0), trans_teal,   ink_teal * 0.78);
    col *= mix(vec3(1.0), trans_coral,  ink_coral * 0.82);
    col *= mix(vec3(1.0), trans_indigo, ink_indigo * 0.72);

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}

