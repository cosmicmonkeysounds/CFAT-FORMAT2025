/**
 * CARPET HOTEL - Multi-Window Video Installation
 * Creates separate windows for each display, each showing one floor
 * Scene switching is synchronized across all windows
 */

import processing.video.*;
import java.io.File;

// Configuration
int NUM_WINDOWS = 2;              // Number of separate windows
int[] DISPLAY_NUMBERS = {1, 2};   // Which display for each window
int VIDEO_WIDTH = 1920;
int VIDEO_HEIGHT = 1080;

// Shared state across all windows
static SharedState sharedState;

void setup() {
  // Create tiny control window
  size(400, 300);
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
  println("\nCONTROLS (use control window):");
  println("1-9, 0: Switch to scene");
  println("UP/DOWN: Navigate scenes");
  println("D: Toggle debug panel");
  println("SPACE: Print scene info");
  println("ESC: Close all windows");
}

void draw() {
  // Update shared state once per frame
  sharedState.update();

  background(40);
  fill(255);
  textAlign(LEFT, TOP);
  textSize(14);

  int y = 20;
  text("=== CARPET HOTEL CONTROL ===", 20, y); y += 30;
  text("Scene: " + sharedState.currentSceneIndex + " / " + (sharedState.numScenes - 1), 20, y); y += 25;
  text("Windows: " + NUM_WINDOWS, 20, y); y += 25;

  y += 10;
  for (int i = 0; i < NUM_WINDOWS; i++) {
    int floorIdx = sharedState.currentSceneIndex + i;
    if (floorIdx < sharedState.floors.size()) {
      Floor f = sharedState.floors.get(floorIdx);
      text("Window " + i + " -> Floor " + floorIdx + ": " + f.name, 20, y);
      y += 20;
    }
  }

  y += 20;
  text("Press 1-9 to switch scenes", 20, y); y += 20;
  text("Press UP/DOWN to navigate", 20, y); y += 20;
  text("Press D to toggle debug", 20, y); y += 20;
}

void keyPressed() {
  sharedState.handleKey(key, keyCode);
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
  ArrayList<Floor> floors;
  ArrayList<String> videoFilenames;
  int currentSceneIndex = 0;
  int numScenes = 0;

  float globalTime = 0;
  float startTime;

  boolean showDebugPanel = false;

  // Animation
  boolean isAnimating = false;
  int targetSceneIndex = 0;
  float cameraYOffset = 0;
  float targetCameraY = 0;
  float animationSpeed = 0.08;

  PApplet parent;

  void init(PApplet p) {
    parent = p;
    startTime = p.millis() / 1000.0;

    // Find videos
    videoFilenames = new ArrayList<String>();
    findCarpetVideos();

    // Create floors
    floors = new ArrayList<Floor>();
    if (videoFilenames.size() > 0) {
      // Load first NUM_WINDOWS videos
      for (int i = 0; i < videoFilenames.size(); i++) {
        if (i < NUM_WINDOWS) {
          Movie movie = new Movie(parent, videoFilenames.get(i));
          floors.add(new Floor(videoFilenames.get(i), movie, i));
        } else {
          floors.add(new Floor(videoFilenames.get(i), null, i));
        }
      }

      numScenes = max(1, floors.size() - NUM_WINDOWS + 1);
      println("Loaded " + floors.size() + " floors, " + numScenes + " scenes");

      // Start first videos
      for (int i = 0; i < min(NUM_WINDOWS, floors.size()); i++) {
        floors.get(i).startPlaying();
      }
    }
  }

  void update() {
    globalTime = (parent.millis() / 1000.0) - startTime;

    // Update animation
    if (isAnimating) {
      float diff = targetCameraY - cameraYOffset;
      cameraYOffset += diff * animationSpeed;

      if (abs(diff) < 0.5) {
        cameraYOffset = targetCameraY;
        isAnimating = false;
        currentSceneIndex = targetSceneIndex;
        println("Arrived at scene " + currentSceneIndex);
      }
    }

    // Manage video playback
    for (int i = 0; i < floors.size(); i++) {
      int minVisible = max(0, currentSceneIndex - 1);
      int maxVisible = min(floors.size() - 1, currentSceneIndex + NUM_WINDOWS);
      boolean isVisible = (i >= minVisible && i <= maxVisible);

      if (isVisible) {
        if (floors.get(i).isLoaded && floors.get(i).video != null) {
          floors.get(i).video.play();
        }
      } else {
        if (floors.get(i).isLoaded && floors.get(i).video != null) {
          floors.get(i).video.pause();
        }
      }
    }
  }

  void handleKey(char k, int kc) {
    if (floors.size() == 0) return;

    // Toggle debug
    if (k == 'd' || k == 'D') {
      showDebugPanel = !showDebugPanel;
      println("Debug panel: " + (showDebugPanel ? "ON" : "OFF"));
      return;
    }

    // Scene info
    if (k == ' ') {
      println("\n=== SCENE " + currentSceneIndex + " ===");
      for (int i = 0; i < NUM_WINDOWS; i++) {
        int floorIdx = currentSceneIndex + i;
        if (floorIdx < floors.size()) {
          println("  Window " + i + " -> Floor " + floorIdx + ": " + floors.get(floorIdx).name);
        }
      }
      return;
    }

    // Navigate scenes
    int newScene = -1;

    if (k >= '1' && k <= '9') {
      newScene = k - '1';
    } else if (k == '0') {
      newScene = 9;
    } else if (k == CODED) {
      if (kc == UP) {
        newScene = currentSceneIndex + 1;
        if (newScene >= numScenes) newScene = numScenes - 1;
      } else if (kc == DOWN) {
        newScene = currentSceneIndex - 1;
        if (newScene < 0) newScene = 0;
      }
    }

    if (newScene >= 0 && newScene < numScenes && newScene != currentSceneIndex) {
      startSceneTransition(newScene);
    }
  }

  void startSceneTransition(int newScene) {
    println("Transitioning to scene " + newScene);
    targetSceneIndex = newScene;

    int sceneDiff = newScene - currentSceneIndex;
    targetCameraY = cameraYOffset - (sceneDiff * VIDEO_HEIGHT);

    isAnimating = true;

    // Load videos for new scene
    for (int i = 0; i < NUM_WINDOWS; i++) {
      int floorIdx = newScene + i;
      if (floorIdx < floors.size()) {
        floors.get(floorIdx).ensureLoaded(parent);
        floors.get(floorIdx).startPlaying();
      }
    }
  }

  void findCarpetVideos() {
    String[] extensions = {".mp4", ".mov", ".MP4", ".MOV"};
    String[] patterns = {"carpet", "carpet_"};

    int videoIndex = 1;
    boolean foundVideo = true;

    while (foundVideo) {
      foundVideo = false;

      for (String pattern : patterns) {
        for (String ext : extensions) {
          String filename = pattern + videoIndex + ext;
          File f = new File(parent.dataPath(filename));
          if (f.exists()) {
            videoFilenames.add(filename);
            println("Found: " + filename);
            foundVideo = true;
            break;
          }
        }
        if (foundVideo) break;
      }

      videoIndex++;
      if (videoIndex > 100) break;
    }
  }

  void cleanup() {
    for (Floor f : floors) {
      if (f.isLoaded && f.video != null) {
        f.video.stop();
      }
    }
  }
}

