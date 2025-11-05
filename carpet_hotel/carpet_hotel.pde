/**
 * CARPET HOTEL - Multi-Window Video Installation
 * Simplified version - each window shows one video
 */

import processing.video.*;
import processing.sound.*;
import java.io.File;

// Configuration
int NUM_WINDOWS = 2;              // Number of separate windows
int[] DISPLAY_NUMBERS = {1, 2};   // Which display for each window
int VIDEO_HEIGHT = 1080;          // Standard video height for animation

// Audio configuration
int AUDIO_SAMPLE_RATE = 44100;    // MUST match sample rate of audio files (check with ffprobe)

// Shared state across all windows
static SharedState sharedState;

void setup() {
  // Create tiny control window
  size(400, 300);
  pixelDensity(1);
  surface.setTitle("Carpet Hotel - Control");

  // Configure audio engine for smooth playback
  // Sample rate must match audio files (44100 Hz)
  Sound s = new Sound(this);
  s.sampleRate(AUDIO_SAMPLE_RATE);

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
  println("Floors loaded: " + sharedState.floors.size());
  println("Videos: " + sharedState.videoNames.size());
  println("Audio: " + sharedState.audioNames.size());
  println("\nTIP: Edit 'transition_config.txt' to customize transition effects");
  println("(Config file is in the same folder as the .pde file)");
  println("\nCONTROLS:");
  println("1-9: Switch to scene");
  println("D: Toggle debug panel");
  println("F: Toggle fullscreen");
  println("R: Reload config file");
  println("SPACE: Print info");
  println("SCROLL: Adjust master volume");
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
  text("Floors: " + sharedState.floors.size() + " (" + sharedState.videoNames.size() + " videos, " + sharedState.audioNames.size() + " audio)", 20, y); y += 25;
  text("Scenes: " + sharedState.getNumScenes(), 20, y); y += 25;
  text("Current scene: " + sharedState.currentScene, 20, y); y += 25;
  text("Master volume: " + nf(sharedState.masterVolume * 100, 0, 0) + "%", 20, y); y += 25;
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
  } else if (key == 'r' || key == 'R') {
    println("\nReloading transition configuration...");
    sharedState.config.loadFromFile(this);
    println("Configuration reloaded!");
  }
}

void movieEvent(Movie m) {
  m.read();
}

void mouseWheel(MouseEvent event) {
  float delta = event.getCount();
  sharedState.masterVolume = constrain(sharedState.masterVolume - delta * 0.05, 0.0, 1.0);
  println("Master volume: " + nf(sharedState.masterVolume * 100, 0, 0) + "%");
}

void exit() {
  if (sharedState != null) {
    sharedState.cleanup();
  }
  super.exit();
}

/**
 * Transition configuration
 */
class TransitionConfig {
  float animationSpeed = 0.1;
  float chromaticIntensity = 8.0;
  int motionBlurSamples = 3;
  float motionBlurIntensity = 15.0;
  float bloomIntensity = 80.0;
  float maxEffectIntensity = 0.8;
  float effectThreshold = 0.05;
  int chromaticRAlpha = 200;
  int chromaticGAlpha = 200;
  int chromaticBAlpha = 200;
  int motionBlurAlphaDivisor = 2;

