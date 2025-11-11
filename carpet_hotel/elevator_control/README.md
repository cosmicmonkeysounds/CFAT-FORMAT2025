# Elevator Control Panel - Arduino Integration

This system provides a hardware elevator control panel that integrates directly with the carpet_hotel project. The Arduino communicates via simple serial messages, and the Python launcher (`run_carpet_hotel.py`) handles conversion to OSC messages for Processing and SuperCollider.

## Hardware Setup

### Components
- **Arduino Nano** board
- **2 Momentary Switches** (normally-closed)
  - DOWN button → Pin A0
  - UP button → Pin A1
- **3 LEDs** with appropriate resistors (typically 220Ω-330Ω)
  - GREEN LED → Pin D2
  - YELLOW LED → Pin D3
  - RED LED → Pin D4

### Wiring
```
Buttons:
  Pin A0 ----[Button]---- GND
  Pin A1 ----[Button]---- GND
  (Internal pull-up resistors are enabled in code)

LEDs:
  Pin D2 ----[330Ω]----[GREEN LED]---- GND
  Pin D3 ----[330Ω]----[YELLOW LED]---- GND
  Pin D4 ----[330Ω]----[RED LED]---- GND
```

## Installation

### 1. Install Arduino IDE and Upload Sketch

1. **Install Arduino IDE**
   - Download from https://www.arduino.cc/en/software
   - Arduino Nano uses the built-in Arduino AVR boards (no additional board packages needed)

2. **Upload the Sketch**
   - Open `elevator_control.ino` in Arduino IDE
   - Select board: Tools → Board → Arduino AVR Boards → Arduino Nano
   - Select processor: Tools → Processor → ATmega328P (Old Bootloader) or ATmega328P depending on your Nano
   - Select port: Tools → Port → (select the port with Arduino Nano)
   - Click Upload button

### 2. Install Python Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt

# Or install individually
pip install python-osc pyserial
```

## Running the System

The Arduino elevator control is **automatically integrated** into the main carpet_hotel launcher!

### Quick Start

1. Upload the Arduino sketch (see Installation section above)
2. Connect the Arduino via USB
3. Run the carpet_hotel launcher:

```bash
python run_carpet_hotel.py
```

The launcher will:
- Auto-detect the Arduino
- Connect via serial
- Convert button presses to OSC messages
- Forward LED control messages from Processing to the Arduino

That's it! No separate bridge script needed.

## OSC Communication Protocol

### Messages SENT (Button Presses → Processing)
- `/carpet/elevator/up` - UP button pressed
- `/carpet/elevator/down` - DOWN button pressed

### Messages RECEIVED (LED Control from Processing)
- `/carpet/elevator/led/red [0 or 1]` - Control RED LED
- `/carpet/elevator/led/yellow [0 or 1]` - Control YELLOW LED
- `/carpet/elevator/led/green [0 or 1]` - Control GREEN LED

### Default Configuration
- **Serial**: 115200 baud (Arduino ↔ Python)
- **OSC**: Port 12000 (Python ↔ Processing)
- **OSC**: Port 12001 (Processing → Python)
- Button presses are sent as OSC to Processing
- LED commands are received via OSC from Processing

## Integration with carpet_hotel

To integrate the elevator control with your carpet_hotel Processing sketch:

### 1. Receive Button Presses (in Processing)

```java
import oscP5.*;

OscP5 oscP5;

void setup() {
  oscP5 = new OscP5(this, 12000);  // Receive on port 12000
}

void oscEvent(OscMessage msg) {
  if (msg.checkAddrPattern("/carpet/elevator/up")) {
    println("Elevator UP button pressed");
    // Your logic here - e.g., go to next scene
    currentScene = (currentScene + 1) % totalScenes;
  }
  else if (msg.checkAddrPattern("/carpet/elevator/down")) {
    println("Elevator DOWN button pressed");
    // Your logic here - e.g., go to previous scene
    currentScene = (currentScene - 1 + totalScenes) % totalScenes;
  }
}
```

### 2. Send LED Commands (from Processing)

```java
import netP5.*;

NetAddress pythonLauncher;

void setup() {
  pythonLauncher = new NetAddress("127.0.0.1", 12001);
}

void controlElevatorLEDs(int red, int yellow, int green) {
  OscMessage msg;

  msg = new OscMessage("/carpet/elevator/led/red");
  msg.add(red);
  oscP5.send(msg, pythonLauncher);

  msg = new OscMessage("/carpet/elevator/led/yellow");
  msg.add(yellow);
  oscP5.send(msg, pythonLauncher);

  msg = new OscMessage("/carpet/elevator/led/green");
  msg.add(green);
  oscP5.send(msg, pythonLauncher);
}

