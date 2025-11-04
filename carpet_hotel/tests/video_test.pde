// Minimal video test sketch
import processing.video.*;

Movie video;
int frameCount = 0;

void setup() {
  size(640, 480);
  println("Setup starting...");

  video = new Movie(this, "carpet1.mp4");
  println("Video object created");
  println("Video duration: " + video.duration());

  video.loop();
  video.play();
  println("Video started playing");

  println("Setup complete!");
}

void draw() {
  frameCount++;

  if (frameCount <= 30) {
    println("Frame " + frameCount +
            " | available: " + video.available() +
            " | dims: " + video.width + "x" + video.height +
            " | time: " + video.time());
  }

  background(0);

  if (video.available()) {
    video.read();
  }

  if (video.width > 0 && video.height > 0) {
    image(video, 0, 0, width, height);

    // Green indicator that video is displaying
    fill(0, 255, 0);
    rect(10, 10, 50, 50);

    fill(255);
    text("Video playing", 70, 35);
    text("Frame: " + frameCount, 70, 50);
  } else {
    fill(255);
    textAlign(CENTER, CENTER);
    text("Waiting for video...", width/2, height/2);
  }
}

void movieEvent(Movie m) {
  m.read();
}
