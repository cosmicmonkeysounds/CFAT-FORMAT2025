"""
Audio separator module.
Extract audio from video files in batch with support for multiple output formats.
"""

import subprocess
import os
import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG_PATH: str = get_ffmpeg_exe()
except ImportError:
    FFMPEG_PATH: str = 'ffmpeg'


# =============================================================================
# Enums and Data Classes
# =============================================================================

class AudioFormat(Enum):
    """Supported audio output formats."""
    WAV = 'wav'
    MP3 = 'mp3'
    AAC = 'aac'
    M4A = 'm4a'
    OGG = 'ogg'
    FLAC = 'flac'


@dataclass(frozen=True)
class SeparationConfig:
    """Configuration for audio separation."""
    output_format: AudioFormat = AudioFormat.WAV
    bitrate: str = '192k'  # For lossy formats
    sample_rate: Optional[int] = None  # None = keep original
    channels: Optional[int] = None  # None = keep original
    output_dir: Optional[Path] = None  # None = same as source
    prefix: str = ''  # Prefix for output filenames
    suffix: str = ''  # Suffix before extension


@dataclass
class SeparationResult:
    """Result of audio separation for a single file."""
    video_path: Path
    audio_path: Optional[Path]
    success: bool
    error: Optional[str] = None


@dataclass
class RemovalResult:
    """Result of audio removal for a single file."""
    input_path: Path
    output_path: Optional[Path]
    success: bool
    error: Optional[str] = None


@dataclass(frozen=True)
class RemovalConfig:
    """Configuration for audio removal."""
    output_dir: Optional[Path] = None  # None = same as source
    prefix: str = ''  # Prefix for output filenames
    suffix: str = '_no_audio'  # Suffix before extension
    codec: str = 'copy'  # Video codec: 'copy' for stream copy (fast), or codec name for re-encode
    overwrite: bool = False  # If True, overwrite original files (ignores prefix/suffix/output_dir)


# =============================================================================
# FFmpeg Codec Functions
# =============================================================================

def get_audio_codec_args(format: AudioFormat, bitrate: str) -> List[str]:
    """Get ffmpeg codec arguments for audio format."""
    codec_map = {
        AudioFormat.WAV: ['-c:a', 'pcm_s16le'],
        AudioFormat.MP3: ['-c:a', 'libmp3lame', '-b:a', bitrate],
        AudioFormat.AAC: ['-c:a', 'aac', '-b:a', bitrate],
        AudioFormat.M4A: ['-c:a', 'aac', '-b:a', bitrate],
        AudioFormat.OGG: ['-c:a', 'libvorbis', '-q:a', '5'],
        AudioFormat.FLAC: ['-c:a', 'flac'],
    }
    return codec_map.get(format, ['-c:a', 'copy'])


# =============================================================================
# Audio Separation Functions
# =============================================================================

