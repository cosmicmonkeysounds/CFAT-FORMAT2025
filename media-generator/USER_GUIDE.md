# Media Generator - User Guide for Non-Technical Users

**Simple guide for gallery staff and non-programmers**

This software creates test video files, images, and audio files. You can use it to generate media files for testing your systems.

---

## Quick Start (Easiest Method)

### If You Have the Executable File

If someone gave you a file called `media-generator` or `media-generator.exe`, you can skip all the installation steps!

**On Windows:**
1. Double-click `media-generator.exe`, or
2. Open Command Prompt (search for "cmd" in Start menu)
3. Drag the `media-generator.exe` file into the window
4. Add your command, like: ` 10 -t mp4`
5. Press Enter

**On Mac:**
1. Open Terminal (search for "Terminal" in Spotlight)
2. Type: `cd ` (note the space after cd)
3. Drag the folder containing `media-generator` into the Terminal window
4. Press Enter
5. Type: `./media-generator 10 -t mp4`
6. Press Enter

If Mac says it's from an "unidentified developer":
- Go to System Preferences → Security & Privacy
- Click "Open Anyway"

**On Linux:**
1. Open Terminal
2. Navigate to the folder: `cd /path/to/folder`
3. Make it executable: `chmod +x media-generator`
4. Run it: `./media-generator 10 -t mp4`

---

## Installation (If You Don't Have the Executable)

### Step 1: Install Python

**On Windows:**
1. Go to https://www.python.org/downloads/
2. Click the big yellow button "Download Python"
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box "Add Python to PATH"
5. Click "Install Now"

**On Mac:**
1. Go to https://www.python.org/downloads/
2. Download the macOS installer
3. Open the .pkg file and follow the instructions

**On Linux (Ubuntu/Debian):**
Open Terminal and type:
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Download This Software

**Option A: Download as ZIP**
1. Click the green "Code" button on the GitHub page
2. Click "Download ZIP"
3. Unzip the file to a folder on your computer

**Option B: Using Git (if you have it)**
Open Terminal/Command Prompt and type:
```bash
git clone https://github.com/yourusername/media-generator.git
cd media-generator
```

### Step 3: Install the Software

Open Terminal (Mac/Linux) or Command Prompt (Windows):

1. Navigate to the folder where you downloaded the software:
   ```bash
   cd /path/to/media-generator
   ```

2. Install it:
   ```bash
   pip3 install -e .
   ```

   Or if that doesn't work:
   ```bash
   pip install -e .
   ```

Wait for it to download and install (this may take a few minutes).

---

## How to Use It

After installation, you can run the software from anywhere on your computer.

### Basic Commands

Open Terminal or Command Prompt and type these commands:

**Generate 10 test videos:**
```bash
media-generator 10 -t mp4
```

**Generate 10 images:**
```bash
media-generator 10 -t jpg
```

**Generate 10 audio files:**
```bash
media-generator 10 -t wav
```

**Save to a specific folder:**
```bash
media-generator 10 -t mp4 -o /path/to/my/folder
```

**Give files a custom name:**
```bash
media-generator 10 -t mp4 --name my_test_video
```
This creates: `my_test_video_1.mp4`, `my_test_video_2.mp4`, etc.

### Common Examples

**Generate 20 HD videos:**
```bash
media-generator 20 -t mp4 -w 1920 -H 1080
```

**Generate 5 small images:**
```bash
media-generator 5 -t jpg -w 640 -H 480
```

**Generate 10 short videos (2 seconds each):**
```bash
media-generator 10 -t mp4 -d 2
```

**Generate audio test tones:**
```bash
media-generator 10 -t wav
```

**Generate stereo audio files:**
```bash
media-generator 10 -t wav --channels 2
```

---

## Understanding the Options

### Media Types (`-t` or `--type`)
- `mp4` - Video files
- `jpg` - JPEG images
- `png` - PNG images
- `gif` - Animated GIFs
- `wav` - Audio files

### Common Options

| Option | What it does | Example |
|--------|-------------|---------|
| First number | How many files to create | `10` creates 10 files |
| `-t` or `--type` | Type of file (mp4, jpg, png, gif, wav) | `-t mp4` |
| `-o` or `--output-dir` | Where to save files | `-o my_videos` |
| `--name` | Base name for files | `--name test_video` |
| `-w` or `--width` | Width in pixels (video/image) | `-w 1920` |
| `-H` or `--height` | Height in pixels (video/image) | `-H 1080` |
| `-d` or `--duration` | Length in seconds (video/audio) | `-d 5` |

### Audio-Specific Options

| Option | What it does | Example |
|--------|-------------|---------|
| `--channels` | Number of audio channels (1=mono, 2=stereo) | `--channels 2` |
| `--bit-depth` | Audio quality (8, 16, 24, or 32) | `--bit-depth 16` |
| `--sample-rate` | Sample rate in Hz | `--sample-rate 44100` |
| `--min-freq` | Lowest tone frequency | `--min-freq 100` |
| `--max-freq` | Highest tone frequency | `--max-freq 1000` |

---

## Where Are My Files?

By default, files are saved in a folder called `test_media` in the same location where you ran the command.

To save files somewhere else, use `-o`:
```bash
media-generator 10 -t mp4 -o /Users/yourname/Desktop/my_videos
```

---

## Troubleshooting

### "Command not found" or "media-generator is not recognized"

**Solution 1:** Try using the full Python module command:
```bash
python3 -m media_generator 10 -t mp4
```
or
```bash
python -m media_generator 10 -t mp4
```

**Solution 2:** Make sure Python is in your PATH (Windows: reinstall Python with "Add to PATH" checked)

### "Permission denied" (Mac/Linux)

Try adding `sudo` before the install command:
```bash
sudo pip3 install -e .
```

### "No module named cv2" or similar errors

Make sure you installed from the correct folder:
```bash
cd /path/to/media-generator
pip3 install -r requirements.txt
```

### Files are being saved to the wrong place

Use the full path with `-o`:
```bash
media-generator 10 -t mp4 -o "/full/path/to/folder"
```

### The program is too slow

- Reduce the video resolution: `-w 1280 -H 720`
- Create fewer files at a time
- Use shorter durations: `-d 1`

---

## Getting Help

To see all available options:
```bash
media-generator --help
```

For technical documentation, see `README.md` in the software folder.

---

## Example Gallery Workflow

**Scenario:** You need 50 test videos for your video playback system

1. Open Terminal/Command Prompt

2. Create a folder on your Desktop:
   ```bash
   mkdir ~/Desktop/gallery_test_videos
   ```

3. Generate the videos:
   ```bash
   media-generator 50 -t mp4 -o ~/Desktop/gallery_test_videos --name gallery_test
   ```

4. This creates 50 files:
   - `gallery_test_1.mp4`
   - `gallery_test_2.mp4`
   - ...
   - `gallery_test_50.mp4`

5. Each video is different (different colors and effects)

6. Use these files to test your playback system!

---

## Quick Reference Card

**Print this out and keep near your computer!**

```
Generate 10 videos:
  media-generator 10 -t mp4

Generate 10 images:
  media-generator 10 -t jpg

Generate 10 audio files:
  media-generator 10 -t wav

Save to Desktop (Mac):
  media-generator 10 -t mp4 -o ~/Desktop/test_files

Save to Desktop (Windows):
  media-generator 10 -t mp4 -o C:\Users\YourName\Desktop\test_files

Custom name:
  media-generator 10 -t mp4 --name my_video

Get help:
  media-generator --help
```

---

## Contact

For technical support, see the README.md file or contact your IT department.
