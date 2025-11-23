#!/usr/bin/env python3
"""
Generate unique test media files with random characteristics.
Self-contained with bundled ffmpeg - no external dependencies required!
"""

import argparse
import sys
import re
import numpy as np
from numpy.typing import NDArray
from pathlib import Path
from typing import Optional, List, Tuple

from media_generator.audio import AudioConfig, MediaOutput, write_audio_file
from media_generator.video import VideoConfig, write_video_file, embed_audio_in_video
from media_generator.image import write_image_file, write_svg_file, write_gif_file
from media_generator.audio_separator import (
    separate_audio_batch,
    separate_audio_from_directory,
    SeparationConfig,
    AudioFormat as SeparatorAudioFormat
)


# =============================================================================
# File Management
# =============================================================================

def find_existing_files(output_dir: Path, base_name: str, extension: str) -> Optional[int]:
    """Find highest numbered file matching pattern. Returns None if no matches."""
    pattern = re.compile(rf'^{re.escape(base_name)}_(\d+)\.{extension}$')
    max_num = 0
    found = False

    if output_dir.exists():
        for file in output_dir.iterdir():
            match = pattern.match(file.name)
            if match:
                found = True
                max_num = max(max_num, int(match.group(1)))

    return max_num if found else None


def prompt_conflict_resolution(output_dir: Path, base_name: str,
                              max_existing: int, file_type: str) -> Tuple[int, bool]:
    """Ask user how to handle existing files. Returns (start_num, overwrite)."""
    print(f"\n⚠️  Found existing files matching pattern '{base_name}_*.{file_type}'")
    print(f"    Highest number found: {max_existing}\n")
    print("Options:")
    print(f"  1) Overwrite - Start from 1 (will overwrite existing files)")
    print(f"  2) Continue - Start from {max_existing + 1} (preserve existing files)\n")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == '1':
        return 1, True
    else:
        return max_existing + 1, False


# =============================================================================
# Frequency Generation
# =============================================================================

def generate_frequencies(n: int, min_freq: float, max_freq: float) -> List[float]:
    """Generate evenly spaced frequencies."""
    if n == 1:
        return [min_freq]
    return list(np.linspace(min_freq, max_freq, n))


# =============================================================================
# Interactive Mode
# =============================================================================

def padded_input(prompt: str, padding_lines: int = 4) -> str:
    """Get input with visual padding for better readability."""
    print("\n" * (padding_lines - 1))
    return input(f"  → {prompt} ").strip()


def section_header(title: str) -> None:
    """Print a pretty section header."""
    print("\n" + "─" * 70)
    print(f"  {title}")
    print("─" * 70)