def extract_audio(video_path: Path, output_path: Path, config: SeparationConfig) -> Tuple[bool, Optional[str]]:
    """
    Extract audio from a single video file.
    Returns (success, error_message) tuple.
    """
    if not video_path.exists():
        return False, f"Video file not found: {video_path}"

    # Build ffmpeg command
    cmd = [FFMPEG_PATH, '-y', '-i', str(video_path)]

    # Add codec arguments
    cmd.extend(get_audio_codec_args(config.output_format, config.bitrate))

    # Add sample rate if specified
    if config.sample_rate:
        cmd.extend(['-ar', str(config.sample_rate)])

    # Add channel configuration if specified
    if config.channels:
        cmd.extend(['-ac', str(config.channels)])

    # Disable video
    cmd.extend(['-vn', str(output_path)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            return False, f"FFmpeg error: {result.stderr}"

        if not output_path.exists() or output_path.stat().st_size == 0:
            return False, "Output file was not created or is empty"

        return True, None

    except subprocess.TimeoutExpired:
        return False, "FFmpeg process timed out after 5 minutes"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def generate_output_path(video_path: Path, config: SeparationConfig) -> Path:
    """Generate output path for extracted audio file."""
    # Determine output directory
    output_dir = config.output_dir if config.output_dir else video_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build filename
    stem = video_path.stem
    filename = f"{config.prefix}{stem}{config.suffix}.{config.output_format.value}"

    return output_dir / filename


def separate_audio_batch(
    video_paths: List[Path],
    config: SeparationConfig = SeparationConfig(),
    verbose: bool = True
) -> List[SeparationResult]:
    """
    Extract audio from multiple video files.

    Args:
        video_paths: List of video file paths
        config: Configuration for audio separation
        verbose: Print progress information

    Returns:
        List of SeparationResult objects
    """
    results: List[SeparationResult] = []
    total = len(video_paths)

    if verbose:
        print(f"Processing {total} video file(s)...")
        print(f"Output format: {config.output_format.value.upper()}")
        if config.output_dir:
            print(f"Output directory: {config.output_dir}")
        print()

    for idx, video_path in enumerate(video_paths, 1):
        if verbose:
            print(f"[{idx}/{total}] Processing: {video_path.name}")

        output_path = generate_output_path(video_path, config)
        success, error = extract_audio(video_path, output_path, config)

        result = SeparationResult(
            video_path=video_path,
            audio_path=output_path if success else None,
            success=success,
            error=error
        )
        results.append(result)

        if verbose:
            if success:
                print(f"  ✓ Saved: {output_path.name}")
            else:
                print(f"  ✗ Failed: {error}")

        if verbose:
            print()

    # Print summary
    if verbose:
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        print("=" * 60)
        print(f"Summary: {successful} succeeded, {failed} failed")
        print("=" * 60)

    return results


def separate_audio_from_directory(
    directory: Path,
    config: SeparationConfig = SeparationConfig(),
    recursive: bool = False,
    video_extensions: Optional[List[str]] = None,
    verbose: bool = True
) -> List[SeparationResult]:
    """
    Extract audio from all video files in a directory.

    Args:
        directory: Directory containing video files
        config: Configuration for audio separation
        recursive: Search subdirectories
        video_extensions: List of video extensions to process (default: common formats)
        verbose: Print progress information

    Returns:
        List of SeparationResult objects
    """
    if video_extensions is None:
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']

    # Normalize extensions to lowercase
    video_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                       for ext in video_extensions]

    # Find video files
    video_paths: List[Path] = []

    if recursive:
        for ext in video_extensions:
            video_paths.extend(directory.rglob(f'*{ext}'))
    else:
        for ext in video_extensions:
            video_paths.extend(directory.glob(f'*{ext}'))

    # Sort for consistent ordering
    video_paths.sort()

    if not video_paths:
        if verbose:
            print(f"No video files found in {directory}")
        return []

    return separate_audio_batch(video_paths, config, verbose)


# =============================================================================
# Audio Removal Functions
# =============================================================================

def remove_audio_from_video(video_path: Path, output_path: Path, config: RemovalConfig) -> Tuple[bool, Optional[str]]:
    """
    Remove audio from a single video file.
    Returns (success, error_message) tuple.
    """
    if not video_path.exists():
        return False, f"Video file not found: {video_path}"

    # If overwriting, use a temporary file first
    if config.overwrite:
        # Create temp file in same directory as source for atomic replace
        temp_fd, temp_path_str = tempfile.mkstemp(
            suffix=video_path.suffix,
            dir=video_path.parent,
            prefix='.tmp_'
        )
        os.close(temp_fd)  # Close the file descriptor
        temp_path = Path(temp_path_str)
        actual_output = temp_path
    else:
        actual_output = output_path

    # Build ffmpeg command
    cmd = [FFMPEG_PATH, '-y', '-i', str(video_path)]

    # Video codec
    if config.codec == 'copy':
        cmd.extend(['-c:v', 'copy'])
    else:
        cmd.extend(['-c:v', config.codec])

    # Remove all audio streams
    cmd.extend(['-an', str(actual_output)])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            if config.overwrite and temp_path.exists():
                temp_path.unlink()
            return False, f"FFmpeg error: {result.stderr}"

        if not actual_output.exists() or actual_output.stat().st_size == 0:
            if config.overwrite and temp_path.exists():
                temp_path.unlink()
            return False, "Output file was not created or is empty"

        # If overwriting, replace the original file with temp file
        if config.overwrite:
            try:
                shutil.move(str(temp_path), str(video_path))
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                return False, f"Failed to overwrite original file: {str(e)}"

        return True, None

    except subprocess.TimeoutExpired:
        if config.overwrite and temp_path.exists():
            temp_path.unlink()
        return False, "FFmpeg process timed out after 5 minutes"
    except Exception as e:
        if config.overwrite and 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
        return False, f"Unexpected error: {str(e)}"


def generate_removal_output_path(video_path: Path, config: RemovalConfig) -> Path:
    """Generate output path for video without audio."""
    # If overwriting, return the original path
    if config.overwrite:
        return video_path

    # Determine output directory
    output_dir = config.output_dir if config.output_dir else video_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build filename
    stem = video_path.stem
    extension = video_path.suffix
    filename = f"{config.prefix}{stem}{config.suffix}{extension}"

    return output_dir / filename


def remove_audio_batch(
    video_paths: List[Path],
    config: RemovalConfig = RemovalConfig(),
    verbose: bool = True
) -> List[RemovalResult]:
    """
    Remove audio from multiple video files.

    Args:
        video_paths: List of video file paths
        config: Configuration for audio removal
        verbose: Print progress information

    Returns:
        List of RemovalResult objects
    """
    results: List[RemovalResult] = []
    total = len(video_paths)

    if verbose:
        print(f"Removing audio from {total} video file(s)...")
        print(f"Video codec: {config.codec.upper()}")
        if config.overwrite:
            print("Mode: OVERWRITE (files will be replaced in-place)")
        elif config.output_dir:
            print(f"Output directory: {config.output_dir}")
        print()

    for idx, video_path in enumerate(video_paths, 1):
        if verbose:
            print(f"[{idx}/{total}] Processing: {video_path.name}")

        output_path = generate_removal_output_path(video_path, config)
        success, error = remove_audio_from_video(video_path, output_path, config)

        result = RemovalResult(
            input_path=video_path,
            output_path=output_path if success else None,
            success=success,
            error=error
        )
        results.append(result)

        if verbose:
            if success:
                if config.overwrite:
                    print(f"  ✓ Overwritten: {output_path.name}")
                else:
                    print(f"  ✓ Saved: {output_path.name}")
            else:
                print(f"  ✗ Failed: {error}")

        if verbose:
            print()

    # Print summary
    if verbose:
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        print("=" * 60)
        print(f"Summary: {successful} succeeded, {failed} failed")
        print("=" * 60)

    return results


def remove_audio_from_directory(
    directory: Path,
    config: RemovalConfig = RemovalConfig(),
    recursive: bool = False,
    video_extensions: Optional[List[str]] = None,
    verbose: bool = True
) -> List[RemovalResult]:
    """
    Remove audio from all video files in a directory.

    Args:
        directory: Directory containing video files
        config: Configuration for audio removal
        recursive: Search subdirectories
        video_extensions: List of video extensions to process (default: common formats)
        verbose: Print progress information

    Returns:
        List of RemovalResult objects
    """
    if video_extensions is None:
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']

    # Normalize extensions to lowercase
    video_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                       for ext in video_extensions]

    # Find video files
    video_paths: List[Path] = []

    if recursive:
        for ext in video_extensions:
            video_paths.extend(directory.rglob(f'*{ext}'))
    else:
        for ext in video_extensions:
            video_paths.extend(directory.glob(f'*{ext}'))

    # Sort for consistent ordering
    video_paths.sort()

    if not video_paths:
        if verbose:
            print(f"No video files found in {directory}")
        return []

    return remove_audio_batch(video_paths, config, verbose)


