#!/usr/bin/env python3
"""
Generate unique test media files (MP4, JPG, PNG, GIF, WAV) with random characteristics.
Videos and images use random colors and effects. Audio files use triangle wave tones.
"""

import cv2
import numpy as np
import argparse
import re
from pathlib import Path
from PIL import Image
import scipy.signal
import scipy.io.wavfile as wavfile


def find_existing_files(output_dir, base_name, extension):
    """
    Find existing files matching the naming pattern and return the highest number.
    Returns None if no matching files found.
    """
    pattern = re.compile(rf'^{re.escape(base_name)}_(\d+)\.{extension}$')
    max_num = 0
    found = False

    if output_dir.exists():
        for file in output_dir.iterdir():
            match = pattern.match(file.name)
            if match:
                found = True
                num = int(match.group(1))
                max_num = max(max_num, num)

    return max_num if found else None


def prompt_conflict_resolution(output_dir, base_name, max_existing, extension):
    """
    Prompt user to decide how to handle existing files.
    Returns (start_number, overwrite_mode)
    """
    print(f"\n⚠️  Found existing files matching pattern '{base_name}_*.{extension}'")
    print(f"    Highest number found: {max_existing}")
    print(f"\nOptions:")
    print(f"  1) Overwrite - Start from 1 (will overwrite existing files)")
    print(f"  2) Continue - Start from {max_existing + 1} (preserve existing files)")

    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        if choice == '1':
            return 1, True
        elif choice == '2':
            return max_existing + 1, False
        else:
            print("Invalid choice. Please enter 1 or 2.")


def apply_random_effects(frame, effect_intensity=0.3):
    """
    Apply random shader-like effects to make each frame unique.
    Effects include noise, scanlines, chromatic shift, and grain.
    """
    h, w = frame.shape[:2]

    # Random noise overlay
    if np.random.random() > 0.3:
        noise = np.random.randint(-30, 30, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise * effect_intensity, 0, 255).astype(np.uint8)

    # Random scanlines
    if np.random.random() > 0.5:
        scanline_spacing = np.random.randint(2, 8)
        scanline_intensity = np.random.uniform(0.1, 0.4)
        for y in range(0, h, scanline_spacing):
            frame[y:y+1] = frame[y:y+1] * (1 - scanline_intensity)

    # Chromatic aberration (slight RGB channel shift)
    if np.random.random() > 0.4:
        shift = np.random.randint(1, 4)
        direction = np.random.choice(['horizontal', 'vertical'])
        if direction == 'horizontal':
            frame[:, shift:, 0] = frame[:, :-shift, 0]  # Shift red channel
            frame[:, :-shift, 2] = frame[:, shift:, 2]  # Shift blue channel
        else:
            frame[shift:, :, 0] = frame[:-shift, :, 0]
            frame[:-shift, :, 2] = frame[shift:, :, 2]

    # Random grain/texture
    if np.random.random() > 0.3:
        grain = np.random.normal(0, 5, frame.shape).astype(np.int16)
        frame = np.clip(frame.astype(np.int16) + grain, 0, 255).astype(np.uint8)

    # Random vignette
    if np.random.random() > 0.6:
        vignette_intensity = np.random.uniform(0.2, 0.5)
        center_x, center_y = w // 2, h // 2
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        vignette = 1 - (dist / max_dist) * vignette_intensity
        vignette = np.clip(vignette, 0, 1)
        frame = (frame * vignette[:, :, np.newaxis]).astype(np.uint8)

    return frame


def generate_random_frame(width, height, seed=None):
    """
    Generate a single random frame with effects.
    """
    if seed is not None:
        np.random.seed(seed)

    # Random base color
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)
    color_variance = np.random.randint(5, 30)

    # Create base frame with slight color variation
    color = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
    color = np.clip(color, 0, 255).astype(np.uint8)

    # Create solid color frame (BGR format for OpenCV)
    frame = np.full((height, width, 3), color[::-1], dtype=np.uint8)

    # Apply random effects
    frame = apply_random_effects(frame, effect_intensity=0.4)

    return frame, base_color


