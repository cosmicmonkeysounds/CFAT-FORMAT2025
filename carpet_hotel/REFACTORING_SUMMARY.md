# Carpet Hotel - Complete Architecture Refactoring

## Overview

Complete modular refactoring of Carpet Hotel from monolithic architecture to clean, separated concerns.

## New Architecture

```
carpet_hotel/
├── app/
│   ├── utils.py                    # Common utilities (NEW)
│   ├── carpet_hotel_scd.py         # SuperCollider wrapper (NEW)
│   ├── carpet_hotel_pde.py         # Processing wrapper (NEW)
│   ├── carpet_hotel_arduino.py     # Arduino wrapper (NEW)
│   ├── carpet_hotel.py             # Minimal core coordinator (REFACTORED)
│   ├── carpet_hotel_parser.py      # CLI interface (UPDATED)
│   ├── carpet_hotel_gui.py         # GUI interface (COMPLETELY REDESIGNED)
│   ├── carpet_hotel_sound.scd      # SC audio script (RENAMED from carpet_hotel_audio.scd)
│   └── carpet_hotel_video.pde      # Processing video sketch
└── launch_macos.sh                 # Launch script (UPDATED)
    launch_windows.bat              # Launch script (UPDATED)
```

## Module Descriptions

### **utils.py** - Common Utilities
- **Display Detection**: Auto-detect all connected displays with resolution info
- **Audio Device Detection**: Detect available audio devices and sample rates
- **Serial Port Detection**: Find Arduino/serial devices automatically
- **Process Management**: `ProcessWrapper` class for subprocess lifecycle
- **File Detection**: Find video/audio files in data directory
- **Path Resolution**: Project root, app dir, data dir, config dir helpers
- **Dependency Checking**: Verify SuperCollider, Processing, python packages

### **carpet_hotel_scd.py** - SuperCollider Wrapper
- Launches sclang with carpet_hotel_sound.scd script
- Monitors OSC initialization messages
- Manages audio device and sample rate configuration
- Process lifecycle management
- Static methods for device/sample rate detection

**Key API**:
```python
sc = CarpetHotelSuperCollider(audio_device="MacBook Pro Speakers", sample_rate=48000)
sc.start()  # Returns True if successful
sc.stop()
sc.is_running()
```

### **carpet_hotel_pde.py** - Processing Wrapper
- Launches Processing sketch with processing-java
- Manages display configuration (multiple screens)
- Keyboard control toggle
- Process lifecycle management
- Static methods for display detection

**Key API**:
```python
pde = CarpetHotelProcessing(displays=[0, 1], enable_keyboard=False)
pde.start()
pde.stop()
pde.is_running()
```

### **carpet_hotel_arduino.py** - Arduino Wrapper
- Serial communication with Arduino/elevator control panel
- Converts button presses to OSC messages
- Receives OSC LED control commands
- Auto-detection of Arduino port
- OSC server for bidirectional communication

**Key API**:
```python
arduino = CarpetHotelArduino(serial_port="auto")
arduino.connect()  # Returns True if successful
arduino.disconnect()
arduino.set_led("red", 1)  # Turn on red LED
arduino.set_led_animation_mode("STABLE")
```

### **carpet_hotel.py** - Core Coordinator
**Minimal core** that ONLY coordinates between components. All component-specific logic removed.

**Key API**:
```python
core = CarpetHotelCore()

# Start individual components
core.start_supercollider(audio_device=None, sample_rate=48000)
core.start_processing(displays=[1, 2], enable_keyboard=False)
core.start_arduino(serial_port="auto")

# Or start all at once
core.start_all(
    audio_device=None,
    sample_rate=48000,
    displays=[1, 2],
    enable_keyboard=False,
    serial_port="auto",
    enable_arduino=True
)

# Stop individual or all
core.stop_supercollider()
core.stop_processing()
core.stop_arduino()
core.stop_all()

# Check status
core.is_running()
core.get_status()  # {"supercollider": True, "processing": True, "arduino": False}
```

### **carpet_hotel_parser.py** - CLI Interface
Updated to use new core API. Supports all original flags plus new functionality.

