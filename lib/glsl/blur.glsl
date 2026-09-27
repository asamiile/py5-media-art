// Separable 9-tap Gaussian blur. `direction` is (1,0) or (0,1) scaled by the spread.
#ifdef GL_ES
precision highp float;
#endif
#define PROCESSING_TEXTURE_SHADER

uniform sampler2D texture;
uniform vec2 texOffset;
uniform vec2 direction;

varying vec4 vertTexCoord;

void main() {
  vec2 uv = vertTexCoord.st;
  vec2 d = direction * texOffset;
  vec3 c = texture2D(texture, uv).rgb * 0.2270270270;
  c += texture2D(texture, uv + d * 1.3846153846).rgb * 0.3162162162;
  c += texture2D(texture, uv - d * 1.3846153846).rgb * 0.3162162162;
  c += texture2D(texture, uv + d * 3.2307692308).rgb * 0.0702702703;
  c += texture2D(texture, uv - d * 3.2307692308).rgb * 0.0702702703;
  gl_FragColor = vec4(c, 1.0);
}