// Example: Set status based on state
void updateElevatorStatus() {
  if (isTransitioning) {
    controlElevatorLEDs(0, 1, 0);  // Yellow during transition
  } else if (isReady) {
    controlElevatorLEDs(0, 0, 1);  // Green when ready
  } else {
    controlElevatorLEDs(1, 0, 0);  // Red when busy
  }
}
```

**Note**: Send LED commands to port 12001 (the Python launcher's receive port), not directly to the Arduino. The Python launcher will forward them via serial.

## Testing

A standalone test script is provided to verify hardware without the full system:

```bash
python test_elevator_arduino.py
```

This test script:
- Connects to Arduino directly via serial (no OSC)
- Displays button presses
- Allows keyboard control of LEDs (r/y/g keys)

## Troubleshooting

### Arduino Issues

**Arduino not found**
- Make sure the USB cable is connected
- Check that the board appears in Arduino IDE under Tools → Port
- Try a different USB cable (some cables are power-only)
- Run `python elevator_osc_bridge.py --list-ports` to see available ports

**Upload fails**
- Try selecting the other processor option: Tools → Processor → ATmega328P (Old Bootloader)
- Check that the correct COM/serial port is selected
- Try pressing the reset button just before uploading

**Buttons not working**
- Check wiring connections
- Verify buttons are normally-closed type (closes when pressed)
- Test continuity with multimeter
- Check serial monitor in Arduino IDE for messages

**LEDs not working**
- Check polarity (long leg = positive/anode)
- Verify resistor values (220Ω-330Ω recommended)
- Test LEDs with multimeter or separate power source

### Integration Issues

**Arduino not detected**
- Check that Arduino is connected and shows up in system
- Check launcher output for Arduino detection messages
- Verify pyserial is installed: `pip install pyserial`
- Make sure no other program is using the serial port (like Arduino IDE serial monitor)

**Button presses not received**
- Check launcher log file for "[Arduino]" messages
- Verify Processing is receiving OSC on port 12000
- Use test_elevator_arduino.py to verify Arduino is sending messages
- Check that `enable_osc_external=True` in launcher

**LEDs not responding**
- Check launcher log for "[Arduino] LED command" messages
- Verify Processing is sending to port 12001
- Use Arduino IDE serial monitor to test LED commands directly (send "RED:1")
- Verify LED addresses match exactly: `/carpet/elevator/led/red`, etc.

### Serial Monitor Conflicts

If you want to use Arduino IDE's serial monitor for debugging:
1. Stop the carpet_hotel launcher (Ctrl+C)
2. Open Arduino IDE serial monitor
3. Watch for button press messages ("up", "down")
4. Send LED commands manually (e.g., "RED:1")

Only one program can access the serial port at a time. The launcher and Arduino IDE serial monitor cannot both be connected simultaneously.

## Architecture

```
┌─────────────────┐
│  Arduino Nano   │
│                 │
│  [Buttons]      │
│  [LEDs]         │
└────────┬────────┘
         │ USB Serial (115200 baud)
         │ "up" / "down"
         │ "RED:1" / "YELLOW:0" etc.
         │
┌────────▼────────────────────────────────┐
│  Python Launcher                        │
│  run_carpet_hotel.py                    │
│                                         │
│  • Manages SuperCollider & Processing  │
│  • Handles Arduino serial I/O          │
│  • Converts serial ↔ OSC               │
└────────┬────────────────────────────────┘
         │ OSC over UDP
         │ (Ports 12000/12001)
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
┌────────▼────────┐  ┌──────▼──────┐  ┌───────▼─────────┐
│  Processing     │  │ SuperCollider│  │  Python Terminal│
│  (Visuals)      │  │ (Audio)      │  │  (Control)      │
└─────────────────┘  └──────────────┘  └─────────────────┘
```

The Arduino sends simple serial messages to keep the embedded code reliable. The Python launcher is the central hub that handles all communication between components via OSC.

## Notes

- Arduino baud rate: 115200
- Button debounce delay: 50ms
- OSC messages use the `/carpet/elevator/*` address space
- The launcher automatically turns off all LEDs on shutdown
- Button presses are sent immediately when detected
- LED states are maintained on the Arduino (persistent until changed)
- Arduino serial communication uses efficient char buffers (no String objects) for reliability
- The Python launcher acts as the central OSC bus for all components