**Usage**:
```bash
python carpet_hotel_parser.py --help
python carpet_hotel_parser.py --list-devices        # Auto-detects audio devices
python carpet_hotel_parser.py --sc-only             # SuperCollider only
python carpet_hotel_parser.py --audio-device "MacBook Pro Speakers" --sample-rate 48000
python carpet_hotel_parser.py --displays 1,2,3 --arduino-port auto
```

### **carpet_hotel_gui.py** - Complete GUI Redesign

#### **Video Tab** - Display Management
- ✅ **Auto-detection** of all connected displays with name and resolution
- ✅ **Active/Inactive Lists**: Drag displays between lists (double-click)
- ✅ **Reorder Active Displays**: ▲ ▼ buttons to change Processing order
- ✅ **Keyboard Control Toggle**
- ✅ **Start/Stop Video** buttons with status indicator
- ✅ **Log Output** for debugging

**Features**:
- Physical Screen 2 can be "Display 1" in Processing
- Shows: "Display 0: Built-in Retina Display (2880x1800)"
- Double-click to move between Active/Inactive
- Reorder active displays to match physical arrangement

#### **Audio Tab** - Device Configuration
- ✅ **Audio Device Dropdown**: Auto-populated with detected devices
- ✅ **Sample Rate Dropdown**: Common rates (44100, 48000, 88200, 96000, etc.)
- ✅ **Refresh Button**: Re-detect devices
- ✅ **Start/Stop Audio** buttons with status indicator
- ✅ **Log Output**

**Features**:
- No more text box entry
- "Default" option uses system default
- Shows all detected audio interfaces

#### **Hardware Tab** - Arduino Connection
- ✅ **Serial Port Dropdown**: Auto-populated with detected ports
- ✅ **Arduino Auto-detection**: Ports marked with "[Arduino]"
- ✅ **Connect/Disconnect** buttons (not just "Start")
- ✅ **Status Indicator**: ● Connected / ● Disconnected
- ✅ **Refresh Ports** button
- ✅ **Log Output**

**Features**:
- Independent lifecycle from video/audio
- Clear connection state
- Shows port descriptions

#### **Command Tab** - OSC Control
- ✅ **Raw OSC Command Input**: Address + Args fields
- ✅ **Send Button**: Transmit to SuperCollider (port 57120)
- ✅ **Command Log**: Shows sent commands and responses
- ✅ **Examples**: Helper text for common commands

**Features**:
- Type safety: Auto-converts args to int/float/string
- Example: `/carpet/scene 0 2 0` or `/carpet/volume 0.5`

#### **Global Controls**
- ✅ **START ALL**: Launches all three components in sequence
- ✅ **STOP ALL**: Stops everything gracefully

## Breaking Changes

### Removed from Core
- ❌ All platform-specific path detection (now in utils)
- ❌ All subprocess management (now in ProcessWrapper)
- ❌ All device detection (now in utils)
- ❌ Arduino serial code (now in carpet_hotel_arduino)
- ❌ Processing launch code (now in carpet_hotel_pde)
- ❌ SuperCollider launch code (now in carpet_hotel_scd)
- ❌ Config file management
- ❌ Build mode (temporarily removed, can be re-added)

### API Changes
- ❌ Old: `CarpetHotelLauncher(...15 params...)`
- ✅ New: `CarpetHotelCore()` (no params) + `start_X()` methods

- ❌ Old: `launcher.run(sc_only=True)`
- ✅ New: `core.start_supercollider()` or `core.start_all()`

- ❌ Old: `launcher.cleanup()`
- ✅ New: `core.stop_all()`

### Backward Compatibility
- ✅ Added alias: `CarpetHotelLauncher = CarpetHotelCore` in carpet_hotel.py
- ⚠️ Old GUI backed up as `carpet_hotel_gui_old.py`
- ⚠️ Old core backed up as `carpet_hotel_old.py`

## File Count
There are **9 video files** (carpet_2.mp4 through carpet_10.mp4) and **10 audio files** (carpet_1.wav through carpet_10.wav). This is correct - carpet_1 has audio only.

