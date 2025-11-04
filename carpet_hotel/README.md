# CARPET HOTEL - Video Installation

A Processing sketch that creates a virtual hotel where each floor contains a looping carpet video. All videos loop independently based on a global timer, and you can switch between floors using alphanumeric keys.

## Setup

### 1. Install Processing Video Library

In Processing, go to:
- **Sketch → Import Library → Add Library**
- Search for "Video"
- Install the **Video | GStreamer-based video library for Processing** by The Processing Foundation

**Why This Library?**
- Most reliable on macOS and other platforms
- Excellent compatibility with Processing's P3D renderer
- Videos render as OpenGL textures in P3D mode = **full shader support!**
- Stable and well-maintained by Processing Foundation
- Works great with multiple simultaneous videos when using P3D

### 2. Prepare Your Video Files

Create a folder structure like this:
```
carpet_hotel/
├── carpet_hotel.pde
└── data/
    ├── carpet1.mp4      (or carpet_1.mp4)
    ├── carpet2.mp4      (or carpet_2.mp4)
    └── carpet3.mp4      (or carpet_3.mp4)
```

**Important**: The `data` folder must be in the same directory as your `.pde` file!

**Video Naming Convention** (both work):
- `carpet1.mp4`, `carpet2.mp4`, `carpet3.mp4`, etc.
- `carpet_1.mp4`, `carpet_2.mp4`, `carpet_3.mp4`, etc.
- Numbers should start at 1 and be sequential
- Supported formats: `.mp4`, `.mov` (or uppercase)

**Alternative with subfolder**:
```
carpet_hotel/
├── carpet_hotel.pde
└── data/
    └── carpets/
        ├── carpet1.mp4
        └── carpet2.mp4
```
If using a subfolder, change line 18 to: `String videoFolderPath = "carpets/";`

### 3. Video Path Configuration

**Default setup** (videos directly in data folder):
```java
String videoFolderPath = "";  // Looks in data/ folder
```

**If using a subfolder**:
```java
String videoFolderPath = "carpets/";  // Looks in data/carpets/ folder
```

**Note**: Processing automatically uses the `data` folder as the base path. Don't use `./data/` or absolute paths!

## How It Works

### Global Timer System
- A global timer starts when the program launches
- Each video has its own duration
- **Loop Time Calculation:** `loopTime = globalTime % videoDuration`
- This means each video loops independently and seamlessly

### Example
If you have three videos:
- Carpet 1: 10 seconds long
- Carpet 2: 7 seconds long  
- Carpet 3: 15 seconds long

At global time = 23 seconds:
- Carpet 1 is at: 23 % 10 = 3 seconds into its loop
- Carpet 2 is at: 23 % 7 = 2 seconds into its loop
- Carpet 3 is at: 23 % 15 = 8 seconds into its loop

## Controls

### Switching Floors
- **1-9**: Jump to floors 0-8
- **0**: Jump to floor 9
- **A-Z**: Jump to floors 10-35 (supports up to 36 total floors)

### Information
- **SPACE**: Print current floor info to console

## Features

✅ **Implemented:**
- Multiple video loading from folder
- Global timer system
- Modulus-based loop synchronization
- Alphanumeric key switching
- Aspect ratio-preserving display
- Real-time info overlay

🔮 **Future Enhancements (mentioned in your design):**
- Stereo WAV audio playback per floor
- Additional data and events per floor
- More sophisticated floor transitions

## Technical Notes

### Video Format Recommendations
- **Codec**: H.264 is most reliable
- **Container**: MP4 works best across platforms
- **Resolution**: 1920x1080 works well; 4K may impact performance

### Performance
- All videos are loaded at startup and loop automatically
- Videos are rendered as OpenGL textures via P3D renderer
- The P3D renderer enables GPU-accelerated rendering and shader support
- Frame reading is handled automatically via `movieEvent()`

### Shader Ready!
Since we're using the P3D renderer, videos are rendered as OpenGL textures and can receive shaders:
```java
PShader myShader = loadShader("frag.glsl");
shader(myShader);
image(video, x, y, w, h); // Shader applied to video!
resetShader();
```

### Troubleshooting

**"No library found for processing.video" error:**
- Install Video library from the Library Manager (Sketch → Import Library → Add Library)
- Search for "Video" and install the one by The Processing Foundation

**"No carpet videos found" error:**
- Check that videos are in the correct folder
- Verify naming convention: `carpet1.mp4`, `carpet2.mp4`, etc.
- Ensure the path in `videoFolderPath` is correct

**Videos not playing smoothly:**
- Try H.264 MP4 format
- Reduce resolution if needed
- Make sure you're using the P3D renderer (already set in the code)

**Black screen or video not displaying:**
- Wait a moment - videos need time to initialize
- Check console for loading messages
- Verify video codecs are supported (H.264 in MP4 is safest)

**macOS Gatekeeper issues:**
- If Processing asks for permissions, allow it to access files
- Videos should be in the sketch's `data` folder

## Future Development Ideas

1. **Audio Integration**: Load corresponding `carpet{n}.wav` files
2. **Events System**: JSON file per floor with timestamped events
3. **Transitions**: Fade or other effects when switching floors
4. **Multi-channel Audio**: Spatial audio based on floor position
5. **Interactive Elements**: Mouse interaction with carpet patterns
6. **Generative Overlays**: Procedural graphics on top of video

## Architecture

The code is structured for easy extension:

```
Floor Class:
- name: String
- video: Movie
- duration: float
- audio: AudioFile (future)
- events: ArrayList<Event> (future)
```

Each floor is self-contained and can be extended with additional properties and methods.

---

**Created for Processing 4.x**  
Requires: Video library (GStreamer-based) by The Processing Foundation  
Renderer: P3D (OpenGL) - enables shader support!
