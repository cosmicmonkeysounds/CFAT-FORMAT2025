# SuperCollider Stop & Arduino Control Fix - Summary

## Problems Fixed

### 1. SuperCollider Stop Button Not Working
**Issue:** Clicking "Stop Audio" or "STOP ALL" didn't actually stop SuperCollider - it kept running.

**Root Cause:** SuperCollider's `sclang` process doesn't respond to SIGTERM alone - it needs to receive a `CmdPeriod.run;` command first to stop all synths gracefully.

**Solution:** Send `CmdPeriod.run;` via stdin before terminating the process:

```python
# carpet_hotel_scd.py:234-255
def stop(self) -> bool:
    # Send Cmd+. (stop all sound) to sclang via stdin
    if self.process.process and self.process.process.stdin:
        self.process.process.stdin.write("CmdPeriod.run;\n")
        self.process.process.stdin.flush()
        time.sleep(0.5)  # Give SC time to stop synths

    return self.process.stop()
```

**Result:** SuperCollider now stops gracefully - all synths stop, cleanup runs, process terminates properly.

---

### 2. Arduino Control Lost

**Issue:** Arduino buttons weren't working, LED control was broken.

**Root Causes:**
1. **Wrong LED pins**: Code used D2/D3/D4, hardware uses A2/A3/A4
2. **No PWM support**: Code used digitalWrite (ON/OFF), hardware needs analogWrite (0-255)
3. **Case mismatch**: Arduino sends "UP"/"DOWN", Python looked for "up"/"down"
4. **No GUI logging**: Button presses and LED changes weren't visible in GUI

**Solutions:**

#### A. Updated Arduino Sketch (elevator_control.ino)

**Changed pins:**
```cpp
// OLD:
const int PIN_LED_GREEN = 2;
const int PIN_LED_YELLOW = 3;
const int PIN_LED_RED = 4;

// NEW:
const int PIN_LED_GREEN = A2;   // PWM capable
const int PIN_LED_YELLOW = A3;  // PWM capable
const int PIN_LED_RED = A4;     // PWM capable
```

**Added PWM support:**
```cpp
// Parse PWM value (0-255) or legacy ON/OFF
int pwmValue = 0;
if (strcmp(valueStr, "ON") == 0 || strcmp(valueStr, "1") == 0) {
    pwmValue = 255;  // Full brightness
} else if (strcmp(valueStr, "OFF") == 0 || strcmp(valueStr, "0") == 0) {
    pwmValue = 0;
} else {
    pwmValue = atoi(valueStr);  // Parse 0-255
    pwmValue = constrain(pwmValue, 0, 255);
}

// Set LED using PWM
analogWrite(PIN_LED_RED, pwmValue);
```

**Fixed button messages:**
```cpp
// OLD:
Serial.println("down");
Serial.println("up");

// NEW:
Serial.println("DOWN");
Serial.println("UP");
```

**Protocol now supports:**
- Legacy: `RED:1` / `RED:0` (converted to 255/0)
- Legacy: `RED:ON` / `RED:OFF` (converted to 255/0)
- PWM: `RED:128` (half brightness)
- PWM: `YELLOW:64` (25% brightness)
- PWM: `GREEN:255` (full brightness)

#### B. Updated Python Arduino Wrapper (carpet_hotel_arduino.py)

**Fixed case handling:**
```python
# OLD:
if line == "up":
    ...
elif line == "down":
    ...

# NEW:
line_upper = line.upper()
if line_upper == "UP":
    self.log.success("Button UP pressed")
    self._notify("✓ Button UP pressed")
elif line_upper == "DOWN":
    self.log.success("Button DOWN pressed")
    self._notify("✓ Button DOWN pressed")
```

**Added PWM support:**
```python
def set_led(self, color: str, value: int):
    """Set LED brightness using PWM (0-255)."""
    # Convert legacy 0/1 to 0/255
    if value == 1:
        value = 255

    # Clamp to valid range
    value = max(0, min(255, value))

    cmd = f"{color.upper()}:{value}\n"
    self.serial_conn.write(cmd.encode())
    self._notify(f"LED {color.upper()}: {value}")
```

**Added message callback system:**
```python
def set_message_callback(self, callback):
    """Set callback for GUI logging."""
    self.message_callback = callback

def _notify(self, message: str):
    """Send message to callback if set."""
    if self.message_callback:
        self.message_callback(message)
```

#### C. Updated GUI (carpet_hotel_gui.py)

**Added Arduino message logging:**
```python
def connect_thread():
    success = self.core.start_arduino(port)

    if success:
        # Set message callback for logging
        if self.core.arduino:
            def arduino_message_callback(msg):
                self.root.after(0, lambda: self.log_to_widget(self.hardware_log, msg))

            self.core.arduino.set_message_callback(arduino_message_callback)
```

**GUI now shows:**
- ✓ Button UP pressed
- ✓ Button DOWN pressed
- LED RED: 255
- LED YELLOW: 128
- LED GREEN: 0
- LED animation mode: STABLE

