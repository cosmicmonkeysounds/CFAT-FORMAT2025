# Random Test Media Generator

Generate unique test media files (MP4 videos, JPG/PNG images, GIF animations, WAV audio) with random characteristics for testing media applications.

**📖 Documentation Guide:**
- **Non-technical users**: See [USER_GUIDE.md](USER_GUIDE.md) for simple installation and usage instructions
- **Developers**: Continue reading this README for technical details
- **Quick reference**: See [QUICKSTART.md](QUICKSTART.md) for command examples

## Features

### Video & Image Features
- **Random solid colors** - Each file gets a unique base color
- **Shader-like effects** - Random noise, scanlines, chromatic aberration, grain, and vignettes
- **Multiple formats** - MP4 videos, JPG/PNG images, GIF animations
- **Fast generation** - Efficient numpy operations keep rendering quick
- **Truly unique** - Each file has different visual characteristics

### Audio Features
- **Triangle wave tones** - Low-pass filtered triangle waves with evenly spaced frequencies
- **Precise level** - -12dBFS output level
- **Smart frequency distribution** - Single file uses min-freq, multiple files are evenly spaced between min-freq and max-freq (default: 100Hz - 1kHz)
- **Multi-channel support** - Mono, stereo, or multi-channel audio
- **Arbitrary bit depth** - Any bit depth from 1-32 bits (non-standard depths quantized appropriately)

### General Features
- **Custom naming** - Set your own base name for files
- **No leading zeros** - Clean numbering: 1, 2, 3... 10, 20, 100 (not 01, 02, 010)
- **Smart conflict handling** - Detects existing files and lets you overwrite or continue

## Installation

### Option 1: Install as Python Package (Recommended for Developers)

Install directly from the repository:
```bash
# Clone the repository
git clone https://github.com/yourusername/media-generator.git
cd media-generator

# Install in development mode
pip3 install -e .
```

Or install from PyPI (if published):
```bash
pip3 install media-generator
```

After installation, you can run it from anywhere:
```bash
media-generator 10 -t mp4
# or
mediagen 10 -t wav
```

### Option 2: Use Standalone Executable (For End Users)

