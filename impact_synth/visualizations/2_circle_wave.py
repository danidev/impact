import pygame
import math
from ..visualization import Visualization

class CircleWave(Visualization):
    def __init__(self, name="Circle Wave"):
        super().__init__(name=name)
        self.time = 0
        self.radius = 100
        self.color = (0, 100, 255)
        self.num_points = 36
    
    def update(self, dt=0.05):
        self.time += dt
    
    def draw(self, surface):
        if not self.synth:
            return False
        
        center_x = self.synth.width // 2
        center_y = self.synth.height // 2
        
        for i in range(self.num_points):
            # Calculate angle and radius with wave effect
            angle = 2 * math.pi * i / self.num_points
            wave_offset = 50 * math.sin(self.time * 2 + i * 0.3)
            r = self.radius + wave_offset
            
            # Calculate coordinates
            x = center_x + int(r * math.cos(angle))
            y = center_y + int(r * math.sin(angle))
            
            # Draw circle at this point
            pygame.draw.circle(surface, self.color, (x, y), 5)
            
            # Connect points with lines
            next_i = (i + 1) % self.num_points
            next_angle = 2 * math.pi * next_i / self.num_points
            next_offset = 50 * math.sin(self.time * 2 + next_i * 0.3)
            next_r = self.radius + next_offset
            
            next_x = center_x + int(next_r * math.cos(next_angle))
            next_y = center_y + int(next_r * math.sin(next_angle))
            
            pygame.draw.line(surface, self.color, (x, y), (next_x, next_y), 2)
        
        return True
