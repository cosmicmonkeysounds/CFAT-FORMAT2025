# Carpet Hotel - Quick Start Guide

Get up and running in **ONE STEP**! The launcher scripts handle all dependencies automatically.

## Instant Setup & Launch

### macOS
```bash
cd /path/to/carpet_hotel
./launch_macos.sh
```

### Windows
```cmd
cd C:\path\to\carpet_hotel
launch_windows.bat
```

**That's it!** The launcher will automatically:
- ✓ Install Homebrew (macOS only, if needed)
- ✓ Install Python3 (if needed)
- ✓ Install SuperCollider (if needed)
- ✓ Install Processing (if needed)
- ✓ Create Python virtual environment
- ✓ Install Python dependencies (pyautogui)
- ✓ Open SuperCollider IDE and execute audio script
- ✓ Launch Processing sketch
- ✓ Coordinate everything

## First Run Notes

### oscP5 Library (Required - One Time Setup)

The launcher will check for the oscP5 Processing library. If not found, you'll need to install it manually:

1. Open Processing IDE
2. Go to `Sketch > Import Library > Add Library...`
3. Search for "oscP5"
4. Click Install
5. Return to the launcher and press Enter

**After this one-time setup, everything is automated!**

### macOS Permissions

On first run, macOS may ask for permissions:
- **Accessibility**: Required for keyboard automation (Cmd+A, Cmd+Enter in SuperCollider)
- Go to: System Settings > Privacy & Security > Accessibility
- Enable Terminal (or your terminal app)

## What the Launcher Does

### Dependency Installation (Automatic)

**macOS:**
1. Installs Homebrew package manager (if needed)
2. Installs Python3 via Homebrew (if needed)
3. Installs SuperCollider via Homebrew (if needed)
4. Downloads and installs Processing from GitHub (if needed)
5. Adds processing-java to your PATH (~/.zshrc or ~/.bash_profile)

**Windows:**
1. Downloads and installs Python3 from python.org (if needed)
2. Downloads and installs SuperCollider from GitHub (if needed)
3. Downloads and installs Processing from GitHub (if needed)
4. Adds Processing to PATH for current session

### Virtual Environment (Automatic)

The launcher creates a `venv/` folder in the carpet_hotel directory and:
- Creates a Python virtual environment (isolated from system Python)
- Installs all pip3 dependencies (pyautogui)
- Activates the environment automatically

**Benefits:**
- No conflicts with system Python packages
- Clean, isolated environment
- All dependencies managed automatically

### Launching the System (Automatic)

The launcher uses GUI automation to properly run SuperCollider:
1. Opens SuperCollider IDE
2. Opens the `carpet_hotel_audio.scd` script
3. Focuses the IDE window
4. Sends keyboard commands: Select All → Execute
5. Waits for audio engine to boot
6. Launches Processing sketch with OSC communication

## Stopping the System

**Press Ctrl+C** in the terminal to stop Processing

**Press Cmd+. (macOS) or Ctrl+. (Windows)** in SuperCollider IDE to stop audio

## Options

### Build an Executable

**macOS:**
```bash
./launch_macos.sh --build
```

Output: `build/carpet_hotel.app`

**Windows:**
```cmd
launch_windows.bat --build
```

Output: `build/carpet_hotel.exe`

**Note:** The executable only includes the Processing sketch. You still need to:
1. Launch SuperCollider IDE
2. Open and execute `carpet_hotel_audio.scd`
3. Then run the executable

### SuperCollider Only (Testing)

**macOS:**
```bash
./launch_macos.sh --sc-only
```

**Windows:**
```cmd
launch_windows.bat --sc-only
```

Runs only the audio engine for testing.

### Help

**macOS:**
```bash
./launch_macos.sh --help
```

**Windows:**
```cmd
launch_windows.bat --help
```

## File Structure

```
carpet_hotel/
├── launch_macos.sh              # Automated setup & launcher (macOS)
├── launch_windows.bat           # Automated setup & launcher (Windows)
├── run_carpet_hotel.py          # Cross-platform Python coordinator
├── carpet_hotel.pde             # Processing sketch (video)
├── carpet_hotel_audio.scd       # SuperCollider script (audio)
├── data/                        # Media files
│   ├── carpet_*.mp4             # Video files
│   └── carpet_*.wav             # Audio files
├── venv/                        # Python virtual environment (auto-created)
└── build/                       # Built executables (created by --build)
```

