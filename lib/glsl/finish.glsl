// Final grade: bloom add, exposure, filmic tone map, chromatic aberration,
// vignette and film grain. Every effect is off at 0.
#ifdef GL_ES
precision highp float;
#endif
#define PROCESSING_TEXTURE_SHADER

uniform sampler2D texture;
uniform sampler2D bloomTex;
uniform vec2 resolution;
uniform float time;

uniform float bloom;       // bloom strength
uniform float exposure;    // linear gain before tone mapping
uniform float tonemap;     // 0 = off, 1 = full ACES-like curve
uniform float aberration;  // radial RGB split, fraction of width
uniform float vignette;    // edge darkening
uniform float grain;       // grain amplitude
uniform float saturation;  // 1 = unchanged
uniform float bloomFlipY;  // 1 when the source is an image rather than an offscreen canvas

varying vec4 vertTexCoord;

// Hash without Sine (Dave Hoskins, MIT): no visible lattice at 4K.
float hash(vec2 p) {
  vec3 p3 = fract(vec3(p.xyx) * 0.1031);
  p3 += dot(p3, p3.yzx + 33.33);
  return fract((p3.x + p3.y) * p3.z);
}

vec3 aces(vec3 x) {
  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main() {
  vec2 uv = vertTexCoord.st;
  vec2 fromCenter = uv - 0.5;

  vec2 shift = fromCenter * aberration;
  vec3 c;
  c.r = texture2D(texture, uv + shift).r;
  c.g = texture2D(texture, uv).g;
  c.b = texture2D(texture, uv - shift).b;

  vec2 bloomUv = vec2(uv.x, mix(uv.y, 1.0 - uv.y, bloomFlipY));
  c += texture2D(bloomTex, bloomUv).rgb * bloom;
  c *= exposure;
  c = mix(clamp(c, 0.0, 1.0), aces(c), tonemap);

  float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(vec3(lum), c, saturation);

  float aspect = resolution.x / resolution.y;
  float r = length(fromCenter * vec2(aspect, 1.0)) / length(vec2(aspect, 1.0) * 0.5);
  c *= 1.0 - vignette * smoothstep(0.35, 1.0, r);

  float n = hash(gl_FragCoord.xy + mod(time * 60.0, 997.0) * vec2(37.0, 17.0)) - 0.5;
  c += n * grain;

  gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}
