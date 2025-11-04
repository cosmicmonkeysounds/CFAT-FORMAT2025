# Media Generator - Smart Launcher Scripts

This package includes smart launcher scripts that automatically handle all setup for you!

## Quick Start

### macOS / Linux
```bash
./run.sh 10 -t mp4 --embed-audio
```

### Windows
```cmd
run.bat 10 -t mp4 --embed-audio
```

Or double-click `run.bat` in Windows Explorer.

## What The Launchers Do Automatically

The launcher scripts handle everything:

1. **Check for Python 3**
   - If not found, automatically install it:
     - macOS: Via Homebrew (installs Homebrew too if needed)
     - Linux: Via apt/yum/dnf/pacman (auto-detects)
     - Windows: Via winget or Chocolatey

2. **Create Virtual Environment**
   - Creates an isolated `venv/` directory
   - Keeps dependencies separate from system Python

3. **Install Dependencies**
   - Automatically installs all required packages
   - Includes bundled ffmpeg (no separate install needed!)

4. **Run The Program**
   - Passes all your arguments through
   - Works exactly like a normal command

## First Run

First time running:
```bash
# macOS/Linux
./run.sh --help

# Windows
run.bat --help
```

You'll see:
```
═══════════════════════════════════════════════════════════════
  Media Generator Setup
═══════════════════════════════════════════════════════════════

✓ Python found: Python 3.13.3
==> Creating virtual environment...
✓ Virtual environment created
==> Installing dependencies...
✓ Dependencies installed successfully

═══════════════════════════════════════════════════════════════
```

This takes ~30 seconds the first time. After that, it starts instantly!

## Subsequent Runs

Every run after the first:
```bash
./run.sh 10 -t mp4 --embed-audio
```

You'll see:
```
═══════════════════════════════════════════════════════════════
  Media Generator Setup
═══════════════════════════════════════════════════════════════

✓ Python found: Python 3.13.3
✓ Virtual environment ready

═══════════════════════════════════════════════════════════════

🎬 Generating 10 MP4 files...
```

Starts instantly - no reinstallation needed!

## Smart Updates

The launchers automatically detect when dependencies need updating:

- If `requirements.txt` changes → Reinstalls packages
- If venv gets corrupted → Recreates it
- Always ensures you have the latest dependencies

## Examples

### Generate Images
```bash
# macOS/Linux
./run.sh 10 -t jpg -w 1920 -H 1080

# Windows
run.bat 10 -t jpg -w 1920 -H 1080
```

### Generate Videos with Audio
```bash
# macOS/Linux
./run.sh 5 -t mp4 --embed-audio --audio-file --audio-format mp3

# Windows
run.bat 5 -t mp4 --embed-audio --audio-file --audio-format mp3
```

### Generate Audio Files
```bash
# macOS/Linux
./run.sh 20 -t ogg --min-freq 200 --max-freq 2000

# Windows
run.bat 20 -t ogg --min-freq 200 --max-freq 2000
```

### Generate SVG Vector Graphics
```bash
# macOS/Linux
./run.sh 10 -t svg -w 800 -H 600

# Windows
run.bat 10 -t svg -w 800 -H 600
```

## File Structure

After first run, you'll see:
```
media-generator/
├── run.sh              # macOS/Linux launcher
├── run.ps1             # Windows PowerShell launcher
├── run.bat             # Windows batch launcher
├── requirements.txt    # Python dependencies
├── media_generator/    # Main package
└── venv/              # Virtual environment (auto-created)
    ├── bin/           # Python executables
    ├── lib/           # Installed packages
    └── .setup_complete # Marker file
```

## Troubleshooting

### "Permission denied" on macOS/Linux
```bash
chmod +x run.sh
```

### "Script execution is disabled" on Windows
Run PowerShell as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned
```

Or use the batch file instead:
```cmd
run.bat --help
```

### Start Fresh
Delete the virtual environment to reinstall everything:
```bash
# macOS/Linux
rm -rf venv/

# Windows (PowerShell)
Remove-Item -Recurse -Force venv/

# Windows (Command Prompt)
rmdir /s /q venv
```

Then run the launcher again - it will recreate everything.

## Advantages

✅ **No Manual Installation** - Everything automatic
✅ **Isolated Environment** - Doesn't affect system Python
✅ **Cross-Platform** - Same experience everywhere
✅ **Self-Updating** - Detects changes automatically
✅ **Bundled FFmpeg** - No separate installation needed
✅ **Small Download** - Just the Python code + scripts (~1MB)
✅ **Easy Distribution** - Share the whole folder

## Advanced Usage

### Custom Python Version
The launcher uses your system's default Python 3. To use a specific version:

```bash
# macOS/Linux - use specific Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m media_generator 10 -t mp4

# Windows - use specific Python
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m media_generator 10 -t mp4
```

### Direct Python Execution
After setup, you can also run directly:

```bash
# macOS/Linux
source venv/bin/activate
python -m media_generator 10 -t mp4

# Windows
venv\Scripts\activate
python -m media_generator 10 -t mp4
```

## Distribution

To share with others, just zip the entire folder:
```
media-generator.zip
├── run.sh
├── run.ps1
├── run.bat
├── requirements.txt
├── media_generator/
└── (everything else)
```

Users just unzip and run:
- macOS/Linux: `./run.sh --help`
- Windows: Double-click `run.bat`

The launcher handles the rest!
