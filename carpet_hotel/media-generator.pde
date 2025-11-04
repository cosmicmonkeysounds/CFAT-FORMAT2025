/**
 * MEDIA GENERATOR - Video Installation
 * A virtual hotel where each floor contains a looping carpet video
 * Use alphanumeric keys to switch between floors
 */

import gohai.glvideo.*;

// Global timer (in seconds)
float globalTime = 0;
float startTime;

// Floor data
ArrayList<Floor> floors;
int currentFloorIndex = 0;

// Video folder path - UPDATE THIS to your folder location
String videoFolderPath = "carpets/";

void setup() {
  size(1280, 720, P3D); // P3D renderer for GPU acceleration
  background(0);
  
  // Initialize global timer
  startTime = millis() / 1000.0;
  
  // Load all carpet videos
  floors = new ArrayList<Floor>();
  loadCarpetVideos();
  
  if (floors.size() == 0) {
    println("ERROR: No carpet videos found!");
    println("Place videos named carpet1.mp4, carpet2.mp4, etc. in: " + videoFolderPath);
  } else {
    println("Loaded " + floors.size() + " floors");
    println("Press keys 1-9, 0, A-Z to switch floors");
    println("Press SPACE to show current floor info");
  }
}

void draw() {
  // Update global timer
  globalTime = (millis() / 1000.0) - startTime;
  
  background(0);
  
  if (floors.size() > 0) {
    Floor currentFloor = floors.get(currentFloorIndex);
    currentFloor.display(globalTime);
  } else {
    // Show error message
    fill(255);
    textAlign(CENTER, CENTER);
    textSize(24);
    text("No carpet videos found!", width/2, height/2);
    textSize(16);
    text("Place videos in: " + videoFolderPath, width/2, height/2 + 40);
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
    return;
  }
  
  // Switch floor if valid
  if (newFloor >= 0 && newFloor < floors.size()) {
    currentFloorIndex = newFloor;
    println("Switched to floor " + currentFloorIndex + ": " + floors.get(currentFloorIndex).name);
  }
}

void loadCarpetVideos() {
  // Try to load videos with different extensions
  String[] extensions = {".mp4", ".mov", ".MP4", ".MOV"};
  
  int videoIndex = 1;
  boolean foundVideo = true;
  
  while (foundVideo) {
    foundVideo = false;
    
    for (String ext : extensions) {
      String filename = "carpet" + videoIndex + ext;
      String filepath = videoFolderPath + filename;
      
      // Check if file exists by trying to load it
      try {
        GLMovie movie = new GLMovie(this, filepath);
        if (movie != null) {
          Floor floor = new Floor(filename, movie);
          floors.add(floor);
          println("Loaded: " + filename + " (duration: " + floor.duration + "s)");
          foundVideo = true;
          break; // Found this index, move to next
        }
      } catch (Exception e) {
        // File doesn't exist, continue
      }
    }
    
    videoIndex++;
    
    // Safety limit
    if (videoIndex > 100) break;
  }
}

/**
 * Floor class - represents one floor/video in the hotel
 */
class Floor {
  String name;
  GLMovie video;
  float duration; // in seconds
  
  Floor(String name, GLMovie video) {
    this.name = name;
    this.video = video;
    
    // Start the video playing and looping
    this.video.loop();
    
    // Get duration
    this.duration = this.video.duration();
    
    // If duration is 0 or invalid, set a default
    if (this.duration <= 0) {
      this.duration = 10.0; // default 10 seconds
      println("WARNING: Could not get duration for " + name + ", using default");
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
    // GLVideo reads frames automatically, no need for available() or read()
    
    // Calculate where we should be in the loop
    float loopTime = getLoopTime(globalTime);
    
    // Draw the video as a texture
    imageMode(CENTER);
    
    // Scale video to fit screen while maintaining aspect ratio
    float videoAspect = (float)video.width / (float)video.height;
    float screenAspect = (float)width / (float)height;
    
    float drawWidth, drawHeight;
    
    if (videoAspect > screenAspect) {
      // Video is wider than screen
      drawWidth = width;
      drawHeight = width / videoAspect;
    } else {
      // Video is taller than screen
      drawHeight = height;
      drawWidth = height * videoAspect;
    }
    
    // Draw video texture
    image(video, width/2, height/2, drawWidth, drawHeight);
    
    // Draw floor info overlay
    drawOverlay(loopTime);
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