  void loadFromFile(PApplet parent) {
    String[] lines = parent.loadStrings(parent.sketchPath("transition_config.txt"));
    if (lines == null) {
      println("Could not load transition_config.txt, using defaults");
      return;
    }

    println("\nLoading transition configuration:");
    for (String line : lines) {
      line = line.trim();
      if (line.length() == 0 || line.startsWith("#")) {
        continue;
      }

      String[] parts = line.split("=");
      if (parts.length != 2) continue;

      String key = parts[0].trim();
      String value = parts[1].trim();

      try {
        switch (key) {
          case "animation_speed":
            animationSpeed = Float.parseFloat(value);
            println("  animation_speed = " + animationSpeed);
            break;
          case "chromatic_intensity":
            chromaticIntensity = Float.parseFloat(value);
            println("  chromatic_intensity = " + chromaticIntensity);
            break;
          case "motion_blur_samples":
            motionBlurSamples = Integer.parseInt(value);
            println("  motion_blur_samples = " + motionBlurSamples);
            break;
          case "motion_blur_intensity":
            motionBlurIntensity = Float.parseFloat(value);
            println("  motion_blur_intensity = " + motionBlurIntensity);
            break;
          case "bloom_intensity":
            bloomIntensity = Float.parseFloat(value);
            println("  bloom_intensity = " + bloomIntensity);
            break;
          case "max_effect_intensity":
            maxEffectIntensity = Float.parseFloat(value);
            println("  max_effect_intensity = " + maxEffectIntensity);
            break;
          case "effect_threshold":
            effectThreshold = Float.parseFloat(value);
            println("  effect_threshold = " + effectThreshold);
            break;
          case "chromatic_r_alpha":
            chromaticRAlpha = Integer.parseInt(value);
            println("  chromatic_r_alpha = " + chromaticRAlpha);
            break;
          case "chromatic_g_alpha":
            chromaticGAlpha = Integer.parseInt(value);
            println("  chromatic_g_alpha = " + chromaticGAlpha);
            break;
          case "chromatic_b_alpha":
            chromaticBAlpha = Integer.parseInt(value);
            println("  chromatic_b_alpha = " + chromaticBAlpha);
            break;
          case "motion_blur_alpha_divisor":
            motionBlurAlphaDivisor = Integer.parseInt(value);
            println("  motion_blur_alpha_divisor = " + motionBlurAlphaDivisor);
            break;
        }
      } catch (Exception e) {
        println("  Error parsing " + key + ": " + value);
      }
    }
  }
}

/**
 * Shared state synchronized across all windows
 */
class SharedState {
  ArrayList<Floor> floors;
  ArrayList<String> videoNames;
  ArrayList<String> audioNames;
  int currentScene = 0;
  boolean showDebug = true;
  boolean isFullscreen = true;

  // Animation state
  boolean isAnimating = false;
  int startScene = 0;
  int targetScene = 0;
  float animationProgress = 0.0;  // 0.0 to total distance in floors
  int animationDirection = 0;     // 1 = up (to higher floor), -1 = down (to lower floor)
  float totalDistance = 0;        // Total floors to travel

  // Audio mixing
  float masterVolume = 0.7;       // Master volume control (0.0 to 1.0)
  int audioUpdateCounter = 0;     // Counter for reducing audio update frequency

  // Configuration
  TransitionConfig config;

  PApplet parent;

  // Keep reference to videos for compatibility
  ArrayList<Movie> videos;

  void init(PApplet p) {
    parent = p;
    videos = new ArrayList<Movie>();
    videoNames = new ArrayList<String>();
    audioNames = new ArrayList<String>();
    floors = new ArrayList<Floor>();

    // Load configuration
    config = new TransitionConfig();
    config.loadFromFile(parent);

    // Find all carpet videos and audio
    findCarpetMedia();

    // Load first NUM_WINDOWS floors
    for (int i = 0; i < min(NUM_WINDOWS, videoNames.size()); i++) {
      String videoFile = videoNames.get(i);
      String audioFile = i < audioNames.size() ? audioNames.get(i) : null;
      Floor floor = new Floor(parent, videoFile, audioFile, i);
      floors.add(floor);
      videos.add(floor.video); // For compatibility
      println("Loaded Floor " + i + ": " + videoFile + " + " + audioFile);
    }

    // Placeholder for unloaded floors
    while (floors.size() < videoNames.size()) {
      floors.add(null);
      videos.add(null);
    }
  }

  int getNumScenes() {
    return max(1, videoNames.size() - NUM_WINDOWS + 1);
  }

  void update() {
    if (isAnimating) {
      // Increment animation progress linearly using config speed
      animationProgress += config.animationSpeed;

      // Check if animation is complete
      if (animationProgress >= totalDistance) {
        animationProgress = totalDistance;
        isAnimating = false;
        currentScene = targetScene;
        println("Arrived at scene " + currentScene);
      }

      // Update audio mixing for transition
      updateTransitionAudio();
    } else {
      // Update audio mixing for current scene
      updateSceneAudio();
    }

    // Update audio amplitudes at reduced frequency (every 3 frames = ~20fps)
    audioUpdateCounter++;
    if (audioUpdateCounter >= 3) {
      audioUpdateCounter = 0;
      for (Floor floor : floors) {
        if (floor != null) {
          floor.updateAmp();
        }
      }
    }
  }

