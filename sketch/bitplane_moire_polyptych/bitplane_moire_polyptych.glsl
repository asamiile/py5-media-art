#ifdef GL_ES
precision highp float;
#endif

uniform vec2 resolution;
uniform float time;
uniform float duration;
uniform float seed;

#include "noise.glsl"

float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

// Emulate bitwise XOR on quantized integer coordinates [0..63]
float bitXorPattern(vec2 uv, float scale) {
  vec2 q = floor(mod(uv * scale, 64.0));
  float acc = 0.0;
  float b = 32.0;
  for (int i = 0; i < 6; i++) {
    float bx = step(b, mod(q.x, b * 2.0));
    float by = step(b, mod(q.y, b * 2.0));
    float xored = abs(bx - by);
    acc += xored * b;
    b *= 0.5;
  }
  return acc / 63.0;
}

void main() {
  vec2 uv = gl_FragCoord.xy / resolution.xy;
  float aspect = resolution.x / resolution.y;
  vec2 p = vec2((uv.x - 0.5) * aspect, uv.y - 0.5);

  // 4-Act Temporal Progression across 17s (normalized phase u in [0, 1])
  float u = clamp(time / max(duration, 1.0), 0.0, 1.0);
  // Act I (0..0.22): Carrier lock | Act II (0.22..0.52): Raster shear
  // Act III (0.52..0.82): Moire bitplane cascade | Act IV (0.82..1.0): Constructivist resolution
  float shearEnv = smoothstep(0.12, 0.38, u) * (1.0 - smoothstep(0.80, 0.96, u));
  float moireEnv = smoothstep(0.35, 0.65, u) * (1.0 - 0.45 * smoothstep(0.84, 0.98, u));

  // Full-Canvas Polyptych Subdivision (asymmetric rhythmic constructivist matrix)
  vec2 grid1 = vec2(8.0, 5.0);
  vec2 cellId1 = floor(uv * grid1);
  vec2 cellUv1 = fract(uv * grid1);
  float h1 = hash21(cellId1 + floor(seed));

  // Sub-subdivide selected cells into finer rhythmic registers
  vec2 subSplit = (h1 < 0.35) ? vec2(2.0, 1.0) : ((h1 < 0.72) ? vec2(1.0, 3.0) : vec2(2.0, 2.0));
  vec2 cellId2 = floor(cellUv1 * subSplit);
  vec2 localUv = fract(cellUv1 * subSplit);
  float cellHash = hash21(cellId1 * 7.13 + cellId2 * 3.71 + floor(seed));

  // Analog scanline tear / horizontal phase displacement inside each polyptych register
  float scanBand = floor(localUv.y * (12.0 + floor(cellHash * 24.0)));
  float glitchPulse = sin(time * (2.5 + cellHash * 4.0) + scanBand * 0.9 + cellHash * 6.28);
  float horizSlip = shearEnv * 0.18 * sign(glitchPulse) * pow(max(0.0, abs(glitchPulse) - 0.45), 1.6);

  vec2 warpedLocal = localUv;
  warpedLocal.x = fract(warpedLocal.x + horizSlip);

  // Mode 1: High-frequency dual-grating Moiré interferometry
  float freqA = 14.0 + floor(cellHash * 22.0);
  float angleA = (cellHash > 0.5 ? 0.0 : 1.5707963) + 0.18 * moireEnv * sin(time * 1.4 + cellHash * 6.28);
  float angleB = angleA + (0.08 + 0.26 * moireEnv) * cos(time * 1.1 - cellHash * 4.0);
  vec2 dirA = vec2(cos(angleA), sin(angleA));
  vec2 dirB = vec2(cos(angleB), sin(angleB));

  float waveA = sin(dot(warpedLocal - 0.5, dirA) * freqA * 6.2831853 + time * 3.2);
  float waveB = sin(dot(warpedLocal - 0.5, dirB) * (freqA * 1.08) * 6.2831853 - time * 2.6);
  float moire = smoothstep(-0.15, 0.15, waveA * waveB);

  // Mode 2: Bitplane XOR carpet weaving
  float xorVal = bitXorPattern(
    warpedLocal + vec2(time * 0.035 * (cellHash - 0.5), 0.0),
    1.0 + moireEnv * 1.5
  );
  float bitGate = step(0.46 + 0.18 * sin(time * 2.0 + cellHash * 9.0), xorVal);

  // Combine signal modes per cell
  float pattern = mix(moire, bitGate, step(0.52, fract(cellHash * 3.7)));

  // Clean structural cell margin (pure visual polyptych grid seam, zero text)
  vec2 edgeDist = min(localUv, 1.0 - localUv);
  float seam = smoothstep(0.008, 0.024, min(edgeDist.x * subSplit.x, edgeDist.y * subSplit.y));

  // Stark Constructivist High-Contrast Palette
  vec3 carbonBlack = vec3(0.067, 0.075, 0.090); // #111317
  vec3 boneWhite   = vec3(0.949, 0.937, 0.914); // #f2efe9
  vec3 vermilion   = vec3(0.902, 0.204, 0.149); // #e63426
  vec3 ultramarine = vec3(0.094, 0.227, 0.831); // #183ad4
  vec3 ochre       = vec3(0.949, 0.706, 0.094); // #f2b418

  // Assign constructivist color role per cell
  vec3 fgColor = boneWhite;
  vec3 bgColor = carbonBlack;
  if (cellHash < 0.24) {
    fgColor = vermilion;
    bgColor = carbonBlack;
  } else if (cellHash < 0.46) {
    fgColor = boneWhite;
    bgColor = ultramarine;
  } else if (cellHash < 0.62) {
    fgColor = carbonBlack;
    bgColor = boneWhite;
  } else if (cellHash < 0.74) {
    fgColor = ochre;
    bgColor = carbonBlack;
  }

  // Dynamic phase-inversion flash in Act III inside accent cells
  float invertCell = step(0.88, sin(time * 1.8 + cellHash * 15.0) * moireEnv);
  float finalSignal = abs(pattern - invertCell);

  vec3 col = mix(bgColor, fgColor, finalSignal);
  col = mix(carbonBlack, col, seam);

  gl_FragColor = vec4(col, 1.0);
}

