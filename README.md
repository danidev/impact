# impact
video synthesizer

## System Requirements

Uses Raspberry Pi OS Lite (32 bit)

## SSH Setup

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

## Installation

### Main Dependencies

```bash
sudo apt install -y python3-pip
sudo apt install python3-pygame
sudo apt install python3-psutil
```

### Minimal X Server (for headless setup)

```bash
sudo apt install --no-install-recommends xserver-xorg xinit x11-xserver-utils
```

### Audio Dependencies

For audio processing, additional dependencies are required:

```bash
sudo apt install portaudio19-dev
sudo apt install python3-pyaudio
```

### MIDI Support

For MIDI control support, install the `rtmidi` package:

```bash
sudo apt install python3-rtmidi
```

## Usage

To run the video synthesizer:

```bash
python3 synth_player.py
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

Create new Python files in the `synth_video/visualizations/` directory. Each visualization should:

1. Import the base Visualization class
2. Create a class that inherits from Visualization
3. Implement the update() and draw() methods

Example:
```python
from ..visualization import Visualization

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
mkdir -p /home/daniele/git/smallprojects/synth-video/samples
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