Download the pre-built executable for your platform from the [Releases](https://github.com/yourusername/media-generator/releases) page:

- **Windows**: `media-generator.exe`
- **macOS**: `media-generator` (may need to run: `xattr -cr media-generator`)
- **Linux**: `media-generator` (may need to run: `chmod +x media-generator`)

No Python installation required!

### Option 3: Run from Source

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run directly
python3 -m media_generator 10 -t mp4
# or
python3 media_generator.py 10 -t mp4
```

## Building Executables

To build standalone executables for distribution:

```bash
# Install build dependencies
pip3 install -e ".[build]"

# Build executable for your platform
python3 build_executable.py
```

The executable will be created in `dist/media-generator` (or `dist/media-generator.exe` on Windows).

**Cross-platform builds:**
- Build on each target platform (Windows, macOS, Linux) to create native executables
- Or use GitHub Actions / CI for automated multi-platform builds

## Usage

### Basic Usage

Generate 10 test MP4 videos:
```bash
python3 media_generator.py 10
```

Generate 10 JPG images:
```bash
python3 media_generator.py 10 -t jpg
```

Generate 10 WAV audio files:
```bash
python3 media_generator.py 10 -t wav
```

### Media Type Examples

```bash
# Generate MP4 videos
python3 media_generator.py 5 -t mp4 -o videos

# Generate JPG images
python3 media_generator.py 10 -t jpg -o images

# Generate PNG images with custom dimensions
python media_generator.py 10 -t png -w 1280 -H 720

# Generate GIF animations
python3 media_generator.py 5 -t gif -d 2 -f 15

# Generate mono WAV files (100-1000Hz range)
python3 media_generator.py 10 -t wav

# Generate stereo WAV files with custom frequency range
python3 media_generator.py 10 -t wav --channels 2 --min-freq 200 --max-freq 800

# Generate 5.1 surround sound WAV files
python3 media_generator.py 5 -t wav --channels 6

# Generate 24-bit stereo WAV files
python3 media_generator.py 10 -t wav --channels 2 --bit-depth 24

# Generate 32-bit mono WAV files with 48kHz sample rate
python3 media_generator.py 10 -t wav --bit-depth 32 --sample-rate 48000

# Generate 12-bit mono WAV files (stored in 16-bit container)
python3 media_generator.py 10 -t wav --bit-depth 12

# Generate 10 files with frequencies evenly spaced from 200-2000Hz
pytho3 media_generator.py 10 -t wav --min-freq 200 --max-freq 2000

# Generate single file at exact frequency (uses min-freq)
python3 media_generator.py 1 -t wav --min-freq 440  # Generates A4 note
```

### Custom Options

```bash
# Generate 5 files in custom directory
python3 media_generator.py 5 -o my_test_files -t jpg

# Custom base name for files
python3 media_generator.py 10 --name my_media -t mp4

# Generate 720p videos at 60fps
python3 media_generator.py 10 -t mp4 -w 1280 -H 720 -f 60

# Generate 5-second GIFs with custom name
python3 media_generator.py 3 -t gif -d 5 --name long_test
```

### All Options

```
positional arguments:
  n                      Number of files to generate

options:
  -h, --help             Show help message
  -t, --type TYPE        Media type: mp4, jpg, png, gif, wav (default: mp4)
  -n, --name NAME        Base name for files (default: test_media)
  -o, --output-dir DIR   Output directory (default: test_media)

Video/Image options:
  -w, --width WIDTH      Width in pixels (default: 1920)
  -H, --height HEIGHT    Height in pixels (default: 1080)
  -f, --fps FPS          Frames per second for video/GIF (default: 30)
  -d, --duration SEC     Duration in seconds for video/GIF/WAV (default: 1)

Audio options (for WAV files):
  --min-freq HZ          Minimum frequency in Hz (default: 100)
  --max-freq HZ          Maximum frequency in Hz (default: 1000)
  --channels NUM         Audio channels (1=mono, 2=stereo, >2=multi-channel) (default: 1)
  --sample-rate HZ       Sample rate in Hz (default: 44100)
  --bit-depth BITS       Bit depth: 1-32 bits (default: 16)
                         Non-standard depths are quantized and stored in next larger container
```

## Output

Files are saved with clean sequential numbering: `test_media_1.mp4`, `test_media_2.jpg`, ..., `test_media_10.wav`, `test_media_20.gif`, etc.

**No leading zeros** - Numbers are natural: 1, 2, 3, 10, 100 (not 01, 02, 03, 010, 0100)

### Conflict Handling

If files with the same naming pattern already exist, you'll be prompted:

```
⚠️  Found existing files matching pattern 'carpet_*.mp4'
    Highest number found: 15

Options:
  1) Overwrite - Start from 1 (will overwrite existing files)
  2) Continue - Start from 16 (preserve existing files)

Enter choice (1 or 2):
```

This lets you safely add more test files without losing your existing ones!

#### Conflict Example

When you run the script and files already exist with the same naming pattern, you'll see this interactive prompt:

```bash
$ python media_generator.py 5 -o test_videos --name carpet

⚠️  Found existing videos matching pattern 'carpet_*.mp4'
    Highest number found: 15

Options:
  1) Overwrite - Start from 1 (will overwrite existing files)
  2) Continue - Start from 16 (preserve existing files)

