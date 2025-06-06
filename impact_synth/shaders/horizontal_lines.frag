#version 120

uniform sampler2D texture;
uniform float time;

void main() {
    vec2 uv = gl_TexCoord[0].xy;
    vec4 color = texture2D(texture, uv);
    
    // Add horizontal lines (more intense on every 10th pixel)
    // Avoid using modulo (%) by using a periodic function
    float y_pos = gl_FragCoord.y;
    float line_pattern = abs(fract(y_pos / 10.0) - 0.5);
    float line_effect = 0.0;
    
    // If we're in the first 20% of the cycle, make the line visible
    if (line_pattern > 0.4) {
        line_effect = 0.5;
    }
    
    // Pulsing effect based on time
    float pulse = sin(time * 2.0) * 0.5 + 0.5;
    
    // Add yellow horizontal lines
    gl_FragColor = mix(color, vec4(1.0, 1.0, 0.0, 1.0), line_effect * pulse);
}
