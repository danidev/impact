#!/usr/bin/env python3
"""
Simple shader test for Pygame + OpenGL.
Renders a colored square and applies a shader with horizontal lines.
"""

import os
import sys
import pygame
import numpy as np
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Try to import OpenGL
try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    HAS_OPENGL = True
    print("OpenGL successfully imported")
except ImportError:
    HAS_OPENGL = False
    print("ERROR: PyOpenGL is required for this test.")
    print("Install with: pip install PyOpenGL PyOpenGL_accelerate")
    sys.exit(1)

# Initialize window
WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Shader Test")

# Basic vertex and fragment shaders
vertex_shader = """
#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec2 texCoord;

out vec2 fragTexCoord;

void main()
{
    gl_Position = vec4(position, 1.0);
    fragTexCoord = texCoord;
}
"""

fragment_shader = """
#version 330 core
in vec2 fragTexCoord;
out vec4 fragColor;

uniform sampler2D texture1;
uniform float time;

void main()
{
    vec4 color = texture(texture1, fragTexCoord);
    
    // Add horizontal lines (more intense where y-coordinate is divisible by 10)
    float line_effect = 0.0;
    if (int(gl_FragCoord.y) % 10 < 2) {
        line_effect = 0.5;
    }
    
    // Pulsing effect based on time
    float pulse = sin(time) * 0.5 + 0.5;
    
    // Add yellow horizontal lines
    fragColor = mix(color, vec4(1.0, 1.0, 0.0, 1.0), line_effect * pulse);
}
"""

def create_shader_program():
    """Create and compile shader program"""
    v_shader = compileShader(vertex_shader, GL_VERTEX_SHADER)
    f_shader = compileShader(fragment_shader, GL_FRAGMENT_SHADER)
    return compileProgram(v_shader, f_shader)

def create_square():
    """Create vertices and texture coordinates for a square"""
    # Vertices: x, y, z, texture_x, texture_y
    vertices = np.array([
        # positions       # texture coords
        -0.5, -0.5, 0.0,  0.0, 0.0,  # bottom left
         0.5, -0.5, 0.0,  1.0, 0.0,  # bottom right
         0.5,  0.5, 0.0,  1.0, 1.0,  # top right
        -0.5,  0.5, 0.0,  0.0, 1.0   # top left
    ], dtype=np.float32)
    
    indices = np.array([
        0, 1, 2,  # first triangle
        2, 3, 0   # second triangle
    ], dtype=np.uint32)
    
    return vertices, indices

def create_texture(width, height):
    """Create a colored square texture"""
    data = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Fill with a purple square
    center_x, center_y = width // 2, height // 2
    square_size = min(width, height) // 3
    
    # Draw colored square in the center
    for y in range(center_y - square_size, center_y + square_size):
        for x in range(center_x - square_size, center_x + square_size):
            if 0 <= x < width and 0 <= y < height:
                data[y, x] = [128, 0, 128, 255]  # purple color
    
    # Generate texture
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    
    # Set texture parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    # Upload texture data
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    
    return texture

def main():
    # Create shader program
    shader_program = create_shader_program()
    
    # Create square geometry
    vertices, indices = create_square()
    
    # Create VAO, VBO, and EBO
    VAO = glGenVertexArrays(1)
    VBO = glGenBuffers(1)
    EBO = glGenBuffers(1)
    
    # Bind VAO
    glBindVertexArray(VAO)
    
    # Bind and set VBO
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    
    # Bind and set EBO
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    
    # Configure vertex attributes
    # Position attribute
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    
    # Texture coordinate attribute
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * vertices.itemsize, ctypes.c_void_p(3 * vertices.itemsize))
    glEnableVertexAttribArray(1)
    
    # Create texture
    texture = create_texture(256, 256)
    
    # Game loop
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    running = True
    
    print("Controls:")
    print("  ESC: Quit")
    print("  SPACE: Toggle shader")
    
    use_shader = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    use_shader = not use_shader
                    print(f"Shader: {'enabled' if use_shader else 'disabled'}")
        
        # Clear the screen
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Use shader program if enabled
        if use_shader:
            glUseProgram(shader_program)
            
            # Set time uniform
            time_location = glGetUniformLocation(shader_program, "time")
            current_time = (pygame.time.get_ticks() - start_time) / 1000.0
            glUniform1f(time_location, current_time)
            
            # Set texture uniform
            glUniform1i(glGetUniformLocation(shader_program, "texture1"), 0)
        else:
            glUseProgram(0)
        
        # Bind texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture)
        
        # Draw square
        glBindVertexArray(VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        
        # Swap buffers
        pygame.display.flip()
        clock.tick(60)
        
        # Print FPS every 2 seconds
        if int(current_time) % 2 == 0 and int(current_time * 10) % 10 == 0:
            print(f"FPS: {clock.get_fps():.1f}")
    
    # Clean up
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    glDeleteBuffers(1, [EBO])
    glDeleteTextures(1, [texture])
    glDeleteProgram(shader_program)
    
    pygame.quit()
    print("Test completed successfully")

if __name__ == "__main__":
    main()
