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

    // Rich Saturated Color Field palette (Ultramarine / Indigo -> Magenta -> Amber / Vermilion)
    vec3 col_indigo      = vec3(0.039, 0.075, 0.235); // #0a133c
    vec3 col_ultramarine = vec3(0.118, 0.243, 0.722); // #1e3eb8
    vec3 col_magenta     = vec3(0.722, 0.118, 0.424); // #b81e6c
    vec3 col_vermilion   = vec3(0.925, 0.282, 0.157); // #ec4828
    vec3 col_amber       = vec3(0.973, 0.698, 0.141); // #f8b224
    vec3 col_cream       = vec3(0.988, 0.949, 0.863); // #fcf2dc

    // Continuous full-bleed color field gradient base
    float field_grad = clamp(0.5 + 0.48 * (p.x * 0.65 - p.y * 0.75 + 0.25 * sin(theta + p.x * 2.5)), 0.0, 1.0);
    vec3 base_col = mix(col_indigo, col_ultramarine, smoothstep(0.0, 0.55, field_grad));
    base_col = mix(base_col, col_magenta, smoothstep(0.35, 0.88, field_grad));

    // Quantized horizontal raster phase-slip displacement across scanbands
    float band_y = floor(uv.y * 48.0) / 48.0;
    float slip_gate = step(0.66, fract(sin(band_y * 91.7) * 43758.5453 + u_loop * 2.0));
    float h_slip = slip_gate * 0.042 * sin(band_y * 37.0 + theta * 2.0);
    vec2 q = p + vec2(h_slip, 0.0);

    // 4 Poly-Rhythmic Phase-Interference Harmonic Wave Lattices
    float a1 = 0.28 + 0.08 * c1;
    float a2 = -0.34 + 0.08 * s1;
    float a3 = 0.78 - 0.06 * c2;
    float a4 = -0.82 + 0.06 * s2;

    float u1 = q.x * cos(a1) + q.y * sin(a1);
    float u2 = q.x * cos(a2) + q.y * sin(a2);
    float u3 = q.x * cos(a3) + q.y * sin(a3);
    float u4 = q.x * cos(a4) + q.y * sin(a4);

    // Frequency modulation (FM) carriers at harmonic temporal ratios 1:2:3:4
    float fm1 = sin(u1 * 28.0 + theta * 1.0 + 1.8 * sin(u2 * 9.0 - theta * 2.0));
    float fm2 = cos(u2 * 32.0 - theta * 2.0 + 1.6 * cos(u3 * 11.0 + theta * 1.0));
    float fm3 = sin(u3 * 22.0 + theta * 3.0 + 1.4 * sin(u4 * 8.0 - theta * 3.0));
    float fm4 = cos(u4 * 26.0 - theta * 4.0 + 1.5 * cos(u1 * 10.0 + theta * 2.0));

    // Beat envelope & phase-locked interference superposition
    float super_wave = 0.34 * fm1 + 0.30 * fm2 + 0.20 * fm3 + 0.16 * fm4;
    float beat_env = 0.5 + 0.5 * cos((u1 - u2) * 14.0 + theta * 2.0) * sin((u3 - u4) * 12.0 - theta);

    // Subcarrier quantization contours & luminous beat crests
    float contour = smoothstep(0.24, 0.02, abs(fract(super_wave * 3.5 + 0.5) - 0.5));
    float crest_warm = smoothstep(0.18, 0.78, super_wave + 0.32 * beat_env);
    float crest_hot  = smoothstep(0.55, 0.94, super_wave * beat_env + 0.25 * fm1);

    // Fine scanline phosphor grille modulation across the full canvas
    float scanline = 0.88 + 0.12 * cos(gl_FragCoord.y * 1.5707963);
    float sub_carrier = 0.5 + 0.5 * sin(q.x * 160.0 + super_wave * 6.2831853 + theta * 3.0);

    vec3 col = base_col;
    col = mix(col, col_vermilion, crest_warm * 0.78);
    col = mix(col, col_amber, (contour * 0.68 + crest_hot * 0.55) * (0.65 + 0.35 * sub_carrier));
    col = mix(col, col_cream, pow(contour * crest_warm, 1.6) * 0.72);

    // Highlight phase-slipped raster bands with warm amber-magenta shift
    col = mix(col, mix(col_amber, col_magenta, 0.4), slip_gate * 0.24 * contour);
    col *= scanline;

    float dither = (hash12(gl_FragCoord.xy + vec2(c3 * 13.0, s3 * 19.0)) - 0.5) * 0.015;
    col = clamp(col + dither, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}

