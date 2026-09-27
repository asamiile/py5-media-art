// Bright-pass for bloom: keeps what is brighter than `threshold` (soft knee).
#ifdef GL_ES
precision highp float;
#endif
#define PROCESSING_TEXTURE_SHADER

uniform sampler2D texture;
uniform float threshold;
uniform float knee;

varying vec4 vertTexCoord;

void main() {
  vec3 c = texture2D(texture, vertTexCoord.st).rgb;
  float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
  float w = smoothstep(threshold - knee, threshold + knee, lum);
  gl_FragColor = vec4(c * w, 1.0);
}
