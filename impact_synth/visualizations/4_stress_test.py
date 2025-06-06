import pygame
import math
import random
from ..visualization import Visualization

class StressTest(Visualization):
    def __init__(self):
        super().__init__(name="Stress Test")
        self.time = 0
        self.num_particles = 100  # Default number of particles
        self.particles = []
        self.colors = []
        self.init_particles()
        
    def init_particles(self):
        """Initialize particles with random properties"""
        self.particles = []
        self.colors = []
        for i in range(self.num_particles):
            # Random position
            x = random.randint(0, 1280)
            y = random.randint(0, 720)
            # Random velocity
            vx = random.uniform(-2, 2)
            vy = random.uniform(-2, 2)
            # Random size
            size = random.randint(3, 15)
            # Random frequency for sine wave movement
            freq = random.uniform(0.5, 3.0)
            # Random amplitude for sine wave movement
            amp = random.randint(10, 50)
            
            self.particles.append([x, y, vx, vy, size, freq, amp])
            # Random color with some brightness
            self.colors.append((
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            ))
    
    def setup(self, synth):
        super().setup(synth)
        # Adjust particle count based on platform
        if hasattr(synth, 'is_raspberry_pi') and synth.is_raspberry_pi:
            # Fewer particles on Raspberry Pi
            self.num_particles = 100
        else:
            # More particles on desktop
            self.num_particles = 100
        self.init_particles()
        
    def update(self, dt=0.05):
        self.time += dt
        
        # Update particle positions
        for i, p in enumerate(self.particles):
            x, y, vx, vy, size, freq, amp = p
            
            # Apply sine wave movement
            x += vx + math.sin(self.time * freq) * 0.5
            y += vy + math.cos(self.time * freq + i * 0.1) * 0.5
            
            # Bounce off edges
            if x < 0 or x > self.width:
                vx = -vx
                x = max(0, min(x, self.width))
            if y < 0 or y > self.height:
                vy = -vy
                y = max(0, min(y, self.height))
                
            # Update particle
            self.particles[i] = [x, y, vx, vy, size, freq, amp]
    
    def draw(self, surface):
        if not surface:
            return False
            
        # Draw connected particles
        if len(self.particles) > 1:
            # Draw connections between particles that are close
            max_distance = 200  # Maximum distance for drawing connections
            
            # Draw lines between nearby particles
            for i in range(len(self.particles)):
                p1 = self.particles[i]
                x1, y1 = p1[0], p1[1]
                
                for j in range(i+1, len(self.particles)):
                    p2 = self.particles[j]
                    x2, y2 = p2[0], p2[1]
                    
                    # Calculate distance
                    dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    if dist < max_distance:
                        # Draw line with alpha based on distance
                        alpha = int(255 * (1 - dist/max_distance))
                        color = self.colors[i]
                        # Create a color with alpha
                        line_color = (color[0], color[1], color[2], alpha)
                        
                        # Draw the line
                        pygame.draw.line(surface, line_color, (x1, y1), (x2, y2), 1)
        
        # Draw particles
        for i, p in enumerate(self.particles):
            x, y, _, _, size, freq, amp = p
            
            # Pulsate size based on time
            current_size = size + int(math.sin(self.time * freq) * 3)
            current_size = max(1, current_size)
            
            # Draw glowing circle
            for s in range(current_size, 0, -1):
                # Decrease alpha for outer circles
                alpha = int(255 * (s / current_size))
                color = self.colors[i]
                glow_color = (color[0], color[1], color[2], alpha)
                pygame.draw.circle(surface, glow_color, (int(x), int(y)), s)
        
        return True
