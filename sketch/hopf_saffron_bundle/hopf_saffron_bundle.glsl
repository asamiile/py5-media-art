#version 150

uniform vec2 resolution;
uniform float time;
uniform float seed;
uniform float phase;

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

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = mat2(0.8, 0.6, -0.6, 0.8);
    for (int i = 0; i < 4; i++) {
        v += a * noise(p);
        p = rot * p * 2.05 + vec2(1.7, 9.2);
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    float aspect = resolution.x / resolution.y;

    // Match py5 screen coordinates where y=0 is top; anchor focal zone at (0.64, 0.40)
    vec2 p = vec2((uv.x - 0.64) * aspect, (1.0 - uv.y) - 0.40);
    float r = length(p);
    float ang = atan(p.y, p.x);

    // Rich Saturated Color Field: Deep Prussian Cobalt (#0a1d38) to Viridian Teal (#0f3844)
    // transitioning to Warm Burnt Ochre-Sienna (#6e2e18) near the off-center stereographic focal zone
    vec3 col_prussian = vec3(0.039, 0.114, 0.220);
    vec3 col_teal     = vec3(0.059, 0.220, 0.267);
    vec3 col_sienna   = vec3(0.431, 0.180, 0.094);
    vec3 col_saffron  = vec3(0.880, 0.540, 0.150);

    float flow = fbm(p * 2.0 + vec2(cos(phase) * 0.22, sin(phase) * 0.22));
    float sweep = smoothstep(-1.2, 0.9, p.x * 0.65 - p.y * 0.55 + (flow - 0.5) * 0.45);

    vec3 col = mix(col_prussian, col_teal, sweep);

    // Crisp logarithmic stereographic loxodrome caustics radiating from the upper-right focal zone
    float lox1 = sin(log(r + 0.14) * 9.0 - ang * 2.0 + phase + flow * 2.2);
    float lox2 = cos(log(r + 0.18) * 14.0 + ang * 3.0 - phase * 0.5 + flow * 1.8);
    float caustic_ridge = exp(-abs(lox1 * 0.65 + lox2 * 0.35) * 5.5);

    float warm_aura = exp(-r * 1.25) * (0.45 + 0.55 * smoothstep(-0.4, 0.8, lox1));
    col = mix(col, col_sienna, warm_aura * 0.72);
    col += col_saffron * caustic_ridge * exp(-r * 0.85) * 0.22;

    // Fine turquoise-cobalt harmonic contours across the expansive lower-left negative space
    float far_contour = exp(-abs(sin(r * 11.0 - phase + ang + flow * 2.5)) * 7.0);
    col += vec3(0.14, 0.46, 0.52) * far_contour * smoothstep(0.25, 1.4, r) * 0.18;

    // Fine grain
    float g = hash21(gl_FragCoord.xy * 0.5 + time) - 0.5;
    col += g * 0.014;

    fragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
