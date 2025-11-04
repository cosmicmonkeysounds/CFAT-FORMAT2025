/**
 * CARPET HOTEL - Video Installation
 * A virtual hotel where each floor contains a looping carpet video
 * Use alphanumeric keys to switch between floors
 */

import processing.video.*;
import java.io.File;

// Global timer (in seconds)
float globalTime = 0;
float startTime;
int frameCounter = 0;  // Track frames for debugging

// Floor data
ArrayList<Floor> floors;
int currentFloorIndex = 0;
ArrayList<String> videoFilenames; // Store filenames, load videos on demand

// Display settings
boolean showDebugPanel = false;  // Toggle with 'd' key
boolean isFullscreen = false;    // Toggle with 'f' key

// Video folder path - UPDATE THIS if your videos are in a subfolder
// "" = videos directly in data folder (data/carpet1.mp4)
// "carpets/" = videos in subfolder (data/carpets/carpet1.mp4)
String videoFolderPath = "";

// Display configuration
// 1 = primary display, 2 = second display, 3 = third display, etc.
// To see available displays, uncomment the line in setup() that prints display info
int DISPLAY_NUMBER = 2;  // ← CHANGE THIS to select which screen to use (1, 2, 3, etc.)

void setup() {
  // Start in fullscreen mode on specified display
  fullScreen(P3D, DISPLAY_NUMBER);
  pixelDensity(1); // Explicitly set to 1 to avoid high-density display issues
  background(0);

  isFullscreen = true; // Track that we started in fullscreen

  // Initialize global timer
  startTime = millis() / 1000.0;

  // Display info
  println("=== DISPLAY INFO ===");
  println("Using display " + DISPLAY_NUMBER);
  println("Display size: " + displayWidth + "x" + displayHeight);
  println("");
  
  // Find all carpet video filenames (don't load them yet)
  videoFilenames = new ArrayList<String>();
  findCarpetVideos();

  // Create Floor objects but only load first video
  floors = new ArrayList<Floor>();
  if (videoFilenames.size() > 0) {
    // Load only the first video
    Movie firstMovie = new Movie(this, videoFilenames.get(0));
    Floor firstFloor = new Floor(videoFilenames.get(0), firstMovie);
    floors.add(firstFloor);

    // Create placeholder floors for the rest
    for (int i = 1; i < videoFilenames.size(); i++) {
      floors.add(new Floor(videoFilenames.get(i), null));
    }
  }

  if (videoFilenames.size() == 0) {
    println("ERROR: No carpet videos found!");
    println("Place videos in the data folder with one of these naming patterns:");
    println("  - carpet1.mp4, carpet2.mp4, etc.");
    println("  - carpet_1.mp4, carpet_2.mp4, etc.");
    if (!videoFolderPath.equals("")) {
      println("Looking in subfolder: data/" + videoFolderPath);
    } else {
      println("Looking in: data/ folder");
    }
  } else {
    println("Found " + videoFilenames.size() + " video files");
    println("Loaded 1 video (others will load on demand)");
    println("\n=== CONTROLS ===");
    println("1-9, 0, A-Z: Switch floors");
    println("UP/DOWN arrows: Navigate floors");
    println("D: Toggle debug panel");
    println("F or ESC: Exit fullscreen (restart to return to fullscreen)");
    println("SPACE: Print current floor info");

    // Start playing the first video
    floors.get(0).startPlaying();
    println("\nSetup complete! Running in FULLSCREEN mode.");
  }
}

void draw() {
  // Update global timer
  globalTime = (millis() / 1000.0) - startTime;
  frameCounter++;

  background(0);

  if (floors.size() > 0) {
    Floor currentFloor = floors.get(currentFloorIndex);
    currentFloor.display(globalTime);
  } else {
    // Show error message
    fill(255);
    textAlign(CENTER, CENTER);
    textSize(24);
    text("No carpet videos found!", width/2, height/2 - 30);
    textSize(16);
    text("Place videos in data/ folder:", width/2, height/2 + 10);
    text("carpet1.mp4 or carpet_1.mp4", width/2, height/2 + 35);
  }
}

