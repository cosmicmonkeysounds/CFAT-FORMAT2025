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

// Video folder path - UPDATE THIS if your videos are in a subfolder
// "" = videos directly in data folder (data/carpet1.mp4)
// "carpets/" = videos in subfolder (data/carpets/carpet1.mp4)
String videoFolderPath = "";

void setup() {
  size(1280, 720, P3D); // P3D renderer for shader support
  pixelDensity(1); // Explicitly set to 1 to avoid high-density display issues
  background(0);

  // Initialize global timer
  startTime = millis() / 1000.0;
  
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
    println("Press keys 1-9, 0, A-Z to switch floors");
    println("Press SPACE to show current floor info");

    // Start playing the first video
    floors.get(0).startPlaying();
    println("Setup complete!");
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
  // Letters A-Z (case insensitive)
  else if ((key >= 'a' && key <= 'z') || (key >= 'A' && key <= 'Z')) {
    char upperKey = Character.toUpperCase(key);
    newFloor = 10 + (upperKey - 'A');
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
  // 'd' key - debug mode
  else if (key == 'd' || key == 'D') {
    println("\n=== DEBUG INFO ===");
    println("Current Floor: " + currentFloorIndex);
    println("Total Floors: " + floors.size());
    println("Global Time: " + globalTime);
    Floor f = floors.get(currentFloorIndex);
    println("Loaded: " + f.isLoaded);
    if (f.isLoaded) {
      println("Current video playing: " + (f.video.time() > 0));
      println("Current video time: " + f.video.time());
      println("Video width: " + f.video.width + ", height: " + f.video.height);
    }
    println("Frame rate: " + frameRate);
    return;
  }
  
  // Switch floor if valid
  if (newFloor >= 0 && newFloor < floors.size()) {
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

      // Draw the video scaled to fit screen
      imageMode(CORNER);

      // Scale video to fit screen while maintaining aspect ratio
      float videoAspect = (float)video.width / (float)video.height;
      float screenAspect = (float)width / (float)height;

      float drawWidth, drawHeight;
      float drawX = 0, drawY = 0;

      if (videoAspect > screenAspect) {
        // Video is wider than screen
        drawWidth = width;
        drawHeight = width / videoAspect;
        drawY = (height - drawHeight) / 2;
      } else {
        // Video is taller than screen
        drawHeight = height;
        drawWidth = height * videoAspect;
        drawX = (width - drawWidth) / 2;
      }

      // Draw video
      image(video, drawX, drawY, drawWidth, drawHeight);

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
    fill(0, 180);
    noStroke();
    rect(10, 10, 300, 90);
    
    fill(255);
    textAlign(LEFT, TOP);
    textSize(16);
    text("Floor: " + currentFloorIndex, 20, 20);
    text("Name: " + name, 20, 40);
    text("Loop: " + nf(loopTime, 0, 2) + " / " + nf(duration, 0, 2) + "s", 20, 60);
    text("Global: " + nf(globalTime, 0, 2) + "s", 20, 80);
  }
}
