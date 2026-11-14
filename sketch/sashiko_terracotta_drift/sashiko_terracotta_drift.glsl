#version 150

uniform vec2 resolution;
uniform float time;
uniform float seed;
uniform float actDensity;
uniform float actShear;

out vec4 fragColor;

const float PI = 3.14159265359;

float hash21(vec2 p) {
    p = fract(p * vec2(127.1, 311.7) + seed * 0.01);
    p += dot(p, p + 34.5);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    float aspect = resolution.x / resolution.y;
    vec2 p = vec2(uv.x * aspect, 1.0 - uv.y);

    // Multi-act billowing textile shear displacement
    vec2 shear_offset = actShear * 0.028 * vec2(
        sin(p.y * 9.0 - time * 1.4),
        cos(p.x * 7.0 + time * 1.2)
    );
    vec2 q = p + shear_offset;

    // High-Key Mineral & Washi / Boro Linen Patchwork Ground (#ede8dc - #e2ddd0)
    vec2 patch_id = floor(q * vec2(3.5, 3.0) + vec2(0.3 * noise(q * 4.0)));
    float patch_rnd = hash21(patch_id);

    vec3 col_alabaster = vec3(0.929, 0.910, 0.863); // #ede8dc
    vec3 col_linen     = vec3(0.890, 0.867, 0.808); // #e3ddce
    vec3 col_sage_tint = vec3(0.863, 0.886, 0.859); // #dce2db
    vec3 col_ochre_wash = vec3(0.914, 0.855, 0.765); // warm mineral wash

    vec3 base_col = mix(col_alabaster, col_linen, step(0.35, patch_rnd));
    base_col = mix(base_col, col_sage_tint, step(0.68, patch_rnd) * 0.75);
    base_col = mix(base_col, col_ochre_wash, step(0.85, patch_rnd) * 0.65);

    // Fine woven linen warp/weft micro-texture across 100% of the canvas
    float weave_x = sin(gl_FragCoord.x * 1.35) * 0.5 + 0.5;
    float weave_y = sin(gl_FragCoord.y * 1.35) * 0.5 + 0.5;
    float weave = (weave_x * 0.5 + weave_y * 0.5) - 0.5;
    base_col += weave * 0.024;

    // Fine geometric Sashiko under-weave (intersecting diagonal & diamond hitomezashi stitches)
    vec2 st_uv = q * 28.0;
    vec2 cell = floor(st_uv);
    vec2 f = fract(st_uv) - 0.5;

    // Diagonal stitch segments that phase-shift over time
    float h_cell = hash21(cell + floor(time * 0.25));
    float d1 = abs(f.x + f.y);
    float d2 = abs(f.x - f.y);
    float dash_mask = smoothstep(0.42, 0.28, max(abs(f.x), abs(f.y)));

    float diag_stitch = 0.0;
    if (h_cell < 0.5 * actDensity) {
        diag_stitch = (1.0 - smoothstep(0.04, 0.09, d1)) * dash_mask;
    } else if (h_cell < 0.95 * actDensity) {
        diag_stitch = (1.0 - smoothstep(0.04, 0.09, d2)) * dash_mask;
    }

    // Color of diagonal sashiko under-stitches alternates by patch
    vec3 col_terracotta = vec3(0.729, 0.290, 0.188); // #ba4a30
    vec3 col_slate      = vec3(0.149, 0.212, 0.251); // #263640
    vec3 col_ochre      = vec3(0.792, 0.525, 0.157); // #ca8628

    vec3 stitch_col = (patch_rnd < 0.45) ? col_slate : ((patch_rnd < 0.78) ? col_terracotta : col_ochre);
    vec3 col = mix(base_col, stitch_col, diag_stitch * 0.58);

    // Subtle boro patch seam shadow
    vec2 patch_f = fract(q * vec2(3.5, 3.0) + vec2(0.3 * noise(q * 4.0)));
    float seam = 1.0 - smoothstep(0.0, 0.025, min(min(patch_f.x, 1.0 - patch_f.x), min(patch_f.y, 1.0 - patch_f.y)));
    col = mix(col, col_slate, seam * 0.18);

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}

