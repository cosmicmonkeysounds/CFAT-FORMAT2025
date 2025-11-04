# Quick Start Guide

## For End Users (No Python Required)

1. Download the executable for your platform:
   - Windows: `media-generator.exe`
   - macOS: `media-generator`
   - Linux: `media-generator`

2. Make it executable (macOS/Linux only):
   ```bash
   chmod +x media-generator
   ```

3. Run it:
   ```bash
   # Windows
   media-generator.exe 10 -t mp4

   # macOS/Linux
   ./media-generator 10 -t mp4
   ```

## For Developers (With Python)

1. Install the package:
   ```bash
   pip3 install -e .
   ```

2. Run from anywhere:
   ```bash
   media-generator 10 -t mp4
   # or
   mediagen 10 -t wav
   ```

## Quick Examples

Generate 10 videos:
```bash
media-generator 10 -t mp4
```

Generate 10 images:
```bash
media-generator 10 -t jpg
```

Generate 10 audio files:
```bash
media-generator 10 -t wav
```

Generate custom audio:
```bash
# 12-bit stereo WAV files at 440Hz
media-generator 1 -t wav --channels 2 --bit-depth 12 --min-freq 440
```

## Need Help?

```bash
media-generator --help
```

See README.md for complete documentation.
