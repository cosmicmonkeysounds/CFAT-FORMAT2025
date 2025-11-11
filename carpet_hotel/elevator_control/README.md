# Elevator Control Panel - Arduino Integration

This system provides a hardware elevator control panel that integrates directly with the carpet_hotel project. The Arduino communicates via simple serial messages, and the Python launcher (`run_carpet_hotel.py`) handles conversion to OSC messages for Processing and SuperCollider.

## Hardware Setup

### Components
- **Arduino Nano** board
- **2 Momentary Switches** (normally-closed)
  - DOWN button → Pin A0
  - UP button → Pin A1
- **3 LEDs** with appropriate resistors (typically 220Ω-330Ω)
  - GREEN LED → Pin D3 (PWM)
  - YELLOW LED → Pin D5 (PWM)
  - RED LED → Pin D6 (PWM)

### Wiring
```
Buttons:
  Pin A0 ----[Button]---- GND
  Pin A1 ----[Button]---- GND
  (Internal pull-up resistors are enabled in code)

LEDs (all PWM-capable pins for animations):
  Pin D3 ----[330Ω]----[GREEN LED]---- GND
  Pin D5 ----[330Ω]----[YELLOW LED]---- GND
  Pin D6 ----[330Ω]----[RED LED]---- GND
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

## LED Animations

The system features automatic LED animations controlled by the Python launcher:

### Stable Scene Mode
- **GREEN LED pulses gently** (50%-100% brightness using PWM)
- Yellow and Red LEDs are off
- Indicates the system is ready and in a stable scene

### Transition Mode
- **LEDs cycle**: RED → YELLOW → GREEN
- Each LED lights up in sequence
- Indicates a scene transition is in progress
- Default period: 400ms per LED

## Communication Protocol

### Serial Protocol (Arduino ↔ Python)

**Sent by Arduino:**
- `up` - UP button pressed
- `down` - DOWN button pressed

**Received by Arduino:**
- `ANIM:STABLE` - Start stable mode (green pulse)
- `ANIM:TRANSITION` - Start transition animation (RGB cycle)
- `ANIM:OFF` - Turn off all LEDs
- `PERIOD:xxx` - Set transition period in milliseconds

### OSC Protocol (Python ↔ Processing)

**Sent to Processing (port 12000):**
- `/carpet/elevator/up` - UP button pressed
- `/carpet/elevator/down` - DOWN button pressed

**Default Configuration:**
- **Serial**: 115200 baud (Arduino ↔ Python)
- **OSC**: Port 12000 (Python → Processing)
- **OSC**: Port 12001 (Processing → Python)
- Button presses trigger scene changes
- LED animations indicate system state automatically

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

### 2. LED Status Indicators

LED animations are **automatically controlled** by the Python launcher based on scene state:
- **Stable scenes**: Green LED pulses gently
- **Scene transitions**: LEDs cycle RED → YELLOW → GREEN

No additional code needed in Processing - the launcher handles LED feedback automatically when scenes change via `/carpet/goto` commands.

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