def interactive_mode() -> Optional[List[str]]:
    """Guide user through media generation options. Returns argument list or None if cancelled."""
    print("\n" + "═" * 70)
    print("  🎨 Media Generator - Interactive Mode")
    print("═" * 70)
    print("\n  Welcome! I'll guide you through creating media files.")
    print("  Each prompt has space above it so you can easily see your options.\n")

    section_header("Step 1: Choose Media Type")

    print("\n  What type of media do you want to generate?\n")
    print("    1️⃣  Video (MP4)")
    print("    2️⃣  Image (JPG, PNG, WebP, BMP, TIFF, SVG)")
    print("    3️⃣  Animation (GIF)")
    print("    4️⃣  Audio (WAV, OGG, MP3, AAC, FLAC)")
    print("    5️⃣  Extract Audio from Videos (Audio Separator)")

    choice = padded_input("Enter choice (1-5):")

    if choice not in ['1', '2', '3', '4', '5']:
        print("\n  ❌ Invalid choice. Exiting.\n")
        return None

    section_header("Step 2: Number of Files")

    n = padded_input("How many files do you want to generate?")
    args = [n]

    # Video
    if choice == '1':
        section_header("Step 3: Video Configuration")

        print("\n  Choose video codec:\n")
        print("    1️⃣  MPEG-4 (default, most compatible)")
        print("    2️⃣  H.264 (high quality)")
        print("    3️⃣  H.265 (best compression)")

        codec_choice = padded_input("Enter choice (1-3) [default: 1]:") or '1'
        codec_map = {'1': 'mpeg4', '2': 'h264', '3': 'h265'}
        args.extend(['--codec', codec_map.get(codec_choice, 'mpeg4')])

        duration = padded_input("Duration in seconds [default: 1]:") or '1'
        args.extend(['-d', duration])

        print("\n  Choose resolution:\n")
        print("    1️⃣  1920x1080 (Full HD)")
        print("    2️⃣  1280x720 (HD)")
        print("    3️⃣  640x480 (SD)")
        print("    4️⃣  Custom")

        res_choice = padded_input("Enter choice (1-4) [default: 1]:") or '1'

        if res_choice == '2':
            args.extend(['-w', '1280', '-H', '720'])
        elif res_choice == '3':
            args.extend(['-w', '640', '-H', '480'])
        elif res_choice == '4':
            width = padded_input("Width in pixels:")
            height = padded_input("Height in pixels:")
            args.extend(['-w', width, '-H', height])
        else:
            args.extend(['-w', '1920', '-H', '1080'])

        fps = padded_input("Frames per second (FPS) [default: 30]:") or '30'
        args.extend(['-f', fps])

        section_header("Step 4: Audio Options")

        print("\n  Do you want audio in your videos?\n")
        print("    1️⃣  No audio")
        print("    2️⃣  Embed audio in video")
        print("    3️⃣  Separate audio file")
        print("    4️⃣  Both embedded and separate")

        audio_choice = padded_input("Enter choice (1-4) [default: 1]:") or '1'

        if audio_choice in ['2', '4']:
            args.append('--embed-audio')

        if audio_choice in ['2', '3', '4']:
            section_header("Step 5: Audio Quality Settings")

            print("\n  Sample rate:\n")
            print("    1️⃣  44100 Hz (CD quality, default)")
            print("    2️⃣  48000 Hz (professional)")
            print("    3️⃣  96000 Hz (high-res)")
            print("    4️⃣  22050 Hz (lower quality)")
            print("    5️⃣  Custom (e.g., 43124.3123 Hz)")

            sample_choice = padded_input("Enter choice (1-5) [default: 1]:") or '1'
            if sample_choice == '5':
                custom_rate = padded_input("Enter custom sample rate (Hz):")
                args.extend(['--sample-rate', custom_rate])
            else:
                sample_map = {'1': '44100', '2': '48000', '3': '96000', '4': '22050'}
                args.extend(['--sample-rate', sample_map.get(sample_choice, '44100')])

            print("\n  Number of channels:\n")
            print("    1️⃣  Mono (1 channel)")
            print("    2️⃣  Stereo (2 channels)")

            channel_choice = padded_input("Enter choice (1-2) [default: 1]:") or '1'
            channel_map = {'1': '1', '2': '2'}
            args.extend(['--channels', channel_map.get(channel_choice, '1')])

            print("\n  Bit depth:\n")
            print("    1️⃣  16-bit (standard, default)")
            print("    2️⃣  24-bit (high quality)")

            bit_choice = padded_input("Enter choice (1-2) [default: 1]:") or '1'
            bit_map = {'1': '16', '2': '24'}
            args.extend(['--bit-depth', bit_map.get(bit_choice, '16')])

        if audio_choice in ['3', '4']:
            args.append('--audio-file')

            print("\n  Audio format for separate file:\n")
            print("    1️⃣  WAV (uncompressed)")
            print("    2️⃣  OGG (Vorbis, compressed)")
            print("    3️⃣  MP3 (compressed)")
            print("    4️⃣  AAC (M4A, compressed)")
            print("    5️⃣  FLAC (lossless)")

            audio_fmt = padded_input("Enter choice (1-5) [default: 1]:") or '1'
            fmt_map = {'1': 'wav', '2': 'ogg', '3': 'mp3', '4': 'm4a', '5': 'flac'}
            args.extend(['--audio-format', fmt_map.get(audio_fmt, 'wav')])

        args.extend(['-t', 'mp4'])

    # Image
    elif choice == '2':
        section_header("Step 3: Image Configuration")

        print("\n  Choose image format:\n")
        print("    1️⃣  JPG (photo quality)")
        print("    2️⃣  PNG (lossless)")
        print("    3️⃣  WebP (modern, efficient)")
        print("    4️⃣  BMP (bitmap)")
        print("    5️⃣  TIFF (high quality)")
        print("    6️⃣  SVG (vector graphics)")

        fmt_choice = padded_input("Enter choice (1-6) [default: 1]:") or '1'
        fmt_map = {'1': 'jpg', '2': 'png', '3': 'webp', '4': 'bmp', '5': 'tiff', '6': 'svg'}
        args.extend(['-t', fmt_map.get(fmt_choice, 'jpg')])

        print("\n  Choose resolution:\n")
        print("    1️⃣  1920x1080 (Full HD)")
        print("    2️⃣  1280x720 (HD)")
        print("    3️⃣  800x600 (SVGA)")
        print("    4️⃣  Custom")

        res_choice = padded_input("Enter choice (1-4) [default: 1]:") or '1'

        if res_choice == '2':
            args.extend(['-w', '1280', '-H', '720'])
        elif res_choice == '3':
            args.extend(['-w', '800', '-H', '600'])
        elif res_choice == '4':
            width = padded_input("Width in pixels:")
            height = padded_input("Height in pixels:")
            args.extend(['-w', width, '-H', height])
        else:
            args.extend(['-w', '1920', '-H', '1080'])

    # GIF
    elif choice == '3':
        section_header("Step 3: Animation Configuration")

        args.extend(['-t', 'gif'])

        duration = padded_input("Duration in seconds [default: 1]:") or '1'
        args.extend(['-d', duration])

        fps = padded_input("Frames per second (FPS) [default: 10]:") or '10'
        args.extend(['-f', fps])

        print("\n  Choose resolution:\n")
        print("    1️⃣  1920x1080 (Full HD)")
        print("    2️⃣  800x600 (Standard)")
        print("    3️⃣  480x360 (Small)")
        print("    4️⃣  Custom")

        res_choice = padded_input("Enter choice (1-4) [default: 2]:") or '2'

        if res_choice == '1':
            args.extend(['-w', '1920', '-H', '1080'])
        elif res_choice == '3':
            args.extend(['-w', '480', '-H', '360'])
        elif res_choice == '4':
            width = padded_input("Width in pixels:")
            height = padded_input("Height in pixels:")
            args.extend(['-w', width, '-H', height])
        else:
            args.extend(['-w', '800', '-H', '600'])

    # Audio
    elif choice == '4':
        section_header("Step 3: Audio Configuration")

        print("\n  Choose audio format:\n")
        print("    1️⃣  WAV (uncompressed, high quality)")
        print("    2️⃣  OGG (Vorbis, compressed, open source)")
        print("    3️⃣  MP3 (compressed, universal)")
        print("    4️⃣  AAC/M4A (compressed, Apple)")
        print("    5️⃣  FLAC (lossless, compressed)")

        fmt_choice = padded_input("Enter choice (1-5) [default: 1]:") or '1'
        fmt_map = {'1': 'wav', '2': 'ogg', '3': 'mp3', '4': 'm4a', '5': 'flac'}
        args.extend(['-t', fmt_map.get(fmt_choice, 'wav')])

        duration = padded_input("Duration in seconds [default: 1]:") or '1'
        args.extend(['-d', duration])

        print("\n  Sample rate:\n")
        print("    1️⃣  44100 Hz (CD quality, default)")
        print("    2️⃣  48000 Hz (professional)")
        print("    3️⃣  96000 Hz (high-res)")
        print("    4️⃣  22050 Hz (lower quality)")
        print("    5️⃣  Custom (e.g., 43124.3123 Hz or pi^10)")

        sample_choice = padded_input("Enter choice (1-5) [default: 1]:") or '1'
        if sample_choice == '5':
            custom_rate = padded_input("Enter custom sample rate (Hz):")
            args.extend(['--sample-rate', custom_rate])
        else:
            sample_map = {'1': '44100', '2': '48000', '3': '96000', '4': '22050'}
            args.extend(['--sample-rate', sample_map.get(sample_choice, '44100')])

        print("\n  Number of channels:\n")
        print("    1️⃣  Mono (1 channel)")
        print("    2️⃣  Stereo (2 channels)")

        channels_choice = padded_input("Enter choice (1-2) [default: 1]:") or '1'
        channel_map = {'1': '1', '2': '2'}
        args.extend(['--channels', channel_map.get(channels_choice, '1')])

        print("\n  Bit depth:\n")
        print("    1️⃣  16-bit (standard, default)")
        print("    2️⃣  24-bit (high quality)")

        bit_choice = padded_input("Enter choice (1-2) [default: 1]:") or '1'
        bit_map = {'1': '16', '2': '24'}
        args.extend(['--bit-depth', bit_map.get(bit_choice, '16')])

        use_custom_freq = padded_input("Use custom frequency range? (y/n) [default: n]:").lower()
        if use_custom_freq == 'y':
            min_freq = padded_input("Minimum frequency (Hz) [default: 100]:") or '100'
            max_freq = padded_input("Maximum frequency (Hz) [default: 1000]:") or '1000'
            args.extend(['--min-freq', min_freq, '--max-freq', max_freq])

    # Audio Separator
    elif choice == '5':
        args.append('--separate-audio')

        section_header("Step 3: Select Video Files or Directory")

        print("\n  How do you want to specify videos?\n")
        print("    1️⃣  Specific video file(s)")
        print("    2️⃣  Directory containing videos")

        source_choice = padded_input("Enter choice (1-2) [default: 2]:") or '2'

        if source_choice == '1':
            video_files = padded_input("Video file path(s) (comma-separated):")
            args.extend(['--video-files', video_files])
        else:
            video_dir = padded_input("Directory path containing videos:")
            args.extend(['--video-dir', video_dir])

            recursive = padded_input("Search subdirectories recursively? (y/n) [default: n]:").lower()
            if recursive == 'y':
                args.append('--recursive')

        section_header("Step 4: Audio Output Configuration")

        print("\n  Choose audio format:\n")
        print("    1️⃣  WAV (uncompressed, high quality)")
        print("    2️⃣  MP3 (compressed, universal)")
        print("    3️⃣  AAC (compressed, high quality)")
        print("    4️⃣  M4A (Apple-friendly)")
        print("    5️⃣  OGG (Vorbis, compressed)")
        print("    6️⃣  FLAC (lossless, compressed)")

        sep_fmt_choice = padded_input("Enter choice (1-6) [default: 1]:") or '1'
        sep_fmt_map = {'1': 'wav', '2': 'mp3', '3': 'aac', '4': 'm4a', '5': 'ogg', '6': 'flac'}
        args.extend(['--sep-format', sep_fmt_map.get(sep_fmt_choice, 'wav')])

        if sep_fmt_choice in ['2', '3', '4']:
            bitrate = padded_input("Bitrate [default: 192k]:") or '192k'
            args.extend(['--sep-bitrate', bitrate])

        output_dir = padded_input("Output directory [default: same as video]:") or ''
        if output_dir:
            args.extend(['--sep-output-dir', output_dir])

        prefix = padded_input("Filename prefix [default: none]:") or ''
        if prefix:
            args.extend(['--sep-prefix', prefix])

        suffix = padded_input("Filename suffix [default: none]:") or ''
        if suffix:
            args.extend(['--sep-suffix', suffix])

        # Skip general output options for separator
        print("\n" + "═" * 70)
        print("  📋 Summary")
        print("═" * 70)
        print(f"\n  Audio format: {sep_fmt_map.get(sep_fmt_choice, 'wav').upper()}")
        if output_dir:
            print(f"  Output directory: {output_dir}/")
        print("\n" + "═" * 70)

        confirm = padded_input("Proceed with audio separation? (y/n) [default: y]:").lower() or 'y'

        if confirm != 'y':
            print("\n  ❌ Cancelled.\n")
            return None

        return args

    # Output options
    section_header("Step 4: Output Settings")

    output_dir = padded_input("Output directory [default: test_media]:") or 'test_media'
    args.extend(['-o', output_dir])

    base_name = padded_input("Base filename [default: test_media]:") or 'test_media'
    args.extend(['-n', base_name])

    # Summary
    print("\n" + "═" * 70)
    print("  📋 Summary")
    print("═" * 70)
    print(f"\n  Files to generate: {n}")
    print(f"  Output directory: {output_dir}/")
    print(f"  Base filename: {base_name}")
    print("\n" + "═" * 70)

    confirm = padded_input("Proceed with generation? (y/n) [default: y]:").lower() or 'y'

    if confirm != 'y':
        print("\n  ❌ Cancelled.\n")
        return None

    return args


