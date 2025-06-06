import pygame
import psutil
import time
import os
import importlib
import inspect

# Try to import OpenGL at module level
try:
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    HAS_OPENGL = True
except ImportError:
    HAS_OPENGL = False

from .graphics import draw_grid
from .graphics import draw_system_info

# Import ShaderManager
from .shader_manager import ShaderManager

class VideoSynthesizer:
    def __init__(self, fullscreen=True):
        pygame.init()
        pygame.mouse.set_visible(False)  # Hide mouse cursor
        
        # Initialize mixer explicitly first
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
        except Exception:
            pass
        
        # Store original display info to restore later
        self.original_display_info = pygame.display.Info()
        
        # Set OpenGL flag based on module import
        self.use_opengl = HAS_OPENGL
        if self.use_opengl:
            print("OpenGL support enabled")
        else:
            print("OpenGL not available. Shaders will be disabled.")
        
        # Use 16:9 resolution for modern displays
        resolution = (1280, 720)
        
        # Set up display flags
        flags = 0
        if fullscreen:
            flags |= pygame.FULLSCREEN
    
        # Add OpenGL flag if available
        if self.use_opengl:
            flags |= pygame.OPENGL | pygame.DOUBLEBUF
            
        # Create the window
        self.screen = pygame.display.set_mode(resolution, flags)
        self.is_fullscreen = fullscreen
        self.width, self.height = resolution  # Store size separately since we can't get it from screen in OpenGL mode
    
        # If using OpenGL, create a Pygame surface for normal drawing
        if self.use_opengl:
            self.pygame_surface = pygame.Surface(resolution)
        else:
            self.pygame_surface = self.screen
        
        # Initialize shader manager
        self.shader_manager = None
        if self.use_opengl:
            try:
                self.shader_manager = ShaderManager(self.width, self.height)
                # Always start with the horizontal lines shader
                self.current_shader = 'horizontal_lines'
            except Exception as e:
                print(f"Failed to initialize shader manager: {e}")
                self.use_opengl = False
                self.pygame_surface = self.screen
    
        # Use small font for better performance
        self.font = pygame.font.Font(None, 20)
        self.clock = pygame.time.Clock()

        self.target_fps = 30
        self.grid_spacing = 50
        self.cpu_sample_interval = 0.1
            
        self.last_cpu_sample = 0
        
        # Variables for FPS calculation
        self.frame_count = 0
        self.fps = 0
        self.last_time = time.time()
        
        # Variables for system monitoring
        self.cpu_values = [0] * 10
        self.mem_values = [0] * 10
        self.cpu_index = 0
        self.mem_index = 0
        
        # Control variables
        self.show_overlay = True
        self.running = True
        
        # Initialize subsystems
        try:
            from .image_utils import ImageManager
            self.image_manager = ImageManager()
        except Exception:
            self.image_manager = None
        
        try:
            from .audio import AudioManager
            self.audio = AudioManager()
        except Exception:
            self.audio = None
            
        # Initialize MIDI manager
        self.midi = None  # Explicitly set to None initially
        try:
            from .midi_manager import MidiManager
            midi_manager = MidiManager()
            
            # Set the midi attribute if any devices were connected
            if hasattr(midi_manager, 'connected') and midi_manager.connected:
                self.midi = midi_manager
                
                # Register CC callback for global brightness
                self.midi.register_cc_callback(7, self.handle_brightness_cc)
                
                # Log connected devices
                if hasattr(midi_manager, 'get_device_list'):
                    device_list = midi_manager.get_device_list()
                    if device_list:
                        print(f"Connected to MIDI devices: {device_list}")
            else:
                # Still set the midi manager even if no devices are connected
                # so it can be used for testing with default CCs
                self.midi = midi_manager
                print("MIDI Manager created but no devices connected")
        except Exception as e:
            print(f"Could not initialize MidiManager: {e}")
            self.midi = None
        
        # Load visualizations
        self.visualizations = []
        self.current_viz_index = 0
        self.load_visualizations()
    
    def handle_events(self):
        """Handle pygame events and return False if should quit"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F1:
                    self.show_overlay = not self.show_overlay
                elif event.key == pygame.K_LEFT:
                    self.prev_visualization()
                elif event.key == pygame.K_RIGHT:
                    self.next_visualization()
                # Remove shader toggle with 'S' key - shader is always active
        return self.running
    
    def update_fps(self):
        """Update and return the current FPS"""
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time > 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        return self.fps
    
    def clear_screen(self, color=(0, 0, 0)):
        """Clear the screen"""
        self.screen.fill(color)
    
    def flip(self):
        """Update the display with optimal performance"""
        # Update FPS counter
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_time > 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_time = current_time
        
        # Sample CPU/memory at appropriate intervals
        if current_time - self.last_cpu_sample >= self.cpu_sample_interval:
            current_cpu = psutil.cpu_percent()
            current_mem = psutil.virtual_memory().percent
            
            # Update lists with new values
            self.cpu_values[self.cpu_index] = current_cpu
            self.mem_values[self.mem_index] = current_mem
            
            # Update indices circularly
            self.cpu_index = (self.cpu_index + 1) % len(self.cpu_values)
            self.mem_index = (self.mem_index + 1) % len(self.mem_values)
            
            self.last_cpu_sample = current_time
        
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Create a surface just for the visualization that we can apply shaders to
        viz_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        viz_surface.fill((0, 0, 0))  # Use solid black instead of transparent
        
        # Draw visualization to its own surface
        current_viz = self.current_visualization()
        if current_viz:
            current_viz.draw(viz_surface)
            
            # Only apply shader if the visualization supports it
            if (self.use_opengl and 
                self.shader_manager and 
                self.current_shader and 
                hasattr(current_viz, 'supports_shader') and 
                current_viz.supports_shader):
                
                # Get time for shader effects
                shader_time = pygame.time.get_ticks() / 1000.0
                
                # Basic uniforms that all shaders might need
                uniforms = {
                    'time': shader_time,
                    'resolution': (float(self.width), float(self.height))
                }
                
                # Apply shader
                try:
                    viz_surface = self.shader_manager.apply_shader(
                        viz_surface, 
                        self.current_shader,
                        uniforms
                    )
                    
                    # Flip the surface vertically to correct orientation
                    viz_surface = pygame.transform.flip(viz_surface, False, True)
                    
                except Exception as e:
                    print(f"Error applying shader: {e}")
    
        # Now blit the visualization surface to the main pygame surface
        self.pygame_surface.fill((0, 0, 0))  # Clear the main surface first
        self.pygame_surface.blit(viz_surface, (0, 0))
        
        # Draw overlay if enabled (after shader application)
        if self.show_overlay:
            draw_grid(self, self.pygame_surface)
            draw_system_info(self, self.pygame_surface)
        
        # If using OpenGL, transfer the Pygame surface to the OpenGL context
        if self.use_opengl:
            try:
                # We've already applied the shader to the visualization,
                # so we don't need to apply it again here.
                # Just render the pygame_surface to the screen
                
                # Convert final surface to OpenGL texture and display it
                texture_data = pygame.image.tostring(self.pygame_surface, "RGBA", 1)
                
                # Clear the screen
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)
                
                # Set up orthographic projection (2D mode)
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                glOrtho(0, self.width, self.height, 0, -1, 1)
                
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                
                # Create a texture
                texture = glGenTextures(1)
                glBindTexture(GL_TEXTURE_2D, texture)
                
                # Set texture parameters
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                
                # Upload texture data
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, 
                             GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
                
                # Enable texturing
                glEnable(GL_TEXTURE_2D)
                
                # Draw a textured quad
                glBegin(GL_QUADS)
                glTexCoord2f(0, 1); glVertex2f(0, 0)  # Bottom-left corner
                glTexCoord2f(1, 1); glVertex2f(self.width, 0)  # Bottom-right corner
                glTexCoord2f(1, 0); glVertex2f(self.width, self.height)  # Top-right corner
                glTexCoord2f(0, 0); glVertex2f(0, self.height)  # Top-left corner
                glEnd()
                
                # Disable texturing
                glDisable(GL_TEXTURE_2D)
                
                # Delete the texture to avoid memory leaks
                glDeleteTextures(1, [texture])
                
            except Exception as e:
                print(f"OpenGL rendering error: {e}")
        else:
            # If not using OpenGL, just fill the screen
            self.screen.fill((0, 0, 0))
            
            # Blit the pygame surface
            if self.pygame_surface is not self.screen:
                self.screen.blit(self.pygame_surface, (0, 0))
    
        # Update the display
        pygame.display.flip()
    
    def tick(self, framerate=30):
        """Control the framerate"""
        self.clock.tick(self.target_fps)
    
    def quit(self):
        """Clean up resources"""
        if hasattr(self, 'audio') and self.audio:
            self.audio.stop()
            
        # Close MIDI
        if hasattr(self, 'midi') and self.midi:
            self.midi.close()
        
        if self.is_fullscreen:
            try:
                pygame.display.set_mode(
                    (self.original_display_info.current_w, self.original_display_info.current_h)
                )
            except:
                pass
        
        pygame.quit()
    
    def load_visualizations(self):
        """Load all visualization modules dynamically"""
        from .visualization import Visualization
        
        viz_dir = os.path.join(os.path.dirname(__file__), 'visualizations')
        visualization_classes = []
        
        # Find visualization classes
        for filename in sorted(os.listdir(viz_dir)):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                
                try:
                    module_path = f"impact_synth.visualizations.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Visualization) and 
                            obj is not Visualization):
                            visualization_classes.append((filename, obj))
                except Exception as e:
                    print(f"Error loading visualization {module_name}: {e}")
                    
        # Create instances of visualizations
        for filename, cls in visualization_classes:
            try:
                viz = cls()
                viz.setup(self)
                self.visualizations.append(viz)
            except Exception:
                pass

    def current_visualization(self):
        """Get the current visualization"""
        if self.visualizations:
            return self.visualizations[self.current_viz_index]
        return None
    
    def next_visualization(self):
        """Switch to next visualization"""
        if self.visualizations:
            self.current_viz_index = (self.current_viz_index + 1) % len(self.visualizations)
    
    def prev_visualization(self):
        """Switch to previous visualization"""
        if self.visualizations:
            self.current_viz_index = (self.current_viz_index - 1) % len(self.visualizations)
    
    def handle_brightness_cc(self, cc_number, value, channel, device_name=None):
        """Handle MIDI CC for global brightness"""
        # Scale from 0-127 to 0.0-1.0
        brightness = value / 127.0
        
        # Include device name in log if available
        device_info = f" from {device_name}" if device_name else ""
        print(f"Received brightness CC{cc_number}={value}{device_info}, brightness: {brightness:.2f}")
        
        # Store this value to use in visualizations
        self.brightness = brightness
    
    # Add methods for shader management
    
    def set_shader(self, shader_name=None):
        """Set the current shader (or disable shaders if None)"""
        if not hasattr(self, 'shader_manager') or not self.shader_manager:
            return False
        
        if shader_name is None:
            self.current_shader = None
            return True
        
        if self.shader_manager.use_shader(shader_name):
            self.current_shader = shader_name
            return True
            
        return False
    
    def toggle_shader(self, shader_name):
        """Toggle a shader on/off"""
        if self.current_shader == shader_name:
            self.current_shader = None
        else:
            self.current_shader = shader_name