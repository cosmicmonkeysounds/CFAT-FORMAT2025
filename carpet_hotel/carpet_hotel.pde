/**
 * CARPET HOTEL - Multi-Window Video Installation
 * Simplified version - each window shows one video
 */

import processing.video.*;
import java.io.File;

// Configuration
int NUM_WINDOWS = 2;              // Number of separate windows
int[] DISPLAY_NUMBERS = {1, 2};   // Which display for each window
int VIDEO_HEIGHT = 1080;          // Standard video height for animation

// Shared state across all windows
static SharedState sharedState;

void setup() {
  // Create tiny control window
  size(400, 300);
  pixelDensity(1);
  surface.setTitle("Carpet Hotel - Control");

  // Initialize shared state
  sharedState = new SharedState();
  sharedState.init(this);

  // Launch separate windows for each display
  for (int i = 0; i < NUM_WINDOWS; i++) {
    String[] args = {"FloorWindow_" + i};
    FloorWindow window = new FloorWindow(i);
    PApplet.runSketch(args, window);
  }

  println("\n=== CARPET HOTEL CONTROL ===");
  println("Windows launched: " + NUM_WINDOWS);
  println("Videos loaded: " + sharedState.videos.size());
  println("\nCONTROLS:");
  println("1-9: Switch to scene");
  println("D: Toggle debug panel");
  println("F: Toggle fullscreen");
  println("SPACE: Print info");
  println("ESC: Close all windows");
}

void draw() {
  // Update animation state
  sharedState.update();

  background(40);
  fill(255);
  textAlign(LEFT, TOP);
  textSize(14);

  int y = 20;
  text("=== CARPET HOTEL CONTROL ===", 20, y); y += 30;
  text("Videos: " + sharedState.videos.size(), 20, y); y += 25;
  text("Scenes: " + sharedState.getNumScenes(), 20, y); y += 25;
  text("Current scene: " + sharedState.currentScene, 20, y); y += 25;
  if (sharedState.isAnimating) {
    float pct = (sharedState.animationProgress / sharedState.totalDistance) * 100;
    text("Animating: " + sharedState.startScene + " -> " + sharedState.targetScene, 20, y); y += 20;
    text("Progress: " + nf(pct, 0, 1) + "% (" + nf(sharedState.animationProgress, 0, 1) + "/" + sharedState.totalDistance + " floors)", 20, y); y += 20;
    text("Effects: " + nf(sharedState.getShaderIntensity() * 100, 0, 1) + "%", 20, y); y += 25;
  }
  text("Debug: " + (sharedState.showDebug ? "ON" : "OFF"), 20, y); y += 25;
  text("Fullscreen: " + (sharedState.isFullscreen ? "ON" : "OFF"), 20, y); y += 25;

  y += 10;
  text("Current windows:", 20, y); y += 20;
  for (int i = 0; i < NUM_WINDOWS; i++) {
    int videoIdx = sharedState.currentScene + i;
    if (videoIdx < sharedState.videoNames.size()) {
      String filename = sharedState.videoNames.get(videoIdx);
      text("  W" + i + " -> Floor " + videoIdx + ": " + filename, 20, y);
      y += 18;
    }
  }
}

void keyPressed() {
  if (key >= '1' && key <= '9') {
    int scene = key - '1';
    if (scene >= 0 && scene < sharedState.getNumScenes()) {
      sharedState.startTransition(scene);
    }
  } else if (key == ' ') {
    println("\n=== SCENE " + sharedState.currentScene + " ===");
    for (int i = 0; i < NUM_WINDOWS; i++) {
      int videoIdx = sharedState.currentScene + i;
      if (videoIdx < sharedState.videos.size()) {
        println("  Window " + i + " -> " + sharedState.videoNames.get(videoIdx));
      }
    }
  } else if (key == 'd' || key == 'D') {
    sharedState.showDebug = !sharedState.showDebug;
    println("Debug panel: " + (sharedState.showDebug ? "ON" : "OFF"));
  }
}

void movieEvent(Movie m) {
  m.read();
}

void exit() {
  if (sharedState != null) {
    sharedState.cleanup();
  }
  super.exit();
}

/**
 * Shared state synchronized across all windows
 */
class SharedState {
  ArrayList<Movie> videos;
  ArrayList<String> videoNames;
  int currentScene = 0;
  boolean showDebug = true;
  boolean isFullscreen = true;

  // Animation state
  boolean isAnimating = false;
  int startScene = 0;
  int targetScene = 0;
  float animationProgress = 0.0;  // 0.0 to total distance in floors
  float animationSpeed = 0.1;     // Speed per frame
  int animationDirection = 0;     // 1 = up (to higher floor), -1 = down (to lower floor)
  float totalDistance = 0;        // Total floors to travel