# =============================================================================
# Main Generation Logic
# =============================================================================

def generate_media_files(args: argparse.Namespace) -> None:
    """Main generation orchestration using functional composition."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for conflicts
    max_existing = find_existing_files(output_dir, args.name, args.type)
    if max_existing is not None:
        start_num, overwrite = prompt_conflict_resolution(output_dir, args.name, max_existing, args.type)
    else:
        start_num = 1
        overwrite = False

    # Media type descriptions
    media_descriptions = {
        'mp4': f'MP4 videos ({args.width}x{args.height}, {args.duration}s @ {args.fps}fps, Codec: {args.codec.upper()})',
        'jpg': f'JPG images ({args.width}x{args.height})',
        'png': f'PNG images ({args.width}x{args.height})',
        'webp': f'WebP images ({args.width}x{args.height})',
        'bmp': f'BMP images ({args.width}x{args.height})',
        'tiff': f'TIFF images ({args.width}x{args.height})',
        'svg': f'SVG vector graphics ({args.width}x{args.height})',
        'gif': f'GIF animations ({args.width}x{args.height}, {args.duration}s @ {args.fps}fps)',
        'wav': f'WAV audio ({args.channels}ch, {args.bit_depth}-bit, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'ogg': f'OGG audio ({args.channels}ch, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'mp3': f'MP3 audio ({args.channels}ch, {args.mp3_bitrate}, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'aac': f'AAC audio ({args.channels}ch, {args.aac_bitrate}, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'm4a': f'M4A audio ({args.channels}ch, {args.aac_bitrate}, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'flac': f'FLAC audio ({args.channels}ch, lossless, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)'
    }

    # Add audio info for videos
    if args.type == 'mp4':
        audio_parts = []
        if args.embed_audio:
            audio_parts.append('embedded')
        if args.audio_file:
            audio_parts.append(f'file:{args.audio_format.upper()}')
        if audio_parts:
            media_descriptions['mp4'] += f", Audio: {' + '.join(audio_parts)}"

    print(f"\n🎬 Generating {args.n} {args.type.upper()} files...")
    print(f"   Type: {media_descriptions[args.type]}")
    print(f"   Output: {output_dir}/\n")

    # Generate frequencies for audio
    is_audio_needed = args.type in ['wav', 'ogg', 'mp3', 'aac', 'm4a', 'flac'] or \
                     (args.type == 'mp4' and (args.embed_audio or args.audio_file))
    frequencies = generate_frequencies(args.n, args.min_freq, args.max_freq) if is_audio_needed else []

    # Generate files
    for i in range(args.n):
        file_num = start_num + i
        output_path = output_dir / f"{args.name}_{file_num}.{args.type}"
        output = MediaOutput(path=output_path, format=args.type)

        # Audio files
        if args.type in ['wav', 'ogg', 'mp3', 'aac', 'm4a', 'flac']:
            audio_config = AudioConfig(
                frequency=frequencies[i],
                duration=args.duration,
                sample_rate=args.sample_rate,
                channels=args.channels,
                bit_depth=args.bit_depth,
                max_freq=args.max_freq,
                bitrate=args.aac_bitrate if args.type in ['aac', 'm4a'] else args.mp3_bitrate
            )
            desc = write_audio_file(output, audio_config)
            print(f"✓ Generated: {output_path.name} ({desc})")

        # Video files
        elif args.type == 'mp4':
            video_config = VideoConfig(
                width=args.width,
                height=args.height,
                fps=args.fps,
                duration=args.duration,
                codec=args.codec
            )
            codec_desc: str
            base_color: NDArray[np.uint8]
            codec_desc, base_color = write_video_file(output, video_config)

            audio_info: str = ""
            if args.embed_audio or args.audio_file:
                audio_config = AudioConfig(
                    frequency=frequencies[i],
                    duration=args.duration,
                    sample_rate=args.sample_rate,
                    channels=args.channels,
                    bit_depth=args.bit_depth,
                    max_freq=args.max_freq
                )

                if args.audio_file:
                    audio_path = output_path.with_suffix(f'.{args.audio_format}')
                    audio_output = MediaOutput(path=audio_path, format=args.audio_format)
                    write_audio_file(audio_output, audio_config)
                    print(f"  ↳ Audio: {audio_path.name}")

                if args.embed_audio:
                    if embed_audio_in_video(output_path, audio_config, args.duration):
                        ch_desc = "mono" if args.channels == 1 else "stereo"
                        audio_info = f", Audio: {frequencies[i]:.1f}Hz {ch_desc}"

            print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)}, Codec: {codec_desc}{audio_info})")

        # Image files
        elif args.type in ['jpg', 'png', 'webp', 'bmp', 'tiff']:
            base_color: NDArray[np.uint8] = write_image_file(output, args.width, args.height)
            print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)})")

        # SVG
        elif args.type == 'svg':
            base_color: NDArray[np.uint8] = write_svg_file(output, args.width, args.height)
            print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)})")

        # GIF
        elif args.type == 'gif':
            gif_config: VideoConfig = VideoConfig(
                width=args.width,
                height=args.height,
                fps=args.fps,
                duration=args.duration
            )
            base_color: NDArray[np.uint8] = write_gif_file(output, gif_config)
            total_frames = int(args.fps * args.duration)
            print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)}, {total_frames} frames)")

    print(f"\n✅ Done! Generated {args.n} {args.type.upper()} files in '{output_dir}/'")


# =============================================================================
# CLI Parser
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all options."""
    parser = argparse.ArgumentParser(
        description='Generate unique test media files with random characteristics'
    )

    parser.add_argument('n', type=int, nargs='?', help='Number of files to generate')
    parser.add_argument('-t', '--type', type=str,
                       choices=['mp4', 'jpg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'svg',
                               'wav', 'ogg', 'mp3', 'aac', 'm4a', 'flac'],
                       default='mp4', help='Media type to generate (default: mp4)')
    parser.add_argument('-n', '--name', type=str, default='test_media',
                       help='Base name for files (default: test_media)')
    parser.add_argument('-o', '--output-dir', type=str, default='test_media',
                       help='Output directory (default: test_media)')

    # Video/Image options
    parser.add_argument('-w', '--width', type=int, default=1920,
                       help='Width for video/image (default: 1920)')
    parser.add_argument('-H', '--height', type=int, default=1080,
                       help='Height for video/image (default: 1080)')
    parser.add_argument('-f', '--fps', type=float, default=30,
                       help='Frames per second for video/GIF (default: 30, supports decimals like 23.98)')
    parser.add_argument('-d', '--duration', type=int, default=1,
                       help='Duration in seconds for video/GIF/audio (default: 1)')

    # Audio options
    parser.add_argument('--min-freq', type=float, default=100,
                       help='Minimum frequency for audio (default: 100)')
    parser.add_argument('--max-freq', type=float, default=1000,
                       help='Maximum frequency for audio (default: 1000)')
    parser.add_argument('--channels', type=int, default=1,
                       help='Number of audio channels (1=mono, 2=stereo) (default: 1)')
    parser.add_argument('--sample-rate', type=float, default=44100,
                       help='Sample rate for audio files in Hz (default: 44100, supports decimals like 43124.3123)')
    parser.add_argument('--bit-depth', type=int, default=16,
                       help='Bit depth for WAV files (default: 16)')

    # Video codec
    parser.add_argument('--codec', type=str,
                       choices=['h264', 'h265', 'vp9', 'av1', 'mpeg4', 'mjpeg', 'xvid'],
                       default='mpeg4',
                       help='Video codec to use for MP4/video generation (default: mpeg4)')

    # Audio options for videos
    parser.add_argument('--embed-audio', action='store_true',
                       help='Embed audio track into video files')
    parser.add_argument('--audio-file', action='store_true',
                       help='Generate standalone audio file alongside video')
    parser.add_argument('--audio-format', type=str,
                       choices=['wav', 'ogg', 'mp3', 'aac', 'm4a', 'flac'],
                       default='wav',
                       help='Format for standalone audio files when using --audio-file (default: wav)')
    parser.add_argument('--mp3-bitrate', type=str, default='192k',
                       help='Bitrate for MP3 files (default: 192k)')
    parser.add_argument('--aac-bitrate', type=str, default='192k',
                       help='Bitrate for AAC/M4A files (default: 192k)')

    # Audio separator options
    parser.add_argument('--separate-audio', action='store_true',
                       help='Run audio separator to extract audio from videos')
    parser.add_argument('--video-files', type=str,
                       help='Comma-separated list of video file paths to extract audio from')
    parser.add_argument('--video-dir', type=str,
                       help='Directory containing video files to extract audio from')
    parser.add_argument('--recursive', action='store_true',
                       help='Search subdirectories recursively when using --video-dir')
    parser.add_argument('--sep-format', type=str,
                       choices=['wav', 'mp3', 'aac', 'm4a', 'ogg', 'flac'],
                       default='wav',
                       help='Output audio format for separator (default: wav)')
    parser.add_argument('--sep-bitrate', type=str, default='192k',
                       help='Bitrate for lossy audio formats in separator (default: 192k)')
    parser.add_argument('--sep-output-dir', type=str,
                       help='Output directory for separated audio files (default: same as video)')
    parser.add_argument('--sep-prefix', type=str, default='',
                       help='Prefix for separated audio filenames')
    parser.add_argument('--sep-suffix', type=str, default='',
                       help='Suffix for separated audio filenames (before extension)')
    parser.add_argument('--sep-sample-rate', type=int,
                       help='Sample rate for separated audio in Hz (default: keep original)')
    parser.add_argument('--sep-channels', type=int, choices=[1, 2],
                       help='Number of channels for separated audio: 1=mono, 2=stereo (default: keep original)')

    return parser


