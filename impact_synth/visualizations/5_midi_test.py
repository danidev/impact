import pygame
from ..visualization import Visualization

class MidiControlledLines(Visualization):
    def __init__(self):
        super().__init__(name="MIDI Lines")
        self.horizontal_pos = 0.5  # Default to center (0.0-1.0 range)
        self.vertical_pos = 0.5    # Default to center (0.0-1.0 range)
        self.line_color = (0, 175, 191)
        self.line_thickness = 3
        
        # CC numbers to control the lines
        self.h_pos_cc = 21  # Horizontal position
        self.v_pos_cc = 22  # Vertical position
        
    def setup(self, synth):
        super().setup(synth)
        
        # Register callbacks for the specific CCs if MIDI is available
        if hasattr(synth, 'midi') and synth.midi:
            synth.midi.register_cc_callback(self.h_pos_cc, self.horizontal_cc_callback)
            synth.midi.register_cc_callback(self.v_pos_cc, self.vertical_cc_callback)
            
            # Pre-set values from existing CC values if any
            self.horizontal_pos = synth.midi.get_cc(self.h_pos_cc, 64) / 127.0
            self.vertical_pos = synth.midi.get_cc(self.v_pos_cc, 64) / 127.0
    
    def update(self, dt=0.05):
        # Check for CC values from MIDI even without callbacks
        if hasattr(self.synth, 'midi') and self.synth.midi:
            # Get CC values - scale from 0-127 to 0.0-1.0
            self.horizontal_pos = self.synth.midi.get_cc(self.h_pos_cc, int(self.horizontal_pos * 127)) / 127.0
            self.vertical_pos = self.synth.midi.get_cc(self.v_pos_cc, int(self.vertical_pos * 127)) / 127.0
    
    def horizontal_cc_callback(self, cc_number, value, channel, device_name=None):
        """Handle CC for horizontal line position"""
        self.horizontal_pos = value / 127.0
    
    def vertical_cc_callback(self, cc_number, value, channel, device_name=None):
        """Handle CC for vertical line position"""
        self.vertical_pos = value / 127.0
    
    def draw(self, surface):
        if not surface:
            return False
        
        # Calculate pixel positions
        h_pixel = int(self.height * self.vertical_pos)
        v_pixel = int(self.width * self.horizontal_pos)
        
        # Draw horizontal line
        pygame.draw.line(
            surface,
            self.line_color,
            (0, h_pixel),
            (self.width, h_pixel),
            self.line_thickness
        )
        
        # Draw vertical line
        pygame.draw.line(
            surface,
            self.line_color,
            (v_pixel, 0),
            (v_pixel, self.height),
            self.line_thickness
        )
        
        # Draw crosshair at intersection
        intersection = (v_pixel, h_pixel)
        pygame.draw.circle(
            surface,
            (255, 0, 0),
            intersection,
            self.line_thickness * 2
        )
        
        # Display CC values near the lines
        font = self.synth.font if hasattr(self.synth, 'font') else pygame.font.Font(None, 20)
        
        # Horizontal line value text
        h_text = f"CC{self.h_pos_cc}: {int(self.horizontal_pos * 127)}"
        h_surf = font.render(h_text, True, self.line_color)
        surface.blit(h_surf, (10, h_pixel + 10))
        
        # Vertical line value text
        v_text = f"CC{self.v_pos_cc}: {int(self.vertical_pos * 127)}"
        v_surf = font.render(v_text, True, self.line_color)
        surface.blit(v_surf, (v_pixel + 10, 10))
        
        return True
