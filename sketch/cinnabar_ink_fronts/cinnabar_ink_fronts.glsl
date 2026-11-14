#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform float duration;
uniform float seed;
uniform vec2 driftDir;

#include "noise.glsl"

// Compute curl-like 2D warp vector from 3D simplex noise
vec2 curlWarp(vec3 p) {
  float eps = 0.06;
  float n1 = fbm(p + vec3(0.0, eps, 0.0), 4);
  float n2 = fbm(p - vec3(0.0, eps, 0.0), 4);
  float n3 = fbm(p + vec3(eps, 0.0, 0.0), 4);
  float n4 = fbm(p - vec3(eps, 0.0, 0.0), 4);
  return vec2(n1 - n2, -(n3 - n4)) / (2.0 * eps);
}

void main() {
  vec2 uv = gl_FragCoord.xy / resolution.xy;
  vec2 p = (gl_FragCoord.xy - 0.5 * resolution.xy) / resolution.y;

  // Normalized progression with smooth traveling advection
  float phase = time / max(duration, 1.0);
  float adv = time * 0.11;

  vec3 basePos = vec3(p * 1.65 + driftDir * (adv * 0.35) + vec2(seed * 0.13, seed * 0.07), adv * 0.22);
  vec2 w1 = curlWarp(basePos);
  vec2 w2 = curlWarp(basePos * 2.15 + vec3(w1 * 0.45, adv * 0.18 + 7.3));

  vec2 warpedP = p + w1 * 0.28 + w2 * 0.12;

  // Four boundary-nucleating ink fronts advancing inward across the full-bleed canvas
  float swell = 0.32 + 0.28 * sin(phase * 3.14159265);
  float fLeft   = (warpedP.x + 0.92) - (0.55 + swell * 0.42 + 0.22 * fbm(vec3(warpedP * 2.4 + seed, adv * 0.25), 5));
  float fRight  = (0.92 - warpedP.x) - (0.52 + swell * 0.40 + 0.22 * fbm(vec3(warpedP * 2.3 - seed, adv * 0.23 + 3.1), 5));
  float fBottom = (warpedP.y + 0.54) - (0.28 + swell * 0.26 + 0.18 * fbm(vec3(warpedP * 2.7 + seed * 0.5, adv * 0.21 + 9.4), 5));
  float fTop    = (0.54 - warpedP.y) - (0.26 + swell * 0.24 + 0.18 * fbm(vec3(warpedP * 2.6 - seed * 0.5, adv * 0.24 + 14.2), 5));

  // Opposing wave potentials
  float potA = smoothstep(0.45, -0.35, min(fLeft, fBottom));
  float potB = smoothstep(0.45, -0.35, min(fRight, fTop));

  // Fine capillary dendritic veins inside the colliding fronts
  float veinField = fbm(vec3(warpedP * 5.2 + w2 * 0.6, adv * 0.32 + seed), 6);
  float ridge1 = 1.0 - abs(veinField);
  ridge1 = pow(clamp(ridge1, 0.0, 1.0), 4.5);

  float fineRipples = sin((fLeft - fRight) * 26.0 - time * 2.4 + veinField * 5.0);
  float capillaryWave = smoothstep(0.65, 0.98, fineRipples) * exp(-abs(fLeft - fRight) * 2.6);

  // Collision zone where opposing boundary fronts meet in open interior space
  float collision = exp(-pow((fLeft - fRight) * 3.2, 2.0)) + 0.65 * exp(-pow((fBottom - fTop) * 3.6, 2.0));
  collision = clamp(collision, 0.0, 1.4);

  // Palette: Deep Nocturnal Monochrome + Single Cinnabar Accent
  vec3 bgSlate     = vec3(0.055, 0.075, 0.106); // #0e131b
  vec3 sumiShadow  = vec3(0.118, 0.157, 0.216); // #1e2837
  vec3 pewterWash  = vec3(0.345, 0.412, 0.502); // #586980
  vec3 silverMist  = vec3(0.776, 0.831, 0.894); // #c6d4e4
  vec3 cinnabar    = vec3(0.910, 0.322, 0.204); // #e85234

  // Paper grain & wet sumi tonal wash
  float paper = fbm(vec3(p * 14.0 + seed, 0.0), 3) * 0.035;
  float inkBody = clamp(0.55 * potA + 0.55 * potB + 0.25 * veinField, 0.0, 1.0);

  vec3 col = mix(bgSlate, sumiShadow, smoothstep(0.05, 0.55, inkBody));
  col = mix(col, pewterWash, smoothstep(0.35, 0.82, inkBody) * (0.65 + 0.35 * ridge1));
  col = mix(col, silverMist, pow(ridge1, 1.6) * smoothstep(0.25, 0.85, potA + potB) * 0.78);

  // Single restrained accent hue: Molten Cinnabar along colliding wavefront seams and capillary fractures
  float emberMask = clamp(collision * (0.42 + 0.88 * ridge1) + capillaryWave * 0.65, 0.0, 1.0);
  float emberCore = pow(emberMask, 2.2);
  col = mix(col, cinnabar, emberMask * 0.78);
  col += cinnabar * emberCore * 0.95;

  col += paper;
  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}

