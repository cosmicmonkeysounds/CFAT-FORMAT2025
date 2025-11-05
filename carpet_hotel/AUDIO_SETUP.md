# Carpet Hotel - Audio Setup (SuperCollider)

The audio engine has been moved to SuperCollider for crystal-clear, professional audio mixing. Processing sends OSC messages to SuperCollider, which handles all audio playback and mixing.

## Setup

### 1. Install SuperCollider
Download from: https://supercollider.github.io/

**Note:** OSC is built into SuperCollider - no library installation needed!

### 2. Install oscP5 Library in Processing
1. Open Processing
2. Go to `Sketch > Import Library > Add Library...`
3. Search for "oscP5"
4. Install the **oscP5** library by Andreas Schlegel

### 3. Start the Audio Engine (One-Step Setup!)
1. Open SuperCollider
2. Open `carpet_hotel_audio.scd`
3. Select all code (`Cmd+A`)
4. Press `Cmd+Enter` to evaluate

**That's it!** The script will:
- Configure audio settings (44100 Hz sample rate)
- Boot the audio server automatically
- Load all audio files
- Start listening for OSC

You should see:
```
=== CARPET HOTEL AUDIO ENGINE ===
Configuring audio server...
Booting audio server...
Audio server ready!
Sample rate: 44100 Hz
Loading audio files...
  Loaded floor 2: carpet_2.wav
  Loaded floor 3: carpet_3.wav
  ...
✓ Audio engine ready!
✓ Listening for OSC on port 57120 (built-in, no library needed)
▶ Now run the Processing sketch!
```

### 4. Run the Processing Sketch
The Processing sketch will automatically send OSC messages to SuperCollider.

## How It Works

### OSC Messages

**Static Scene:**
```
/carpet/scene [sceneNum, numWindows, isAnimating]
```
- `sceneNum`: Current scene number (0, 1, 2, ...)
- `numWindows`: Number of active screens/floors (2)
- `isAnimating`: Always 0 for static scenes

**Transition:**
```
/carpet/transition [currentFloor, progress, direction, numWindows]
```
- `currentFloor`: Current floor number during transition
- `progress`: Progress within current floor (0.0 to 1.0)
- `direction`: 1 = moving up, -1 = moving down
- `numWindows`: Number of screens (2)

**Volume Control:**
```
/carpet/volume [volume]
```
- `volume`: Master volume (0.0 to 1.0)

### Audio Mixing

**Static Scenes:**
- Equal power mixing: `volumePerFloor = masterVolume / sqrt(numWindows)`
- Only active floors play audio
- Smooth 50ms lag on all amplitude changes

**Transitions:**
- Up to 4 floors can be audible during transitions
- Smooth crossfading using sine/cosine curves:
  - Fade in: `sin(progress * π/2)`
  - Fade out: `cos(progress * π/2)`
- Equal power mixing maintained throughout

## Testing

In SuperCollider, you can manually test OSC messages:

```supercollider
// Test scene 0 with 2 windows
n = NetAddr("127.0.0.1", 57120);
n.sendMsg("/carpet/scene", 0, 2, 0);

// Test transition (floor 0, 50% progress, going up)
n.sendMsg("/carpet/transition", 0, 0.5, 1, 2);

// Adjust master volume to 50%
n.sendMsg("/carpet/volume", 0.5);
```

## Troubleshooting

**No audio:**
- Check SuperCollider audio server is booted (look for "localhost" in bottom right)
- Make sure audio files are in `data/` folder
- Check SuperCollider post window for errors

**Crackling/glitches:**
- These should be completely eliminated with SuperCollider!
- If you still hear issues, try increasing server audio buffer in SuperCollider:
  ```supercollider
  s.options.blockSize = 256;  // Larger = more latency but smoother
  s.reboot;
  ```

**OSC not connecting:**
- Make sure both Processing and SuperCollider are running
- Check that SuperCollider is listening on port 57120
- Check Processing console for "OSC initialized" message

## Stopping

To stop the audio engine in SuperCollider:
- Press `Cmd+.` (Command + Period) to stop all sound
- The engine will automatically clean up

## Advantages of SuperCollider

✓ **No crackling** - Professional audio engine designed for live performance
✓ **Smooth crossfades** - Built-in 50ms lag for all amplitude changes
✓ **Better CPU usage** - Audio runs in dedicated audio thread
✓ **Equal power mixing** - Mathematically correct mixing algorithms
✓ **Low latency** - Optimized for real-time audio
✓ **Easy debugging** - Can test OSC messages independently
✓ **Built-in OSC** - No libraries or dependencies to install
✓ **One command setup** - Just evaluate the .scd file and you're ready!
