/**
 * CARPET HOTEL - Multi-Window Video Installation
 * Simplified version - each window shows one video
 */

import processing.video.*;
import java.io.File;

// Configuration
int NUM_WINDOWS = 2;              // Number of separate windows
int[] DISPLAY_NUMBERS = {1, 2};   // Which display for each window

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
  println("SPACE: Print info");
  println("ESC: Close all windows");
}

void draw() {
  background(40);
  fill(255);
  textAlign(LEFT, TOP);
  textSize(14);

  int y = 20;
  text("=== CARPET HOTEL CONTROL ===", 20, y); y += 30;
  text("Videos: " + sharedState.videos.size(), 20, y); y += 25;
  text("Current scene: " + sharedState.currentScene, 20, y); y += 25;

  y += 10;
  for (int i = 0; i < NUM_WINDOWS; i++) {
    int videoIdx = sharedState.currentScene + i;
    if (videoIdx < sharedState.videos.size()) {
      text("Window " + i + " -> Video " + videoIdx, 20, y);
      y += 20;
    }
  }
}

void keyPressed() {
  if (key >= '1' && key <= '9') {
    int scene = key - '1';
    if (scene >= 0 && scene < sharedState.getNumScenes()) {
      sharedState.currentScene = scene;
      println("Scene " + scene);
    }
  } else if (key == ' ') {
    println("\n=== SCENE " + sharedState.currentScene + " ===");
    for (int i = 0; i < NUM_WINDOWS; i++) {
      int videoIdx = sharedState.currentScene + i;
      if (videoIdx < sharedState.videos.size()) {
        println("  Window " + i + " -> " + sharedState.videoNames.get(videoIdx));
      }
    }
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

    // Add to list
    for (String filename : foundFiles) {
      videoNames.add(filename);
      println("Found: " + filename);
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

  FloorWindow(int index) {
    this.windowIndex = index;
  }

  public void settings() {
    fullScreen(P2D, DISPLAY_NUMBERS[windowIndex]);
    pixelDensity(1);
  }

  public void setup() {
    background(0);
    surface.setTitle("Carpet Hotel - Window " + windowIndex);
  }

  public void draw() {
    background(0);

    // Calculate which video to show
    int videoIdx = sharedState.currentScene + windowIndex;

    if (videoIdx >= 0 && videoIdx < sharedState.videoNames.size()) {
      // Ensure video is loaded
      sharedState.ensureVideoLoaded(videoIdx);

      Movie video = sharedState.videos.get(videoIdx);

      if (video != null) {
        // Read frame
        if (video.available()) {
          video.read();
        }

        // Draw video
        if (video.width > 0 && video.height > 0) {
          image(video, 0, 0, width, height);

          // Debug indicator
          fill(0, 255, 0);
          noStroke();
          rect(10, 10, 50, 50);
          fill(255);
          text("Window " + windowIndex + " | Video " + videoIdx, 70, 35);
        } else {
          // Waiting for video
          fill(255);
          textAlign(CENTER, CENTER);
          text("Loading video...", width/2, height/2);
        }
      } else {
        // Video not loaded
        fill(255);
        textAlign(CENTER, CENTER);
        text("Video " + videoIdx + " not loaded", width/2, height/2);
      }
    } else {
      // No video for this window
      fill(255);
      textAlign(CENTER, CENTER);
      text("No video", width/2, height/2);
    }
  }

  public void keyPressed() {
    if (key >= '1' && key <= '9') {
      int scene = key - '1';
      if (scene >= 0 && scene < sharedState.getNumScenes()) {
        sharedState.currentScene = scene;
        println("Scene " + scene);
      }
    } else if (key == ' ') {
      println("\n=== SCENE " + sharedState.currentScene + " ===");
      for (int i = 0; i < NUM_WINDOWS; i++) {
        int vIdx = sharedState.currentScene + i;
        if (vIdx < sharedState.videoNames.size()) {
          println("  Window " + i + " -> " + sharedState.videoNames.get(vIdx));
        }
      }
    }
  }
}