def generate_video(output_path, width=1920, height=1080, fps=30, duration=1):
    """
    Generate a single test video with random color and effects.
    """
    # Random base color
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)

    # Add some color variation for interest
    color_variance = np.random.randint(5, 30)

    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    total_frames = fps * duration

    # Generate unique noise seed for this video
    video_seed = np.random.randint(0, 1000000)

    for frame_num in range(total_frames):
        # Set seed for reproducible but unique per-video randomness
        np.random.seed(video_seed + frame_num)

        # Create base frame with slight color variation
        color = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
        color = np.clip(color, 0, 255).astype(np.uint8)

        # Create solid color frame (BGR format for OpenCV)
        frame = np.full((height, width, 3), color[::-1], dtype=np.uint8)

        # Apply random effects
        frame = apply_random_effects(frame, effect_intensity=0.4)

        # Write frame
        out.write(frame)

    out.release()
    print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)})")


def generate_image(output_path, width=1920, height=1080, format='jpg'):
    """
    Generate a single test image (JPG or PNG) with random color and effects.
    """
    seed = np.random.randint(0, 1000000)
    frame, base_color = generate_random_frame(width, height, seed)

    # Convert BGR to RGB for PIL
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Save using PIL
    img = Image.fromarray(frame_rgb)
    img.save(str(output_path), quality=95 if format.lower() == 'jpg' else None)

    print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)})")


def generate_gif(output_path, width=1920, height=1080, fps=30, duration=1):
    """
    Generate a single test GIF with random color and effects.
    """
    # Random base color
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)
    color_variance = np.random.randint(5, 30)

    total_frames = fps * duration
    video_seed = np.random.randint(0, 1000000)

    frames = []
    for frame_num in range(total_frames):
        # Set seed for reproducible but unique per-GIF randomness
        np.random.seed(video_seed + frame_num)

        # Create base frame with slight color variation
        color = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
        color = np.clip(color, 0, 255).astype(np.uint8)

        # Create solid color frame (BGR format for OpenCV)
        frame = np.full((height, width, 3), color[::-1], dtype=np.uint8)

        # Apply random effects
        frame = apply_random_effects(frame, effect_intensity=0.4)

        # Convert BGR to RGB for PIL
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(Image.fromarray(frame_rgb))

    # Save as GIF
    frames[0].save(
        str(output_path),
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),  # duration per frame in ms
        loop=0
    )

    print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)}, {len(frames)} frames)")


