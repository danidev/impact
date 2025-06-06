# impact
Video synthesizer for Linux and macOS

## System Requirements

- Linux (Ubuntu, Debian, etc.) or macOS
- Python 3.6+
- OpenGL-compatible graphics

## Installation

### Linux Setup

```bash
# Install system dependencies
sudo apt install -y python3-pip python3-pygame python3-psutil

# Audio dependencies
sudo apt install -y portaudio19-dev python3-pyaudio

# MIDI support
sudo apt install -y python3-rtmidi

# Install Python packages (if not covered by system packages)
pip3 install --user pygame psutil pyaudio python-rtmidi
```

### macOS Setup

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python if needed
brew install python

# Install dependencies
pip3 install pygame psutil pyaudio python-rtmidi

# Note: On newer macOS versions, you might need to grant permissions
# for terminal access to your MIDI devices
```

## Usage

To run the video synthesizer:

```bash
python3 impact.py
```

To run in windowed mode instead of fullscreen:

```bash
python3 impact.py --windowed
```

### Controls

- **F1**: Toggle overlay (grid and system information)
- **Left/Right Arrow Keys**: Cycle through visualizations
- **ESC**: Exit the application

## MIDI Support

The system supports MIDI input for controlling visualizations through Control Change (CC) messages. Connect a MIDI controller before starting the application to enable this functionality.

The system displays the connected MIDI device and recently received CC messages in the overlay, making it easy to see which controls are being used.

### MIDI Implementation

- Automatically detects and connects to the first available MIDI device
- Processes Control Change (CC) messages
- Can register callbacks for specific CC numbers
- Provides access to current CC values for visualizations

Example of using MIDI in a visualization:

```python
def setup(self, synth):
    super().setup(synth)
    
    # Register a callback for CC #7 (often volume)
    if hasattr(synth, 'midi') and synth.midi:
        synth.midi.register_cc_callback(7, self.handle_cc7)
        
def handle_cc7(self, cc_number, value, channel):
    # Scale from 0-127 to 0.0-1.0
    self.intensity = value / 127.0
    
def draw(self, surface):
    # Use a CC value directly
    if hasattr(self.synth, 'midi') and self.synth.midi:
        # Get CC #1 (often modulation) with default value 0
        mod_value = self.synth.midi.get_cc(1, 0) / 127.0
```

## Adding Visualizations

Create new Python files in the `impact_synth/visualizations/` directory. Each visualization should:

1. Import the base Visualization class
2. Create a class that inherits from Visualization
3. Implement the update() and draw() methods

Example:
```python
from ..visualization import Visualization
import pygame

class MyVisualization(Visualization):
    def __init__(self):
        super().__init__(name="My Cool Visualization")
        # Initialize your variables here
        
    def update(self, dt=0.05):
        # Update animation state
        pass
        
    def draw(self, surface):
        # Draw directly to the provided surface
        # surface is the main screen surface
        pygame.draw.circle(surface, (255, 0, 0), (self.width//2, self.height//2), 100)
        return True
```

## Audio Files

For audio visualizations, place WAV files in the `samples` directory:

```bash
mkdir -p samples
# Then copy your WAV files to this directory
```

The audio visualizations will automatically detect and use WAV files from this directory.

## Similar Projects

This project is inspired by and similar to:
- [EYESY_OS_for_RasPiSound](https://github.com/jqrsound/EYESY_OS_for_RasPiSound) - A Raspberry Pi-based video synthesizer system
- [EYESY Python Modes](https://github.com/jqrsound/EYESY_OS_for_RasPiSound/tree/main/presets/Modes/Python) - A collection of Python-based visual modes for the EYESY video synthesizer
- [ETCVIZ Modes](https://github.com/kbsezginel/etcviz/tree/master/docs/ETC/Modes) - Additional visualization modes for the ETC (Eye Think Computer) visual synthesizer
- You might want to check their implementations for additional visualization ideas and techniques

## Resources

- [Pygame Documentation](https://www.pygame.org/docs/)
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)