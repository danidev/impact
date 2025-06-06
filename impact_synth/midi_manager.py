import time
import threading
import platform
import sys

# Determine the operating system
SYSTEM = platform.system()  # 'Darwin' for macOS, 'Linux' for Linux

# Try multiple rtmidi import strategies for cross-platform compatibility
rtmidi = None
RTMIDI_API_TYPE = None

try:
    # Try standard rtmidi
    import rtmidi
    if hasattr(rtmidi, 'RtMidiIn'):
        RTMIDI_API_TYPE = "original"
    elif hasattr(rtmidi, 'MidiIn'):
        RTMIDI_API_TYPE = "python-rtmidi"
    else:
        # Try alternative imports
        try:
            from rtmidi import RtMidiIn
            rtmidi = sys.modules['rtmidi']
            RTMIDI_API_TYPE = "rtmidi-module"
        except:
            try:
                import rtmidi.midiutil as midiutil
                rtmidi = sys.modules['rtmidi']
                RTMIDI_API_TYPE = "rtmidi-midiutil"
            except:
                RTMIDI_API_TYPE = "unknown"
except ImportError:
    try:
        # Try pip rtmidi-python
        import rtmidi_python as rtmidi
        RTMIDI_API_TYPE = "rtmidi-python"
    except ImportError:
        rtmidi = None
        RTMIDI_API_TYPE = "not-available"

print(f"MIDI system: {SYSTEM}, API type: {RTMIDI_API_TYPE}")

