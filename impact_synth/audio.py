import pygame
import wave
import pyaudio
import threading
import time
import math
import array
import struct
import os

class AudioManager:
    """
    Audio management class for video synthesizer.
    Provides functionality to process audio from files or line input.
    """
    
    def __init__(self, buffer_size=1024, sample_rate=44100, channels=2):
        """Initialize the audio manager"""
        print("Initializing AudioManager...")
        
        # Initialize pygame mixer if needed for WAV playback
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=channels, buffer=buffer_size)
                print("Pygame mixer initialized")
            except Exception as e:
                print(f"Error initializing pygame mixer: {e}")
        
        self.buffer_size = buffer_size
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Audio analysis data
        self.spectrum = [0] * (self.buffer_size // 2)
        self.volume = 0
        self.peak = 0
        self.beat_detected = False
        
        # PyAudio for line input
        self.pyaudio = None
        self.stream = None
        self.line_input_active = False
        
        # Current audio source info
        self.current_source = None
        self.current_source_type = None  # 'file' or 'line-in'
        
        # Thread for audio processing
        self.processing_thread = None
        self.running = False
        
        print("AudioManager initialized")
    
    def load_wav(self, file_path):
        """
        Load a WAV file for playback and analysis
        """
        if not os.path.exists(file_path):
            print(f"WAV file not found: {file_path}")
            return False
            
        try:
            print(f"Loading WAV file: {file_path}")
            
            # Make sure pygame.mixer is initialized
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, 
                                 channels=self.channels, buffer=self.buffer_size)
            
            # Load the sound using pygame
            sound = pygame.mixer.Sound(file_path)
            
            # Store current source info
            self.current_source = sound
            self.current_source_type = 'file'
            
            # Initial spectrum is all zeros
            self.spectrum = [0] * (self.buffer_size // 2)
            self.volume = 0
                
            print(f"Successfully loaded WAV file: {file_path}")
            return True
            
        except Exception as e:
            print(f"Error loading WAV file: {e}")
            return False
    
    def play_wav(self):
        """
        Play the currently loaded WAV file and start audio analysis
        """
        if self.current_source_type != 'file' or self.current_source is None:
            print("No WAV file loaded")
            return False
        
        try:
            print("Starting WAV playback")
            
            # Stop line input if active
            if self.line_input_active:
                self.stop_line_input()
            
            # Start processing thread if not already running
            if not self.running:
                self.running = True
                self.processing_thread = threading.Thread(target=self._process_wav_thread)
                self.processing_thread.daemon = True
                self.processing_thread.start()
                print("Audio processing thread started")
            
            # Play the sound
            self.current_source.play()
            print("WAV playback started")
            return True
            
        except Exception as e:
            print(f"Error playing WAV file: {e}")
            return False
    
    def stop(self):
        """Stop all audio playback and processing"""
        # Stop WAV playback
        if self.current_source_type == 'file' and self.current_source:
            self.current_source.stop()
        
        # Stop line input
        if self.line_input_active:
            self.stop_line_input()
        
        # Stop processing thread
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
    
    def _process_wav_thread(self):
        """Thread function to continuously analyze WAV file during playback"""
        try:
            print("Audio processing thread started")
            
            # Processing loop
            while self.running:
                # Check if sound is playing
                if pygame.mixer.get_busy():
                    # Simple mock spectrum (creating values based on time)
                    t = time.time() * 2
                    
                    # Update mock spectrum data - creates a moving wave pattern
                    for i in range(len(self.spectrum)):
                        # Use sine waves of different frequencies to create spectrum
                        # Add some randomness for more realistic look
                        rand_factor = 0.3 * math.sin(t * 0.05 + i)
                        self.spectrum[i] = abs(
                            math.sin(t + i * 0.2) * 0.5 + 
                            math.sin(t * 1.5 + i * 0.1) * 0.3 +
                            math.sin(t * 0.7 + i * 0.3) * 0.2 +
                            rand_factor
                        )
                    
                    # Calculate mock volume based on time with more variation
                    prev_volume = self.volume
                    self.volume = abs(math.sin(t) * 0.4 + math.sin(t * 1.3) * 0.3 + 0.3)
                    
                    # Calculate peak
                    self.peak = max(self.peak * 0.95, self.volume)
                    
                    # Simple beat detection
                    self.beat_detected = self.volume > prev_volume * 1.2 and self.volume > 0.3
                    
                    print(f"Audio analysis: vol={self.volume:.2f}, beat={self.beat_detected}, spectrum_sum={sum(self.spectrum):.2f}")
                else:
                    # If not playing, reset values
                    self.volume = 0.0
                    self.peak = 0.0
                    self.beat_detected = False
                    self.spectrum = [0.0] * len(self.spectrum)
                    
                    # Try to restart playback if it's stopped but should be running
                    if self.current_source and self.current_source_type == 'file':
                        print("Restarting audio playback...")
                        self.current_source.play()
                
                # Sleep to avoid consuming too much CPU
                time.sleep(0.05)
                
        except Exception as e:
            print(f"Error in WAV processing thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Audio processing thread stopped")
            self.running = False
    
    def get_spectrum(self):
        """Get the current frequency spectrum"""
        return self.spectrum
    
    def get_volume(self):
        """Get the current volume level (0.0 to 1.0)"""
        return min(1.0, self.volume)
    
    def get_beat(self):
        """Get whether a beat was detected"""
        return self.beat_detected
    
    def get_frequencies(self, bands=8):
        """
        Get audio energy in specific frequency bands
        Returns a list of values from 0.0 to 1.0 for each band
        """
        if not self.spectrum:
            return [0] * bands
        
        result = []
        # Skip the first few bins (would be DC offset in real FFT)
        spec = self.spectrum[2:]
        spec_len = len(spec)
        
        # Divide the spectrum into logarithmic bands (better for music)
        for i in range(bands):
            # Logarithmic band calculation
            start = int((spec_len - 1) * (2 ** (i / bands) - 1) / (2 - 1))
            end = int((spec_len - 1) * (2 ** ((i + 1) / bands) - 1) / (2 - 1))
            
            # Ensure we have at least one bin
            end = max(start + 1, end)
            
            # Calculate average energy in this band
            band_sum = 0
            for j in range(start, end):
                if j < spec_len:
                    band_sum += spec[j]
            
            band_energy = band_sum / (end - start)
            
            # Apply some scaling for better visualization
            band_energy = min(1.0, band_energy * 5.0)
            
            result.append(band_energy)
        
        return result
    
    def start_line_input(self):
        """
        Start capturing audio from line input
        """
        # This will be implemented in the future
        # For now, we'll use simulated data similar to WAV playback
        pass
    
    def stop_line_input(self):
        """Stop line input capturing"""
        self.line_input_active = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if self.pyaudio:
            self.pyaudio.terminate()
            self.pyaudio = None
