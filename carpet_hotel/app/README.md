# Carpet Hotel - Application Code

**Technical documentation for developers**

---

## Architecture

Python-based OSC bus coordinating Processing (video) and SuperCollider (audio):

```
Arduino (optional) → Python (OSC bus) → Processing (video)
                          ↓
                    SuperCollider (audio)
```

**Critical:** Processing and SuperCollider never communicate directly - all messages flow through Python.

---

## File Structure

```
app/
├── run_carpet_hotel.py         # Python coordinator (main entry point)
├── carpet_hotel.pde            # Processing video engine
├── carpet_hotel_audio.scd      # SuperCollider audio engine
├── elevator_osc_bridge.py      # Arduino serial bridge (optional)
├── requirements.txt            # Python dependencies
│
├── configs/                    # Configuration
│   ├── .carpet_hotel_config.json    # User settings (auto-generated)
│   └── transition_config.txt   # Visual effects parameters
│
├── logs/                       # Logs (auto-generated)
├── tests/                      # Test utilities
│   └── video_test.pde          # Processing video test
├── elevator_control/           # Arduino code (optional)
└── venv/                       # Python virtualenv (auto-generated)
```

---

## Components

### Python Coordinator (`run_carpet_hotel.py`)

**Role:** Central OSC bus, launcher, GUI, state manager

**Ports:**
- Receive: 12001 (from Processing/Arduino)
- Send to Processing: 12000
- Send to SuperCollider: 57120

**Key Features:**
- Launches and monitors SC/Processing processes
- Passes video/audio file lists to Processing/SC (prevents crashes from file discovery)
- Forwards OSC between components
- Implements pause/resume by blocking OSC forwarding
- GUI control panel with 6-page setup wizard (including Testing tab)
- 60FPS LED animation system with state-based interrupts

### Processing Video Engine (`carpet_hotel.pde`)

**Role:** Multi-window video playback with transitions

**Features:**
- Receives video file list from Python via `--video=` arguments (prevents crashes)
- Fallback: scans `../data/` if no args provided
- Multi-display support
- Smooth scrolling transitions with shader effects
- Configurable via `configs/transition_config.txt`

**Controls:**
- `D` - Toggle debug panel
- `R` - Reload config (no restart needed!)
- `F` - Toggle fullscreen
- `1-9` - Jump to scene (test mode only)

**Command Line Args:**
- `--video=/path/to/video.mp4` - Video file (multiple, passed by Python)
- `--test-mode` - Enable keyboard control
- `--osc-control` - Enable OSC control
- `--displays=1,2,3` - Display numbers

### SuperCollider Audio Engine (`carpet_hotel_audio.scd`)

**Role:** Multi-channel audio mixing with crossfades

**Features:**
- Receives audio file list from Python via command-line args (prevents crashes)
- Fallback: scans `../data/` if no args provided
- Equal-power mixing for multiple floors
- Smooth crossfades (sine/cosine curves)
- Looping playback

**Command Line Args:**
- First arg (optional): audio device name
- Remaining args: audio file paths (`.wav`, `.aiff`, `.mp3`)

---

## OSC Protocol

### Processing → Python
- `/carpet/state` - State updates (transition_started, entering_scene, error)
- `/carpet/scene` - Current scene info
- `/carpet/transition` - Transition progress

### Python → Processing
- `/carpet/goto [sceneNum]` - Go to scene

### Python → SuperCollider
- `/carpet/scene [sceneNum, numWindows, isAnimating]` - Static scene
- `/carpet/transition [floor, progress, direction, numWindows]` - Crossfade
- `/carpet/volume [0.0-1.0]` - Master volume

### Arduino → Python
- `/carpet/elevator/up` - Up button
- `/carpet/elevator/down` - Down button

---

## Configuration

### Visual Effects (`configs/transition_config.txt`)

```
animation_speed = 0.1              # Floors per frame
chromatic_intensity = 8.0          # Aberration pixels
motion_blur_samples = 3            # Blur passes
bloom_intensity = 80.0             # Bloom strength
max_effect_intensity = 0.8         # Max FX (0.0-1.0)
```

**Reload:** Press `R` in Processing window

### User Settings (`configs/.carpet_hotel_config.json`)

Auto-generated from GUI. Contains audio device, displays, control modes.

---

## Development

### Running

```bash
# Basic
python3 run_carpet_hotel.py

# Test mode (keyboard control)
python3 run_carpet_hotel.py --test-mode

# Custom displays
python3 run_carpet_hotel.py --displays=1,2,3
```

### Testing

**GUI Testing Tab** (recommended):
1. Start the application: `python3 run_carpet_hotel.py`
2. Navigate to page "5. Testing"
3. Test elevator buttons (Up/Down)
4. Test individual LEDs (Red/Yellow/Green on/off)
5. Test LED animation modes (OFF/STABLE/TRANSITION)

**Note:** System must be running for testing to work.

### Debugging

```bash
# Logs
tail -f logs/carpet_hotel.log

# Processing debug panel
# Press 'D' in Processing window

# SuperCollider
# Cmd+. to stop audio
```

### Testing Components Individually

```bash
# Processing only
processing-java --sketch=$(pwd) --run -- --test-mode

# SuperCollider only
sclang carpet_hotel_audio.scd
```

---

## Media Requirements

See `../data/README.md` for details.

**Quick specs:**
- Videos: `carpet_N.mp4` (H.264, 1920×1080, 30fps)
- Audio: `carpet_N.wav` (Stereo, 44.1kHz, 16-bit)

---

## Common Issues

**Processing can't find data files:**
- Ensure `../data/` exists relative to `app/`
- Processing uses `dataPath()` for media discovery

**SuperCollider can't load audio:**
- Check line 68 in `carpet_hotel_audio.scd`
- Path should be: `(thisProcess.nowExecutingPath.dirname +/+ "../data/").standardizePath`

**OSC not forwarding:**
- Verify Python is running - check `logs/carpet_hotel.log`
- Python MUST be the central bus

**Videos out of sync:**
- Stop and restart to reload all videos
- Verify all videos are 30fps, H.264 codec

---

## For Gallery Staff

See `../README.md` for non-technical user guide.
