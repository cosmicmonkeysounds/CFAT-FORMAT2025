# User Guide - For Non-Technical Users

**Simple guide for gallery staff and artists using interactive mode**

This tool creates test video, image, and audio files. No programming knowledge required!

## First Time Setup

### Step 1: Run the Script

**macOS/Linux:** Open Terminal, navigate to the media-generator folder, then run:
```bash
./run-macos-linux.sh
```

**Windows:** Double-click `run-windows.bat` in File Explorer, or open Command Prompt and run:
```cmd
run-windows.bat
```

### Step 2: Wait for Setup (First Time Only)

The first time takes about 30 seconds. You'll see:
```
═══════════════════════════════════════════════
  Media Generator Setup
═══════════════════════════════════════════════

✓ Python found
✓ Creating virtual environment...
✓ Installing dependencies...
```

After this first setup, it starts instantly!

### Step 3: Follow the Prompts

The interactive mode will guide you through:
1. How many files to create
2. What type (Video, Image, Audio, Animation)
3. Format and quality options
4. Where to save the files

Just answer each question and press Enter.

## Common Tasks

### Generate Test Videos

**Interactive mode (easiest):**
```bash
./run-macos-linux.sh
```
Then choose:
- Media type: `1` (Video)
- Number of files: `10`
- Format: `1` (MP4)
- Add audio: `y` (yes)

**Quick command:**
```bash
# macOS/Linux
./run-macos-linux.sh 10 -t mp4 --embed-audio

# Windows
run-windows.bat 10 -t mp4 --embed-audio
```

### Generate Test Images

**Quick command:**
```bash
# 10 JPG images
./run-macos-linux.sh 10 -t jpg

# 10 high-resolution PNG images
./run-macos-linux.sh 10 -t png -w 1920 -H 1080
```

### Generate Audio Files

**Quick command:**
```bash
# 10 WAV files
./run-macos-linux.sh 10 -t wav

# 10 stereo audio files
./run-macos-linux.sh 10 -t wav --channels 2
```

## Where Are My Files?

By default, files go into a `test_media` folder where you ran the script.

To save somewhere else, add `-o` with the folder path:

```bash
# macOS/Linux - save to Desktop
./run-macos-linux.sh 10 -t mp4 -o ~/Desktop/my_videos

# Windows - save to Desktop
run-windows.bat 10 -t mp4 -o C:\Users\YourName\Desktop\my_videos
```

## What Files Can It Create?

**Videos:** MP4 files (H.264, H.265, and other formats)
**Images:** JPG, PNG, WebP, BMP, TIFF, SVG
**Audio:** WAV, MP3, OGG, AAC, FLAC
**Animations:** GIF

Each file has unique random colors, effects, and audio.

## Troubleshooting

### "Permission denied" (macOS/Linux)

Run this once:
```bash
chmod +x run-macos-linux.sh
```

### Something Went Wrong - Start Fresh

Delete the setup and try again:

**macOS/Linux:**
```bash
rm -rf venv/
./run-macos-linux.sh
```

**Windows:**
```cmd
rmdir /s /q venv
run-windows.bat
```

### Can't Find My Files

Use the full path to the folder:
```bash
./run-macos-linux.sh 10 -t mp4 -o "/full/path/to/folder"
```

## Example: Gallery Testing Workflow

**You need 50 test videos for the gallery playback system:**

1. Open Terminal (macOS/Linux) or Command Prompt (Windows)
2. Navigate to the media-generator folder
3. Run:
   ```bash
   # macOS/Linux
   ./run-macos-linux.sh 50 -t mp4 --embed-audio -o ~/Desktop/gallery_videos

   # Windows
   run-windows.bat 50 -t mp4 --embed-audio -o C:\Users\YourName\Desktop\gallery_videos
   ```
4. Wait ~2 minutes
5. Find 50 unique videos on your Desktop in the `gallery_videos` folder

Each video has different colors and a unique audio tone - perfect for testing!

## Quick Reference

Print this out and keep it handy:

```
INTERACTIVE MODE (Easiest):
  ./run-macos-linux.sh          (macOS/Linux)
  run-windows.bat               (Windows)

QUICK COMMANDS:
  10 videos:   ./run-macos-linux.sh 10 -t mp4 --embed-audio
  10 images:   ./run-macos-linux.sh 10 -t jpg
  10 audio:    ./run-macos-linux.sh 10 -t wav

SAVE TO SPECIFIC FOLDER:
  Add: -o /path/to/folder

CUSTOM NAME:
  Add: --name my_video

GET HELP:
  ./run-macos-linux.sh --help
```

## Need Advanced Options?

See [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for:
- All command line options
- Advanced codecs and formats
- Custom resolutions and frame rates
- Development and building