  PApplet parent;

  void init(PApplet p) {
    parent = p;
    videos = new ArrayList<Movie>();
    videoNames = new ArrayList<String>();

    // Find all carpet videos
    findCarpetVideos();

    // Load first NUM_WINDOWS videos
    for (int i = 0; i < min(NUM_WINDOWS, videoNames.size()); i++) {
      Movie m = new Movie(parent, videoNames.get(i));
      m.loop();
      m.play();
      videos.add(m);
      println("Loaded: " + videoNames.get(i));
    }

    // Placeholder for unloaded videos
    while (videos.size() < videoNames.size()) {
      videos.add(null);
    }
  }

  int getNumScenes() {
    return max(1, videoNames.size() - NUM_WINDOWS + 1);
  }

  void update() {
    if (isAnimating) {
      // Increment animation progress linearly
      animationProgress += animationSpeed;

      // Check if animation is complete
      if (animationProgress >= totalDistance) {
        animationProgress = totalDistance;
        isAnimating = false;
        currentScene = targetScene;
        println("Arrived at scene " + currentScene);
      }
    }
  }

  void startTransition(int newScene) {
    if (newScene == currentScene || isAnimating) {
      return; // Already there or currently animating
    }

    println("Starting transition from scene " + currentScene + " to scene " + newScene);
    startScene = currentScene;
    targetScene = newScene;
    animationDirection = (newScene > currentScene) ? 1 : -1;
    totalDistance = abs(newScene - currentScene);
    animationProgress = 0.0;
    isAnimating = true;

    println("Will scroll through " + totalDistance + " floor(s)");

    // Preload videos along the path
    int minScene = min(currentScene, targetScene);
    int maxScene = max(currentScene, targetScene);
    for (int scene = minScene; scene <= maxScene; scene++) {
      for (int i = 0; i < NUM_WINDOWS; i++) {
        int videoIdx = scene + i;
        if (videoIdx >= 0 && videoIdx < videoNames.size()) {
          ensureVideoLoaded(videoIdx);
        }
      }
    }
  }

  float getShaderIntensity() {
    if (!isAnimating || totalDistance == 0) return 0.0;

    // Peak at 50% of journey, return to 0 at start and end
    float normalizedProgress = animationProgress / totalDistance;
    // Sine wave that peaks at 0.5
    return sin(normalizedProgress * PI) * 0.8; // Max intensity 0.8
  }

  void ensureVideoLoaded(int index) {
    if (index >= 0 && index < videoNames.size() && videos.get(index) == null) {
      println("Loading: " + videoNames.get(index));
      Movie m = new Movie(parent, videoNames.get(index));
      m.loop();
      m.play();
      videos.set(index, m);
    }
  }

  void findCarpetVideos() {
    println("\nSearching for videos in: " + parent.dataPath(""));

    File dataFolder = new File(parent.dataPath(""));
    if (!dataFolder.exists() || !dataFolder.isDirectory()) {
      println("ERROR: Data folder does not exist!");
      return;
    }

    String[] files = dataFolder.list();
    if (files == null || files.length == 0) {
      println("ERROR: Data folder is empty!");
      return;
    }

    // Find all carpet videos
    ArrayList<String> foundFiles = new ArrayList<String>();
    for (String filename : files) {
      String lower = filename.toLowerCase();
      if ((lower.startsWith("carpet_") || lower.startsWith("carpet")) &&
          (lower.endsWith(".mp4") || lower.endsWith(".mov"))) {
        foundFiles.add(filename);
      }
    }

    // Sort by number
    java.util.Collections.sort(foundFiles, new java.util.Comparator<String>() {
      public int compare(String a, String b) {
        int numA = extractNumber(a);
        int numB = extractNumber(b);
        return Integer.compare(numA, numB);
      }
    });

    // Add to list (sorted low to high by number)
    println("\nVideos found (sorted by floor number):");
    for (int i = 0; i < foundFiles.size(); i++) {
      String filename = foundFiles.get(i);
      videoNames.add(filename);
      println("  Floor " + i + ": " + filename);
    }
  }

  int extractNumber(String filename) {
    String name = filename.replaceAll("\\.[^.]*$", "");
    String numStr = name.replaceAll("[^0-9]", "");
    try {
      return Integer.parseInt(numStr);
    } catch (Exception e) {
      return 0;
    }
  }

  void cleanup() {
    for (Movie m : videos) {
      if (m != null) {
        m.stop();
      }
    }
  }
}