/**
 * Individual floor window
 */
class FloorWindow extends PApplet {
  int windowIndex;

  FloorWindow(int index) {
    this.windowIndex = index;
  }

  public void settings() {
    fullScreen(P3D, DISPLAY_NUMBERS[windowIndex]);
    pixelDensity(1);
  }

  public void setup() {
    background(0);
    surface.setTitle("Carpet Hotel - Window " + windowIndex);
  }

  public void draw() {
    background(0);

    // Calculate which floor to show
    int floorIdx = sharedState.currentSceneIndex + windowIndex;

    if (floorIdx >= 0 && floorIdx < sharedState.floors.size()) {
      Floor floor = sharedState.floors.get(floorIdx);

      // Calculate viewport with letterboxing
      float videoAspect = (float)VIDEO_WIDTH / (float)VIDEO_HEIGHT;
      float screenAspect = (float)width / (float)height;

      float viewportWidth, viewportHeight;

      if (videoAspect > screenAspect) {
        viewportWidth = width;
        viewportHeight = width / videoAspect;
      } else {
        viewportHeight = height;
        viewportWidth = height * videoAspect;
      }

      float scaleX = viewportWidth / VIDEO_WIDTH;
      float scaleY = viewportHeight / VIDEO_HEIGHT;
      float viewportX = (width - viewportWidth) / 2;
      float viewportY = (height - viewportHeight) / 2;

      pushMatrix();
      translate(viewportX, viewportY);
      scale(scaleX, scaleY);
      translate(0, sharedState.cameraYOffset);

      // Render floor
      pushMatrix();
      translate(0, -floorIdx * VIDEO_HEIGHT);
      floor.display(sharedState.globalTime, sharedState.showDebugPanel, sharedState.cameraYOffset, sharedState.targetCameraY, sharedState.isAnimating, sharedState.targetSceneIndex, sharedState.floors.size(), sharedState.currentSceneIndex);
      popMatrix();

      // During animation, render adjacent floor
      if (sharedState.isAnimating) {
        int nextFloorIdx = floorIdx + (sharedState.targetSceneIndex > sharedState.currentSceneIndex ? 1 : -1);
        if (nextFloorIdx >= 0 && nextFloorIdx < sharedState.floors.size()) {
          Floor nextFloor = sharedState.floors.get(nextFloorIdx);
          if (nextFloor.isLoaded) {
            pushMatrix();
            translate(0, -nextFloorIdx * VIDEO_HEIGHT);
            nextFloor.display(sharedState.globalTime, false, 0, 0, false, 0, 0, 0);
            popMatrix();
          }
        }
      }

      popMatrix();
    }
  }
}

