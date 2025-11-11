# OSC Architecture - Core as Brain

## Overview

The Carpet Hotel system uses a centralized architecture where **`carpet_hotel.py` (the Core) acts as the brain** that manages all communication and state.

## Architecture Diagram

```
                    ┌─────────────────────┐
                    │  carpet_hotel.py    │
                    │     (CORE/BRAIN)    │
                    │                     │
                    │  Manages:           │
                    │  - Global state     │
                    │  - OSC routing      │
                    │  - Coordination     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
     ┌────────────────┐ ┌──────────────┐ ┌──────────────┐
     │   Processing   │ │ SuperCollider│ │   Arduino    │
     │    (Video)     │ │   (Audio)    │ │  (Hardware)  │
     └────────────────┘ └──────────────┘ └──────────────┘
```

## Communication Flow

### Processing ←→ Core

**Processing sends to Core (port 12001):**
- `/carpet/scene [scene, numWindows, isAnimating]` - Scene changes
- `/carpet/transition [floor, progress, direction, numWindows]` - Transitions
- `/carpet/volume [volume]` - Volume changes (from mouse wheel)
- `/carpet/state [state, ...]` - State updates

**Core → Processing:**
- `/carpet/goto [scene]` - Scene change commands (from GUI/Arduino)

### Core ←→ SuperCollider

**Core sends to SuperCollider (port 57120):**
- `/carpet/scene [scene, numWindows, isAnimating]` - Forwarded from Processing
- `/carpet/transition [floor, progress, direction, numWindows]` - Forwarded from Processing
- `/carpet/volume [volume]` - Forwarded from Processing

**SuperCollider:**
- Only receives - does not send back to Core
- Processes all audio based on OSC commands

## Global State Management

The Core maintains all global state:

```python
class CarpetHotelCore:
    # Global state (brain manages all state)
    current_scene: int = 0        # Current scene number
    master_volume: float = 0.7    # Master volume (0.0 - 1.0)
    num_displays: int = 2         # Number of displays/windows
    is_animating: bool = False    # Whether transitioning
```

### State Flow

1. **Processing changes scene**:
   - User presses key or Arduino button
   - Processing starts animation
   - Processing sends `/carpet/scene` to Core
   - Core updates `current_scene`
   - Core forwards to SuperCollider
   - Audio changes to match scene

2. **User adjusts volume**:
   - User scrolls mouse wheel in Processing
   - Processing sends `/carpet/volume` to Core
   - Core updates `master_volume`
   - Core forwards to SuperCollider
   - Audio volume changes

3. **GUI/Arduino controls**:
   - GUI or Arduino sends command to Core
   - Core updates state
   - Core sends `/carpet/goto` to Processing
   - Processing animates scene change
   - Processing sends back `/carpet/scene` to confirm
   - Core forwards to SuperCollider

## Initialization Sequence

1. **User starts SuperCollider** (GUI or code):
   ```python
   core.start_supercollider()
   # SuperCollider boots, loads audio files
   # Sets sc_running = True
   ```

2. **User starts Processing** (GUI or code):
   ```python
   core.start_processing(displays=[1, 2])
   # Processing launches
   # Core automatically sets up OSC (if not already done)
   # Sets pde_running = True
   ```

3. **Core detects both running**:
   ```python
   if sc_running and pde_running:
       # Wait 2 seconds for Processing OSC to init
       time.sleep(2)

       # Send initial scene to start audio
       send_initial_scene()
       # Sends /carpet/scene 0 2 0 to SC
       # Sends /carpet/volume 0.7 to SC

       # Audio starts playing!
   ```

## Why This Architecture?

### Advantages

1. **Single Source of Truth**: Core manages all state
2. **Decoupled Components**: Processing/SC don't know about each other
3. **Easy Testing**: Can test Core → SC without Processing
4. **Flexible Control**: GUI, Arduino, keyboard all go through Core
5. **State Synchronization**: Core always knows current state
6. **Simple Debugging**: All communication logged in Core

### Components are Dumb

- **Processing**: Just displays video, sends what it's doing
- **SuperCollider**: Just plays audio, does what it's told
- **Arduino**: Just sends button presses
- **Core**: Smart - manages, coordinates, decides

## OSC Ports

| Component | Role | Port | Direction |
|-----------|------|------|-----------|
| Processing | Send | 12001 | → Core |
| Core | Receive | 12001 | ← Processing |
| Core | Send | 57120 | → SuperCollider |
| SuperCollider | Receive | 57120 | ← Core |

Note: Processing also receives on port 12000 for commands from Core.

## Code Example

### Starting with Audio

```python
from carpet_hotel import CarpetHotelCore

core = CarpetHotelCore()

# Start audio
core.start_supercollider()

# Start video
core.start_processing(displays=[1, 2], enable_keyboard=True)

# Core automatically:
# - Sets up OSC routing
# - Sends initial scene to SC
# - Audio starts playing!

# Wait
input("Press Enter to stop...")

# Stop
core.stop_all()
```

### Volume Control Flow

```python
# User scrolls mouse wheel in Processing window

# Processing (app.pde):
void mouseWheel(MouseEvent event) {
    float delta = event.getCount() * -0.05;
    masterVolume = constrain(masterVolume + delta, 0.0, 1.0);
    sendVolumeOSC();  # Sends to Core on port 12001
}

# Core (carpet_hotel.py):
def _handle_volume(self, address, *args):
    volume = float(args[0])
    self.master_volume = volume  # Update state
    self.sc_client.send_message("/carpet/volume", [volume])  # Forward to SC
    print(f"[Core] Volume {int(volume * 100)}% → SuperCollider")

# SuperCollider (carpet_hotel_sound.scd):
OSCdef(\carpetVolume, { |msg|
    newVolume = msg[1].asFloat.clip(0.0, 1.0);
    masterVolume = newVolume;  # Audio volume changes
}, '/carpet/volume');
```

## Troubleshooting

### No Audio After Starting

**Check OSC setup:**
```python
print(f"OSC server: {core.osc_server}")  # Should not be None
print(f"SC client: {core.sc_client}")    # Should not be None
```

**Check state:**
```python
print(f"SC running: {core.sc_running}")      # Should be True
print(f"Processing running: {core.pde_running}")  # Should be True
```

**Manually send scene:**
```python
core.send_initial_scene()  # Should print messages and audio should start
```

### Audio Cuts Out

- Check Core is still running
- Check SC process is alive
- Check for OSC errors in console

### Volume Not Changing

- Check mouse wheel events in Processing
- Check Core receives `/carpet/volume` messages
- Check SC receives volume updates
- Check `masterVolume` in SC console

## Testing

### Quick OSC Flow Test

```bash
python3 app/tests/test_audio_osc.py
```

This test:
1. Starts SuperCollider
2. Starts Processing
3. Verifies OSC setup
4. Audio should play automatically
5. Waits for Ctrl+C

### Manual OSC Test

```python
from carpet_hotel import CarpetHotelCore

core = CarpetHotelCore()
core.start_supercollider()
time.sleep(5)  # Wait for SC to boot

# Setup OSC manually
core.setup_osc()

# Send test scene
core.send_initial_scene()
# Audio should play!
```

## Summary

**Core is the brain. Processing and SuperCollider are just hands and mouth.**

- Core manages state
- Core routes messages
- Core coordinates everything
- Components just do their jobs

This makes the system:
- Easy to understand
- Easy to debug
- Easy to extend
- Reliable and predictable
