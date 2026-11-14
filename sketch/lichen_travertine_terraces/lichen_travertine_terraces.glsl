#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform float seed;
uniform float sweepAngle;

#include "noise.glsl"

void main() {
  vec2 p = (gl_FragCoord.xy - 0.5 * resolution.xy) / resolution.y;

  // Rotate coordinate system into diagonal stratified sweep
  mat2 rot = mat2(cos(sweepAngle), -sin(sweepAngle), sin(sweepAngle), cos(sweepAngle));
  vec2 q = rot * p;

  // Organic scalloped warping of the diagonal horizon strata (gour / rimstone dam morphogenesis)
  float tFlow = time * 0.14;
  float lobeWarp1 = fbm(vec3(q.x * 2.4 + seed, q.y * 1.6 - tFlow * 0.4, tFlow * 0.25), 5);
  float lobeWarp2 = fbm(vec3(q.x * 5.8 - seed * 0.5, q.y * 3.8 - tFlow * 0.7, tFlow * 0.35), 4);

  // Scalloped cusp profile characteristic of travertine rimstone pools (abs(sin) lobes)
  float scallop = 0.085 * abs(sin(q.x * 4.5 + lobeWarp1 * 2.8)) + 0.035 * abs(cos(q.x * 9.2 - lobeWarp2 * 2.2));
  float elevation = (q.y + 0.65) + 0.22 * lobeWarp1 + 0.07 * lobeWarp2 - scallop;

  // Quantize into 16 diagonal stepped travertine terraces with smooth calcified lips
  float numTerraces = 15.0;
  float scaledElev = elevation * numTerraces - time * 0.38;
  float terraceIdx = floor(scaledElev);
  float terraceFract = fract(scaledElev);

  // Terrace lip ridge (sharp rise at terrace boundary) & flat pool basin
  float lipMask = smoothstep(0.76, 0.96, terraceFract) * (1.0 - smoothstep(0.96, 1.0, terraceFract));
  float lipShadow = smoothstep(0.0, 0.16, terraceFract);

  // Turing-like micro-crenulation / calcified flute ribs perpendicular to the terrace lip
  float microRibs = 0.5 + 0.5 * sin(q.x * 68.0 + lobeWarp2 * 14.0 + terraceIdx * 1.7);
  float lichenBand = smoothstep(0.58, 0.84, terraceFract) * (1.0 - lipMask);

  // Cascading thermal water ripples inside each pool basin
  float poolRipple = sin((terraceFract * 18.0) - time * 3.4 + lobeWarp2 * 6.0);
  float caustic = smoothstep(0.45, 0.95, poolRipple) * (1.0 - smoothstep(0.65, 0.92, terraceFract));

  // Mid-Tone Atmospheric Dusk / Celadon Slate Palette
  vec3 duskSlate   = vec3(0.212, 0.235, 0.251); // #363c40
  vec3 celadonPool = vec3(0.290, 0.365, 0.384); // #4a5d62
  vec3 mistAqua    = vec3(0.447, 0.549, 0.565); // #728c90
  vec3 chalkRim    = vec3(0.894, 0.875, 0.831); // #e4dfd4
  vec3 amberLichen = vec3(0.847, 0.549, 0.196); // #d88c32

  // Pool depth gradient across each terrace step
  vec3 col = mix(duskSlate, celadonPool, smoothstep(0.08, 0.62, terraceFract));
  col = mix(col, mistAqua, caustic * 0.52);

  // Thermophilic amber-ochre lichen accretion zone just behind the calcified rim
  col = mix(col, amberLichen, lichenBand * (0.55 + 0.45 * microRibs) * 0.82);

  // Calcified travertine chalk lip with micro-fluted ribs
  col = mix(col, chalkRim, lipMask * (0.72 + 0.28 * microRibs));

  // Subtle drop-shadow under each overhanging terrace dam
  col *= (0.74 + 0.26 * lipShadow);

  // Mineral grain texture
  float mineralGrain = snoise(vec3(gl_FragCoord.xy * 0.28 + seed * 9.0, 0.0)) * 0.018;
  col += mineralGrain;

  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}

