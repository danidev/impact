import os
import pygame

# Try to import OpenGL
try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileShader, compileProgram
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False
    print("OpenGL support disabled. Install PyOpenGL for shader effects.")

class ShaderManager:
    """Manages loading, compiling and applying OpenGL shaders"""
    
    def __init__(self, width, height):
        self.shaders = {}  # Dictionary to store compiled shader programs
        self.width = width
        self.height = height
        self.current_shader = None
        self.use_shaders = HAS_OPENGL
        
        # FBO for offscreen rendering
        self.fbo = None
        self.render_texture = None
        
        if self.use_shaders:
            self._setup_fbo()
            self._load_builtin_shaders()
    
    def _setup_fbo(self):
        """Set up the framebuffer object for offscreen rendering"""
        if not self.use_shaders:
            return
            
        try:
            # Create FBO
            self.fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
            
            # Create texture for rendering
            self.render_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.render_texture)
            
            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            
            # Create empty texture
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, 
                         GL_RGBA, GL_UNSIGNED_BYTE, None)
            
            # Attach texture to FBO
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, 
                                  GL_TEXTURE_2D, self.render_texture, 0)
            
            # Check FBO status
            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                print(f"Error: Framebuffer not complete, status: {status}")
                self.use_shaders = False
            
            # Unbind FBO
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            
        except Exception as e:
            print(f"Error setting up FBO: {e}")
            self.use_shaders = False
    
    def _load_builtin_shaders(self):
        """Load built-in shaders"""
        shader_dir = os.path.join(os.path.dirname(__file__), 'shaders')
        
        # Load default vertex shader
        with open(os.path.join(shader_dir, 'default.vert'), 'r') as f:
            default_vert = f.read()
        
        # Load fragment shaders
        shader_files = {
            'horizontal_lines': 'horizontal_lines.frag',
        }
        
        for name, filename in shader_files.items():
            try:
                with open(os.path.join(shader_dir, filename), 'r') as f:
                    frag_source = f.read()
                
                self.add_shader(name, default_vert, frag_source)
                print(f"Loaded shader: {name}")
            except Exception as e:
                print(f"Error loading shader {name}: {e}")
    
    def add_shader(self, name, vert_source, frag_source):
        """Compile and add a shader program"""
        if not self.use_shaders:
            return False
            
        try:
            vert = compileShader(vert_source, GL_VERTEX_SHADER)
            frag = compileShader(frag_source, GL_FRAGMENT_SHADER)
            program = compileProgram(vert, frag)
            
            self.shaders[name] = program
            return True
        except Exception as e:
            print(f"Error compiling shader {name}: {e}")
            return False
    
    def use_shader(self, name=None):
        """Set the current shader to use"""
        if not self.use_shaders:
            return False
            
        if name is None:
            # Disable shaders
            self.current_shader = None
            glUseProgram(0)
            return True
            
        if name in self.shaders:
            self.current_shader = name
            return True
        else:
            print(f"Shader {name} not found")
            return False
    
    def apply_shader(self, surface, shader_name, uniforms=None):
        """Apply a shader to a pygame surface and return the result"""
        if not self.use_shaders or shader_name not in self.shaders:
            return surface
            
        try:
            # Convert Pygame surface to texture data
            texture_data = pygame.image.tostring(surface, "RGBA", 1)
            
            # Bind FBO
            glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
            glViewport(0, 0, self.width, self.height)
            
            # Clear framebuffer
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            # Set up orthographic projection
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(-1, 1, -1, 1, -1, 1)
            
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            # Create temporary texture for input surface
            input_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, input_texture)
            
            # Set texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            
            # Upload texture data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 
                         0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
            
            # Use shader program
            shader_program = self.shaders[shader_name]
            glUseProgram(shader_program)
            
            # Set uniforms
            if uniforms:
                for name, value in uniforms.items():
                    loc = glGetUniformLocation(shader_program, name)
                    if loc != -1:  # -1 means the uniform was not found
                        if isinstance(value, float):
                            glUniform1f(loc, value)
                        elif isinstance(value, int):
                            glUniform1i(loc, value)
                        elif isinstance(value, tuple) and len(value) in (2, 3, 4):
                            if len(value) == 2:
                                glUniform2f(loc, *value)
                            elif len(value) == 3:
                                glUniform3f(loc, *value)
                            elif len(value) == 4:
                                glUniform4f(loc, *value)
            
            # Set texture uniform
            texture_loc = glGetUniformLocation(shader_program, "texture")
            glUniform1i(texture_loc, 0)
            
            # Draw fullscreen quad
            glBegin(GL_QUADS)
            glTexCoord2f(0, 1); glVertex3f(-1, -1, 0)  # Bottom-left
            glTexCoord2f(1, 1); glVertex3f(1, -1, 0)   # Bottom-right
            glTexCoord2f(1, 0); glVertex3f(1, 1, 0)    # Top-right
            glTexCoord2f(0, 0); glVertex3f(-1, 1, 0)   # Top-left
            glEnd()
            
            # Read pixels back
            glReadBuffer(GL_COLOR_ATTACHMENT0)
            buffer = glReadPixels(0, 0, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE)
            
            # Clean up
            glUseProgram(0)
            glDeleteTextures(1, [input_texture])
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            
            # Create Pygame surface from buffer
            img = pygame.image.fromstring(buffer, (self.width, self.height), "RGBA")
            
            # OpenGL coordinate system is flipped compared to Pygame
            img = pygame.transform.flip(img, False, True)
            
            return img
            
        except Exception as e:
            print(f"Error applying shader {shader_name}: {e}")
            import traceback
            traceback.print_exc()
            return surface
    
    def resize(self, width, height):
        """Resize the render target for shaders"""
        if not self.use_shaders:
            return
            
        self.width = width
        self.height = height
        
        # Recreate FBO with new size
        self._cleanup()
        self._setup_fbo()
    
    def _cleanup(self):
        """Clean up OpenGL resources"""
        if not self.use_shaders:
            return
            
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
            self.fbo = None
            
        if self.render_texture:
            glDeleteTextures(1, [self.render_texture])
            self.render_texture = None
            
        for program in self.shaders.values():
            glDeleteProgram(program)
        
        self.shaders = {}
    
    def __del__(self):
        """Destructor to clean up resources"""
        self._cleanup()
