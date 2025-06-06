import pygame
import os
import math
import time
from ..visualization import Visualization

class AudioWave(Visualization):
    def __init__(self):
        super().__init__(name="Audio Waveform")
        self.color = (0, 200, 255)
        self.base_height = 100
        self.bands = 8  # Reduced to 8 frequency bands for simpler visualization
        self.time = 0
        self.mock_spectrum = None
        self.mock_volume = 0
        self.mock_beat = False
    
    def setup(self, synth):
        super().setup(synth)
        
        # Debug: Check if audio manager exists
        if not hasattr(self.synth, 'audio') or self.synth.audio is None:
            print("ERROR: Audio manager not found in synthesizer")
            print("Will use simulated audio data instead")
            self.mock_spectrum = [0] * self.bands
            return
            
        # Simply try to load a WAV file with the same name as this visualization
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        sample_dir = os.path.join(project_dir, 'samples')
        
        # Get the filename without extension and with .wav
        visualization_name = os.path.splitext(os.path.basename(__file__))[0]
        wav_filename = f"{visualization_name}.wav"
        wav_path = os.path.join(sample_dir, wav_filename)
        
        print(f"Looking for matching WAV file: {wav_path}")
        
        if os.path.exists(wav_path):
            print(f"Found matching WAV file: {wav_path}")
            success = self.synth.audio.load_wav(wav_path)
            if success:
                self.synth.audio.play_wav()
        else:
            print(f"No matching WAV file found at: {wav_path}")
            
            # Create samples directory if it doesn't exist
            if not os.path.exists(sample_dir):
                try:
                    os.makedirs(sample_dir)
                except Exception as e:
                    print(f"Could not create samples directory: {e}")
                    
            print(f"Please place a WAV file named '{wav_filename}' in the samples directory")

    def update(self, dt=0.05):
        self.time += dt
        
        # If no audio manager, update mock audio data
        if not hasattr(self.synth, 'audio') or self.synth.audio is None:
            t = self.time * 2
            
            # Create mock spectrum data
            if self.mock_spectrum is None:
                self.mock_spectrum = [0] * self.bands
                
            for i in range(len(self.mock_spectrum)):
                self.mock_spectrum[i] = abs(math.sin(t + i * 0.2) * 0.5 + 
                                     math.sin(t * 1.5 + i * 0.1) * 0.3 +
                                     math.sin(t * 0.7 + i * 0.3) * 0.2)
            
            # Mock volume
            prev_volume = self.mock_volume
            self.mock_volume = abs(math.sin(t) * 0.4 + 0.2)
            
            # Mock beat detection
            self.mock_beat = self.mock_volume > prev_volume * 1.3 and self.mock_volume > 0.1
    
    def draw(self, surface):
        if not self.synth:
            return
            
        # Get spectrum data - either real or mock
        if hasattr(self.synth, 'audio') and self.synth.audio is not None:
            frequencies = self.synth.audio.get_frequencies(self.bands)
            volume = self.synth.audio.get_volume()
            beat = self.synth.audio.get_beat()
        else:
            frequencies = self.mock_spectrum
            volume = self.mock_volume
            beat = self.mock_beat
        
        # Only print debug info occasionally to avoid console spam
        if int(self.time * 10) % 50 == 0:  # Print roughly every 5 seconds
            print(f"Drawing audio wave: vol={volume:.2f}, beat={beat}, freqs_sum={sum(frequencies):.2f}")
        
        # Ensure we have some values to draw
        if not frequencies or all(f == 0 for f in frequencies):
            # If we have no real data, generate some dummy values for visualization
            t = self.time * 2
            frequencies = [abs(math.sin(t + i * 0.2)) for i in range(self.bands)]
            volume = abs(math.sin(t) * 0.6 + 0.4)  # Ensure we have visible volume
            
        # Calculate bar width based on screen size and number of bands
        # Use a percentage of screen width for all bars
        total_bars_width = int(self.synth.width * 0.8)  # Use 80% of screen width
        bar_width = total_bars_width // self.bands
        padding = bar_width // 4
        
        # Calculate starting x position to center the bars
        start_x = (self.synth.width - (bar_width + padding) * self.bands + padding) // 2
        
        # Draw background on beat
        if beat:
            # Simple white flash on beat
            surface.fill((50, 50, 50))
        
        # Draw frequency bars
        for i, freq in enumerate(frequencies):
            # Make sure frequency has a minimum value for visibility
            freq = max(0.05, freq)
            
            # Calculate bar height based on frequency intensity (ensure minimum height)
            # Limit height to stay within screen
            max_height = self.synth.height - 100  # Leave some space at top and bottom
            bar_height = min(max_height, max(20, int(self.base_height * freq * (1 + volume))))
            
            # Calculate position - centered horizontally
            x = start_x + i * (bar_width + padding)
            y = self.synth.height - bar_height - 50  # Bottom padding
            
            # Simple black and white color scheme
            color = (128, 128, 128)  # White bars
            
            # Draw bar
            pygame.draw.rect(
                surface, 
                color, 
                (x, y, bar_width, bar_height)
            )
        
        # Draw volume meter at the bottom with minimum width for visibility
        volume_width = max(20, int(self.synth.width * 0.8 * volume))
        
        # Draw volume meter background
        pygame.draw.rect(
            surface,
            (50, 50, 50),
            (self.synth.width // 10, self.synth.height - 20, int(self.synth.width * 0.8), 10)
        )
        
        # Draw active volume meter
        pygame.draw.rect(
            surface,
            (255, 255, 255),
            (self.synth.width // 10, self.synth.height - 20, volume_width, 10)
        )