# Technical Guide

**For technical artists, developers, and contributors**

## Table of Contents

- [Installation](#installation)
- [Command Line Reference](#command-line-reference)
- [Advanced Usage](#advanced-usage)
- [Project Architecture](#project-architecture)
- [Development](#development)
- [Building & Distribution](#building--distribution)

## Installation

### Method 1: Smart Launcher (Recommended)

No manual installation needed:

```bash
# macOS/Linux
./run-macos-linux.sh --help

# Windows
run-windows.bat --help
```

The launcher automatically:
- Detects and installs Python if needed
- Creates virtual environment in `venv/`
- Installs all dependencies (including bundled ffmpeg)
- Runs the program

**First run:** ~30 seconds setup
**Subsequent runs:** Instant startup

### Method 2: Python Package Install

```bash
pip3 install -e .
media-generator 10 -t mp4
mediagen 10 -t wav  # Short alias
```

### Method 3: Run from Source

```bash
pip3 install -r requirements.txt
python3 -m media_generator 10 -t mp4
```

## Command Line Reference

### Basic Syntax

```bash
./run-macos-linux.sh [count] [options]
```

### Core Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `count` | int | - | Number of files to generate |
| `-t, --type` | str | mp4 | Media type: mp4, jpg, png, webp, bmp, tiff, svg, gif, wav, ogg, mp3, m4a, flac |
| `-o, --output-dir` | path | test_media | Output directory |
| `-n, --name` | str | test_media | Base filename |

### Video Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-w, --width` | int | 1280 | Video/image width |
| `-H, --height` | int | 720 | Video/image height |
| `-f, --fps` | float | 30 | Frames per second (supports decimals: 23.98, 29.97, etc.) |
| `-d, --duration` | float | 1.0 | Duration in seconds |
| `--codec` | str | mpeg4 | Video codec: mpeg4, libx264, libx265, libvpx-vp9, libaom-av1, mjpeg, libxvid |

### Audio Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--embed-audio` | flag | - | Embed audio in video |
| `--audio-file` | flag | - | Generate separate audio file |
| `--audio-format` | str | wav | Audio format: wav, ogg, mp3, m4a, flac |
| `--sample-rate` | float | 44100 | Sample rate in Hz (supports decimals) |
| `--channels` | int | 1 | Audio channels (1=mono, 2=stereo, 6=5.1, etc.) |
| `--bit-depth` | int | 16 | Audio bit depth (1-32 bits) |
| `--min-freq` | float | 100 | Minimum frequency in Hz |
| `--max-freq` | float | 1000 | Maximum frequency in Hz |
| `--bitrate` | str | 192k | Audio bitrate for compressed formats |

### Animation Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-d, --duration` | float | 2.0 | GIF duration in seconds |
| `-f, --fps` | int | 15 | GIF frame rate |

## Advanced Usage

### Decimal Frame Rates

```bash
# Film rate (23.976 fps)
./run-macos-linux.sh 10 -t mp4 -f 23.976

# NTSC rate (29.97 fps)
./run-macos-linux.sh 10 -t mp4 -f 29.97

# PAL rate (25 fps)
./run-macos-linux.sh 10 -t mp4 -f 25
```

### Arbitrary Sample Rates

```bash
# Non-standard sample rate for testing
./run-macos-linux.sh 5 -t wav --sample-rate 43124.3123

# High-quality audio (96kHz)
./run-macos-linux.sh 10 -t flac --sample-rate 96000
```

### Video with Multiple Audio Outputs

```bash
# Generate video with both embedded and separate audio
./run-macos-linux.sh 5 -t mp4 --embed-audio --audio-file --audio-format mp3
```

### Advanced Video Codecs

```bash
# H.264 (widely compatible)
./run-macos-linux.sh 10 -t mp4 --codec libx264

# H.265 (better compression)
./run-macos-linux.sh 10 -t mp4 --codec libx265

# VP9 (open source)
./run-macos-linux.sh 10 -t mp4 --codec libvpx-vp9

# AV1 (next-gen compression)
./run-macos-linux.sh 10 -t mp4 --codec libaom-av1
```

### Multi-Channel Audio

```bash
# Stereo
./run-macos-linux.sh 10 -t wav --channels 2

# 5.1 surround
./run-macos-linux.sh 10 -t wav --channels 6

# High bit-depth stereo
./run-macos-linux.sh 10 -t wav --channels 2 --bit-depth 24
```

### SVG Vector Graphics

```bash
# Generate scalable vector graphics
./run-macos-linux.sh 20 -t svg -w 800 -H 600
```

## Project Architecture

### Directory Structure

```
media-generator/
├── media_generator/              # Main Python package
│   ├── __init__.py              # Package metadata & version
│   ├── __main__.py              # CLI and orchestration
│   ├── audio.py                 # Audio generation (WAV, OGG, MP3, M4A, FLAC)
│   ├── video.py                 # Video generation (MP4, codecs)
│   ├── image.py                 # Image/animation (JPG, PNG, WebP, BMP, TIFF, SVG, GIF)
│   └── test.py                  # Test suite (20 comprehensive tests)
│
├── run-macos-linux.sh           # Smart launcher (macOS/Linux)
├── run-windows.bat              # Smart launcher (Windows)
├── pyproject.toml               # Package configuration
├── requirements.txt             # Dependencies
├── README.md                    # Entry point
├── USER_GUIDE.md                # Non-technical guide
└── TECHNICAL_GUIDE.md           # This file
```

### Code Architecture

**Functional programming style with immutable data structures:**

```python
# Immutable configuration objects
@dataclass(frozen=True)
class AudioConfig:
    frequency: float
    duration: float
    sample_rate: float = 44100
    channels: int = 1
    bit_depth: int = 16
    max_freq: float = 1000
    bitrate: str = '192k'

@dataclass(frozen=True)
class VideoConfig:
    width: int = 1920
    height: int = 1080
    fps: float = 30
    duration: float = 1
    codec: str = 'mpeg4'
```

### Core Components

**`audio.py`** - Audio generation:
- `AudioConfig` - Immutable audio configuration dataclass
- `generate_audio_data()` - Triangle wave oscillator with low-pass filtering
- `write_audio_file()` - Audio file writing (WAV, OGG, MP3, M4A, FLAC)
- Pure functions for wave generation, filtering, normalization, quantization

**`video.py`** - Video generation:
- `VideoConfig` - Immutable video configuration dataclass
- `write_video_file()` - Video generation with various codecs
- `embed_audio_in_video()` - Audio/video muxing
- `generate_video_frames()` - Frame generation with random effects
- Codec support: H.264, H.265, VP9, AV1, MPEG-4, MJPEG, Xvid

**`image.py`** - Image and animation generation:
- `write_image_file()` - Image generation (JPG, PNG, WebP, BMP, TIFF)
- `write_svg_file()` - SVG vector graphics with random shapes
- `write_gif_file()` - GIF animation
- Reuses video frame generation for consistency

**`__main__.py`** - CLI and orchestration:
- `create_parser()` - Argument parsing
- `interactive_mode()` - User-friendly guided interface
- `generate_media_files()` - Main generation orchestration
- `find_existing_files()` - Conflict detection
- `prompt_conflict_resolution()` - File conflict handling

### Dependencies

**Core:**
- `numpy` - Array processing
- `scipy` - Signal processing (filters, waveforms)
- `Pillow (PIL)` - Image manipulation
- `opencv-python (cv2)` - Video frame processing
- `imageio` - GIF generation
- `ffmpeg-python` - FFmpeg wrapper
- `imageio-ffmpeg` - Bundled FFmpeg binaries (no separate install needed)

## Development

### Setup Development Environment

```bash
git clone <repository-url>
cd media-generator
pip3 install -e .
```

The `-e` flag installs in editable mode - code changes take effect immediately.

### Running Tests

**Automated Test Suite:**
```bash
# Run comprehensive test suite (20 tests)
python3 -m media_generator.test

# Or run directly
python3 media_generator/test.py
```

**Manual Testing:**
```bash
# Test all media types
./run-macos-linux.sh 3 -t mp4 --embed-audio
./run-macos-linux.sh 3 -t jpg
./run-macos-linux.sh 3 -t gif
./run-macos-linux.sh 3 -t wav --channels 2
./run-macos-linux.sh 3 -t svg

# Test decimal FPS
./run-macos-linux.sh 1 -t mp4 -f 23.98

# Test decimal sample rates
./run-macos-linux.sh 1 -t wav --sample-rate 43124.3123

# Test interactive mode
./run-macos-linux.sh
```

### Adding New Media Type

1. Add format to `--type` choices in `create_parser()` (__main__.py:line)
2. Add generation function in `core.py`:
   ```python
   def write_newformat_file(output: MediaOutput, config: SomeConfig) -> str:
       # Generate content
       # Write to output.path
       # Return description
       return description
   ```
3. Add case in `generate_media_files()` in `__main__.py`
4. Update interactive mode if needed
5. Test thoroughly

### Code Style

Follow functional programming principles:
- Use immutable dataclasses for configuration
- Write pure functions (no side effects)
- Separate I/O from logic
- Type hints for clarity
- Descriptive names

## Distribution

### Method 1: Smart Launcher (Recommended)

Distribute the entire folder with launcher scripts:
- Users run `./run-macos-linux.sh` or `run-windows.bat`
- Automatic Python installation and setup on first run
- No manual installation required
- Small download size (~1MB source code)
- Easy to update (just replace Python files)

**To distribute:**
1. Zip the entire `media-generator/` folder
2. Share with users
3. Users unzip and run the launcher script
4. First run handles all setup automatically

### Method 2: Python Package

Install locally for development:
```bash
pip3 install -e .
```

Publish to PyPI:
```bash
python3 -m build
python3 -m twine upload dist/*
```

Users can then install with: `pip install media-generator`

### Virtual Environment Management

The smart launchers manage virtual environments automatically:

**First run:**
- Creates `venv/` directory
- Installs dependencies from `requirements.txt`
- Creates `.setup_complete` marker

**Subsequent runs:**
- Instant startup (activates existing venv)
- Only reinstalls if `requirements.txt` changes

**Manual cleanup:**
```bash
# macOS/Linux
rm -rf venv/

# Windows
rmdir /s /q venv
```

Then run launcher again to recreate.

## Troubleshooting

### Import Errors After Editing

```bash
pip3 uninstall media-generator
pip3 install -e .
```

### FFmpeg Not Found

Package includes bundled FFmpeg via `imageio-ffmpeg`. If issues occur:
```bash
pip3 uninstall imageio-ffmpeg
pip3 install imageio-ffmpeg
```

### Permission Issues (macOS/Linux)

```bash
chmod +x run-macos-linux.sh
```

### Virtual Environment Corruption

```bash
rm -rf venv/
./run-macos-linux.sh  # Recreates everything
```

## Configuration Files

### `pyproject.toml`

Modern Python package configuration:
- Package metadata (name, version, description)
- Dependencies
- Entry points (command-line scripts)
- Python version requirement (>=3.8)

### `requirements.txt`

Simple dependency list:
- Used by smart launchers for quick setup
- Compatible with older tools
- Useful for: `pip install -r requirements.txt`

Both files are needed and serve different purposes.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes following functional programming style
4. Test thoroughly with various parameters
5. Commit with clear messages
6. Create Pull Request

## License

MIT License - See LICENSE file for details.
