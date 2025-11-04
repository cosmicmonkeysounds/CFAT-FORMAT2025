# Random Test Video Generator

Generate unique 1920x1080 MP4 videos with random colors and shader-like effects for testing video applications.

## Features

- **Random solid colors** - Each video gets a unique base color
- **Shader-like effects** - Random noise, scanlines, chromatic aberration, grain, and vignettes
- **Fast generation** - Efficient numpy operations keep rendering quick
- **Truly unique** - Each video has different visual characteristics

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Generate 10 test videos:
```bash
python generate_test_videos.py 10
```

### Custom Options
```bash
# Generate 5 videos in custom directory
python generate_test_videos.py 5 -o my_test_videos

# Generate 720p videos at 60fps
python generate_test_videos.py 10 -w 1280 -H 720 -f 60

# Generate 5-second videos
python generate_test_videos.py 3 -d 5
```

### All Options
```
positional arguments:
  n                     Number of videos to generate

options:
  -h, --help            Show help message
  -o, --output-dir DIR  Output directory (default: test_videos)
  -w, --width WIDTH     Video width (default: 1920)
  -H, --height HEIGHT   Video height (default: 1080)
  -f, --fps FPS         Frames per second (default: 30)
  -d, --duration SEC    Duration in seconds (default: 1)
```

## Output

Videos are saved as `test_video_0001.mp4`, `test_video_0002.mp4`, etc. in the output directory.

Each video includes randomized:
- Base color (RGB)
- Noise patterns
- Scanline effects
- Chromatic aberration
- Film grain
- Vignetting

Perfect for testing video players, encoders, and upload systems!
