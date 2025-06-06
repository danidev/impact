import pygame
import pygame.surfarray
import os
import math
from ..visualization import Visualization

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
            
        return surface