/**
 * Floor class
 */
class Floor {
  String name;
  Movie video;
  float duration;
  boolean isLoaded;
  int floorIndex;
  float yPosition;

  Floor(String name, Movie video, int index) {
    this.name = name;
    this.video = video;
    this.isLoaded = (video != null);
    this.floorIndex = index;
    this.yPosition = -index * VIDEO_HEIGHT;

    if (this.isLoaded) {
      this.duration = this.video.duration();
      if (this.duration <= 0) {
        this.duration = 10.0;
        println("WARNING: Could not get duration for " + name + ", using default");
      }
      this.video.loop();
    } else {
      this.duration = 10.0;
    }
  }

  void ensureLoaded(PApplet parent) {
    if (!isLoaded) {
      println("Loading video: " + name);
      this.video = new Movie(parent, name);
      this.duration = this.video.duration();
      if (this.duration <= 0) {
        this.duration = 10.0;
      }
      this.video.loop();
      this.isLoaded = true;
    }
  }

  void startPlaying() {
    if (isLoaded && video != null) {
      video.play();
    }
  }

  void stopPlaying() {
    if (isLoaded && video != null) {
      video.pause();
    }
  }

  float getLoopTime(float globalTime) {
    return globalTime % duration;
  }

  void display(float globalTime, boolean showDebug, float cameraY, float targetY, boolean animating, int targetScene, int totalFloors, int currentScene) {
    if (!isLoaded || video == null) {
      fill(50);
      rectMode(CORNER);
      rect(0, 0, VIDEO_WIDTH, VIDEO_HEIGHT);
      fill(255);
      textAlign(CENTER, CENTER);
      textSize(20);
      text("Floor " + floorIndex + " - Not loaded", VIDEO_WIDTH/2, VIDEO_HEIGHT/2);
      return;
    }

    if (video.available()) {
      video.read();
    }

    if (video.width > 0 && video.height > 0) {
      float loopTime = getLoopTime(globalTime);

      // Draw video
      imageMode(CORNER);
      float videoAspect = (float)video.width / (float)video.height;
      float sceneAspect = (float)VIDEO_WIDTH / (float)VIDEO_HEIGHT;

      float drawWidth, drawHeight;
      float drawX = 0, drawY = 0;

      if (videoAspect > sceneAspect) {
        drawHeight = VIDEO_HEIGHT;
        drawWidth = VIDEO_HEIGHT * videoAspect;
        drawX = (VIDEO_WIDTH - drawWidth) / 2;
      } else {
        drawWidth = VIDEO_WIDTH;
        drawHeight = VIDEO_WIDTH / videoAspect;
        drawY = (VIDEO_HEIGHT - drawHeight) / 2;
      }

      image(video, drawX, drawY, drawWidth, drawHeight);

      // Debug overlay
      if (showDebug) {
        int playingCount = 0;
        int loadedCount = 0;
        for (Floor f : sharedState.floors) {
          if (f.isLoaded) {
            loadedCount++;
            try {
              if (f.video != null && f.video.isPlaying()) playingCount++;
            } catch (Exception e) {
              if (f.video != null && f.video.time() > 0) playingCount++;
            }
          }
        }

        fill(0, 200);
        noStroke();
        rect(10, 10, 450, 280);

        fill(255);
        textAlign(LEFT, TOP);
        textSize(14);
        int y = 15;
        int lineHeight = 20;

        text("=== CARPET HOTEL DEBUG ===", 20, y); y += lineHeight;
        text("Scene: " + currentScene + " / " + (sharedState.numScenes - 1), 20, y); y += lineHeight;
        text("This floor: " + floorIndex + " (" + name + ")", 20, y); y += lineHeight;
        text("Loop: " + nf(loopTime, 0, 2) + " / " + nf(duration, 0, 2) + "s", 20, y); y += lineHeight;
        text("Global Time: " + nf(globalTime, 0, 2) + "s", 20, y); y += lineHeight;
        y += 5;
        text("Camera Y: " + nf(cameraY, 0, 1), 20, y); y += lineHeight;
        text("Target Y: " + nf(targetY, 0, 1), 20, y); y += lineHeight;
        text("Animating: " + animating, 20, y); y += lineHeight;
        if (animating) {
          text("Target Scene: " + targetScene, 20, y); y += lineHeight;
        }
        y += 5;
        text("Videos Playing: " + playingCount + " / " + loadedCount, 20, y); y += lineHeight;
        text("This Video: " + (isLoaded ? "loaded" : "not loaded"), 20, y); y += lineHeight;
        if (isLoaded && video != null) {
          try {
            text("Playing: " + video.isPlaying(), 20, y); y += lineHeight;
          } catch (Exception e) {
            text("Playing: " + (video.time() > 0), 20, y); y += lineHeight;
          }
        }
        text("Frame Rate: " + nf(frameRate, 0, 1) + " fps", 20, y);
      }
    }
  }
}
