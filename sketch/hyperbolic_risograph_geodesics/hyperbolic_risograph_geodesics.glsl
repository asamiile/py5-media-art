#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform float seed;
uniform vec2 camDrift;

#include "noise.glsl"

// Evaluate PSL(2, Z) modular tessellation (2, 3, inf) & Ford horocycles in upper half-plane H^2
vec4 hyperbolicModularPlate(vec2 p, float t, vec2 plateOffset) {
  vec2 q = p + plateOffset;

  // Gentle diagonal shear so the ideal boundary sweeps dynamically across the 3840x2160 frame
  float tilt = 0.24 + 0.08 * sin(t * 0.25 + seed * 0.1);
  mat2 rot = mat2(cos(tilt), -sin(tilt), sin(tilt), cos(tilt));
  vec2 rq = rot * q;

  // Create two mirrored hyperbolic upper-half-planes meeting along a sinuous horizon curve
  float horizonWave = 0.08 * sin(rq.x * 2.2 - t * 0.35 + seed);
  float distFromHorizon = abs(rq.y - horizonWave);

  // Map distance from horizon into Im(z) in [0.032, 0.92] where modular folding is maximally rich
  float yHyper = 0.032 + 0.78 * pow(clamp(distFromHorizon * 1.35, 0.0, 1.2), 1.15);
  float xHyper = rq.x * 1.85 + t * 0.28 + camDrift.x;

  // Continuous hyperbolic dilation (modular zoom)
  float zoom = exp(0.32 * sin(t * 0.42 + rq.x * 0.8));
  vec2 z = vec2(xHyper, yHyper * zoom);

  float foldParity = 0.0;
  float minArcDist = 10.0;
  float minAxisDist = 10.0;

  // Iterative PSL(2, Z) fundamental domain reduction:
  // T: z -> z - round(Re(z)),  S: z -> -1/z
  for (int i = 0; i < 12; i++) {
    z.x -= floor(z.x + 0.5);
    minAxisDist = min(minAxisDist, abs(z.x));
    float r2 = dot(z, z);
    minArcDist = min(minArcDist, abs(sqrt(r2) - 1.0));
    if (r2 < 1.0) {
      z = vec2(-z.x, z.y) / max(r2, 1e-5);
      foldParity = 1.0 - foldParity;
    } else {
      break;
    }
  }

  // In the fundamental domain {|Re(z)| <= 0.5, |z| >= 1}:
  // 1) Dual subdivision by imaginary axis Re(z) = 0 gives (2, 3, inf) Schwarz triangles
  float triParity = mod(foldParity + step(0.0, z.x), 2.0);
  // 2) Ford horocycles at Im(z) = const in fundamental domain
  float horocycle = smoothstep(0.42, 0.48, fract(log(max(z.y, 1.0)) * 2.6 - t * 0.45));
  // 3) Geodesic boundary walls (|z| = 1 and Re(z) = 0, +/-0.5)
  float wallDist = min(minArcDist, min(abs(z.x), abs(abs(z.x) - 0.5)));
  float geodesicStroke = smoothstep(0.095, 0.012, wallDist);
  // 4) Cuspidal Ford circle medallions around Im(z) -> 1.0..2.2
  float fordCircle = smoothstep(0.38, 0.12, length(vec2(z.x, z.y - 1.35)));

  return vec4(triParity, geodesicStroke, horocycle, fordCircle);
}

void main() {
  vec2 p = (gl_FragCoord.xy - 0.5 * resolution.xy) / resolution.y;

  // Authentic risograph plate registration offsets (in normalized screen units)
  vec2 regTeal   = vec2(-0.0055,  0.0038);
  vec2 regCoral  = vec2( 0.0062, -0.0042);
  vec2 regIndigo = vec2( 0.0018,  0.0052);

  vec4 fTeal   = hyperbolicModularPlate(p, time, regTeal);
  vec4 fCoral  = hyperbolicModularPlate(p * 1.012, time + 0.14, regCoral);
  vec4 fIndigo = hyperbolicModularPlate(p * 0.988, time - 0.11, regIndigo);

  // Risograph rotated halftone dot screens + warm cotton paper fiber grain
  vec2 pix = gl_FragCoord.xy;
  float htTeal   = 0.5 + 0.5 * sin(pix.x * 0.85 + pix.y * 0.32) * cos(pix.y * 0.85 - pix.x * 0.32);
  float htCoral  = 0.5 + 0.5 * sin(pix.x * 0.78 - pix.y * 0.46) * cos(pix.y * 0.78 + pix.x * 0.46);
  float grain    = snoise(vec3(pix * 0.32 + seed * 11.0, 0.0));
  float fiber    = fbm(vec3(p * 7.5 + seed, 0.0), 4);

  // Plate 1: Teal Spot Ink (dominant Schwarz triangle tiles + horocycle bands)
  float tealMask = clamp(
    fTeal.x * (0.58 + 0.28 * htTeal) + fTeal.z * 0.42 + fTeal.y * 0.35,
    0.0, 1.0
  ) * (0.86 + 0.14 * grain);

  // Plate 2: Fluorescent Coral Spot Ink (conjugate tiles + Ford circle medallions + geodesic arcs)
  float coralMask = clamp(
    (1.0 - fCoral.x) * fCoral.w * (0.76 + 0.24 * htCoral)
    + fCoral.y * 0.68
    + (1.0 - fCoral.x) * 0.32 * smoothstep(0.3, 0.9, htCoral),
    0.0, 1.0
  ) * (0.88 + 0.12 * grain);

  // Plate 3: Deep Indigo Overprint Ink (crisp geodesic skeleton + cuspidal depth)
  float indigoMask = clamp(
    fIndigo.y * 0.88 + fIndigo.w * fIndigo.x * 0.55 + fIndigo.z * 0.24,
    0.0, 1.0
  ) * (0.85 + 0.15 * grain);

  // Warm cotton paper ground (#ede8de) across 100% of the canvas
  vec3 paperCol  = vec3(0.929, 0.910, 0.871) + fiber * 0.024 + grain * 0.015;
  vec3 tealCol   = vec3(0.086, 0.604, 0.557); // #169a8e
  vec3 coralCol  = vec3(0.941, 0.353, 0.275); // #f05a46
  vec3 indigoCol = vec3(0.118, 0.176, 0.361); // #1e2d5c

  // Subtractive risograph overprint multiplication on warm paper
  vec3 col = paperCol;
  col = mix(col, col * mix(vec3(1.0), tealCol * 1.05, 0.88), tealMask * 0.76);
  col = mix(col, mix(coralCol, coralCol * col * 1.12, 0.62), coralMask * 0.80);
  col = mix(col, indigoCol * col * 1.06, indigoMask * 0.86);

  gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
