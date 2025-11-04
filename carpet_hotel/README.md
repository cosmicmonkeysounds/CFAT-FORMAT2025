# MEDIA GENERATOR - Video Installation

A Processing sketch that creates a virtual hotel where each floor contains a looping carpet video. All videos loop independently based on a global timer, and you can switch between floors using alphanumeric keys.

## Setup

### 1. Install GLVideo Library

In Processing, go to:
- **Sketch → Import Library → Add Library**
- Search for "GLVideo"
- Install the **GL Video | Hardware accelerated video library using GStreamer** by Gottfried Haider

**Why GLVideo?**
- GPU-accelerated (essential for your shader effects!)
- Videos are loaded as OpenGL textures
- Much better performance with multiple simultaneous videos
- Works seamlessly with P3D renderer
- Perfect for shader-based video manipulation

### 2. Prepare Your Video Files

Create a folder structure like this:
```
media-generator/
├── media-generator.pde
└── data/
    └── carpets/
        ├── carpet1.mp4
        ├── carpet2.mov
        ├── carpet3.mp4
        └── ...
```

**Video Naming Convention:**
- Files must be named `carpet{number}.{extension}`
- Numbers should start at 1 and be sequential
- Supported formats: `.mp4`, `.mov` (or uppercase)

### 3. Update Video Path (if needed)

In the sketch, line 19:
```java
String videoFolderPath = "carpets/";
```

Change this if your videos are in a different location relative to the sketch's `data` folder.

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
- **Resolution**: GLVideo handles HD very well (1920x1080 or even 4K)

### Performance
- All videos are loaded as GPU textures at startup
- Videos are hardware-accelerated using OpenGL
- The P3D renderer ensures GPU-based rendering
- GLVideo automatically manages frame reading

### Shader Ready!
Since GLVideo loads videos as OpenGL textures, you can easily apply shaders:
```java
PShader myShader = loadShader("frag.glsl", "vert.glsl");
shader(myShader);
image(video, x, y, w, h); // Shader applied to video!
```

### Troubleshooting

**"No library found for gohai.glvideo" error:**
- Install GLVideo library from the Library Manager
- Make sure you have the latest version

**"No carpet videos found" error:**
- Check that videos are in the correct folder
- Verify naming convention: `carpet1.mp4`, `carpet2.mp4`, etc.
- Ensure the path in `videoFolderPath` is correct

**Videos not playing smoothly:**
- GLVideo is GPU-accelerated, so performance should be excellent
- If issues persist, try H.264 MP4 format
- Check GPU drivers are up to date

**Console shows file errors:**
- GLVideo requires GStreamer on your system
- On some systems, you may need to install GStreamer separately

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
Requires: GLVideo library (Hardware accelerated video using GStreamer)  
Renderer: P3D (OpenGL)