void keyPressed() {
  if (floors.size() == 0) return;

  // Check for special function keys FIRST (before A-Z handler catches them)

  // 'd' key - toggle debug panel
  if (key == 'd' || key == 'D') {
    showDebugPanel = !showDebugPanel;
    println("Debug panel: " + (showDebugPanel ? "ON" : "OFF"));
    return;
  }
  // 'f' or ESC key - exit fullscreen to windowed mode
  else if (key == 'f' || key == 'F' || key == ESC) {
    if (key == ESC) {
      key = 0; // Prevent Processing from auto-exiting on ESC
    }

    if (isFullscreen) {
      // Exit fullscreen to windowed mode
      isFullscreen = false;
      surface.setSize(1280, 720);
      // Center window
      surface.setLocation((displayWidth - 1280) / 2, (displayHeight - 720) / 2);
      println("Switched to windowed mode (1280x720)");
      println("Note: Restart sketch to return to fullscreen");
    } else {
      println("Already in windowed mode. Restart sketch for fullscreen.");
    }
    return;
  }
  // Space bar - show info
  else if (key == ' ') {
    Floor currentFloor = floors.get(currentFloorIndex);
    println("\n=== CURRENT FLOOR INFO ===");
    println("Floor: " + currentFloorIndex);
    println("Name: " + currentFloor.name);
    println("Duration: " + currentFloor.duration + " seconds");
    println("Global Time: " + globalTime + " seconds");
    println("Loop Time: " + currentFloor.getLoopTime(globalTime) + " seconds");
    println("Loaded: " + currentFloor.isLoaded);
    if (currentFloor.isLoaded) {
      println("Video dimensions: " + currentFloor.video.width + "x" + currentFloor.video.height);
    }
    return;
  }

  // Map keys to floor indices
  int newFloor = -1;

  // Numbers 1-9
  if (key >= '1' && key <= '9') {
    newFloor = key - '1';
  }
  // Number 0
  else if (key == '0') {
    newFloor = 9;
  }
  // Letters A-Z (case insensitive) - for floors 10+
  else if ((key >= 'a' && key <= 'z') || (key >= 'A' && key <= 'Z')) {
    char upperKey = Character.toUpperCase(key);
    newFloor = 10 + (upperKey - 'A');
  }

  // Handle arrow keys (keyCode for special keys)
  if (key == CODED) {
    if (keyCode == UP) {
      // Go UP to higher floor number
      newFloor = currentFloorIndex + 1;
      if (newFloor >= floors.size()) newFloor = floors.size() - 1; // Clamp to max
    } else if (keyCode == DOWN) {
      // Go DOWN to lower floor number
      newFloor = currentFloorIndex - 1;
      if (newFloor < 0) newFloor = 0; // Clamp to 0
    }
  }

  // Switch floor if valid and different from current
  if (newFloor >= 0 && newFloor < floors.size() && newFloor != currentFloorIndex) {
    // Stop current video
    floors.get(currentFloorIndex).stopPlaying();

    // Switch to new floor
    currentFloorIndex = newFloor;

    // Start new video
    floors.get(currentFloorIndex).startPlaying();

    println("Switched to floor " + currentFloorIndex + ": " + floors.get(currentFloorIndex).name);
  }
}

void findCarpetVideos() {
  // Find all carpet video files without loading them
  String[] extensions = {".mp4", ".mov", ".MP4", ".MOV"};
  String[] patterns = {"carpet", "carpet_"}; // Support both carpet1 and carpet_1

  int videoIndex = 1;
  boolean foundVideo = true;

  while (foundVideo) {
    foundVideo = false;

    // Try each naming pattern
    for (String pattern : patterns) {
      for (String ext : extensions) {
        String filename = pattern + videoIndex + ext;
        String filepath = videoFolderPath + filename;

        // Check if file exists
        File f = new File(dataPath(filepath));
        if (f.exists()) {
          videoFilenames.add(filepath);
          println("Found: " + filename);
          foundVideo = true;
          break; // Found this index, move to next
        }
      }
      if (foundVideo) break; // Found video with this pattern, move to next index
    }

    videoIndex++;

    // Safety limit
    if (videoIndex > 100) break;
  }
}

// Called by Processing when movie is ready
void movieEvent(Movie m) {
  m.read();
}

/**
 * Floor class - represents one floor/video in the hotel
 */
class Floor {
  String name;
  Movie video;
  float duration; // in seconds
  boolean isLoaded;