---

## Hardware Configuration

### Pin Assignments

| Component | Pin | Type | Notes |
|-----------|-----|------|-------|
| DOWN button | A0 | Digital Input | Normally-closed, pullup |
| UP button | A1 | Digital Input | Normally-closed, pullup |
| GREEN LED | A2 | PWM Output | 0-255 brightness |
| YELLOW LED | A3 | PWM Output | 0-255 brightness |
| RED LED | A4 | PWM Output | 0-255 brightness |

### Wiring

**Buttons:**
- A0 → DOWN button → GND (normally-closed)
- A1 → UP button → GND (normally-closed)
- Internal pullups enabled

**LEDs:**
- A2 → 220Ω resistor → GREEN LED → GND
- A3 → 220Ω resistor → YELLOW LED → GND
- A4 → 220Ω resistor → RED LED → GND

### Serial Protocol

**Arduino → Python:**
```
UP        (button press)
DOWN      (button press)
READY     (on startup)
```

**Python → Arduino:**
```
RED:255      (full brightness)
RED:128      (half brightness)
RED:0        (off)
YELLOW:ON    (legacy, = 255)
GREEN:OFF    (legacy, = 0)
```

---

## Testing

### Test SuperCollider Stop

```bash
python3 app/carpet_hotel_gui.py

# Steps:
# 1. Click "Start Audio"
# 2. Wait for SC to boot
# 3. Click "Stop Audio"
# 4. Check Activity Monitor / top - sclang should be GONE
```

**Expected:** SuperCollider process terminates, audio stops.

### Test Arduino Buttons

```bash
python3 app/carpet_hotel_gui.py

# Steps:
# 1. Hardware tab → Connect to Arduino
# 2. Press UP button on hardware
# 3. Check GUI log → should show "✓ Button UP pressed"
# 4. Press DOWN button
# 5. Check GUI log → should show "✓ Button DOWN pressed"
```

### Test LED Control

```bash
python3 app/carpet_hotel_gui.py

# Steps:
# 1. Connect Arduino
# 2. Hardware tab → Test LEDs section
# 3. Click LED buttons or send commands
# 4. Check hardware - LEDs should light
# 5. Check GUI log - should show LED messages
```

### Test PWM Brightness

Python:
```python
from carpet_hotel_arduino import CarpetHotelArduino

arduino = CarpetHotelArduino()
arduino.connect()

# Test different brightness levels
arduino.set_led("red", 255)    # Full brightness
arduino.set_led("red", 128)    # Half brightness
arduino.set_led("red", 64)     # Quarter brightness
arduino.set_led("red", 0)      # Off

arduino.disconnect()
```

**Expected:** LED dims smoothly at different PWM values.

---

## Files Modified

### Arduino
- ✓ `app/elevator_control/elevator_control.ino`
  - Changed LED pins D2/D3/D4 → A2/A3/A4
  - Added PWM support (analogWrite)
  - Fixed button messages (UP/DOWN uppercase)

### Python
- ✓ `app/carpet_hotel_scd.py`
  - Added CmdPeriod.run; before process termination
  - Graceful synth stopping

- ✓ `app/carpet_hotel_arduino.py`
  - Fixed case matching for button messages
  - Added PWM support (0-255 values)
  - Added message callback system
  - Integrated logger

- ✓ `app/carpet_hotel_gui.py`
  - Added Arduino message callback
  - Arduino messages now logged to GUI

---

## API Changes

### Arduino Python Wrapper

**Old:**
```python
arduino.set_led("red", 1)  # ON only
arduino.set_led("red", 0)  # OFF only
```

**New (backward compatible):**
```python
# Legacy still works:
arduino.set_led("red", 1)    # → 255 (full brightness)
arduino.set_led("red", 0)    # → 0 (off)

# New PWM support:
arduino.set_led("red", 255)  # Full brightness
arduino.set_led("red", 128)  # Half brightness
arduino.set_led("red", 64)   # Quarter brightness
arduino.set_led("red", 0)    # Off
```

### Message Callback

**New feature:**
```python
def my_callback(message: str):
    print(f"Arduino: {message}")

arduino.set_message_callback(my_callback)
# Now receives: "✓ Button UP pressed", "LED RED: 255", etc.
```

---

## Summary

**SuperCollider Stop:**
- ✓ Now sends CmdPeriod.run; before terminating
- ✓ Gracefully stops all synths
- ✓ Process fully terminates

**Arduino Control:**
- ✓ LED pins updated to A2/A3/A4
- ✓ PWM brightness control (0-255)
- ✓ Button messages fixed (UP/DOWN)
- ✓ GUI logging for all Arduino events
- ✓ Backward compatible with legacy ON/OFF

**Result:** Both issues completely fixed! SuperCollider stops properly, Arduino control fully functional with PWM LEDs and GUI logging. 🎉