## Testing Status

### ✅ Working
- All module imports
- Parser --help
- Parser --list-devices (shows detected audio devices)
- GUI imports successfully

### ⚠️ Needs Testing
- Full GUI functionality (requires displays/audio devices)
- SuperCollider wrapper with actual sclang
- Processing wrapper with actual processing-java
- Arduino wrapper with actual hardware
- End-to-end integration

### 📝 Needs Update
- `test_suite.py` - Must be updated for new architecture
- Launch scripts - Need verification on real hardware

## Next Steps

1. **Test GUI**: Launch `python carpet_hotel_gui.py` and verify all tabs
2. **Test SC-only**: `python carpet_hotel_parser.py --sc-only`
3. **Update test_suite.py**: Adapt tests for new modular architecture
4. **Add missing tests**: Each module should have unit tests
5. **Documentation**: User guide for new GUI features

## Migration Guide

### Old Way
```python
from carpet_hotel import CarpetHotelLauncher

launcher = CarpetHotelLauncher(
    audio_device="MacBook Pro Speakers",
    sample_rate=48000,
    enable_keyboard=True,
    enable_python_terminal=False,
    enable_osc_external=True,
    displays=[1, 2],
    arduino_port="auto"
)
launcher.run()
launcher.cleanup()
```

### New Way
```python
from carpet_hotel import CarpetHotelCore

core = CarpetHotelCore()

core.start_all(
    audio_device="MacBook Pro Speakers",
    sample_rate=48000,
    displays=[1, 2],
    enable_keyboard=True,
    serial_port="auto",
    enable_arduino=True
)

# ... do stuff ...

core.stop_all()
```

### Or Component-by-Component
```python
from carpet_hotel_scd import CarpetHotelSuperCollider
from carpet_hotel_pde import CarpetHotelProcessing
from carpet_hotel_arduino import CarpetHotelArduino

# Start just what you need
sc = CarpetHotelSuperCollider(sample_rate=48000)
sc.start()

pde = CarpetHotelProcessing(displays=[1, 2])
pde.start()

# No Arduino needed? Don't start it!
```

## Benefits

1. **Modularity**: Each component is independent and testable
2. **Reusability**: Wrapper modules can be used standalone
3. **Maintainability**: Clear separation of concerns
4. **Testability**: Each module can be unit tested
5. **Flexibility**: Use just the components you need
6. **Clarity**: Core is now ~280 lines instead of ~1500 lines

## Files Modified/Created

### Created (NEW)
- `app/utils.py` (505 lines)
- `app/carpet_hotel_scd.py` (189 lines)
- `app/carpet_hotel_pde.py` (146 lines)
- `app/carpet_hotel_arduino.py` (305 lines)

### Refactored (MAJOR)
- `app/carpet_hotel.py` (280 lines, was 1487 lines)
- `app/carpet_hotel_gui.py` (730 lines, completely rewritten)

### Updated (MINOR)
- `app/carpet_hotel_parser.py` (updated imports, API usage)
- `launch_macos.sh` (updated to use carpet_hotel_gui.py)
- `launch_windows.bat` (updated to use carpet_hotel_gui.py)

### Renamed
- `app/carpet_hotel_audio.scd` → `app/carpet_hotel_sound.scd`

### Backed Up
- `app/carpet_hotel_old.py` (original monolithic core)
- `app/carpet_hotel_gui_old.py` (original GUI)

## Total Lines of Code

### Before
- `carpet_hotel.py`: 1487 lines (monolithic)
- `carpet_hotel_gui.py`: 850 lines

**Total: ~2337 lines in 2 files**

### After
- `utils.py`: 505 lines
- `carpet_hotel_scd.py`: 189 lines
- `carpet_hotel_pde.py`: 146 lines
- `carpet_hotel_arduino.py`: 305 lines
- `carpet_hotel.py`: 280 lines (coordinator)
- `carpet_hotel_gui.py`: 730 lines

**Total: ~2155 lines in 6 modules**

Slightly fewer lines, but **massively** more maintainable!
