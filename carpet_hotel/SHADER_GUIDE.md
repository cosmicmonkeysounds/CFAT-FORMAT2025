# Adding Shader Effects to Carpet Hotel

## Important: P3D Renderer = Shader Support ✨

Even though we're using Processing's standard Video library (not GLVideo), **you still have full shader support!** The P3D renderer converts videos to OpenGL textures, which means you can apply any GLSL shader to your video streams.

This is the best of both worlds:
- ✅ Reliable video playback (standard Video library)
- ✅ Full shader capabilities (P3D renderer)
- ✅ Works great on macOS and all platforms
- ✅ Stable and well-documented

## Quick Start

### 1. Basic Shader Integration

Add these variables at the top of your sketch:

```java
PShader floorShader;
boolean useShader = false;
```

In `setup()`, after loading videos:

```java
// Load shader
try {
  floorShader = loadShader("shaders/example.glsl");
  println("Shader loaded successfully");
} catch (Exception e) {
  println("Could not load shader: " + e.getMessage());
}
```

In `draw()`, before drawing the floor:

```java
if (useShader && floorShader != null) {
  shader(floorShader);
  // Pass uniforms
  floorShader.set("time", globalTime);
  floorShader.set("resolution", float(width), float(height));
}

// Draw floor
currentFloor.display(globalTime);

if (useShader) {
  resetShader();
}
```

Add to `keyPressed()`:

```java
// Toggle shader on/off with 's' key
else if (key == 's' || key == 'S') {
  useShader = !useShader;
  println("Shader: " + (useShader ? "ON" : "OFF"));
}
```

### 2. Per-Floor Shaders

For different shaders on different floors, add to the `Floor` class:

```java
class Floor {
  String name;
  GLMovie video;
  float duration;
  PShader shader; // Add this
  
  Floor(String name, GLMovie video) {
    this.name = name;
    this.video = video;
    this.duration = this.video.duration();
    
    // Try to load a floor-specific shader
    try {
      String shaderName = "shaders/" + name.replace(".mp4", "").replace(".mov", "") + ".glsl";
      this.shader = loadShader(shaderName);
      println("Loaded shader for " + name);
    } catch (Exception e) {
      // No shader for this floor
      this.shader = null;
    }
  }
  
  void display(float globalTime) {
    // Apply shader if available
    if (shader != null) {
      shader(shader);
      shader.set("time", globalTime);
      shader.set("loopTime", getLoopTime(globalTime));
      shader.set("resolution", float(width), float(height));
    }
    
    // ... rest of display code ...
    
    if (shader != null) {
      resetShader();
    }
  }
}
```

## Shader Ideas for Carpet Videos

### 1. **Kaleidoscope Effect**
Perfect for carpet patterns - creates symmetrical reflections

### 2. **Displacement Mapping**
Warp the video based on its own brightness values

### 3. **Feedback Loop**
Mix current frame with previous frames for trails

### 4. **Color Cycling**
Rotate hues over time while preserving pattern

### 5. **Pixelation/Mosaic**
Break video into tiles with various effects

### 6. **Edge Detection**
Highlight the patterns and geometry in carpets

### 7. **Chromatic Aberration**
RGB channel separation for glitchy aesthetic

### 8. **Mirror/Symmetry**
Create symmetric patterns from asymmetric carpets

## Multi-Video Shader Compositing

For rendering multiple videos simultaneously with shaders:

```java
PGraphics layer1, layer2;

void setup() {
  size(1280, 720, P3D);
  layer1 = createGraphics(width, height, P3D);
  layer2 = createGraphics(width, height, P3D);
}

void draw() {
  // Render floor 0 to layer1
  layer1.beginDraw();
  layer1.image(floors.get(0).video, 0, 0);
  layer1.endDraw();
  
  // Render floor 1 to layer2
  layer2.beginDraw();
  layer2.image(floors.get(1).video, 0, 0);
  layer2.endDraw();
  
  // Composite with shader
  shader(compositeShader);
  compositeShader.set("tex1", layer1);
  compositeShader.set("tex2", layer2);
  rect(0, 0, width, height);
  resetShader();
}
```

## Advanced: Audio-Reactive Shaders

Once you add audio:

```java
// In Floor class
void display(float globalTime) {
  if (shader != null) {
    shader(shader);
    shader.set("time", globalTime);
    shader.set("audioLevel", audio.getCurrentLevel()); // Audio amplitude
    shader.set("audioSpectrum", audio.getFFT()); // Frequency data
  }
  
  // ... render video ...
}
```

## Performance Tips

1. **Minimize uniform updates**: Only set changing values
2. **Texture resolution**: Match video resolution to avoid upscaling
3. **Shader complexity**: Keep fragment shader operations minimal
4. **Multiple passes**: Use PGraphics for complex multi-pass effects

## File Structure

```
carpet_hotel/
├── carpet_hotel.pde
└── data/
    ├── carpets/
    │   ├── carpet1.mp4
    │   └── carpet2.mp4
    └── shaders/
        ├── example.glsl
        ├── carpet1.glsl  (floor-specific shader)
        ├── kaleidoscope.glsl
        └── feedback.glsl
```

## Resources

- **Standard Video Library + P3D**: Videos become OpenGL textures, perfect for shaders!
- **Why not GLVideo?**: Better cross-platform compatibility, especially on macOS
- **The Book of Shaders**: https://thebookofshaders.com/
- **Shadertoy**: Convert GLSL shaders to Processing format
- **Processing Shader Tutorial**: https://processing.org/tutorials/pshader

---

Ready to make those carpets dance! 🎨✨
