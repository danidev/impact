import pygame

class Visualization:
    """Base class for all visualizations"""
    
    def __init__(self, name="Unnamed Visualization"):
        self.name = name
        self.synth = None
        self.width = 0
        self.height = 0
        self.time = 0
        self.supports_shader = False  # Set to True in visualizations that support shaders
        
    def setup(self, synth):
        """Set up the visualization with the synthesizer instance"""
        self.synth = synth
        self.width = synth.width
        self.height = synth.height
        
    def update(self, dt=0.05):
        """Update the visualization state"""
        self.time += dt
        
    def draw(self, surface):
        """Draw the visualization on the given surface"""
        # This should be overridden by subclasses
        pass
    
    def applyShader(self, shader_name=None, uniforms=None):
        """
        Apply a shader to this visualization's output.
        Returns True if the visualization handles shader application itself,
        False if the main renderer should apply the shader.
        """
        # By default, visualizations don't handle shaders themselves
        return False


