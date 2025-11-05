# Media Generator

Generate unique test media files (video, images, animations, audio) with random visual and audio characteristics.

## Choose Your Guide

**🎨 Non-Technical User?** (Gallery staff, artists using interactive mode)
→ See **[USER_GUIDE.md](USER_GUIDE.md)**

**💻 Technical User?** (Artists using CLI, developers)
→ See **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)**

## Quick Start

### Interactive Mode (Easiest)

Just run without arguments and follow the prompts:

```bash
# macOS/Linux
./run-macos-linux.sh

# Windows - double-click run-windows.bat, or:
run-windows.bat
```

First run automatically installs everything (takes ~30 seconds). After that, starts instantly.

### Command Line Mode

```bash
# macOS/Linux
./run-macos-linux.sh 10 -t mp4 --embed-audio

# Windows
run-windows.bat 10 -t mp4 --embed-audio
```

## Common Examples

```bash
# 10 videos with audio
./run-macos-linux.sh 10 -t mp4 --embed-audio

# 10 JPG images (1920x1080)
./run-macos-linux.sh 10 -t jpg -w 1920 -H 1080

# 10 stereo audio files
./run-macos-linux.sh 10 -t wav --channels 2

# 5 GIF animations
./run-macos-linux.sh 5 -t gif -d 2 -f 15
```

## Features

- **Video**: MP4 with multiple codecs (H.264, H.265, VP9, AV1)
- **Images**: JPG, PNG, WebP, BMP, TIFF, SVG
- **Animations**: GIF with configurable duration and FPS
- **Audio**: WAV, OGG, MP3, AAC/M4A, FLAC
- **Unique content**: Random colors, effects, and audio per file
- **Smart launchers**: Automatic Python and dependency installation
- **Interactive mode**: Guided experience for non-technical users

## Testing

Run the comprehensive test suite (20 tests):

```bash
python3 test.py
```

## Getting Help

```bash
./run-macos-linux.sh --help    # macOS/Linux
run-windows.bat --help         # Windows
```

## License

MIT License