# =============================================================================
# Utility Functions
# =============================================================================

def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available."""
    try:
        result = subprocess.run(
            [FFMPEG_PATH, '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def get_video_info(video_path: Path) -> Optional[dict]:
    """Get basic information about a video file using ffprobe."""
    ffprobe_path = FFMPEG_PATH.replace('ffmpeg', 'ffprobe')

    try:
        result = subprocess.run([
            ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception:
        pass

    return None


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """CLI entry point for audio separator."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Extract audio from video files in batch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract audio from all MP4 files in a directory as WAV
  python -m media_generator.audio_separator /path/to/videos

  # Extract as MP3 with custom bitrate
  python -m media_generator.audio_separator /path/to/videos -f mp3 -b 320k

  # Process specific files
  python -m media_generator.audio_separator video1.mp4 video2.mp4 -f flac

  # Recursive search with custom output directory
  python -m media_generator.audio_separator /path/to/videos -r -o /output/dir

  # Add prefix/suffix to output files
  python -m media_generator.audio_separator /path/to/videos --prefix "audio_" --suffix "_extracted"
        """
    )

    parser.add_argument(
        'inputs',
        nargs='*',
        help='Video file(s) or directory containing videos'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['wav', 'mp3', 'aac', 'm4a', 'ogg', 'flac'],
        default='wav',
        help='Output audio format (default: wav)'
    )

    parser.add_argument(
        '-b', '--bitrate',
        default='192k',
        help='Bitrate for lossy formats (default: 192k)'
    )

    parser.add_argument(
        '-r', '--sample-rate',
        type=int,
        help='Output sample rate in Hz (default: keep original)'
    )

    parser.add_argument(
        '-c', '--channels',
        type=int,
        choices=[1, 2],
        help='Number of audio channels: 1=mono, 2=stereo (default: keep original)'
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        help='Output directory (default: same as source)'
    )

    parser.add_argument(
        '--prefix',
        default='',
        help='Prefix for output filenames'
    )

    parser.add_argument(
        '--suffix',
        default='',
        help='Suffix for output filenames (before extension)'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Search subdirectories recursively'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress progress output'
    )

    parser.add_argument(
        '--check-ffmpeg',
        action='store_true',
        help='Check if ffmpeg is available and exit'
    )

    args = parser.parse_args()

    # Check ffmpeg availability
    if args.check_ffmpeg:
        if check_ffmpeg_available():
            print(f"✓ FFmpeg is available at: {FFMPEG_PATH}")
            sys.exit(0)
        else:
            print(f"✗ FFmpeg is not available or not working")
            sys.exit(1)

    # Require inputs if not just checking ffmpeg
    if not args.inputs:
        parser.error("the following arguments are required: inputs")

    if not check_ffmpeg_available():
        print("Error: FFmpeg is not available or not working", file=sys.stderr)
        print(f"Expected path: {FFMPEG_PATH}", file=sys.stderr)
        sys.exit(1)

    # Build configuration
    config = SeparationConfig(
        output_format=AudioFormat(args.format),
        bitrate=args.bitrate,
        sample_rate=args.sample_rate,
        channels=args.channels,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        prefix=args.prefix,
        suffix=args.suffix
    )

    # Process inputs
    video_paths: List[Path] = []

    for input_path in args.inputs:
        p = Path(input_path)

        if not p.exists():
            print(f"Warning: {input_path} does not exist, skipping", file=sys.stderr)
            continue

        if p.is_file():
            video_paths.append(p)
        elif p.is_dir():
            # Process directory
            results = separate_audio_from_directory(
                p,
                config=config,
                recursive=args.recursive,
                verbose=not args.quiet
            )
            # Don't add to video_paths since we already processed
            continue
        else:
            print(f"Warning: {input_path} is not a file or directory, skipping", file=sys.stderr)

    # Process individual files if any
    if video_paths:
        results = separate_audio_batch(video_paths, config, verbose=not args.quiet)

        # Exit with error code if any failed
        if any(not r.success for r in results):
            sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
