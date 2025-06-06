import pygame
import pygame.surfarray
import os
import math
import numpy as np
from ..visualization import Visualization

# Add PyOpenGL imports for shader support
try:
    import OpenGL.GL as gl
    from OpenGL.GL import shaders
    SHADER_SUPPORT = True
except ImportError:
    SHADER_SUPPORT = False
    print("PyOpenGL not available. Install with: pip install PyOpenGL PyOpenGL_accelerate")

class ImageDisplay(Visualization):
    def __init__(self):
        super().__init__(name="Image Display")
        self.time = 0
        self.rotation = 0
        self.image_name = "test"
        self.loaded = False
        self.raspberry_pi_mode = False  # Will be set by VideoSynthesizer
        self.cached_image = None
        self.last_rotation = -1  # Force initial render
        self.use_shader = False  # Toggle for shader effect
        self.shader_program = None
        self.fbo = None  # Framebuffer object for rendering
        
    def setup(self, synth):
        super().setup(synth)
        
        # Check if we're running on Raspberry Pi
        if hasattr(synth, 'is_raspberry_pi') and synth.is_raspberry_pi:
            self.raspberry_pi_mode = True
            print(f"Running {self.name} in Raspberry Pi optimization mode")
        
        # Check if image manager exists
        if not hasattr(self.synth, 'image_manager') or self.synth.image_manager is None:
            print("ERROR: Image manager not found in synthesizer")
            return
            
        # Try to load an image with the same name as this visualization
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        assets_dir = os.path.join(project_dir, 'assets', 'images')
        
        # Create assets directory if it doesn't exist
        if not os.path.exists(assets_dir):
            try:
                os.makedirs(assets_dir)
                print(f"Created assets directory: {assets_dir}")
            except Exception as e:
                print(f"Could not create assets directory: {e}")
        
        # Get the filename without extension
        visualization_name = os.path.splitext(os.path.basename(__file__))[0]
        
        # Try different image formats
        for ext in ['.png', '.jpg', '.jpeg']:
            image_filename = f"{visualization_name}{ext}"
            image_path = os.path.join(assets_dir, image_filename)
            
            if os.path.exists(image_path):
                print(f"Found matching image: {image_path}")
                self.synth.image_manager.load_image(image_path, self.image_name)
                self.loaded = True
                break
        
        if not self.loaded:
            print(f"No matching image found for {visualization_name}")
            print(f"Please place an image named {visualization_name}.png or {visualization_name}.jpg in {assets_dir}")
            
            # Create a placeholder image
            placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)
            placeholder.fill((100, 100, 100))
            font = pygame.font.Font(None, 24)
            text = font.render("Image Not Found", True, (255, 255, 255))
            text_rect = text.get_rect(center=(100, 100))
            placeholder.blit(text, text_rect)
            
            # Store the placeholder in the image manager
            self.synth.image_manager.images[self.image_name] = placeholder
            self.loaded = True

        # Initialize shader if OpenGL is available
        if SHADER_SUPPORT:
            try:
                self._setup_shader()
                self.use_shader = True
                print("VCR shader initialized successfully")
            except Exception as e:
                print(f"Failed to initialize shader: {e}")
                self.use_shader = False
                
    def _setup_shader(self):
        # VCR lines effect fragment shader
        fragment_shader = """
        #version 120
        uniform sampler2D texture;
        uniform float time;
        uniform vec2 resolution;
        
        void main() {
            vec2 uv = gl_TexCoord[0].xy;
            
            // VCR distortion effect
            float vPos = uv.y * resolution.y;
            float vSize = resolution.y;
            float vScale = 0.5;
            
            // VHS scanlines
            float scanline = sin(vPos * 0.5 + time * 6.0) * 0.5 + 0.5;
            scanline = pow(scanline, 1.5);
            scanline *= 0.5;
            
            // Noise
            float noise = fract(sin(dot(uv, vec2(12.9898, 78.233) * time * 0.1)) * 43758.5453);
            noise *= 0.15;
            
            // Color shifting for VHS look
            float colorShift = sin(time) * 0.001;
            vec4 baseColor = texture2D(texture, uv);
            vec4 shiftedColor = texture2D(texture, vec2(uv.x + colorShift, uv.y));
            
            // Apply effects
            vec4 color = mix(baseColor, shiftedColor, 0.5);
            color.rgb = mix(color.rgb, color.rgb * (1.0 - scanline), 0.3);
            color.rgb += noise * vec3(0.1, 0.1, 0.1);
            
            // Occasional horizontal glitch
            float glitchTime = floor(time * 1.5);
            float glitchSeed = fract(sin(glitchTime) * 43758.5453);
            if (glitchSeed > 0.93) {
                float glitchPos = floor(vPos / (10.0 + 40.0 * fract(glitchSeed * 10.0)));
                if (fract(glitchPos * 0.5) < 0.5) {
                    color.rgb = texture2D(texture, vec2(uv.x + sin(glitchTime) * 0.1, uv.y)).rgb;
                }
            }
            
            gl_FragColor = color;
        }
        """
        
        vertex_shader = """
        #version 120
        void main() {
            gl_TexCoord[0] = gl_MultiTexCoord0;
            gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
        }
        """
        
        # Compile shaders
        vertex = shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER)
        fragment = shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER)
        self.shader_program = shaders.compileProgram(vertex, fragment)
        
        # Create framebuffer object for rendering
        self.fbo = gl.glGenFramebuffers(1)
        self.texture = gl.glGenTextures(1)
        
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.width, self.height, 0, 
                        gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
        gl.glFramebufferTexture2D(gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, 
                                 gl.GL_TEXTURE_2D, self.texture, 0)
        
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
    
    def apply_shader(self, surface):
        """Apply the VCR shader effect to the surface"""
        if not SHADER_SUPPORT or not self.shader_program:
            return surface
            
        try:
            # Get surface data as texture
            texture_data = pygame.image.tostring(surface, "RGBA", 1)
            
            # Bind FBO and set viewport
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self.fbo)
            gl.glViewport(0, 0, self.width, self.height)
            
            # Clear the framebuffer
            gl.glClearColor(0.0, 0.0, 0.0, 1.0)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
            # Set up texture
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture)
            gl.glTexSubImage2D(gl.GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
                              gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, texture_data)
            
            # Use shader program
            gl.glUseProgram(self.shader_program)
            
            # Set uniforms
            gl.glUniform1i(gl.glGetUniformLocation(self.shader_program, "texture"), 0)
            gl.glUniform1f(gl.glGetUniformLocation(self.shader_program, "time"), self.time)
            gl.glUniform2f(gl.glGetUniformLocation(self.shader_program, "resolution"), 
                          float(self.width), float(self.height))
            
            # Draw fullscreen quad
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord2f(0, 0); gl.glVertex3f(-1, -1, 0)
            gl.glTexCoord2f(1, 0); gl.glVertex3f(1, -1, 0)
            gl.glTexCoord2f(1, 1); gl.glVertex3f(1, 1, 0)
            gl.glTexCoord2f(0, 1); gl.glVertex3f(-1, 1, 0)
            gl.glEnd()
            
            # Read pixels back
            gl.glReadBuffer(gl.GL_COLOR_ATTACHMENT0)
            buffer = gl.glReadPixels(0, 0, self.width, self.height, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
            
            # Create a surface from the buffer
            img = pygame.image.fromstring(buffer, (self.width, self.height), "RGBA")
            
            # Flip the image (OpenGL coordinates are flipped compared to Pygame)
            img = pygame.transform.flip(img, False, True)
            
            # Clean up
            gl.glUseProgram(0)
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
            
            return img
            
        except Exception as e:
            print(f"Shader application failed: {e}")
            return surface

    def update(self, dt=0.05):
        self.time += dt
        
        # Rotate the image slowly - use larger steps on Raspberry Pi
        # rotation_speed = 25 if not self.raspberry_pi_mode else 5
        # self.rotation = (self.rotation + dt * rotation_speed) % 360
    
    def draw(self, surface):
        if not self.synth or not hasattr(self.synth, 'image_manager'):
            return surface
            
        # Check if we have audio to sync with
        has_audio = hasattr(self.synth, 'audio') and self.synth.audio is not None
        beat = False
        
        if has_audio:
            beat = self.synth.audio.get_beat()
        
        # Get the image
        image = self.synth.image_manager.get_image(self.image_name)
        if not image:
            return surface
            
        # Calculate center position
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Optimize for Raspberry Pi
        if self.raspberry_pi_mode:
            # 1. Skip color inversion completely
            orig_image = image
            
            # 2. Only rotate when rotation changes significantly to save CPU
            if self.cached_image is None or abs(self.rotation - self.last_rotation) > 5:
                # Use simpler rotation without antialiasing
                display_image = pygame.transform.rotate(orig_image, self.rotation)
                self.cached_image = display_image
                self.last_rotation = self.rotation
            else:
                display_image = self.cached_image
                
            # 3. Fill with solid color instead of getting pixel
            surface.fill((0, 0, 0))
        else:
            # Regular desktop mode - full effects
            # Invert colors every 3 seconds
            should_invert = int(self.time) % 6 < 2  # Toggle every 3 seconds
            
            if should_invert:
                # Create a copy of the image
                orig_image = image.copy()
                
                try:
                    # Get pixel array (surfarray is already imported at the top)
                    pixels = pygame.surfarray.pixels3d(orig_image)
                    # Invert RGB values (255 - value)
                    pixels[:,:,:] = 255 - pixels[:,:,:]
                    # Delete reference to release
                    del pixels
                except:
                    pass
            else:
                orig_image = image
            
            # Get the color from pixel (0,0) of the original image
            try:
                corner_color = orig_image.get_at((0, 0))
                # Fill the surface with this color before drawing the image
                surface.fill(corner_color[:3])
            except:
                # If we can't get the color, just continue without filling
                pass
                
            # Apply rotation
            display_image = pygame.transform.rotate(orig_image, self.rotation)
        
        # Get the rect for positioning (centered)
        img_rect = display_image.get_rect()
        img_rect.center = (center_x, center_y)
        
        # Draw to surface
        surface.blit(display_image, img_rect)
        
        # Apply shader post-processing if enabled
        if self.use_shader and SHADER_SUPPORT:
            surface = self.apply_shader(surface)
            
        return surface
