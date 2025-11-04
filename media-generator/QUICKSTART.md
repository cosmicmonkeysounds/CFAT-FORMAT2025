# Quick Start Guide

**🆕 New user?** See [USER_GUIDE.md](USER_GUIDE.md) for detailed installation instructions.

## Installation

### For End Users (No Python Required)
Download the executable from [Releases](https://github.com/yourusername/media-generator/releases):
```bash
# Windows: Run media-generator.exe
# macOS/Linux: chmod +x media-generator && ./media-generator
```

### For Developers (With Python)
```bash
pip3 install -e .
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