def generate_triangle_wave(frequency, sample_rate, duration):
    """
    Generate a triangle wave at the specified frequency.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Triangle wave using sawtooth with width=0.5
    wave = scipy.signal.sawtooth(2 * np.pi * frequency * t, width=0.5)
    return wave


def generate_wav(output_path, frequency, duration=1, sample_rate=44100, channels=1,
                bit_depth=16, max_freq=1000):
    """
    Generate a WAV file with low-pass filtered triangle wave tone at -12dBFS.
    Supports arbitrary bit depths (1-32 bits). Non-standard bit depths are quantized
    and stored in the next larger standard container (8, 16, 24, or 32-bit).
    """

    # Generate triangle wave
    wave = generate_triangle_wave(frequency, sample_rate, duration)

    # Apply low-pass filter (cutoff at 2x the frequency or max_freq, whichever is lower)
    cutoff = min(frequency * 2, max_freq)
    nyquist = sample_rate / 2
    normalized_cutoff = cutoff / nyquist

    # Design a 4th order Butterworth low-pass filter
    b, a = scipy.signal.butter(4, normalized_cutoff, btype='low')
    wave = scipy.signal.filtfilt(b, a, wave)

    # Normalize to -12dBFS
    # -12dBFS means the amplitude should be 10^(-12/20) = 0.251189
    target_amplitude = 10 ** (-12 / 20)
    wave = wave / np.max(np.abs(wave)) * target_amplitude

    # Validate bit depth
    if bit_depth < 1 or bit_depth > 32:
        raise ValueError(f"Bit depth must be between 1 and 32, got {bit_depth}")

    # Determine container format (standard WAV bit depths)
    if bit_depth <= 8:
        container_bits = 8
        dtype = np.uint8
        is_unsigned = True
    elif bit_depth <= 16:
        container_bits = 16
        dtype = np.int16
        is_unsigned = False
    elif bit_depth <= 24:
        container_bits = 24
        dtype = np.int32  # 24-bit stored in 32-bit container
        is_unsigned = False
    else:  # bit_depth <= 32
        container_bits = 32
        dtype = np.int32
        is_unsigned = False

    # For arbitrary bit depths, we quantize to that many levels (2^bit_depth)
    if is_unsigned:
        # 8-bit audio is unsigned (0-255)
        offset = 2 ** (container_bits - 1)
        max_value = offset - 1  # 127 for 8-bit
        # Quantize to desired bit depth
        quant_max = (2 ** bit_depth) // 2 - 1
        wave_quantized = np.round(wave * quant_max) / quant_max
        # Scale to container
        wave_scaled = np.clip(wave_quantized * max_value, -max_value, max_value).astype(dtype) + offset
    else:
        # Signed formats (16, 24, 32-bit)
        if container_bits == 16:
            container_max = 32767
        elif container_bits == 24:
            container_max = 8388607  # 2^23 - 1
        else:  # 32-bit
            container_max = 2147483647  # 2^31 - 1

        # Quantize to desired bit depth
        quant_max = (2 ** bit_depth) // 2 - 1
        wave_quantized = np.round(wave * quant_max) / quant_max

        # Scale to container format
        offset = 0
        wave_scaled = np.clip(wave_quantized * container_max, -container_max, container_max).astype(dtype)

    # Create multi-channel audio if needed
    if channels == 1:
        audio_data = wave_scaled
    else:
        # For multi-channel, create slightly different random variations
        audio_data = np.zeros((len(wave_scaled), channels), dtype=dtype)
        for ch in range(channels):
            # Add slight random phase variation for each channel
            phase_shift = np.random.uniform(0, 0.1)
            ch_wave = generate_triangle_wave(frequency, sample_rate, duration + phase_shift)
            ch_wave = ch_wave[:len(wave)]  # Trim to match length
            ch_wave = scipy.signal.filtfilt(b, a, ch_wave)
            ch_wave = ch_wave / np.max(np.abs(ch_wave)) * target_amplitude

            # Apply same quantization
            if is_unsigned:
                ch_wave_quantized = np.round(ch_wave * quant_max) / quant_max
                audio_data[:, ch] = np.clip(ch_wave_quantized * max_value, -max_value, max_value).astype(dtype) + offset
            else:
                ch_wave_quantized = np.round(ch_wave * quant_max) / quant_max
                audio_data[:, ch] = np.clip(ch_wave_quantized * container_max, -container_max, container_max).astype(dtype)

    # Write WAV file
    wavfile.write(str(output_path), sample_rate, audio_data)

    ch_desc = f"{channels}-channel" if channels > 2 else ("stereo" if channels == 2 else "mono")
    bit_desc = f"{bit_depth}-bit" if container_bits == bit_depth else f"{bit_depth}-bit (in {container_bits}-bit container)"
    print(f"✓ Generated: {output_path.name} ({ch_desc}, {bit_desc}, {frequency:.1f}Hz, -12dBFS)")


def main():
    parser = argparse.ArgumentParser(
        description='Generate unique test media files with random characteristics'
    )
    parser.add_argument(
        'n',
        type=int,
        help='Number of files to generate'
    )
    parser.add_argument(
        '-t', '--type',
        type=str,
        choices=['mp4', 'jpg', 'png', 'gif', 'wav'],
        default='mp4',
        help='Media type to generate (default: mp4)'
    )
    parser.add_argument(
        '-n', '--name',
        type=str,
        default='test_media',
        help='Base name for files (default: test_media)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='test_media',
        help='Output directory (default: test_media)'
    )

    # Video/Image options
    parser.add_argument(
        '-w', '--width',
        type=int,
        default=1920,
        help='Width for video/image (default: 1920)'
    )
    parser.add_argument(
        '-H', '--height',
        type=int,
        default=1080,
        help='Height for video/image (default: 1080)'
    )
    parser.add_argument(
        '-f', '--fps',
        type=int,
        default=30,
        help='Frames per second for video/GIF (default: 30)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=1,
        help='Duration in seconds for video/GIF/WAV (default: 1)'
    )

    # Audio options
    parser.add_argument(
        '--min-freq',
        type=int,
        default=100,
        help='Minimum frequency for WAV files in Hz (default: 100)'
    )
    parser.add_argument(
        '--max-freq',
        type=int,
        default=1000,
        help='Maximum frequency for WAV files in Hz (default: 1000)'
    )
    parser.add_argument(
        '--channels',
        type=int,
        default=1,
        help='Number of audio channels for WAV (1=mono, 2=stereo, >2=multi-channel) (default: 1)'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=44100,
        help='Sample rate for WAV files (default: 44100)'
    )
    parser.add_argument(
        '--bit-depth',
        type=int,
        default=16,
        help='Bit depth for WAV files: 1-32 bits (default: 16). Non-standard depths are quantized and stored in next larger container.'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Check for existing files and handle conflicts
    max_existing = find_existing_files(output_dir, args.name, args.type)
    start_num = 1

    if max_existing is not None:
        start_num, overwrite = prompt_conflict_resolution(output_dir, args.name, max_existing, args.type)
        if overwrite:
            print(f"\n🔄 Will overwrite existing files starting from 1")
        else:
            print(f"\n➕ Continuing from number {start_num}")

    # Display generation info based on media type
    media_type_desc = {
        'mp4': f'MP4 videos ({args.width}x{args.height}, {args.duration}s @ {args.fps}fps)',
        'jpg': f'JPG images ({args.width}x{args.height})',
        'png': f'PNG images ({args.width}x{args.height})',
        'gif': f'GIF animations ({args.width}x{args.height}, {args.duration}s @ {args.fps}fps)',
        'wav': f'WAV audio ({args.channels}ch, {args.bit_depth}-bit, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)'
    }

    print(f"\n🎬 Generating {args.n} {args.type.upper()} files...")
    print(f"   Type: {media_type_desc[args.type]}")
    print(f"   Output: {output_dir}/\n")

    # Pre-calculate frequencies for WAV files (evenly spaced)
    if args.type == 'wav':
        if args.n == 1:
            # Single file uses min_freq
            frequencies = [args.min_freq]
        else:
            # Multiple files use evenly spaced frequencies
            frequencies = np.linspace(args.min_freq, args.max_freq, args.n)
    else:
        frequencies = None

    # Generate files
    for i in range(args.n):
        file_num = start_num + i
        output_path = output_dir / f"{args.name}_{file_num}.{args.type}"

        if args.type == 'mp4':
            generate_video(
                output_path,
                width=args.width,
                height=args.height,
                fps=args.fps,
                duration=args.duration
            )
        elif args.type in ['jpg', 'png']:
            generate_image(
                output_path,
                width=args.width,
                height=args.height,
                format=args.type
            )
        elif args.type == 'gif':
            generate_gif(
                output_path,
                width=args.width,
                height=args.height,
                fps=args.fps,
                duration=args.duration
            )
        elif args.type == 'wav':
            generate_wav(
                output_path,
                frequency=frequencies[i],
                duration=args.duration,
                sample_rate=args.sample_rate,
                channels=args.channels,
                bit_depth=args.bit_depth,
                max_freq=args.max_freq
            )

    print(f"\n✅ Done! Generated {args.n} {args.type.upper()} files in '{output_dir}/'")


if __name__ == '__main__':
    main()