Enter choice (1 or 2):
```

**CHOOSING OPTION 1 (Overwrite):**
Will create: carpet_1.mp4, carpet_2.mp4, carpet_3.mp4, carpet_4.mp4, carpet_5.mp4
(Overwrites any existing files with these names)

**CHOOSING OPTION 2 (Continue):**
Will create: carpet_16.mp4, carpet_17.mp4, carpet_18.mp4, carpet_19.mp4, carpet_20.mp4
(Preserves all existing files, starts after the highest number found)

This makes it safe to add more test files to a directory without accidentally destroying your existing test files!

## Media Type Details

### MP4 Videos
Each video includes randomized:
- Base color (RGB)
- Noise patterns
- Scanline effects
- Chromatic aberration
- Film grain
- Vignetting

Perfect for testing video players, encoders, and upload systems!

### JPG/PNG Images
Single frame images with the same random effects as videos:
- Unique color scheme per image
- Random visual effects
- High quality output (JPG quality=95)

Great for testing image processing, galleries, and thumbnails!

### GIF Animations
Animated GIFs with the same effects as MP4 videos:
- Multiple frames with evolving effects
- Configurable duration and frame rate
- Looping animations

Ideal for testing GIF support and animation handling!

### WAV Audio Files
High-quality test audio with precise characteristics:
- **Triangle wave oscillator** - Pure triangle wave generation
- **Low-pass filtered** - 4th order Butterworth filter at 2x frequency or max-freq
- **Evenly spaced frequencies** - When generating multiple files, frequencies are evenly distributed between min-freq and max-freq. Single files use min-freq.
- **Precise level** - Normalized to exactly -12dBFS
- **Multi-channel** - Supports mono, stereo, or any number of channels
- **Arbitrary bit depth** - 1-32 bits supported. Non-standard bit depths (like 12-bit, 7-bit) are quantized to that resolution and stored in the next larger standard container (8, 16, 24, or 32-bit).
- **Professional quality** - Configurable sample rate (default 44.1kHz)

**Frequency Distribution Examples:**
- 1 file: Uses min-freq (100Hz by default)
- 3 files: 100Hz, 550Hz, 1000Hz (evenly spaced)
- 10 files: 100Hz, 200Hz, 300Hz, ..., 1000Hz

**Bit Depth Examples:**
- 16-bit: Standard 16-bit PCM
- 12-bit: Quantized to 4096 levels, stored in 16-bit container
- 8-bit: Standard 8-bit PCM (unsigned)
- 24-bit: Standard 24-bit PCM

Perfect for testing audio systems, DAWs, and media players!

## Package Structure

```
media-generator/
├── media_generator/          # Main package
│   ├── __init__.py          # Package initialization
│   └── __main__.py          # Main application code
├── build_executable.py      # Build script for creating executables
├── pyproject.toml           # Package configuration
├── requirements.txt         # Python dependencies
├── MANIFEST.in             # Package data files
├── LICENSE                 # MIT License
├── README.md               # This file
└── .github/
    └── workflows/
        └── build.yml        # GitHub Actions CI/CD

Generated files (not in repo):
├── dist/                    # Built executables
├── build/                   # Build artifacts
└── *.spec                   # PyInstaller spec files
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip3 install -e ".[dev]"

# Run tests (add tests in tests/ directory)
pytest
```

### Code Formatting

```bash
# Format code with black
black media_generator/

# Lint with flake8
flake8 media_generator/
```

### Making Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Commit: `git commit -am 'Add new feature'`
6. Push: `git push origin feature-name`
7. Create a Pull Request

## Distribution

### Publishing to PyPI

```bash
# Build distribution packages
python3 -m build

# Upload to PyPI (requires account)
python3 -m twine upload dist/*
```

### Creating Releases

1. Tag a version: `git tag v1.0.0`
2. Push tag: `git push origin v1.0.0`
3. GitHub Actions will automatically build executables for all platforms
4. Download artifacts from Actions or check the Releases page

### Manual Distribution

If not using GitHub Actions:

1. Build on each platform (Windows, macOS, Linux)
2. Run: `python3 build_executable.py`
3. Collect executables from `dist/` directory
4. Distribute to users

## Command Aliases

After installing as a package, you can use either command:

```bash
media-generator 10 -t mp4    # Full name
mediagen 10 -t wav           # Short alias
```

For standalone executables, use:
```bash
./media-generator 10 -t mp4  # Unix/macOS
media-generator.exe 10 -t mp4  # Windows
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
