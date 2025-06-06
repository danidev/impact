#!/usr/bin/env python3

import argparse
from impact_synth.video_synthesizer import VideoSynthesizer
from impact_synth.graphics import draw_grid, draw_system_info

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Impact video synthesizer')
    parser.add_argument('--windowed', action='store_true', help='Run in windowed mode instead of fullscreen')
    args = parser.parse_args()
    
    # Initialize the video synthesizer
    synth = VideoSynthesizer(fullscreen=not args.windowed)
    
    # Main loop
    while synth.running:
        # Handle events (keyboard, quit, etc.)
        if not synth.handle_events():
            break
            
        # Clear the screen
        synth.clear_screen()
        
        # Get current visualization and update it
        current_viz = synth.current_visualization()
        if current_viz:
            current_viz.update()
        
        # Update the display and control framerate
        synth.flip()  # This now handles drawing the visualization
        synth.tick(30)
    
    # Clean up resources
    synth.quit()

if __name__ == "__main__":
    main()