  Floor(String name, Movie video) {
    this.name = name;
    this.video = video;
    this.isLoaded = (video != null);

    if (this.isLoaded) {
      // Get duration
      this.duration = this.video.duration();

      // If duration is 0 or invalid, set a default
      if (this.duration <= 0) {
        this.duration = 10.0; // default 10 seconds
        println("WARNING: Could not get duration for " + name + ", using default");
      }

      // Set to loop mode but don't start playing yet
      this.video.loop();
    } else {
      // Placeholder - will be loaded on demand
      this.duration = 10.0;
    }
  }

  // Load this video if not already loaded
  void ensureLoaded() {
    if (!isLoaded) {
      println("Loading video: " + name);
      this.video = new Movie(carpet_hotel.this, name);

      // Get duration
      this.duration = this.video.duration();
      if (this.duration <= 0) {
        this.duration = 10.0;
        println("WARNING: Could not get duration for " + name + ", using default");
      }

      // Set to loop mode
      this.video.loop();
      this.isLoaded = true;
    }
  }

  // Start playing this video
  void startPlaying() {
    ensureLoaded();
    println("Starting video: " + name);
    this.video.play();
  }

  // Stop playing this video
  void stopPlaying() {
    if (isLoaded && video != null) {
      this.video.pause();
    }
  }
  
  /**
   * Calculate the loop time for this video based on global time
   * Uses modulus to find position within the loop
   */
  float getLoopTime(float globalTime) {
    return globalTime % duration;
  }
  
  /**
   * Display this floor's video
   */
  void display(float globalTime) {
    // Make sure video is loaded
    if (!isLoaded || video == null) {
      fill(255);
      textAlign(CENTER, CENTER);
      textSize(20);
      text("Video not loaded", width/2, height/2);
      return;
    }

    // Read video frame if available (like in working test)
    if (video.available()) {
      video.read();
    }

    // Check if video has valid dimensions
    if (video.width > 0 && video.height > 0) {
      // Calculate where we should be in the loop
      float loopTime = getLoopTime(globalTime);

      // Draw the video centered with letterboxing (black bars)
      imageMode(CENTER);

      // Calculate aspect ratios
      float videoAspect = (float)video.width / (float)video.height;
      float screenAspect = (float)width / (float)height;

      float drawWidth, drawHeight;

      // CONTAIN mode: Scale to fit within screen, add black bars as needed
      if (videoAspect > screenAspect) {
        // Video is wider than screen - fit to width, black bars top/bottom
        drawWidth = width;
        drawHeight = width / videoAspect;
      } else {
        // Video is taller than screen - fit to height, black bars left/right
        drawHeight = height;
        drawWidth = height * videoAspect;
      }

      // Draw video centered (black bars fill remaining space naturally)
      image(video, width/2, height/2, drawWidth, drawHeight);

      // Draw floor info overlay
      drawOverlay(loopTime);
    } else {
      // Video not ready yet, show loading message
      fill(255);
      textAlign(CENTER, CENTER);
      textSize(20);
      text("Loading video...", width/2, height/2);
    }
  }
  
  /**
   * Draw UI overlay with floor information
   */
  void drawOverlay(float loopTime) {
    if (showDebugPanel) {
      // Extended debug panel
      fill(0, 200);
      noStroke();
      rect(10, 10, 400, 220);

      fill(255);
      textAlign(LEFT, TOP);
      textSize(16);
      int y = 20;
      int lineHeight = 22;

      text("=== CARPET HOTEL DEBUG ===", 20, y); y += lineHeight;
      text("Floor: " + currentFloorIndex + " / " + (floors.size() - 1), 20, y); y += lineHeight;
      text("Name: " + name, 20, y); y += lineHeight;
      text("Loop: " + nf(loopTime, 0, 2) + " / " + nf(duration, 0, 2) + "s", 20, y); y += lineHeight;
      text("Global Time: " + nf(globalTime, 0, 2) + "s", 20, y); y += lineHeight;
      text("Loaded: " + isLoaded, 20, y); y += lineHeight;
      if (isLoaded && video != null) {
        text("Video Time: " + nf(video.time(), 0, 2) + "s", 20, y); y += lineHeight;
        text("Video Dims: " + video.width + "x" + video.height, 20, y); y += lineHeight;
        text("Playing: " + (video.time() > 0), 20, y); y += lineHeight;
      }
      text("Frame Rate: " + nf(frameRate, 0, 1) + " fps", 20, y); y += lineHeight;
    }
    // No overlay when debug panel is off - clean video display
  }
}