  void updateSceneAudio() {
    // Equal power mixing for active screens in current scene
    // Volume per floor = masterVolume / sqrt(NUM_WINDOWS)
    float volumePerFloor = masterVolume / sqrt(NUM_WINDOWS);

    // Set all floors to silent first
    for (int i = 0; i < floors.size(); i++) {
      Floor floor = floors.get(i);
      if (floor != null) {
        floor.setTargetAmp(0.0);
      }
    }

    // Set volume for active floors in current scene
    for (int i = 0; i < NUM_WINDOWS; i++) {
      int floorIdx = currentScene + i;
      if (floorIdx >= 0 && floorIdx < floors.size()) {
        Floor floor = floors.get(floorIdx);
        if (floor != null) {
          floor.setTargetAmp(volumePerFloor);
        }
      }
    }
  }

  void updateTransitionAudio() {
    // During transition, up to 4 floors can be audible (cross-fading)
    // Calculate which floors are currently "zooming past"
    int currentFloor = startScene + (int)animationProgress * animationDirection;
    float fractionalProgress = animationProgress - floor(animationProgress);

    // Set all floors to silent first
    for (int i = 0; i < floors.size(); i++) {
      Floor floor = floors.get(i);
      if (floor != null) {
        floor.setTargetAmp(0.0);
      }
    }

    // Calculate which floors are audible
    // We need floors for current window positions plus the next ones sliding in
    ArrayList<Integer> audibleFloors = new ArrayList<Integer>();

    // Current floors for each window
    for (int i = 0; i < NUM_WINDOWS; i++) {
      int floorIdx = currentFloor + i;
      if (!audibleFloors.contains(floorIdx)) {
        audibleFloors.add(floorIdx);
      }
    }

    // Next floors sliding in
    int nextFloor = currentFloor + animationDirection;
    for (int i = 0; i < NUM_WINDOWS; i++) {
      int floorIdx = nextFloor + i;
      if (!audibleFloors.contains(floorIdx)) {
        audibleFloors.add(floorIdx);
      }
    }

    // Limit to 4 floors maximum
    while (audibleFloors.size() > 4) {
      audibleFloors.remove(audibleFloors.size() - 1);
    }

    // Equal power mixing for audible floors
    float volumePerFloor = masterVolume / sqrt(audibleFloors.size());

    // Smooth equal-power crossfade using cosine curves
    // This prevents crackling and maintains perceived loudness
    for (int floorIdx : audibleFloors) {
      if (floorIdx >= 0 && floorIdx < floors.size()) {
        Floor floor = floors.get(floorIdx);
        if (floor != null) {
          // Determine if this floor is fading in or out
          boolean isNext = false;
          for (int i = 0; i < NUM_WINDOWS; i++) {
            if (floorIdx == nextFloor + i) {
              isNext = true;
              break;
            }
          }

          // Apply smooth equal-power crossfade curves
          float crossfadeGain;
          if (isNext) {
            // Fading in: use sine curve (0 to 1)
            // Starts at 0 when progress=0, ends at 1 when progress=1
            crossfadeGain = sin(fractionalProgress * HALF_PI);
          } else {
            // Fading out: use cosine curve (1 to 0)
            // Starts at 1 when progress=0, ends at 0 when progress=1
            crossfadeGain = cos(fractionalProgress * HALF_PI);
          }

          // Set target volume with smooth crossfade
          float finalVolume = volumePerFloor * crossfadeGain;
          floor.setTargetAmp(finalVolume);
        }
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
    return sin(normalizedProgress * PI) * config.maxEffectIntensity;
  }

  void ensureFloorLoaded(int index) {
    if (index >= 0 && index < videoNames.size() && floors.get(index) == null) {
      String videoFile = videoNames.get(index);
      String audioFile = index < audioNames.size() ? audioNames.get(index) : null;
      println("Loading Floor " + index + ": " + videoFile + " + " + audioFile);
      Floor floor = new Floor(parent, videoFile, audioFile, index);
      floors.set(index, floor);
      videos.set(index, floor.video);
    }
  }

  void ensureVideoLoaded(int index) {
    ensureFloorLoaded(index);
  }

  void findCarpetMedia() {
    println("\nSearching for media in: " + parent.dataPath(""));

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
    ArrayList<String> foundVideos = new ArrayList<String>();
    for (String filename : files) {
      String lower = filename.toLowerCase();
      if ((lower.startsWith("carpet_") || lower.startsWith("carpet")) &&
          (lower.endsWith(".mp4") || lower.endsWith(".mov"))) {
        foundVideos.add(filename);
      }
    }

    // Find all carpet audio
    ArrayList<String> foundAudio = new ArrayList<String>();
    for (String filename : files) {
      String lower = filename.toLowerCase();
      if ((lower.startsWith("carpet_") || lower.startsWith("carpet")) &&
          (lower.endsWith(".wav") || lower.endsWith(".mp3") || lower.endsWith(".aiff"))) {
        foundAudio.add(filename);
      }
    }

    // Sort by number
    java.util.Comparator<String> numberComparator = new java.util.Comparator<String>() {
      public int compare(String a, String b) {
        int numA = extractNumber(a);
        int numB = extractNumber(b);
        return Integer.compare(numA, numB);
      }
    };

    java.util.Collections.sort(foundVideos, numberComparator);
    java.util.Collections.sort(foundAudio, numberComparator);

    // Add to lists (sorted low to high by number)
    println("\nMedia found (sorted by floor number):");
    int maxFloors = max(foundVideos.size(), foundAudio.size());
    for (int i = 0; i < maxFloors; i++) {
      String videoFile = i < foundVideos.size() ? foundVideos.get(i) : null;
      String audioFile = i < foundAudio.size() ? foundAudio.get(i) : null;

      if (videoFile != null) {
        videoNames.add(videoFile);
      }
      if (audioFile != null) {
        audioNames.add(audioFile);
      }

      print("  Floor " + i + ": ");
      if (videoFile != null) print(videoFile);
      if (videoFile != null && audioFile != null) print(" + ");
      if (audioFile != null) print(audioFile);
      println();
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
    for (Floor f : floors) {
      if (f != null) {
        f.cleanup();
      }
    }
  }
}

/**
 * Floor class - contains a video and audio file that loop independently
 */
class Floor {
  Movie video;
  SoundFile audio;
  String videoName;
  String audioName;
  int floorNumber;
  float currentAmp = 0.0;          // Track current amplitude
  float targetAmp = 0.0;           // Target amplitude
  static final float AMP_THRESHOLD = 0.01;  // Only update if change > 1%

  Floor(PApplet parent, String videoFile, String audioFile, int number) {
    this.videoName = videoFile;
    this.audioName = audioFile;
    this.floorNumber = number;

    // Load video
    if (videoFile != null) {
      video = new Movie(parent, videoFile);
      video.loop();
      video.play();
    }

    // Load audio
    if (audioFile != null) {
      audio = new SoundFile(parent, audioFile);
      audio.loop();
      audio.amp(0.0); // Start silent, will be controlled by mixing
      currentAmp = 0.0;
      targetAmp = 0.0;
    }
  }

  // Set target amplitude (will be smoothly applied)
  void setTargetAmp(float amp) {
    targetAmp = constrain(amp, 0.0, 1.0);
  }

  // Update amplitude smoothly (call less frequently than every frame)
  void updateAmp() {
    if (audio == null) return;

    // Smooth interpolation toward target
    float diff = targetAmp - currentAmp;

    // Only update if difference is significant
    if (abs(diff) > AMP_THRESHOLD) {
      // Smooth step toward target (slower movement = smoother audio)
      currentAmp += diff * 0.15; // 15% per update
      audio.amp(currentAmp);
    } else if (abs(diff) > 0.001) {
      // Final snap to target when very close
      currentAmp = targetAmp;
      audio.amp(currentAmp);
    }
  }

  void cleanup() {
    if (video != null) {
      video.stop();
    }
    if (audio != null) {
      audio.stop();
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

    // Enable clipping to prevent videos from rendering outside viewport
    pushMatrix();

    if (sharedState.isAnimating) {
      // During animation, render both current and target videos
      renderAnimatedTransition();
    } else {
      // Normal rendering - just show current video
      int videoIdx = displayScene + windowIndex;
      renderVideo(videoIdx, 0, 0);
    }

    popMatrix();

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

    // Each window needs to render 2 videos during transition:
    // 1. The video currently visible in this window
    // 2. The video that's sliding in from off-screen

    // Current video for this window
    int currentVideoIdx = currentFloor + windowIndex;

    // Next video that's sliding in (offset by screen height)
    int nextFloor = currentFloor + sharedState.animationDirection;
    int nextVideoIdx = nextFloor + windowIndex;

    // Render both videos with proper offset
    if (sharedState.animationDirection > 0) {
      // Going UP: new floor slides in from BOTTOM
      renderVideoWithEffects(currentVideoIdx, 0, offsetPixels);
      renderVideoWithEffects(nextVideoIdx, 0, offsetPixels + VIDEO_HEIGHT);
    } else {
      // Going DOWN: new floor slides in from TOP
      renderVideoWithEffects(currentVideoIdx, 0, offsetPixels);
      renderVideoWithEffects(nextVideoIdx, 0, offsetPixels - VIDEO_HEIGHT);
    }
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

      if (intensity > sharedState.config.effectThreshold) {
        // Apply shader effects during transition
        pushMatrix();
        translate(drawX, drawY);

        // Apply chromatic aberration by drawing RGB channels separately
        tint(255, 0, 0, sharedState.config.chromaticRAlpha); // Red channel
        float chromaticOffset = intensity * sharedState.config.chromaticIntensity;
        image(video, -chromaticOffset, 0, drawWidth, drawHeight);

        tint(0, 255, 0, sharedState.config.chromaticGAlpha); // Green channel
        image(video, 0, 0, drawWidth, drawHeight);

        tint(0, 0, 255, sharedState.config.chromaticBAlpha); // Blue channel
        image(video, chromaticOffset, 0, drawWidth, drawHeight);

        noTint();

        // Motion blur effect - draw multiple slightly offset copies
        int blurSamples = sharedState.config.motionBlurSamples;
        float blurDirection = sharedState.animationDirection * intensity * sharedState.config.motionBlurIntensity;
        for (int i = 1; i <= blurSamples; i++) {
          tint(255, 255 / (i * sharedState.config.motionBlurAlphaDivisor));
          image(video, 0, -blurDirection * i, drawWidth, drawHeight);
        }

        noTint();
        popMatrix();

        // Bloom effect - draw a blurred bright overlay
        tint(255, intensity * sharedState.config.bloomIntensity); // Subtle bloom
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
    rect(10, 10, 600, 580);

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

    // Audio info
    Floor floor = sharedState.floors.get(videoIdx);
    if (floor != null && floor.audio != null) {
      text("Audio File: " + floor.audioName, 20, y); y += lineHeight;
      text("Audio Playing: " + floor.audio.isPlaying(), 20, y); y += lineHeight;
    } else {
      text("Audio File: none", 20, y); y += lineHeight;
    }

    y += 5;
    fill(255, 200, 100);
    text("=== AUDIO MIXING ===", 20, y); y += lineHeight;
    fill(255);
    text("Master Volume: " + nf(sharedState.masterVolume * 100, 0, 0) + "% (scroll to adjust)", 20, y); y += lineHeight;
    text("Active floors: " + (sharedState.isAnimating ? "transitioning" : NUM_WINDOWS), 20, y); y += lineHeight;

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
    fill(100, 255, 100);
    text("=== CONFIG (press R to reload) ===", 20, y); y += lineHeight;
    fill(255);
    text("Speed: " + nf(sharedState.config.animationSpeed, 0, 2) +
         " | Chromatic: " + nf(sharedState.config.chromaticIntensity, 0, 1), 20, y); y += lineHeight;
    text("Blur samples: " + sharedState.config.motionBlurSamples +
         " | Blur intensity: " + nf(sharedState.config.motionBlurIntensity, 0, 1), 20, y); y += lineHeight;
    text("Bloom: " + nf(sharedState.config.bloomIntensity, 0, 1) +
         " | Max FX: " + nf(sharedState.config.maxEffectIntensity, 0, 2), 20, y); y += lineHeight;

    y += 5;
    fill(100);
    text("Press D to hide | F for fullscreen | R to reload config | Scroll for volume", 20, y);
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
    } else if (key == 'r' || key == 'R') {
      println("\nReloading transition configuration...");
      sharedState.config.loadFromFile(sharedState.parent);
      println("Configuration reloaded!");
    }
  }

  public void mouseWheel(MouseEvent event) {
    float delta = event.getCount();
    sharedState.masterVolume = constrain(sharedState.masterVolume - delta * 0.05, 0.0, 1.0);
    println("Master volume: " + nf(sharedState.masterVolume * 100, 0, 0) + "%");
  }
}
