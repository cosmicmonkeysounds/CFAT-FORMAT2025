# Random Test Video Generator

Generate unique 1920x1080 MP4 videos with random colors and shader-like effects for testing video applications.

## Features

- **Random solid colors** - Each video gets a unique base color
- **Shader-like effects** - Random noise, scanlines, chromatic aberration, grain, and vignettes
- **Fast generation** - Efficient numpy operations keep rendering quick
- **Truly unique** - Each video has different visual characteristics
- **Custom naming** - Set your own base name for the videos
- **No leading zeros** - Clean numbering: 1, 2, 3... 10, 20, 100 (not 01, 02, 010)
- **Smart conflict handling** - Detects existing files and lets you overwrite or continue

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

# Custom base name for videos
python generate_test_videos.py 10 --name my_video

# Generate 720p videos at 60fps
python generate_test_videos.py 10 -w 1280 -H 720 -f 60

# Generate 5-second videos with custom name
python generate_test_videos.py 3 -d 5 --name long_test
```

### All Options
```
positional arguments:
  n                     Number of videos to generate

options:
  -h, --help            Show help message
  -n, --name NAME       Base name for video files (default: test_video)
  -o, --output-dir DIR  Output directory (default: test_videos)
  -w, --width WIDTH     Video width (default: 1920)
  -H, --height HEIGHT   Video height (default: 1080)
  -f, --fps FPS         Frames per second (default: 30)
  -d, --duration SEC    Duration in seconds (default: 1)
```

## Output

Videos are saved with clean sequential numbering: `test_video_1.mp4`, `test_video_2.mp4`, ..., `test_video_10.mp4`, `test_video_20.mp4`, etc.

**No leading zeros** - Numbers are natural: 1, 2, 3, 10, 100 (not 01, 02, 03, 010, 0100)

### Conflict Handling
If videos with the same naming pattern already exist, you'll be prompted:
```
⚠️  Found existing videos matching pattern 'carpet_*.mp4'
    Highest number found: 15

Options:
  1) Overwrite - Start from 1 (will overwrite existing files)
  2) Continue - Start from 16 (preserve existing files)

Enter choice (1 or 2):
```

This lets you safely add more test videos without losing your existing ones!

Each video includes randomized:
- Base color (RGB)
- Noise patterns
- Scanline effects
- Chromatic aberration
- Film grain
- Vignetting

Perfect for testing video players, encoders, and upload systems!
