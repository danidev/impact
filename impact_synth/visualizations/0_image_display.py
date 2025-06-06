import pygame
import pygame.surfarray
import os
import math
import time
import traceback  # Add this import
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
        self.cached_image = None
        self.last_rotation = -1  # Force initial render
        self.supports_shader = True  # This visualization supports shaders
        
    def setup(self, synth):
        super().setup(synth)
        
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

    def update(self, dt=0.05):
        self.time += dt
        
    def draw(self, surface):
        if not self.synth or not hasattr(self.synth, 'image_manager'):
            return surface
        
        # Get the image
        image = self.synth.image_manager.get_image(self.image_name)
        if not image:
            return surface
            
        # Calculate center position
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Invert colors every 3 seconds
        should_invert =  False #int(self.time) % 6 < 2  # Toggle every 3 seconds
        
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
        
        # Don't apply shader here anymore - it will be handled by applyShader method
        return surface
    
    def applyShader(self, shader_name=None, uniforms=None):
        """Apply shader if supported"""
        # We'll let the main renderer apply the shader
        # This method must return False for the shader to be applied by VideoSynthesizer
        return False