/**
 * Individual floor window - just plays one video
 */
class FloorWindow extends PApplet {
  int windowIndex;
  int displayNum;

  FloorWindow(int index) {
    this.windowIndex = index;
    this.displayNum = DISPLAY_NUMBERS[index];
  }

  public void settings() {
    fullScreen(P2D, displayNum);
    pixelDensity(1);
  }

  public void setup() {
    background(0);
    surface.setTitle("Carpet Hotel - Window " + windowIndex);
  }

  public void draw() {
    background(0);

    // Determine which scene we're showing (current or animating to target)
    int displayScene = sharedState.currentScene;

    if (sharedState.isAnimating) {
      // During animation, render both current and target videos
      renderAnimatedTransition();
    } else {
      // Normal rendering - just show current video
      int videoIdx = displayScene + windowIndex;
      renderVideo(videoIdx, 0, 0);
    }

    // Debug panel (on top of everything)
    if (sharedState.showDebug) {
      int videoIdx = displayScene + windowIndex;
      if (videoIdx >= 0 && videoIdx < sharedState.videos.size() && sharedState.videos.get(videoIdx) != null) {
        drawDebugPanel(sharedState.videos.get(videoIdx), videoIdx);
      }
    }
  }

  void renderAnimatedTransition() {
    // Calculate which floor we're between
    int currentFloor = sharedState.startScene + (int)sharedState.animationProgress * sharedState.animationDirection;
    float fractionalProgress = sharedState.animationProgress - floor(sharedState.animationProgress);

    // Calculate vertical offset for smooth scrolling
    // When going UP (higher floor), floors should scroll DOWN on screen (negative direction)
    // When going DOWN (lower floor), floors should scroll UP on screen (positive direction)
    float offsetPixels = fractionalProgress * VIDEO_HEIGHT * (-sharedState.animationDirection);

    // Current floor video
    int currentVideoIdx = currentFloor + windowIndex;
    renderVideoWithEffects(currentVideoIdx, 0, offsetPixels);

    // Next floor video (in the direction of travel)
    int nextFloor = currentFloor + sharedState.animationDirection;
    int nextVideoIdx = nextFloor + windowIndex;
    float nextOffset = sharedState.animationDirection > 0 ? -VIDEO_HEIGHT : VIDEO_HEIGHT;
    renderVideoWithEffects(nextVideoIdx, 0, nextOffset + offsetPixels);
  }

  void renderVideo(int videoIdx, float baseX, float baseY) {
    renderVideoWithEffects(videoIdx, baseX, baseY);
  }

  void renderVideoWithEffects(int videoIdx, float baseX, float baseY) {
    if (videoIdx < 0 || videoIdx >= sharedState.videoNames.size()) {
      return; // Out of bounds
    }

    // Ensure video is loaded
    sharedState.ensureVideoLoaded(videoIdx);
    Movie video = sharedState.videos.get(videoIdx);

    if (video == null) {
      return; // Not loaded yet
    }

    // Read frame
    if (video.available()) {
      video.read();
    }

    // Draw video
    if (video.width > 0 && video.height > 0) {
      // Calculate letterboxing to maintain aspect ratio
      float videoAspect = (float)video.width / (float)video.height;
      float screenAspect = (float)width / (float)height;

      float drawWidth, drawHeight, drawX, drawY;

      if (videoAspect > screenAspect) {
        // Video is wider - fit to width
        drawWidth = width;
        drawHeight = width / videoAspect;
        drawX = 0;
        drawY = (height - drawHeight) / 2;
      } else {
        // Video is taller - fit to height
        drawHeight = height;
        drawWidth = height * videoAspect;
        drawX = (width - drawWidth) / 2;
        drawY = 0;
      }

      // Apply animation offset
      drawY += baseY;

      // Get shader intensity (peaks at 50% of transition)
      float intensity = sharedState.getShaderIntensity();

      if (intensity > 0.05) {
        // Apply shader effects during transition
        pushMatrix();
        translate(drawX, drawY);

        // Apply chromatic aberration by drawing RGB channels separately
        tint(255, 0, 0, 200); // Red channel
        float chromaticOffset = intensity * 8;
        image(video, -chromaticOffset, 0, drawWidth, drawHeight);

        tint(0, 255, 0, 200); // Green channel
        image(video, 0, 0, drawWidth, drawHeight);

        tint(0, 0, 255, 200); // Blue channel
        image(video, chromaticOffset, 0, drawWidth, drawHeight);

        noTint();

        // Motion blur effect - draw multiple slightly offset copies
        int blurSamples = 3;
        float blurDirection = sharedState.animationDirection * intensity * 15;
        for (int i = 1; i <= blurSamples; i++) {
          tint(255, 255 / (i * 2));
          image(video, 0, -blurDirection * i, drawWidth, drawHeight);
        }

        noTint();
        popMatrix();

        // Bloom effect - draw a blurred bright overlay
        tint(255, intensity * 80); // Subtle bloom
        image(video, drawX, drawY, drawWidth, drawHeight);
        noTint();
      } else {
        // Normal rendering without effects
        image(video, drawX, drawY, drawWidth, drawHeight);
      }
    }
  }

