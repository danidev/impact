from ..graphics import draw_sinusoid
from ..visualization import Visualization

class SineWave(Visualization):
    def __init__(self, name="Sine Wave"):
        super().__init__(name=name)
        self.offset = 0
        self.amplitude = 50
        self.frequency = 0.01
        self.color = (0, 255, 0)
    
    def update(self, dt=0.05):
        """Update the wave animation"""
        self.offset += dt
    
    def draw(self, surface):
        if not self.synth:
            return
        
        draw_sinusoid(self.synth,surface,self.offset,self.color,self.amplitude,self.frequency),(0,0)