# =============================================================================
# Audio Separator Logic
# =============================================================================

def run_audio_separator(args: argparse.Namespace) -> None:
    """Run the audio separator with the given configuration."""
    # Build separation config
    config = SeparationConfig(
        output_format=SeparatorAudioFormat(args.sep_format),
        bitrate=args.sep_bitrate,
        sample_rate=args.sep_sample_rate if hasattr(args, 'sep_sample_rate') else None,
        channels=args.sep_channels if hasattr(args, 'sep_channels') else None,
        output_dir=Path(args.sep_output_dir) if args.sep_output_dir else None,
        prefix=args.sep_prefix,
        suffix=args.sep_suffix
    )

    # Process video files or directory
    if args.video_files:
        # Split comma-separated file paths and create Path objects
        video_paths = [Path(p.strip()) for p in args.video_files.split(',')]

        # Validate files exist
        for path in video_paths:
            if not path.exists():
                print(f"Error: Video file not found: {path}", file=sys.stderr)
                sys.exit(1)

        results = separate_audio_batch(video_paths, config, verbose=True)

    elif args.video_dir:
        video_dir = Path(args.video_dir)

        if not video_dir.exists() or not video_dir.is_dir():
            print(f"Error: Directory not found or not a directory: {video_dir}", file=sys.stderr)
            sys.exit(1)

        results = separate_audio_from_directory(
            directory=video_dir,
            config=config,
            recursive=args.recursive,
            verbose=True
        )
    else:
        print("Error: Either --video-files or --video-dir must be specified with --separate-audio", file=sys.stderr)
        sys.exit(1)

    # Exit with error code if any failed
    if any(not r.success for r in results):
        sys.exit(1)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point."""
    parser = create_parser()

    # Check for interactive mode
    if len(sys.argv) == 1:
        interactive_args = interactive_mode()
        if interactive_args is None:
            return
        args = parser.parse_args(interactive_args)
    else:
        args = parser.parse_args()

    # Check if running audio separator
    if args.separate_audio:
        run_audio_separator(args)
        return

    # Validate
    if args.n is None:
        parser.error("the following arguments are required: n")

    generate_media_files(args)


if __name__ == '__main__':
    main()
