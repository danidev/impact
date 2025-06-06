import pygame

class Visualization:
    """Base class for all visualizations"""
    
    def __init__(self, name="Unnamed Visualization"):
        self.name = name
        self.width = 0
        self.height = 0
        self.synth = None
    
    def setup(self, synth):
        """Initialize visualization with video synthesizer reference"""
        self.synth = synth
        self.width = synth.width
        self.height = synth.height
    
    def update(self, dt=0.05):
        """Update the visualization state"""
        pass

    def draw(self, surface):
        pass


