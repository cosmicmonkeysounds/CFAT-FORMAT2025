// Example fragment shader for Carpet Hotel
// This demonstrates how to apply shader effects to your video floors
// Place this in: data/shaders/example.glsl

#ifdef GL_ES
precision mediump float;
#endif

uniform sampler2D texture;
uniform vec2 resolution;
uniform float time;

varying vec4 vertColor;
varying vec4 vertTexCoord;

void main() {
  vec2 uv = vertTexCoord.xy;
  
  // Get the video pixel color
  vec4 color = texture2D(texture, uv);
  
  // Example effect 1: Subtle color shift based on time
  // color.r += sin(time * 0.5) * 0.1;
  
  // Example effect 2: Scanlines
  // float scanline = sin(uv.y * resolution.y * 2.0) * 0.1;
  // color.rgb -= scanline;
  
  // Example effect 3: Vignette
  vec2 center = uv - 0.5;
  float vignette = 1.0 - dot(center, center) * 0.8;
  color.rgb *= vignette;
  
  gl_FragColor = color;
}
