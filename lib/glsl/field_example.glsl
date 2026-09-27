// Starting point for a GPU field: domain-warped fbm with a two-tone palette.
// Copy into sketch/<work_name>/ and edit; draw with lib.shaders.draw_fullscreen().
#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform float seed;  // random per run (no fixed seeds)
uniform vec3 colorA;
uniform vec3 colorB;

#include "noise.glsl"

void main() {
  vec2 uv = (gl_FragCoord.xy - 0.5 * resolution) / resolution.y;
  vec3 p = vec3(uv * 2.2 + seed, time * 0.08);
  vec2 warp = vec2(fbm(p, 5), fbm(p + vec3(5.2, 1.3, 0.0), 5));
  float f = fbm(p + vec3(warp * 1.6, 0.0), 6);
  float t = smoothstep(-0.6, 0.7, f);
  vec3 col = mix(colorA, colorB, t);
  col += pow(max(f, 0.0), 3.0) * 2.5;  // bright ridges feed the bloom pass
  gl_FragColor = vec4(col, 1.0);
}