## Troubleshooting

### "Accessibility permissions required" (macOS)

macOS blocks keyboard automation by default:
1. Go to System Settings > Privacy & Security > Accessibility
2. Add and enable your Terminal app
3. Run the launcher again

### "Please install oscP5 manually"

The oscP5 library must be installed via Processing IDE:
1. Open Processing IDE
2. Sketch > Import Library > Add Library...
3. Search "oscP5" and install
4. Return to launcher and press Enter

### Python installation requires restart (Windows)

If Python is installed automatically, you may need to:
1. Close the terminal window
2. Open a new terminal
3. Run `launch_windows.bat` again

### SuperCollider window doesn't focus

If the automation fails to execute SuperCollider code:
1. Make sure the SuperCollider IDE window is visible (not minimized)
2. Try increasing sleep times in run_carpet_hotel.py (lines 151, 156, 176)
3. Or run manually (see below)

### Manual Execution (Fallback)

If automation fails, you can run manually:

**Terminal 1 - SuperCollider:**
1. Open SuperCollider IDE
2. Open `carpet_hotel_audio.scd`
3. Select All (Cmd+A / Ctrl+A)
4. Execute (Cmd+Enter / Ctrl+Enter)

**Terminal 2 - Processing:**
```bash
# macOS
source venv/bin/activate
processing-java --sketch=. --run

# Windows
venv\Scripts\activate.bat
processing-java --sketch=. --run
```

## Advanced: Manual Dependency Installation

If you prefer to install dependencies manually instead of using the automated launcher:

### macOS
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3
brew install --cask supercollider
# Download Processing from: https://processing.org/download

# Add to ~/.zshrc:
export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip3 install pyautogui

# Install oscP5 in Processing IDE
# Then run:
python3 run_carpet_hotel.py
```

### Windows
```cmd
REM Install Python3 from: https://www.python.org/downloads/
REM Install SuperCollider from: https://supercollider.github.io/downloads
REM Install Processing from: https://processing.org/download

REM Setup Python environment
python -m venv venv
venv\Scripts\activate.bat
pip3 install pyautogui

REM Install oscP5 in Processing IDE
REM Then run:
python run_carpet_hotel.py
```

## Quick Reference

| Platform | Command | What It Does |
|----------|---------|--------------|
| macOS | `./launch_macos.sh` | Setup + run everything |
| macOS | `./launch_macos.sh --build` | Build .app |
| Windows | `launch_windows.bat` | Setup + run everything |
| Windows | `launch_windows.bat --build` | Build .exe |
| Both | `Ctrl+C` | Stop Processing |
| macOS | `Cmd+.` in SC | Stop audio |
| Windows | `Ctrl+.` in SC | Stop audio |

## System Requirements

- **macOS**: 10.13 or later (Intel or Apple Silicon)
- **Windows**: Windows 10 or later (64-bit)
- **Disk Space**: ~500MB for all dependencies
- **Internet**: Required for first-time dependency downloads

## What's Happening Behind the Scenes?

### OSC Communication

The Processing sketch sends OSC messages to SuperCollider:
- `/carpet/scene` - Static scene (which floors are visible)
- `/carpet/transition` - Transition state (crossfading between floors)

SuperCollider receives these messages and:
- Adjusts audio volumes for active floors (equal-power mixing)
- Crossfades audio during transitions (smooth sine/cosine curves)
- Loops audio files independently of video

### GUI Automation

The launcher uses `pyautogui` to simulate keyboard input:
- Opens SuperCollider IDE
- Waits for loading
- Selects all code (Cmd+A / Ctrl+A)
- Executes code (Cmd+Enter / Ctrl+Enter)

This mimics exactly how you'd manually run the code!

---

**Need detailed documentation?** See:
- **CLI_SETUP.md** - Complete command-line setup details
- **AUDIO_SETUP.md** - SuperCollider audio engine internals
- **README.md** - Project overview and architecture
