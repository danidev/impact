import pygame
import random
import numpy as np
from ..visualization import Visualization

class ALifeSimulation(Visualization):
    def __init__(self):
        super().__init__(name="A-Life Simulation")
        
        # Configuration
        self.grid_width = 50  # Default number of cells horizontally
        self.grid_height = 30  # Default number of cells vertically
        self.cell_size = 10    # Will be recalculated based on screen size
        self.update_interval = 0.1  # Time between updates (seconds)
        self.time_since_update = 0
        self.evolution_speed = 1.0  # Multiplier for update speed
        
        # Colors
        self.background_color = (0, 0, 0)
        self.cell_color = (0, 200, 100)
        self.grid_color = (20, 20, 20)
        self.show_grid = True
        
        # Game state
        self.grid = None
        
        # MIDI control
        self.width_cc = 21     # CC for grid width
        self.height_cc = 22    # CC for grid height
        self.speed_cc = 23     # CC for evolution speed
        self.color_cc = 24     # CC to change cell color
        self.reset_cc = 44     # CC to reset/randomize the grid
        
        # Additional properties
        self.density = 0.3     # Initial cell density
        self.density_cc = 25   # CC for density when resetting
        
    def scalecc(self, value, min_val, max_val):
        """
        Scale a CC value (0-127) to the specified range (min_val to max_val)
        Ensures the input value is safely in the 0-127 range before scaling
        """
        # First ensure value is within valid CC range
        safe_value = max(0, min(127, float(value)))
        
        # Then scale from 0-127 to min_val-max_val
        range_size = max_val - min_val
        scaled = min_val + (safe_value / 127.0) * range_size
        return scaled
    
    def setup(self, synth):
        super().setup(synth)
        
        # Calculate cell size based on screen dimensions
        self.calculate_cell_size()
        
        # Initialize the grid
        self.initialize_grid()
        
        # Register MIDI callbacks if available
        if hasattr(synth, 'midi') and synth.midi:
            # Register callbacks with error handling
            try:
                synth.midi.register_cc_callback(self.width_cc, self.change_width)
                synth.midi.register_cc_callback(self.height_cc, self.change_height)
                synth.midi.register_cc_callback(self.speed_cc, self.change_speed)
                synth.midi.register_cc_callback(self.reset_cc, self.reset_grid)
                synth.midi.register_cc_callback(self.color_cc, self.change_color)
                synth.midi.register_cc_callback(self.density_cc, self.change_density)
                
                # Pre-load initial values from existing CC values with safe scaling
                # Ensure minimum grid dimensions and handle type conversion safely
                width_cc_val = synth.midi.get_cc(self.width_cc, 64) 
                self.grid_width = max(10, int(self.scalecc(width_cc_val, 10, 100)))
                
                height_cc_val = synth.midi.get_cc(self.height_cc, 64)
                self.grid_height = max(10, int(self.scalecc(height_cc_val, 10, 100)))
                
                speed_cc_val = synth.midi.get_cc(self.speed_cc, 64)
                self.evolution_speed = self.scalecc(speed_cc_val, 0.2, 2.0)
                
                density_cc_val = synth.midi.get_cc(self.density_cc, 38)
                self.density = self.scalecc(density_cc_val, 0.05, 0.95)
                
                # Apply color using the CC value directly with proper error handling
                color_cc_val = synth.midi.get_cc(self.color_cc, 64)
                self.change_color(self.color_cc, color_cc_val, 0)
                
                # Recalculate size and initialize again with new dimensions
                self.calculate_cell_size()
                self.initialize_grid()
            except Exception as e:
                print(f"Error setting up MIDI for A-Life: {e}")
                # Fallback to defaults
                self.grid_width = 50
                self.grid_height = 30
                self.calculate_cell_size()
                self.initialize_grid()

    def calculate_cell_size(self):
        """Calculate the cell size based on screen dimensions and grid size"""
        if not hasattr(self, 'width') or not hasattr(self, 'height'):
            # Default if we don't have screen dimensions yet
            self.cell_size = 10
            return
            
        # Calculate maximum possible cell size to fit the grid
        max_cell_width = self.width // self.grid_width
        max_cell_height = self.height // self.grid_height
        
        # Use the smaller dimension to keep cells square
        self.cell_size = min(max_cell_width, max_cell_height)
        
        # Ensure cell size is at least 2 pixels
        self.cell_size = max(2, self.cell_size)
    
    def initialize_grid(self):
        """Initialize the grid with random values"""
        # Ensure minimum grid dimensions
        self.grid_width = max(5, self.grid_width)
        self.grid_height = max(5, self.grid_height)
        
        try:
            # Create a new grid with proper dimensions
            self.grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
            
            # Randomly seed some cells using current density setting
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    if random.random() < self.density:
                        self.grid[y, x] = 1
        except Exception as e:
            print(f"Error initializing grid: {e}")
            # Fallback to a minimal grid
            self.grid_width = 10
            self.grid_height = 10
            self.grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
    
    def update(self, dt=0.05):
        # Check for MIDI values if available
        if hasattr(self.synth, 'midi') and self.synth.midi:
            # Get CC values and scale appropriately with the scalecc function
            new_width = int(self.scalecc(self.synth.midi.get_cc(self.width_cc, 64), 10, 100))
            new_height = int(self.scalecc(self.synth.midi.get_cc(self.height_cc, 64), 10, 100))
            
            # Only recreate the grid if dimensions have changed
            if new_width != self.grid_width or new_height != self.grid_height:
                self.grid_width = new_width
                self.grid_height = new_height
                self.calculate_cell_size()
                self.initialize_grid()
            
            # Update evolution speed with scalecc
            self.evolution_speed = self.scalecc(self.synth.midi.get_cc(self.speed_cc, 64), 0.2, 2.0)
        
        # Update the simulation at regular intervals
        self.time_since_update += dt * self.evolution_speed
        if self.time_since_update >= self.update_interval:
            self.time_since_update = 0
            self.evolve_grid()
    
    def evolve_grid(self):
        """Apply Conway's Game of Life rules to evolve the grid"""
        try:
            # Create a new grid with same dimensions
            new_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
            
            # Apply Conway's rules to each cell
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    # Count live neighbors (using wrap-around)
                    neighbors = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue  # Skip the cell itself
                            
                            # Get neighbor coordinates with wrap-around
                            nx = (x + dx) % self.grid_width
                            ny = (y + dy) % self.grid_height
                            
                            # Safety check before accessing
                            if 0 <= ny < self.grid_height and 0 <= nx < self.grid_width:
                                # Count live neighbors
                                if self.grid[ny, nx] == 1:
                                    neighbors += 1
                    
                    # Apply Conway's Game of Life rules
                    if self.grid[y, x] == 1:
                        if neighbors == 2 or neighbors == 3:
                            new_grid[y, x] = 1  # Survival
                    else:
                        if neighbors == 3:
                            new_grid[y, x] = 1  # Reproduction
            
            # Update the grid
            self.grid = new_grid
        except Exception as e:
            print(f"Error evolving grid: {e}")
            # Don't update the grid if there was an error
    
    def draw(self, surface):
        if not surface:
            return False
        
        # Fill background
        surface.fill(self.background_color)
        
        # Safety check - make sure grid exists and dimensions match
        if self.grid is None or self.grid.shape[0] != self.grid_height or self.grid.shape[1] != self.grid_width:
            try:
                # Recreate the grid if there's a mismatch
                self.initialize_grid()
            except Exception as e:
                print(f"Error recreating grid in draw: {e}")
                return False
        
        # Calculate grid offset to center the grid on screen
        offset_x = (self.width - self.grid_width * self.cell_size) // 2
        offset_y = (self.height - self.grid_height * self.cell_size) // 2
        
        # Draw grid lines
        if self.show_grid and self.cell_size > 3:
            for x in range(self.grid_width + 1):
                pygame.draw.line(
                    surface,
                    self.grid_color,
                    (offset_x + x * self.cell_size, offset_y),
                    (offset_x + x * self.cell_size, offset_y + self.grid_height * self.cell_size)
                )
            for y in range(self.grid_height + 1):
                pygame.draw.line(
                    surface,
                    self.grid_color,
                    (offset_x, offset_y + y * self.cell_size),
                    (offset_x + self.grid_width * self.cell_size, offset_y + y * self.cell_size)
                )
        
        # Draw cells with safety checks
        for y in range(min(self.grid_height, self.grid.shape[0])):
            for x in range(min(self.grid_width, self.grid.shape[1])):
                try:
                    if self.grid[y, x] == 1:
                        pygame.draw.rect(
                            surface,
                            self.cell_color,
                            (
                                offset_x + x * self.cell_size,
                                offset_y + y * self.cell_size,
                                self.cell_size - 1 if self.show_grid else self.cell_size,
                                self.cell_size - 1 if self.show_grid else self.cell_size
                            )
                        )
                except IndexError:
                    # Skip any cells that might be out of bounds
                    continue
        
        # Remove text information display - clean visual without overlay
        
        return True
    
    # MIDI Callbacks
    def change_width(self, cc_number, value, channel, device_name=None):
        """Callback for width CC control"""
        try:
            new_width = int(self.scalecc(value, 10, 100))
            if new_width != self.grid_width:
                old_grid = self.grid.copy() if self.grid is not None else None
                old_width = self.grid_width
                old_height = self.grid_height
                
                # Update the dimension
                self.grid_width = new_width
                self.calculate_cell_size()
                
                # Create a new grid with new dimensions
                new_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
                
                # Copy contents from old grid if possible
                if old_grid is not None:
                    # Determine common dimensions
                    common_height = min(old_height, self.grid_height)
                    common_width = min(old_width, self.grid_width)
                    
                    # Copy the overlapping portion
                    new_grid[:common_height, :common_width] = old_grid[:common_height, :common_width]
                
                # Set the new grid
                self.grid = new_grid
        except Exception as e:
            print(f"Error changing width: {e}")
            # Keep old dimensions if there was an error
    
    def change_height(self, cc_number, value, channel, device_name=None):
        """Callback for height CC control"""
        try:
            new_height = int(self.scalecc(value, 10, 100))
            if new_height != self.grid_height:
                old_grid = self.grid.copy() if self.grid is not None else None
                old_width = self.grid_width
                old_height = self.grid_height
                
                # Update the dimension
                self.grid_height = new_height
                self.calculate_cell_size()
                
                # Create a new grid with new dimensions
                new_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
                
                # Copy contents from old grid if possible
                if old_grid is not None:
                    # Determine common dimensions
                    common_height = min(old_height, self.grid_height)
                    common_width = min(old_width, self.grid_width)
                    
                    # Copy the overlapping portion
                    new_grid[:common_height, :common_width] = old_grid[:common_height, :common_width]
                
                # Set the new grid
                self.grid = new_grid
        except Exception as e:
            print(f"Error changing height: {e}")
            # Keep old dimensions if there was an error
    
    def update(self, dt=0.05):
        # Check for MIDI values if available
        if hasattr(self.synth, 'midi') and self.synth.midi:
            # Get CC values and scale appropriately with the scalecc function
            new_width = int(self.scalecc(self.synth.midi.get_cc(self.width_cc, 64), 10, 100))
            new_height = int(self.scalecc(self.synth.midi.get_cc(self.height_cc, 64), 10, 100))
            
            # Only recreate the grid if dimensions have changed
            if new_width != self.grid_width or new_height != self.grid_height:
                self.grid_width = new_width
                self.grid_height = new_height
                self.calculate_cell_size()
                self.initialize_grid()
            
            # Update evolution speed with scalecc
            self.evolution_speed = self.scalecc(self.synth.midi.get_cc(self.speed_cc, 64), 0.2, 2.0)
        
        # Update the simulation at regular intervals
        self.time_since_update += dt * self.evolution_speed
        if self.time_since_update >= self.update_interval:
            self.time_since_update = 0
            self.evolve_grid()
    
    def evolve_grid(self):
        """Apply Conway's Game of Life rules to evolve the grid"""
        try:
            # Create a new grid with same dimensions
            new_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
            
            # Apply Conway's rules to each cell
            for y in range(self.grid_height):
                for x in range(self.grid_width):
                    # Count live neighbors (using wrap-around)
                    neighbors = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue  # Skip the cell itself
                            
                            # Get neighbor coordinates with wrap-around
                            nx = (x + dx) % self.grid_width
                            ny = (y + dy) % self.grid_height
                            
                            # Safety check before accessing
                            if 0 <= ny < self.grid_height and 0 <= nx < self.grid_width:
                                # Count live neighbors
                                if self.grid[ny, nx] == 1:
                                    neighbors += 1
                    
                    # Apply Conway's Game of Life rules
                    if self.grid[y, x] == 1:
                        if neighbors == 2 or neighbors == 3:
                            new_grid[y, x] = 1  # Survival
                    else:
                        if neighbors == 3:
                            new_grid[y, x] = 1  # Reproduction
            
            # Update the grid
            self.grid = new_grid
        except Exception as e:
            print(f"Error evolving grid: {e}")
            # Don't update the grid if there was an error
    
    def draw(self, surface):
        if not surface:
            return False
        
        # Fill background
        surface.fill(self.background_color)
        
        # Safety check - make sure grid exists and dimensions match
        if self.grid is None or self.grid.shape[0] != self.grid_height or self.grid.shape[1] != self.grid_width:
            try:
                # Recreate the grid if there's a mismatch
                self.initialize_grid()
            except Exception as e:
                print(f"Error recreating grid in draw: {e}")
                return False
        
        # Calculate grid offset to center the grid on screen
        offset_x = (self.width - self.grid_width * self.cell_size) // 2
        offset_y = (self.height - self.grid_height * self.cell_size) // 2
        
        # Draw grid lines
        if self.show_grid and self.cell_size > 3:
            for x in range(self.grid_width + 1):
                pygame.draw.line(
                    surface,
                    self.grid_color,
                    (offset_x + x * self.cell_size, offset_y),
                    (offset_x + x * self.cell_size, offset_y + self.grid_height * self.cell_size)
                )
            for y in range(self.grid_height + 1):
                pygame.draw.line(
                    surface,
                    self.grid_color,
                    (offset_x, offset_y + y * self.cell_size),
                    (offset_x + self.grid_width * self.cell_size, offset_y + y * self.cell_size)
                )
        
        # Draw cells with safety checks
        for y in range(min(self.grid_height, self.grid.shape[0])):
            for x in range(min(self.grid_width, self.grid.shape[1])):
                try:
                    if self.grid[y, x] == 1:
                        pygame.draw.rect(
                            surface,
                            self.cell_color,
                            (
                                offset_x + x * self.cell_size,
                                offset_y + y * self.cell_size,
                                self.cell_size - 1 if self.show_grid else self.cell_size,
                                self.cell_size - 1 if self.show_grid else self.cell_size
                            )
                        )
                except IndexError:
                    # Skip any cells that might be out of bounds
                    continue
        
        # Remove text information display - clean visual without overlay
        
        return True
    
    # MIDI Callbacks
    def change_width(self, cc_number, value, channel, device_name=None):
        """Callback for width CC control"""
        try:
            new_width = int(self.scalecc(value, 10, 100))
            if new_width != self.grid_width:
                old_grid = self.grid.copy() if self.grid is not None else None
                old_width = self.grid_width
                old_height = self.grid_height
                
                # Update the dimension
                self.grid_width = new_width
                self.calculate_cell_size()
                
                # Create a new grid with new dimensions
                new_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
                
                # Copy contents from old grid if possible
                if old_grid is not None:
                    # Determine common dimensions
                    common_height = min(old_height, self.grid_height)
                    common_width = min(old_width, self.grid_width)
                    
                    # Copy the overlapping portion
                    new_grid[:common_height, :common_width] = old_grid[:common_height, :common_width]
                
                # Set the new grid
                self.grid = new_grid
        except Exception as e:
            print(f"Error changing width: {e}")
            # Keep old dimensions if there was an error
    
    def change_height(self, cc_number, value, channel, device_name=None):
        """Callback for height CC control"""
        try:
            new_height = int(self.scalecc(value, 10, 100))
            if new_height != self.grid_height:
                old_grid = self.grid.copy() if self.grid is not None else None
                old_width = self.grid_width
                old_height = self.grid_height
                
                # Update the dimension
                self.grid_height = new_height
                self.calculate_cell_size()
                
                # Create a new grid with new dimensions
                new_grid = np.zeros((self.grid_height, self.grid_width), dtype=np.int8)
                
                # Copy contents from old grid if possible
                if old_grid is not None:
                    # Determine common dimensions
                    common_height = min(old_height, self.grid_height)
                    common_width = min(old_width, self.grid_width)
                    
                    # Copy the overlapping portion
                    new_grid[:common_height, :common_width] = old_grid[:common_height, :common_width]
                
                # Set the new grid
                self.grid = new_grid
        except Exception as e:
            print(f"Error changing height: {e}")
            # Keep old dimensions if there was an error
    
    def change_speed(self, cc_number, value, channel, device_name=None):
        """Callback for evolution speed CC control"""
        self.evolution_speed = self.scalecc(value, 0.2, 2.0)
    
    def reset_grid(self, cc_number, value, channel, device_name=None):
        """Callback to reset/randomize the grid"""
        # Just use a threshold, no need to scale here since we're only checking if > 64
        safe_value = max(0, min(127, int(value)))
        if safe_value > 64:  # Only trigger on higher values
            self.initialize_grid()
    
    def change_color(self, cc_number, value, channel, device_name=None):
        """Callback to change the cell color"""
        # Map 0-127 to a hue value and convert to RGB
        hue = self.scalecc(value, 0.0, 1.0)
        
        # Simple HSV to RGB conversion (just for hue)
        c = 1.0
        x = c * (1 - abs((hue * 6) % 2 - 1))
        m = 0
        
        if hue < 1/6:
            r, g, b = c, x, 0
        elif hue < 2/6:
            r, g, b = x, c, 0
        elif hue < 3/6:
            r, g, b = 0, c, x
        elif hue < 4/6:
            r, g, b = 0, x, c
        elif hue < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        r, g, b = int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
        self.cell_color = (r, g, b)
    
    def change_density(self, cc_number, value, channel, device_name=None):
        """Callback to change initialization density"""
        self.density = self.scalecc(value, 0.05, 0.95)
        # Don't immediately reinitialize - wait for reset trigger