class MidiManager:
    """
    MIDI manager to handle MIDI input and CC messages from all connected devices
    Cross-platform compatible (Linux, macOS, and potentially Windows)
    """
    
    def __init__(self):
        self.running = True
        self.connected = False
        self.midi_inputs = []  # List of all MIDI inputs
        self.midi_devices = []  # List of connected device names
        self.midi_threads = []  # List of processing threads
        
        # Dict to store CC values: {cc_number: value}
        self.cc_values = {}
        
        # Track last CC received: (cc_number, value)
        self.last_cc = None
        
        # Dict to store CC callbacks: {cc_number: [callback_functions]}
        self.cc_callbacks = {}
        
        # Initialize MIDI if available
        self.rtmidi = rtmidi
        
        # Available MIDI ports
        self.available_ports = []
        
        if self.rtmidi:
            self.init_midi()
    
    def create_midi_in(self):
        """Create a MIDI input object based on the detected API type"""
        if RTMIDI_API_TYPE == "original":
            return self.rtmidi.RtMidiIn()
        elif RTMIDI_API_TYPE == "python-rtmidi":
            return self.rtmidi.MidiIn()
        elif RTMIDI_API_TYPE == "rtmidi-python":
            return self.rtmidi.MidiIn()
        elif RTMIDI_API_TYPE == "rtmidi-module":
            return RtMidiIn()
        elif RTMIDI_API_TYPE == "rtmidi-midiutil":
            return midiutil.open_midiinput(interactive=False)[0]
        else:
            raise Exception("Unknown rtmidi API type")
    
    def get_port_count(self, midi_in):
        """Get the number of available MIDI ports"""
        if RTMIDI_API_TYPE == "original":
            return midi_in.getPortCount()
        elif RTMIDI_API_TYPE == "python-rtmidi":
            return midi_in.get_port_count()
        elif RTMIDI_API_TYPE == "rtmidi-python":
            return midi_in.get_port_count()
        elif RTMIDI_API_TYPE in ["rtmidi-module", "rtmidi-midiutil"]:
            return midi_in.getPortCount()
        else:
            return 0
    
    def get_port_name(self, midi_in, port_index):
        """Get the name of a MIDI port"""
        if RTMIDI_API_TYPE == "original":
            return midi_in.getPortName(port_index)
        elif RTMIDI_API_TYPE == "python-rtmidi":
            return midi_in.get_port_name(port_index)
        elif RTMIDI_API_TYPE == "rtmidi-python":
            return midi_in.get_port_name(port_index)
        elif RTMIDI_API_TYPE in ["rtmidi-module", "rtmidi-midiutil"]:
            return midi_in.getPortName(port_index)
        else:
            return f"Unknown Port {port_index}"
    
    def open_port(self, midi_in, port_index):
        """Open a MIDI port"""
        if RTMIDI_API_TYPE == "original":
            midi_in.openPort(port_index)
        elif RTMIDI_API_TYPE == "python-rtmidi":
            midi_in.open_port(port_index)
        elif RTMIDI_API_TYPE == "rtmidi-python":
            midi_in.open_port(port_index)
        elif RTMIDI_API_TYPE in ["rtmidi-module", "rtmidi-midiutil"]:
            midi_in.openPort(port_index)
    
    def close_port(self, midi_in):
        """Close a MIDI port"""
        if RTMIDI_API_TYPE == "original":
            midi_in.closePort()
        elif RTMIDI_API_TYPE == "python-rtmidi":
            midi_in.close_port()
        elif RTMIDI_API_TYPE == "rtmidi-python":
            midi_in.close_port()
        elif RTMIDI_API_TYPE in ["rtmidi-module", "rtmidi-midiutil"]:
            midi_in.closePort()
    
    def ignore_types(self, midi_in, sysex=False, timing=False, active_sensing=False):
        """Configure MIDI message filtering"""
        if RTMIDI_API_TYPE == "original":
            midi_in.ignoreTypes(sysex, timing, active_sensing)
        elif RTMIDI_API_TYPE == "python-rtmidi":
            midi_in.ignore_types(sysex, timing, active_sensing)
        elif RTMIDI_API_TYPE == "rtmidi-python":
            # rtmidi-python doesn't support this, but it's usually not critical
            pass
        elif RTMIDI_API_TYPE in ["rtmidi-module", "rtmidi-midiutil"]:
            midi_in.ignoreTypes(sysex, timing, active_sensing)
    
    def get_message(self, midi_in):
        """Get a MIDI message from the input"""
        if RTMIDI_API_TYPE == "original":
            return midi_in.getMessage(0)  # Non-blocking call
        elif RTMIDI_API_TYPE == "python-rtmidi":
            return midi_in.get_message()
        elif RTMIDI_API_TYPE == "rtmidi-python":
            message = midi_in.get_message()
            if message:
                return message
            return None
        elif RTMIDI_API_TYPE in ["rtmidi-module", "rtmidi-midiutil"]:
            return midi_in.getMessage(0)  # Non-blocking call
        else:
            return None
    
    def init_midi(self):
        """Initialize MIDI inputs for all available devices"""
        if not self.rtmidi:
            return False
            
        try:
            # Create a temporary MIDI input to scan ports
            temp_midi = self.create_midi_in()
            port_count = self.get_port_count(temp_midi)
            
            if port_count == 0:
                return False
            
            # Store available ports
            self.available_ports = []
            self.midi_inputs = []
            self.midi_devices = []
                
            # Open all available ports
            for i in range(port_count):
                try:
                    # Get port name
                    port_name = self.get_port_name(temp_midi, i)
                    self.available_ports.append(port_name)
                    
                    # Create a new MIDI input for this port
                    midi_in = self.create_midi_in()
                    self.open_port(midi_in, i)
                    self.ignore_types(midi_in, False, False, False)
                    
                    # Store the MIDI input and device name
                    self.midi_inputs.append(midi_in)
                    self.midi_devices.append(port_name)
                    
                    # Create a processing thread for this input
                    thread = threading.Thread(target=self.process_midi, args=(midi_in, port_name, i))
                    thread.daemon = True
                    thread.start()
                    self.midi_threads.append(thread)
                except Exception as e:
                    print(f"Error opening MIDI port {i}: {e}")
            
            # If we have at least one MIDI input, we're connected
            if self.midi_inputs:
                self.connected = True
                
                # Use the first device name for backward compatibility
                if self.midi_devices:
                    self.midi_device = self.midi_devices[0]
                else:
                    self.midi_device = "Multiple devices"
                
            return self.connected
                
        except Exception as e:
            print(f"Error initializing MIDI: {e}")
            return False
    
    def process_midi(self, midi_in, device_name, port_index):
        """Process incoming MIDI messages in a separate thread for a specific input"""
        while self.running:
            # Check for messages
            try:
                msg = self.get_message(midi_in)
                if msg:
                    # Process the message
                    self.handle_midi_message(msg, device_name, port_index)
            except Exception as e:
                break
                
            # Sleep to prevent busy-waiting
            time.sleep(0.001)
    
    def handle_midi_message(self, msg, device_name, port_index):
        """Process a MIDI message from any device"""
        if not msg:
            return
            
        try:
            # Different rtmidi implementations have different message formats
            if RTMIDI_API_TYPE == "python-rtmidi":
                # For python-rtmidi, message is a tuple (data, timestamp)
                data, timestamp = msg
                self.process_cc_message(data, device_name)
            elif RTMIDI_API_TYPE == "rtmidi-python":
                # For rtmidi-python, message is already the data
                self.process_cc_message(msg, device_name)
            else:
                # For original rtmidi, we need to handle the RtMidiMessage object
                if hasattr(msg, 'getMessage'):
                    data = msg.getMessage()
                    self.process_cc_message(data, device_name)
                elif hasattr(msg, 'getControllerNumber'):
                    # Some rtmidi implementations have direct controller methods
                    cc_number = msg.getControllerNumber()
                    cc_value = msg.getControllerValue()
                    channel = msg.getChannel()
                    
                    # Store the CC value
                    self.cc_values[cc_number] = cc_value
                    
                    # Track the last CC received
                    self.last_cc = (cc_number, cc_value)
                    
                    # Call any registered callbacks
                    self.trigger_callbacks(cc_number, cc_value, channel, device_name)
                elif isinstance(msg, list) or isinstance(msg, tuple):
                    # Some implementations just return a list/tuple of bytes
                    self.process_cc_message(msg, device_name)
        except Exception as e:
            print(f"Error processing MIDI message: {e}")

    def process_cc_message(self, data, device_name):
        """Process raw MIDI data to extract CC messages"""
        if len(data) >= 2:
            status_byte = data[0]
            message_type = status_byte & 0xF0  # Upper 4 bits = message type
            channel = status_byte & 0x0F  # Lower 4 bits = channel
            
            # Handle Control Change messages (0xB0)
            if message_type == 0xB0 and len(data) >= 3:
                cc_number = data[1]
                cc_value = data[2]
                
                # Store the CC value
                self.cc_values[cc_number] = cc_value
                
                # Track the last CC received
                self.last_cc = (cc_number, cc_value)
                
                # Call any registered callbacks
                self.trigger_callbacks(cc_number, cc_value, channel, device_name)
    
    def get_cc(self, cc_number, default=0):
        """Get the current value of a CC controller"""
        return self.cc_values.get(cc_number, default)
    
    def register_cc_callback(self, cc_number, callback):
        """Register a callback function for a specific CC number"""
        if cc_number not in self.cc_callbacks:
            self.cc_callbacks[cc_number] = []
            
        self.cc_callbacks[cc_number].append(callback)
    
    def unregister_cc_callback(self, cc_number, callback):
        """Unregister a callback function"""
        if cc_number in self.cc_callbacks and callback in self.cc_callbacks[cc_number]:
            self.cc_callbacks[cc_number].remove(callback)
    
    def trigger_callbacks(self, cc_number, value, channel, device_name=None):
        """Trigger all registered callbacks for a CC number"""
        if cc_number in self.cc_callbacks:
            for callback in self.cc_callbacks[cc_number]:
                try:
                    # If the callback accepts 4 arguments, pass the device name as well
                    import inspect
                    sig = inspect.signature(callback)
                    if len(sig.parameters) >= 4:
                        callback(cc_number, value, channel, device_name)
                    else:
                        callback(cc_number, value, channel)
                except Exception:
                    pass
    
    def close(self):
        """Clean up MIDI resources"""
        self.running = False
        
        # Join all threads
        for thread in self.midi_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Close all MIDI inputs
        for midi_in in self.midi_inputs:
            try:
                self.close_port(midi_in)
            except:
                pass
                
        self.connected = False
        
    def get_port_list(self):
        """Return the list of available MIDI ports"""
        return self.available_ports
        
    def get_device_list(self):
        """Return the list of connected MIDI devices"""
        return self.midi_devices
