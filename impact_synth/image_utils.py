import pygame
import os

class ImageManager:
    """
    Image management class for video synthesizer.
    Provides functionality to load, store, and manipulate images.
    """
    
    def __init__(self):
        """Initialize the image manager"""
        self.images = {}  # Dictionary to store loaded images
        
    def load_image(self, image_path, image_name=None):
        """
        Load an image and store it in the manager
        
        Args:
            image_path: Path to the image file
            image_name: Optional name to reference the image (defaults to filename)
            
        Returns:
            True if loading was successful, False otherwise
        """
        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return False
            
        try:
            # If no image_name is provided, use the filename without extension
            if image_name is None:
                image_name = os.path.splitext(os.path.basename(image_path))[0]
                
            # Load the image
            image = pygame.image.load(image_path).convert_alpha()
            
            # Store the image
            self.images[image_name] = image
            
            print(f"Successfully loaded image: {image_path} as '{image_name}'")
            return True
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def get_image(self, image_name):
        """
        Get a loaded image by name
        
        Args:
            image_name: Name of the image to retrieve
            
        Returns:
            The image surface, or None if not found
        """
        if image_name in self.images:
            return self.images[image_name]
        else:
            print(f"Image '{image_name}' not found in manager")
            return None
    
    def get_copy(self, image_name):
        """
        Get a copy of a loaded image by name (for manipulation)
        
        Args:
            image_name: Name of the image to retrieve
            
        Returns:
            A copy of the image surface, or None if not found
        """
        image = self.get_image(image_name)
        if image:
            return image.copy()
        return None
    
    def scale_image(self, image_name, width, height):
        """
        Scale an image to the specified dimensions
        
        Args:
            image_name: Name of the image to scale
            width: New width
            height: New height
            
        Returns:
            Scaled image surface, or None if image not found
        """
        image = self.get_image(image_name)
        if image:
            return pygame.transform.scale(image, (width, height))
        return None
    
    def rotate_image(self, image_name, angle):
        """
        Rotate an image by the specified angle (in degrees)
        
        Args:
            image_name: Name of the image to rotate
            angle: Rotation angle in degrees
            
        Returns:
            Rotated image surface, or None if image not found
        """
        image = self.get_image(image_name)
        if image:
            return pygame.transform.rotate(image, angle)
        return None
    
    def create_surface_from_image(self, image_name, width, height):
        """
        Create a new surface with the image centered and scaled
        
        Args:
            image_name: Name of the image to use
            width: Width of the new surface
            height: Height of the new surface
            
        Returns:
            New surface with the image centered, or None if image not found
        """
        image = self.get_image(image_name)
        if not image:
            return None
            
        # Create a new transparent surface
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Calculate position to center the image
        img_width, img_height = image.get_size()
        
        # Scale if needed to fit within the surface
        scale_factor = min(width / img_width, height / img_height)
        if scale_factor < 1:
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            image = pygame.transform.scale(image, (new_width, new_height))
            img_width, img_height = new_width, new_height
        
        # Center the image
        x = (width - img_width) // 2
        y = (height - img_height) // 2
        
        # Blit the image onto the surface
        surface.blit(image, (x, y))
        
        return surface