  void drawDebugPanel(Movie video, int videoIdx) {
    // Semi-transparent background
    fill(0, 200);
    noStroke();
    rect(10, 10, 550, 420);

    // Debug text
    fill(0, 255, 0);
    textAlign(LEFT, TOP);
    textSize(14);
    int y = 20;
    int lineHeight = 22;

    text("=== CARPET HOTEL DEBUG ===", 20, y); y += lineHeight + 5;

    fill(255);
    text("Window: " + windowIndex, 20, y); y += lineHeight;
    text("Display: " + DISPLAY_NUMBERS[windowIndex], 20, y); y += lineHeight;
    text("Screen: " + width + "x" + height, 20, y); y += lineHeight;

    y += 5;
    text("Scene: " + sharedState.currentScene + " / " + (sharedState.getNumScenes() - 1), 20, y); y += lineHeight;
    if (sharedState.isAnimating) {
      float pct = (sharedState.animationProgress / sharedState.totalDistance) * 100;
      text("Animating: " + sharedState.startScene + " -> " + sharedState.targetScene + " (" + nf(pct, 0, 1) + "%)", 20, y); y += lineHeight;
      text("Direction: " + (sharedState.animationDirection > 0 ? "UP (higher floor)" : "DOWN (lower floor)"), 20, y); y += lineHeight;
      text("Floors traveled: " + nf(sharedState.animationProgress, 0, 2) + " / " + sharedState.totalDistance, 20, y); y += lineHeight;
      text("Shader intensity: " + nf(sharedState.getShaderIntensity() * 100, 0, 1) + "%", 20, y); y += lineHeight;
    }
    text("Video Index: " + videoIdx + " / " + (sharedState.videoNames.size() - 1), 20, y); y += lineHeight;
    text("Video File: " + sharedState.videoNames.get(videoIdx), 20, y); y += lineHeight;

    y += 5;
    text("Video Resolution: " + video.width + "x" + video.height, 20, y); y += lineHeight;
    text("Video Time: " + nf(video.time(), 0, 2) + "s", 20, y); y += lineHeight;

    try {
      text("Video Duration: " + nf(video.duration(), 0, 2) + "s", 20, y); y += lineHeight;
    } catch (Exception e) {
      text("Video Duration: unknown", 20, y); y += lineHeight;
    }

    try {
      text("Video Playing: " + video.isPlaying(), 20, y); y += lineHeight;
    } catch (Exception e) {
      text("Video Playing: " + (video.time() > 0), 20, y); y += lineHeight;
    }

    y += 5;
    text("Frame Rate: " + nf(frameRate, 0, 1) + " fps", 20, y); y += lineHeight;
    text("Frame Count: " + frameCount, 20, y); y += lineHeight;

    y += 10;
    fill(100);
    text("Press D to hide debug | Press F to toggle fullscreen", 20, y);
  }

  public void keyPressed() {
    if (key >= '1' && key <= '9') {
      int scene = key - '1';
      if (scene >= 0 && scene < sharedState.getNumScenes()) {
        sharedState.startTransition(scene);
      }
    } else if (key == ' ') {
      println("\n=== SCENE " + sharedState.currentScene + " ===");
      for (int i = 0; i < NUM_WINDOWS; i++) {
        int vIdx = sharedState.currentScene + i;
        if (vIdx < sharedState.videoNames.size()) {
          println("  Window " + i + " -> " + sharedState.videoNames.get(vIdx));
        }
      }
    } else if (key == 'd' || key == 'D') {
      sharedState.showDebug = !sharedState.showDebug;
      println("Debug panel: " + (sharedState.showDebug ? "ON" : "OFF"));
    } else if (key == 'f' || key == 'F') {
      sharedState.isFullscreen = !sharedState.isFullscreen;
      if (sharedState.isFullscreen) {
        // Return to fullscreen
        surface.setSize(displayWidth, displayHeight);
        println("Window " + windowIndex + " fullscreen ON");
      } else {
        // Windowed mode
        surface.setSize(1280, 720);
        println("Window " + windowIndex + " fullscreen OFF");
      }
    }
  }
}
