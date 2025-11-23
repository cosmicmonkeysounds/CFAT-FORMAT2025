# Audio Separator Guide

The audio separator module extracts audio from video files in batch with support for multiple output formats.

## Features

- Extract audio from single or multiple video files
- Process entire directories (with optional recursive search)
- Multiple output formats: WAV, MP3, AAC, M4A, OGG, FLAC
- Configurable bitrate, sample rate, and channels
- Custom output directory and filename prefixes/suffixes
- Progress reporting and error handling

## Command Line Usage

### Basic Examples

```bash
# Extract audio from a single video as WAV (default)
python -m media_generator.audio_separator video.mp4

# Extract from multiple videos
python -m media_generator.audio_separator video1.mp4 video2.mp4 video3.mp4

# Process all videos in a directory
python -m media_generator.audio_separator /path/to/videos/

# Recursive directory search
python -m media_generator.audio_separator /path/to/videos/ --recursive
```

### Format and Quality Options

```bash
# Extract as MP3 with high bitrate
python -m media_generator.audio_separator video.mp4 -f mp3 -b 320k

# Extract as FLAC (lossless)
python -m media_generator.audio_separator video.mp4 -f flac

# Convert to mono audio
python -m media_generator.audio_separator video.mp4 -c 1

# Resample to 48kHz
python -m media_generator.audio_separator video.mp4 -r 48000
```

### Output Control

```bash
# Save to specific directory
python -m media_generator.audio_separator video.mp4 -o /output/path/

# Add prefix to output filenames
python -m media_generator.audio_separator video.mp4 --prefix "audio_"

# Add suffix before extension
python -m media_generator.audio_separator video.mp4 --suffix "_extracted"

# Combine prefix, suffix, and custom directory
python -m media_generator.audio_separator /videos/ -o /audio/ --prefix "track_" --suffix "_audio" -f mp3
```

### Other Options

```bash
# Quiet mode (no progress output)
python -m media_generator.audio_separator video.mp4 -q

# Check if FFmpeg is available
python -m media_generator.audio_separator --check-ffmpeg

# Show help
python -m media_generator.audio_separator --help
```

## Python API Usage

You can also use the audio separator as a Python module:

```python
from pathlib import Path
from media_generator.audio_separator import (
    separate_audio_batch,
    separate_audio_from_directory,
    SeparationConfig,
    AudioFormat
)

# Example 1: Process specific files
video_files = [
    Path('video1.mp4'),
    Path('video2.mp4'),
    Path('video3.mp4')
]

config = SeparationConfig(
    output_format=AudioFormat.MP3,
    bitrate='320k',
    output_dir=Path('/output/directory'),
    prefix='audio_'
)

results = separate_audio_batch(video_files, config, verbose=True)

# Check results
for result in results:
    if result.success:
        print(f"✓ {result.video_path} -> {result.audio_path}")
    else:
        print(f"✗ {result.video_path}: {result.error}")

# Example 2: Process entire directory
results = separate_audio_from_directory(
    directory=Path('/videos'),
    config=SeparationConfig(
        output_format=AudioFormat.WAV,
        channels=2  # Force stereo
    ),
    recursive=True,
    verbose=True
)

# Example 3: Custom configuration for each file
from media_generator.audio_separator import extract_audio, generate_output_path

video_path = Path('my_video.mp4')

config = SeparationConfig(
    output_format=AudioFormat.FLAC,
    sample_rate=44100,
    channels=1,  # Mono
    suffix='_mono'
)

output_path = generate_output_path(video_path, config)
success, error = extract_audio(video_path, output_path, config)

if success:
    print(f"Audio saved to: {output_path}")
else:
    print(f"Error: {error}")
```

## Supported Formats

### Video Input Formats
- MP4, AVI, MOV, MKV, WebM, FLV, WMV, M4V
- Any format supported by FFmpeg

### Audio Output Formats

| Format | Codec | Type | Notes |
|--------|-------|------|-------|
| WAV | PCM | Lossless | Uncompressed, large files |
| MP3 | LAME | Lossy | Universal compatibility |
| AAC | AAC | Lossy | Good quality, smaller than MP3 |
| M4A | AAC | Lossy | Apple-friendly container |
| OGG | Vorbis | Lossy | Open-source alternative to MP3 |
| FLAC | FLAC | Lossless | Compressed but perfect quality |

## Configuration Options

### SeparationConfig Parameters

- `output_format`: AudioFormat enum (WAV, MP3, AAC, M4A, OGG, FLAC)
- `bitrate`: Bitrate string for lossy formats (e.g., '192k', '320k')
- `sample_rate`: Target sample rate in Hz (None = keep original)
- `channels`: Number of channels: 1=mono, 2=stereo (None = keep original)
- `output_dir`: Output directory Path (None = same as source)
- `prefix`: Prefix for output filenames
- `suffix`: Suffix before file extension

## Error Handling

The module provides detailed error messages and exit codes:

- Exit code 0: All files processed successfully
- Exit code 1: One or more files failed to process

Each `SeparationResult` contains:
- `video_path`: Original video file path
- `audio_path`: Output audio file path (None if failed)
- `success`: Boolean indicating success
- `error`: Error message string (None if successful)

## Requirements

- Python 3.7+
- FFmpeg (automatically included via imageio_ffmpeg)
- All dependencies are included in the media-generator package

## Tips

1. **Large batches**: Use `--quiet` to suppress verbose output for large batches
2. **Quality**: Use FLAC for archival quality, MP3 320k for high quality with smaller size
3. **Mono conversion**: Use `-c 1` to reduce file size when stereo isn't needed
4. **Testing**: Use `--check-ffmpeg` to verify FFmpeg is working before processing
5. **Organization**: Use `--prefix` and `--suffix` to organize output files by category
