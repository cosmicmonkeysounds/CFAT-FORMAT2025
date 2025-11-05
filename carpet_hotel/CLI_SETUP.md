# Carpet Hotel - Command Line & Build Setup

Complete guide for running Carpet Hotel from the command line and building executables.

## Prerequisites

1. **SuperCollider** - Already installed ✓
2. **Processing** - Download from https://processing.org/download
3. **Python 3** - Already on macOS ✓

## Setup Processing Command Line Tool

### 1. Install Processing
If not already installed, download and install Processing 4.

### 2. Add processing-java to PATH

Processing includes a command-line tool called `processing-java`. Add it to your PATH:

**Option A: Temporary (this session only)**
```bash
export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"
```

**Option B: Permanent (recommended)**
Add to your `~/.zshrc` or `~/.bash_profile`:
```bash
echo 'export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Verify installation:**
```bash
processing-java --help
```

You should see the Processing help text.

### 3. Install oscP5 Library

The sketch needs the oscP5 library. Install it via Processing IDE first:
1. Open Processing IDE
2. `Sketch > Import Library > Add Library...`
3. Search for "oscP5"
4. Install

OR install via command line:
```bash
processing-java --install-contrib=oscP5
```

## Using the Launcher Script

### Make the Script Executable
```bash
cd /Users/jjm/Documents/CFAT2025/carpets/carpet_hotel
chmod +x run_carpet_hotel.py
```

### Run Everything
```bash
python3 run_carpet_hotel.py
```

This will:
1. ✓ Check dependencies
2. ✓ Launch SuperCollider audio engine
3. ✓ Wait for initialization
4. ✓ Launch Processing sketch
5. ✓ Monitor both processes

**Press Ctrl+C to stop everything cleanly**

### Run SuperCollider Only (for testing)
```bash
python3 run_carpet_hotel.py --sc-only
```

### Build Executable
```bash
python3 run_carpet_hotel.py --build
```

This creates a standalone macOS application in `build/` directory.

## Manual Command Line Usage

### Run Processing Sketch Manually
```bash
processing-java --sketch=/path/to/carpet_hotel --run
```

### Run SuperCollider Manually
```bash
/Applications/SuperCollider.app/Contents/MacOS/sclang carpet_hotel_audio.scd
```

## Building Executables

### Build with Python Script
```bash
python3 run_carpet_hotel.py --build
```

Output will be in `build/` directory as a `.app` bundle.

### Build Manually
```bash
processing-java \
  --sketch=/Users/jjm/Documents/CFAT2025/carpets/carpet_hotel \
  --output=/Users/jjm/Documents/CFAT2025/carpets/carpet_hotel/build \
  --export \
  --platform=macosx \
  --force
```

### Run the Built Application
```bash
open build/carpet_hotel.app
```

**Important:** The built app will still need SuperCollider running separately for audio!

## Advanced Configuration

### Custom Paths

If SuperCollider or Processing are installed in non-standard locations:

```bash
# Set custom paths
export SC_PATH="/path/to/sclang"
export PROCESSING_JAVA="/path/to/processing-java"

# Then run
python3 run_carpet_hotel.py
```

### Create a Launch Script

Create `launch.sh`:
```bash
#!/bin/bash
cd /Users/jjm/Documents/CFAT2025/carpets/carpet_hotel
python3 run_carpet_hotel.py
```

Make it executable:
```bash
chmod +x launch.sh
```

Run it:
```bash
./launch.sh
```

## Troubleshooting

### "processing-java: command not found"
- Make sure Processing is installed
- Check that PATH includes Processing MacOS directory
- Run: `ls /Applications/Processing.app/Contents/MacOS/processing-java`

### "SuperCollider not found"
- Default path: `/Applications/SuperCollider.app/Contents/MacOS/sclang`
- Set custom path: `export SC_PATH=/your/path/to/sclang`

### "oscP5 library not found"
Install via Processing IDE or:
```bash
processing-java --install-contrib=oscP5
```

### Build fails
- Make sure all libraries are installed (oscP5)
- Check that Processing sketch runs normally first
- Try running Processing manually: `processing-java --sketch=. --run`

### Audio doesn't work in built app
The built Processing app doesn't include SuperCollider. You need to:
1. Run SuperCollider separately with the audio script
2. Then launch the built Processing app

Or use the Python launcher script which coordinates both.

## Complete Workflow

**Development:**
```bash
# Run from source with auto-coordination
python3 run_carpet_hotel.py
```

**Production Build:**
```bash
# Build the executable
python3 run_carpet_hotel.py --build

# The script still coordinates both apps
python3 run_carpet_hotel.py
```

## Quick Reference

```bash
# Run everything
python3 run_carpet_hotel.py

# Build executable
python3 run_carpet_hotel.py --build

# Test audio only
python3 run_carpet_hotel.py --sc-only

# Run built app (needs SC running separately)
open build/carpet_hotel.app

# Stop everything
Ctrl+C
```

## Notes

- The Python script handles graceful shutdown of both processes
- SuperCollider audio engine must be running for audio to work
- Press `Cmd+.` in SuperCollider to stop audio manually
- Press `Ctrl+C` in terminal to stop Python launcher
- Built executables are in the `build/` directory
- Video files must be in the `data/` directory
- Audio files must be in the `data/` directory
