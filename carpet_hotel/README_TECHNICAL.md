# CARPET HOTEL - Technical Documentation
## For Technical Artists & Developers

**Multi-window synchronized video installation with OSC-coordinated audio.**

Python orchestrates Processing (visuals) and SuperCollider (audio) as central OSC bus.

---

## 📚 Table of Contents

1. [System Architecture](#system-architecture)
2. [Quick CLI Usage](#quick-cli-usage)
3. [Running Components Separately](#running-components-separately)
4. [Command-Line Options](#command-line-options)
5. [OSC Protocol Specification](#osc-protocol-specification)
6. [Development Workflow](#development-workflow)
7. [Building & Deployment](#building--deployment)
8. [Advanced Configuration](#advanced-configuration)
9. [Troubleshooting (Technical)](#troubleshooting-technical)

---

## System Architecture

### OSC Message Flow

```
┌──────────────┐
│   Arduino    │ (optional external controller)
│  Elevator    │
│  Controller  │
└──────┬───────┘
       │ OSC Port 12001 (to Python)
       ↓
┌─────────────────────────────────────────────┐
│     Python (run_carpet_hotel.py)            │
│  ═══════════════════════════════════════════ │
│  Central OSC Bus & System Coordinator       │
│  ─────────────────────────────────────────  │
│  Responsibilities:                          │
│  • Launch & monitor SuperCollider/Processing│
│  • Forward OSC between all components       │
│  • Implement pause/resume state             │
│  • Provide GUI control panel                │
│  • Handle graceful shutdown                 │
│  ─────────────────────────────────────────  │
│  Ports:                                     │
│  • Receive: 12001 (from Processing/Arduino) │
│  • Send to Processing: 12000                │
│  • Send to SuperCollider: 57120             │
└────┬────────────────────────┬───────────────┘
     │                        │
     │ Port 12000            │ Port 57120
     │ (Python→Proc)         │ (Python→SC)
     ↓                        ↓
┌──────────────┐        ┌──────────────┐
│  Processing  │        │SuperCollider │
│              │        │              │
│ Port 12001 ← │        │ Port 57120 ← │
│ Port 12000 ↓ │        │              │
│              │        │              │
│ Video Engine │        │ Audio Engine │
│ Multi-window │        │ Equal-power  │
│ Transitions  │        │ Mixing       │
│ Shaders      │        │ Crossfades   │
└──────────────┘        └──────────────┘
```

**Critical Architecture Principle:**
- Python is the **ONLY** OSC bus
- Processing and SuperCollider **NEVER** communicate directly
- All state flows through Python
- Python implements pause/resume by blocking OSC forwarding

---

### Component Responsibilities

| Component | Language | Role | Dependencies |
|-----------|----------|------|--------------|
| **run_carpet_hotel.py** | Python 3 | OSC bus, launcher, GUI | python-osc, screeninfo, tkinter |
| **carpet_hotel.pde** | Processing | Video playback, visual transitions | Video library, oscP5 |
| **carpet_hotel_audio.scd** | SuperCollider | Audio mixing, crossfades | Built-in OSC |
| **Arduino Controller** | C++ (optional) | Physical interface | OSC library |

---

### File Structure

```
carpet_hotel/
├── run_carpet_hotel.py           # Python coordinator (central OSC bus)
├── carpet_hotel.pde              # Processing video sketch
├── carpet_hotel_audio.scd        # SuperCollider audio engine
├── transition_config.txt         # Transition effects config
├── requirements.txt              # Python dependencies
│
├── data/                         # Media files
│   ├── carpet_1.mp4 ... 10.mp4 # Videos (H.264 MP4, 1920×1080)
│   └── carpet_1.wav ... 10.wav # Audio (Stereo WAV, 44.1kHz)
│
├── launch_macos.sh               # Auto-installer & launcher (macOS)
├── launch_windows.bat            # Auto-installer & launcher (Windows)
│
├── .carpet_hotel_config.json    # Saved settings (auto-generated)
├── carpet_hotel.log              # Runtime log (auto-generated)
└── venv/                         # Python virtual environment (auto-generated)
```

---

## Quick CLI Usage

### GUI Mode (Recommended)
```bash
python run_carpet_hotel.py
```
Opens control panel with saved settings. Best for most users.

### CLI Mode with Options
```bash
# Specify audio device
python run_carpet_hotel.py --audio-device "MacBook Pro Speakers"

# Enable keyboard control
python run_carpet_hotel.py --test-mode

# Enable OSC control (Python terminal + external OSC)
python run_carpet_hotel.py --osc-control

# Custom display configuration
python run_carpet_hotel.py --displays=1,2,3

# Combine multiple options
python run_carpet_hotel.py \
  --audio-device "Built-in Output" \
  --test-mode \
  --osc-control \
  --displays=2,1
```

### Test Audio Only
```bash
python run_carpet_hotel.py --sc-only
```
Launches SuperCollider audio engine only for testing.

### Build Processing Executable
```bash
python run_carpet_hotel.py --build
```
Creates standalone Processing app (still needs SC + Python).

---

## Running Components Separately

### 1. SuperCollider Audio Engine

**Command-line launch:**
```bash
# macOS
/Applications/SuperCollider.app/Contents/MacOS/sclang carpet_hotel_audio.scd

# macOS with custom audio device
/Applications/SuperCollider.app/Contents/MacOS/sclang carpet_hotel_audio.scd "MacBook Pro Speakers"

# Windows
"C:\Program Files\SuperCollider\sclang.exe" carpet_hotel_audio.scd

# Linux
sclang carpet_hotel_audio.scd
```

**What it does:**
- Loads 10 audio files (`carpet_1.wav` ... `carpet_10.wav`)
- Creates looping players for each (start silent)
- Listens for OSC on port 57120
- Implements equal-power audio mixing
- Handles smooth crossfades during transitions

**OSC Interface:**
- Receives: `/carpet/scene`, `/carpet/transition`, `/carpet/volume`
- No output OSC (one-way)

**Stop:** Press `Cmd+.` (macOS) or `Ctrl+.` (Windows/Linux)

---

### 2. Processing Visual Engine

**Command-line launch:**
```bash
# Basic run
processing-java --sketch=. --run

# With keyboard control
processing-java --sketch=. --run --test-mode

# With OSC control
processing-java --sketch=. --run --osc-control

# With display configuration
processing-java --sketch=. --run --displays=1,2,3

# All options combined
processing-java --sketch=. --run --test-mode --osc-control --displays=2,1
```

**What it does:**
- Loads 10 video files (`carpet_1.mp4` ... `carpet_10.mp4`)
- Creates N windows (one per display)
- Global timer system for seamless loops
- Smooth shader-based transitions
- Sends OSC state updates to Python

**OSC Interface:**
- Sends to Python: port 12001 (state updates, audio commands)
- Receives from Python: port 12000 (scene commands)

**Keyboard controls (if `--test-mode` enabled):**
- `1-9` - Jump to scenes
- `UP/DOWN` - Next/previous scene
- Mouse wheel - Volume
- `D` - Debug overlay
- `F` - Fullscreen
- `ESC` - Quit

**Stop:** Press `ESC` or close windows

---

### 3. Python Coordinator

**CLI mode:**
```bash
# For development/testing with terminal control
python run_carpet_hotel.py --test-mode --osc-control
```

**GUI mode:**
```bash
# For production/exhibition with control panel
python run_carpet_hotel.py
```

**What it does:**
- Launches SuperCollider with retry logic
- Launches Processing with configured options
- Forwards OSC messages between components
- Implements pause/resume state (blocks forwarding when paused)
- Provides GUI control panel
- Saves/loads settings from `.carpet_hotel_config.json`
- Handles graceful shutdown (kills SC/Processing on exit)

**Stop:** Press `Ctrl+C` (CLI) or click Stop/Quit (GUI)

---

## Command-Line Options

### `--audio-device <name>`
Specify SuperCollider audio output device.

```bash
python run_carpet_hotel.py --audio-device "MacBook Pro Speakers"
```

**Common device names:**
- `"MacBook Pro Speakers"`
- `"Built-in Output"`
- `"Multi-Output Device"` (for aggregate devices)
- `"Soundflower"` / `"BlackHole"` (virtual audio routing)

**How to find device names:**
In SuperCollider IDE:
```supercollider
ServerOptions.devices
```

---

### `--test-mode`
Enable keyboard control in Processing windows.

```bash
python run_carpet_hotel.py --test-mode
```

**Enables:**
- Keyboard shortcuts (1-9, arrows)
- Immediate scene switching
- Good for testing, rehearsal

---

### `--osc-control`
Enable OSC control (Python terminal + external OSC).

```bash
python run_carpet_hotel.py --osc-control
```

**Enables:**
- Python terminal interface (type scene numbers)
- External OSC reception (Arduino, TouchOSC, etc.)
- Port 12001 listening

---

### `--displays=<numbers>`
Specify which displays to use (comma-separated, in order).

```bash
python run_carpet_hotel.py --displays=1,2      # Two displays
python run_carpet_hotel.py --displays=2,1      # Reverse order
python run_carpet_hotel.py --displays=1,2,3,4  # Four displays
```

**Order matters:**
- First number = primary floor
- Second number = adjacent floor
- Etc.

**How display numbers work:**
- Detected by `screeninfo` library
- Uses actual monitor names (e.g., "Samsung Odyssey G9")
- Coordinates from OS display settings

---

### `--sc-only`
Run SuperCollider audio engine only (no Processing).

```bash
python run_carpet_hotel.py --sc-only
```

**Use cases:**
- Testing audio setup
- Debugging audio device issues
- Developing audio engine

---

### `--build`
Build Processing executable.

```bash
python run_carpet_hotel.py --build
```

**Output:**
- macOS: `build/carpet_hotel.app`
- Windows: `build/carpet_hotel.exe`
- Linux: `build/carpet_hotel`

**Important notes:**
- Executable includes Processing sketch only
- Still needs SuperCollider running separately
- Still needs Python for OSC routing
- Use Python launcher for full system

---

## OSC Protocol Specification

### Python → Processing

**Port:** 12000

| Address | Type Args | Description | Example |
|---------|-----------|-------------|---------|
| `/carpet/goto` | `[int]` | Jump to scene | `/carpet/goto 3` |
| `/carpet/pause` | `[int]` | Pause (1) or resume (0) | `/carpet/pause 1` |

---

### Processing → Python

**Port:** 12001

| Address | Type Args | Description | Forwarded to SC? |
|---------|-----------|-------------|------------------|
| `/carpet/state` | `[string, ...]` | State update | No |
| `/carpet/scene` | `[int, int, int]` | Current scene info | **Yes** |
| `/carpet/transition` | `[int, float, int, int]` | Transition state | **Yes** |
| `/carpet/volume` | `[float]` | Volume change | **Yes** |

**State strings:**
- `"entering_scene"` - Just entered static scene
- `"entering_transition"` - Starting transition
- `"transition_started"` - Transition animation began
- `"error"` - Error occurred

---

### Python → SuperCollider

**Port:** 57120

| Address | Type Args | Description | Notes |
|---------|-----------|-------------|-------|
| `/carpet/scene` | `[int, int, int]` | Static scene | `[sceneNum, numWindows, isAnimating]` |
| `/carpet/transition` | `[int, float, int, int]` | Crossfade | `[currentFloor, progress, direction, numWindows]` |
| `/carpet/volume` | `[float]` | Master volume | `0.0` to `1.0` |

**Audio mixing details:**
- Equal-power mixing: `volumePerFloor = masterVolume / sqrt(numAudibleFloors)`
- Crossfade curves: sine (fade in), cosine (fade out)
- All audio loops independently via `PlayBuf`

---

### External Controller → Python

**Port:** 12001 (same as Processing)

Send any Processing → Python message from external controller.

**Example (Arduino):**
```cpp
OSCMessage msg("/carpet/goto");
msg.add(5);  // Go to scene 5
Udp.beginPacket(pythonIP, 12001);
msg.send(Udp);
Udp.endPacket();
```

---

## Development Workflow

### 1. Test Audio Alone
```bash
# Terminal 1: Launch SuperCollider only
python run_carpet_hotel.py --sc-only

# Terminal 2: Send test OSC
python3
>>> from pythonosc import udp_client
>>> sc = udp_client.SimpleUDPClient("127.0.0.1", 57120)
>>> sc.send_message("/carpet/scene", [0, 2, 0])  # Scene 0, 2 windows
>>> sc.send_message("/carpet/volume", [0.5])     # 50% volume
>>> sc.send_message("/carpet/transition", [0, 0.5, 1, 2])  # Crossfade
```

---

### 2. Test Visuals Alone
```bash
# Run Processing with keyboard control
processing-java --sketch=. --run --test-mode

# Use keyboard:
# - 1-9 keys to test scenes
# - UP/DOWN for transitions
# - Mouse wheel for volume
# - D for debug overlay
```

---

### 3. Test Python OSC Bus
```bash
# Terminal 1: Run Python with OSC
python run_carpet_hotel.py --osc-control --displays=1,2

# Terminal 2: Watch logs
tail -f carpet_hotel.log

# In Terminal 1: Type scene numbers
Scene > 3
Scene > 5

# Verify OSC forwarding in log
```

---

### 4. Full System Integration Test
```bash
# CLI mode with all options
python run_carpet_hotel.py --test-mode --osc-control --displays=1,2

# Or GUI mode (recommended)
python run_carpet_hotel.py
```

---

### 5. Debug OSC Messages
Add print statements in Python:

```python
def forward_to_sc(self, address, *args):
    """Forward OSC messages to SuperCollider."""
    print(f"[DEBUG] Forwarding {address} {args} to SC")  # Add this
    if self.sc_osc_client and not self.is_paused:
        self.sc_osc_client.send_message(address, args)
```

Watch SuperCollider console for `[OSC-RECV]` messages.

---

## Building & Deployment

### Build Processing Executable

**Using Python script:**
```bash
python run_carpet_hotel.py --build
```

**Manual build:**
```bash
processing-java \
  --sketch=. \
  --output=build \
  --export \
  --platform=macosx \  # or 'windows', 'linux'
  --force
```

**Result:**
- macOS: `build/carpet_hotel.app`
- Windows: `build/carpet_hotel.exe`

---

### Deployment Package

For gallery installation, package:

```
carpet_hotel_install/
├── launch_macos.sh or launch_windows.bat
├── run_carpet_hotel.py
├── carpet_hotel.pde
├── carpet_hotel_audio.scd
├── requirements.txt
├── data/
│   ├── carpet_1.mp4 ... 10.mp4
│   └── carpet_1.wav ... 10.wav
└── README.md  (gallery guide)
```

**Installation steps:**
1. Copy entire folder to exhibition computer
2. Double-click launch script
3. Follow GUI setup
4. Done!

---

## Advanced Configuration

### Environment Variables

```bash
# SuperCollider path (if not in standard location)
export SCLANG_PATH="/custom/path/to/sclang"

# Processing command-line tool
export PROCESSING_JAVA="/custom/path/to/processing-java"

# Then run
python run_carpet_hotel.py
```

---

### Custom OSC Ports

**Edit run_carpet_hotel.py:**
```python
self.processing_send_port = 12000  # Python → Processing
self.processing_recv_port = 12001  # Processing → Python
self.sc_send_port = 57120          # Python → SuperCollider
```

**Edit carpet_hotel.pde:**
```java
int SC_PORT = 57120;
int PYTHON_SEND_PORT = 12001;
int PYTHON_RECV_PORT = 12000;
```

**Firewall rules:**
Allow UDP ports 12000, 12001, 57120 for localhost.

---

### Python Virtual Environment (Recommended)

```bash
# Create isolated environment
python3 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python run_carpet_hotel.py

# Deactivate when done
deactivate
```

**Benefits:**
- Isolated from system Python
- Reproducible dependencies
- No conflicts with other projects

---

### Modify Transition Effects

Edit `transition_config.txt`:
```
transitionDuration=3.0     # Seconds
easingType=SMOOTH_STEP     # or LINEAR, EASE_IN_OUT
shaderEffect=CROSSFADE     # or WIPE, PIXELATE
```

See [SHADER_GUIDE.md](SHADER_GUIDE.md) for custom shaders.

---

## Troubleshooting (Technical)

### SuperCollider Won't Boot

**Symptom:**
```
ERROR: Server 'localhost' exited with exit code 1
ERROR: could not initialize audio.
```

**Diagnosis:**
```bash
# Check audio device availability
sclang
ServerOptions.devices  # List all devices
s.options.device = "MacBook Pro Speakers";
s.boot;
```

**Fixes:**
1. **Wrong audio device:**
   - Try different device in GUI
   - Or: `python run_carpet_hotel.py --audio-device "Built-in Output"`

2. **Device in use by another app:**
   - Quit other audio apps (DAWs, browsers with audio)
   - Check Activity Monitor / Task Manager

3. **Sample rate mismatch:**
   - Set device to 44100 Hz in Audio MIDI Setup (macOS)
   - Edit `carpet_hotel_audio.scd`: `s.options.sampleRate = 48000;`

4. **Permissions (macOS):**
   - System Settings → Privacy & Security → Microphone
   - Allow Terminal / Python

**Advanced debugging:**
```bash
# Run SC with verbose output
sclang -l sclang.log carpet_hotel_audio.scd
cat sclang.log
```

---

### Processing Windows on Wrong Displays

**Symptom:**
- Both windows on same display
- Windows on laptop instead of external monitors

**Diagnosis:**
```python
# Check screen detection
python3
>>> from screeninfo import get_monitors
>>> for m in get_monitors():
...     print(f"{m.name}: {m.x}, {m.y}, {m.width}x{m.height}")
```

**Fixes:**
1. **Screen detection failed:**
   - Install screeninfo: `pip install screeninfo`
   - Check display is connected and powered on
   - Restart with display connected

2. **Wrong display order:**
   - Use GUI display selector (hover to preview)
   - Or: `python run_carpet_hotel.py --displays=2,1` (swap order)

3. **Processing ignoring display config:**
   - Check Processing sketch is receiving `--displays` arg
   - Add debug: `println(DISPLAY_NUMBERS);` in `setup()`

4. **macOS Spaces interfering:**
   - System Settings → Mission Control
   - Uncheck "Displays have separate Spaces"
   - Logout and login

---

### OSC Messages Not Forwarding

**Symptom:**
- Processing sends OSC but SC doesn't respond
- Python receives but doesn't forward

**Diagnosis:**
```python
# Add debug prints in run_carpet_hotel.py

def forward_to_sc(self, address, *args):
    print(f"[DEBUG-FWD] {address} {args} paused={self.is_paused}")
    if self.sc_osc_client and not self.is_paused:
        self.sc_osc_client.send_message(address, args)
        print(f"[DEBUG-SENT] → SC")
```

**Fixes:**
1. **Python not receiving:**
   - Check Processing is sending to port 12001
   - Check firewall allows localhost UDP
   - Verify OSC control is enabled

2. **Python not forwarding:**
   - Check `self.sc_osc_client` is initialized
   - Check `self.is_paused == False`
   - Verify SC port 57120 is correct

3. **SC not receiving:**
   - Check SC is running and listening
   - In SC console: should see `[OSC-RECV]` messages
   - Try manual OSC test (see Development Workflow)

4. **Pause state stuck:**
   - Click Resume in GUI
   - Or restart Python coordinator

---

### Python Dependencies Missing

**Symptom:**
```
ModuleNotFoundError: No module named 'pythonosc'
```

**Fix:**
```bash
pip install python-osc screeninfo

# Or install from requirements.txt
pip install -r requirements.txt

# If pip not found:
python3 -m pip install python-osc screeninfo
```

**Virtual environment issue:**
```bash
# Make sure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows

# Then install
pip install -r requirements.txt
```

---

### Processing Won't Launch

**Symptom:**
```
processing-java: command not found
```

**Fix:**
```bash
# macOS: Add to PATH
export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"

# Make permanent (add to ~/.zshrc or ~/.bash_profile)
echo 'export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
which processing-java
processing-java --help
```

**Windows:**
```cmd
REM Add Processing to PATH
set PATH=%PATH%;C:\Program Files\Processing

REM Or use full path
"C:\Program Files\Processing\processing-java.exe" --sketch=. --run
```

---

### Video Files Not Loading

**Symptom:**
```
[PROC] WARNING: Video carpet_3.mp4 failed to load
[PROC] No carpet videos found!
```

**Diagnosis:**
```bash
# Check files exist
ls -l data/carpet_*.mp4

# Check file format
ffprobe data/carpet_1.mp4
```

**Fixes:**
1. **Files missing:**
   - Ensure `data/` folder exists
   - Copy videos: `carpet_1.mp4`, `carpet_2.mp4`, etc.
   - Naming must match exactly (underscore, not dash)

2. **Wrong format:**
   - Convert to H.264 MP4:
   ```bash
   ffmpeg -i input.mov -c:v libx264 -preset slow -crf 18 -c:a aac -b:a 192k carpet_1.mp4
   ```

3. **Codec unsupported:**
   - Processing uses GStreamer
   - H.264 in MP4 container is most reliable
   - Avoid HEVC/H.265, ProRes, etc.

4. **File permissions:**
   ```bash
   chmod 644 data/carpet_*.mp4
   ```

---

### Built Executable Won't Run

**Symptom:**
- App crashes on launch
- "Library not found" errors

**Fixes:**
1. **oscP5 not included:**
   - Install oscP5 in Processing IDE first
   - Then rebuild: `python run_carpet_hotel.py --build`

2. **Data folder not found:**
   - Ensure `data/` folder is in same directory as `.app`
   - Or inside `.app/Contents/Java/` (macOS)

3. **Java version mismatch:**
   - Processing 4 requires Java 17+
   - Check: `java -version`

4. **Run from source instead:**
   ```bash
   processing-java --sketch=. --run
   ```

---

### Memory / Performance Issues

**Symptom:**
- Stuttering video playback
- High CPU usage
- Crashes after running a while

**Fixes:**
1. **Reduce video resolution:**
   - Use 1920×1080 instead of 4K
   - Lower bitrate: `ffmpeg ... -crf 23 ...` (higher = smaller)

2. **Fewer displays:**
   - Start with 2 displays
   - Add more incrementally

3. **Increase Java heap:**
   Edit Processing sketch:
   ```java
   // In settings()
   // Not available in PDE mode - must build manually
   ```

4. **Check GPU acceleration:**
   - Processing uses OpenGL via P3D renderer
   - Update graphics drivers
   - macOS: Check Metal support

5. **SuperCollider memory:**
   Edit `carpet_hotel_audio.scd`:
   ```supercollider
   s.options.memSize = 131072;  // Double default
   ```

---

### Logs & Debugging

**Log file location:**
```
carpet_hotel.log  # In project directory
```

**Enable verbose logging:**

**Python (run_carpet_hotel.py):**
```python
# Add at top
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Processing (carpet_hotel.pde):**
```java
// Already prints to console
// Check terminal output or Processing console
```

**SuperCollider (carpet_hotel_audio.scd):**
```supercollider
// Add debug posts
("Debug: " ++ var.asString).postln;
```

**Monitor all OSC:**
```bash
# Use osculator or Protokol to watch OSC traffic
# Or in Python:
python -m pythonosc.tools.dump_osc 12001
```

---

## See Also

- **[README.md](README.md)** - Gallery staff guide
- **[AUDIO_SETUP.md](AUDIO_SETUP.md)** - Audio engine internals
- **[SHADER_GUIDE.md](SHADER_GUIDE.md)** - Custom transition shaders
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Additional troubleshooting

---

## Quick Reference

```bash
# GUI mode (recommended)
python run_carpet_hotel.py

# CLI with options
python run_carpet_hotel.py --audio-device "MacBook Pro Speakers" --test-mode --displays=1,2

# Test components separately
python run_carpet_hotel.py --sc-only
processing-java --sketch=. --run --test-mode
sclang carpet_hotel_audio.scd

# Build executable
python run_carpet_hotel.py --build

# Send test OSC
python3 -c "from pythonosc import udp_client; c = udp_client.SimpleUDPClient('127.0.0.1', 57120); c.send_message('/carpet/volume', [0.5])"

# Check dependencies
pip list | grep osc
processing-java --help
sclang --version
```

---

**Architecture principle:** Python is the brain. All OSC flows through Python. Processing and SuperCollider are render engines that receive commands and send state.
