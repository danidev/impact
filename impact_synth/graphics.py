import pygame
import math
import psutil

def draw_grid(synth, surface=None, spacing=50, color=(50, 50, 50)):
    """Draw a grid directly onto the provided surface"""
    # Use provided surface or create a new one if needed
    if surface is None:
        surface = pygame.Surface((synth.width, synth.height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # Clear with transparency
    
    for x in range(0, synth.width, spacing):
        pygame.draw.line(surface, color, (x, 0), (x, synth.height))
    for y in range(0, synth.height, spacing):
        pygame.draw.line(surface, color, (0, y), (synth.width, y))
        
    return surface

def draw_sinusoid(synth, surface=None, time_offset=0, color=(0, 255, 0), amplitude=50, frequency=0.01):
    """Draw a sinusoid with glow effect directly onto the provided surface"""
    # Use provided surface or create a new one if needed
    if surface is None:
        surface = pygame.Surface((synth.width, synth.height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # Clear with transparency
    
    # Calculate sinusoid points
    points = []
    for x in range(0, synth.width, 2):
        y = int(synth.height / 2 + amplitude * math.sin(frequency * x + time_offset))
        points.append((x, y))
    
    if len(points) > 1:
        # Method to create glow: draw thicker lines with lower opacity
        # Layer 4 (outermost)
        pygame.draw.lines(surface, (0, 40, 0), False, points, 10)
        # Layer 3
        pygame.draw.lines(surface, (0, 80, 0), False, points, 8)
        # Layer 2
        pygame.draw.lines(surface, (0, 120, 0), False, points, 6)
        # Layer 1
        pygame.draw.lines(surface, (0, 160, 0), False, points, 4)
        # Main line
        pygame.draw.lines(surface, color, False, points, 2)
    
    return surface

def draw_system_info(synth, surface=None):
    """Draw system information directly onto the provided surface"""
    # Use provided surface or create a new one if needed
    if surface is None:
        surface = pygame.Surface((synth.width, synth.height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))  # Clear with transparency
    
    # Read current values
    current_cpu = psutil.cpu_percent()
    current_mem = psutil.virtual_memory().percent
    
    # Update lists with new values
    synth.cpu_values[synth.cpu_index] = current_cpu
    synth.mem_values[synth.mem_index] = current_mem
    
    # Update indices circularly
    synth.cpu_index = (synth.cpu_index + 1) % len(synth.cpu_values)
    synth.mem_index = (synth.mem_index + 1) % len(synth.mem_values)
    
    # Calculate averages
    avg_cpu = sum(synth.cpu_values) / len(synth.cpu_values)
    avg_mem = sum(synth.mem_values) / len(synth.mem_values)

    # Format values with fixed decimal places (1 decimal)
    cpu_formatted = f"{avg_cpu:.1f}".rjust(5)
    mem_formatted = f"{avg_mem:.1f}".rjust(5)
    
    # Display all system information on a single line in the bottom
    info_text = f"CPU: {cpu_formatted}% | MEM: {mem_formatted}% | FPS: {synth.fps} | RES: {synth.width}x{synth.height}"
    text_surface = synth.font.render(info_text, True, (255, 255, 255))
    
    # Position text centered at the bottom of the screen
    info_x = (synth.width - text_surface.get_width()) // 2
    info_y = synth.height - text_surface.get_height() - 20
    
    # Create a black background behind the text for better readability
    padding = 10  # Padding around text
    bg_rect = pygame.Rect(
        info_x - padding, 
        info_y - padding,
        text_surface.get_width() + (padding * 2),
        text_surface.get_height() + (padding * 2)
    )
    pygame.draw.rect(surface, (0, 0, 0), bg_rect)  # Semi-transparent black
    
    # Draw the text on top of the background
    surface.blit(text_surface, (info_x, info_y))
    
    # Display the current visualization name at the top of the screen
    current_viz = synth.current_visualization()
    if current_viz:
        viz_name = current_viz.name
        name_surface = synth.font.render(viz_name, True, (255, 255, 255))
        name_x = (synth.width - name_surface.get_width()) // 2
        name_y = 20  # 20 pixels from the top
        
        # Create a black background behind the visualization name
        name_bg_rect = pygame.Rect(
            name_x - padding,
            name_y - padding,
            name_surface.get_width() + (padding * 2),
            name_surface.get_height() + (padding * 2)
        )
        pygame.draw.rect(surface, (0, 0, 0), name_bg_rect)  # Semi-transparent black
        
        # Draw the name on top of the background
        surface.blit(name_surface, (name_x, name_y))
    
    # Add MIDI information if available - devices on separate lines and last CC
    if hasattr(synth, 'midi') and synth.midi is not None:
        # Get list of connected devices
        devices = getattr(synth.midi, 'midi_devices', [])
        
        # Calculate line height first before using it
        line_height = synth.font.get_height() + 2
        
        # Calculate how many lines we need (one per device + one for last CC)
        num_lines = len(devices) + 1 if devices else 1
        
        # Create a list of text lines
        midi_lines = []
        
        # Add one line per device
        if devices:
            for device in devices:
                midi_lines.append(f"MIDI: {device}")
        else:
            midi_lines.append("MIDI: No devices")
        
        # Add line for last CC
        last_cc = getattr(synth.midi, 'last_cc', None)
        if last_cc:
            cc_num, cc_val = last_cc
            midi_lines.append(f"Last CC: {cc_num}={cc_val}")
        else:
            midi_lines.append("No CC received")
        
        # Render MIDI info text
        try:
            # Position at middle left of the screen
            midi_x = 10  # Keep at left edge
            midi_y = (synth.height // 2) - ((line_height * num_lines) // 2)  # Vertically centered
            
            # Create background for MIDI info
            padding = 5
            # Calculate total height needed
            total_height = (line_height * num_lines) + (padding * 2)
            
            # Find longest line to determine width
            max_width = 0
            for line in midi_lines:
                line_width = synth.font.size(line)[0]
                max_width = max(max_width, line_width)
            
            # Create background rect
            midi_bg_rect = pygame.Rect(
                midi_x - padding,
                midi_y - padding,
                max_width + (padding * 2),
                total_height
            )
            pygame.draw.rect(surface, (0, 0, 50), midi_bg_rect)  # Dark blue background
            
            # Draw each line of text
            for i, line in enumerate(midi_lines):
                line_y = midi_y + (i * line_height)
                midi_surface = synth.font.render(line, True, (200, 200, 255))
                surface.blit(midi_surface, (midi_x, line_y))
        except Exception:
            pass
    
    return surface
