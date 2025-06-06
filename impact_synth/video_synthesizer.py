import pygame
import psutil
import time
import os
import importlib
import inspect

from .graphics import draw_grid
from .graphics import draw_system_info

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
        
        # Detect Raspberry Pi for performance optimizations
        self.is_raspberry_pi = False
        try:
            if 'arm' in os.uname().machine.lower():
                self.is_raspberry_pi = True
                # Set environment variables for better performance on Pi
                os.environ['SDL_VIDEODRIVER'] = 'fbcon'
                os.environ['SDL_FBDEV'] = '/dev/fb0'
        except:
            pass
        
        # Use 16:9 resolution for modern displays
        resolution = (1280, 720)
        flags = pygame.FULLSCREEN if fullscreen else 0
        
        self.screen = pygame.display.set_mode(resolution, flags)
        self.is_fullscreen = fullscreen
        self.width, self.height = self.screen.get_size()
        
        # Use small font for better performance
        self.font = pygame.font.Font(None, 20)
        self.clock = pygame.time.Clock()
        
        # Set performance parameters
        if self.is_raspberry_pi:
            self.target_fps = 20
            self.grid_spacing = 50
            self.cpu_sample_interval = 1.0
        else:
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
        
        # Draw visualization directly to screen
        current_viz = self.current_visualization()
        if current_viz:
            current_viz.draw(self.screen)
        
        # Draw overlay if enabled
        if self.show_overlay:
            draw_grid(self, self.screen)
            draw_system_info(self, self.screen)
        
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
        
        # Mark special visualizations for platform-specific handling
        for viz in self.visualizations:
            if viz.name == "Image Display" and self.is_raspberry_pi:
                if hasattr(viz, 'raspberry_pi_mode'):
                    viz.raspberry_pi_mode = True

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