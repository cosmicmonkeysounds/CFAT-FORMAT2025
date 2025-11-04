#!/usr/bin/env python3
"""
Generate unique test media files (MP4, JPG, PNG, GIF, WAV, OGG, MP3, WebP, BMP, TIFF, SVG)
with random characteristics.

Videos and images use random colors and effects. Audio files use triangle wave tones.
Self-contained with bundled ffmpeg - no external dependencies required!
"""

import cv2
import numpy as np
import argparse
import re
from pathlib import Path
from PIL import Image
import scipy.signal
import scipy.io.wavfile as wavfile
import tempfile
import subprocess
import os

# Import bundled ffmpeg
try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG_PATH = get_ffmpeg_exe()
except ImportError:
    # Fallback to system ffmpeg if imageio-ffmpeg not installed
    FFMPEG_PATH = 'ffmpeg'


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


def generate_video(output_path, width=1920, height=1080, fps=30, duration=1,
                  codec='mpeg4', audio_frequency=None, audio_sample_rate=44100,
                  audio_channels=1, audio_bit_depth=16, max_freq=1000,
                  embed_audio=False, save_separate_audio=False, audio_format='wav'):
    """
    Generate a single test video with random color and effects.
    Optionally embeds audio and/or saves separate audio file.

    Args:
        audio_frequency: If provided, generate audio at this frequency
        embed_audio: If True, embed audio into video file
        save_separate_audio: If True, save audio as separate file
        audio_format: Format for separate audio file ('wav', 'ogg', 'mp3')
    """
    # Random base color
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)
    color_variance = np.random.randint(5, 30)

    # Get codec info
    fourcc_str, _, codec_desc = get_video_codec(codec)
    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)

    # Generate video without audio first (always needed)
    temp_video_path = None
    final_output_path = output_path

    if audio_frequency is not None:
        # Create temp file for video without audio
        temp_video_path = output_path.with_suffix('.temp.mp4')
        video_path_to_write = temp_video_path
    else:
        video_path_to_write = output_path

    # Setup video writer
    out = cv2.VideoWriter(str(video_path_to_write), fourcc, fps, (width, height))

    total_frames = fps * duration
    video_seed = np.random.randint(0, 1000000)

    for frame_num in range(total_frames):
        np.random.seed(video_seed + frame_num)
        color = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
        color = np.clip(color, 0, 255).astype(np.uint8)
        frame = np.full((height, width, 3), color[::-1], dtype=np.uint8)
        frame = apply_random_effects(frame, effect_intensity=0.4)
        out.write(frame)

    out.release()

    # Handle audio if requested
    audio_info = ""

    if audio_frequency is not None:
        # Generate audio data
        audio_data, sample_rate = generate_audio_data(
            audio_frequency, duration, audio_sample_rate,
            audio_channels, audio_bit_depth, max_freq
        )

        # Create temporary WAV file for ffmpeg
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
            tmp_audio_path = tmp_audio.name
            wavfile.write(tmp_audio_path, sample_rate, audio_data)

        try:
            # Only embed audio if the flag was set (not just save_separate_audio)
            if embed_audio:
                # Use bundled ffmpeg to combine video and audio
                result = subprocess.run([
                    FFMPEG_PATH, '-y', '-i', str(video_path_to_write),
                    '-i', tmp_audio_path,
                    '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
                    '-shortest', str(final_output_path)
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"⚠ Warning: Failed to embed audio (ffmpeg error). Keeping video without audio.")
                    if temp_video_path and temp_video_path.exists():
                        temp_video_path.rename(final_output_path)
                else:
                    # Clean up temp video file
                    if temp_video_path and temp_video_path.exists():
                        os.remove(temp_video_path)

                    ch_desc = f"{audio_channels}ch" if audio_channels > 2 else ("stereo" if audio_channels == 2 else "mono")
                    audio_info = f", Audio: {audio_frequency:.1f}Hz {ch_desc}"
            else:
                # No audio embedding, just move temp video to final location if needed
                if temp_video_path and temp_video_path.exists():
                    temp_video_path.rename(final_output_path)

            # Save separate audio file if requested
            if save_separate_audio:
                audio_output_path = output_path.with_suffix(f'.{audio_format}')

                if audio_format == 'wav':
                    wavfile.write(str(audio_output_path), sample_rate, audio_data)
                elif audio_format == 'ogg':
                    # Convert WAV to OGG using bundled ffmpeg
                    conv_result = subprocess.run([
                        FFMPEG_PATH, '-y', '-i', tmp_audio_path,
                        '-c:a', 'libvorbis', '-q:a', '5',
                        str(audio_output_path)
                    ], capture_output=True, text=True)
                    if conv_result.returncode != 0:
                        print(f"  ⚠ Warning: Failed to create separate OGG audio file")
                elif audio_format == 'mp3':
                    # Convert WAV to MP3 using bundled ffmpeg
                    conv_result = subprocess.run([
                        FFMPEG_PATH, '-y', '-i', tmp_audio_path,
                        '-c:a', 'libmp3lame', '-b:a', '192k',
                        str(audio_output_path)
                    ], capture_output=True, text=True)
                    if conv_result.returncode != 0:
                        print(f"  ⚠ Warning: Failed to create separate MP3 audio file")

                if os.path.exists(audio_output_path):
                    print(f"  ↳ Audio: {audio_output_path.name}")

        finally:
            # Clean up temp audio file
            if os.path.exists(tmp_audio_path):
                os.remove(tmp_audio_path)

    print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)}, Codec: {codec_desc}{audio_info})")


def generate_image(output_path, width=1920, height=1080, format='jpg'):
    """
    Generate a single test image (JPG, PNG, WebP, BMP, TIFF) with random color and effects.
    """
    seed = np.random.randint(0, 1000000)
    frame, base_color = generate_random_frame(width, height, seed)

    # Convert BGR to RGB for PIL
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Save using PIL
    img = Image.fromarray(frame_rgb)

    # Set quality for lossy formats
    save_kwargs = {}
    if format.lower() == 'jpg':
        save_kwargs['quality'] = 95
    elif format.lower() == 'webp':
        save_kwargs['quality'] = 90
        save_kwargs['method'] = 6

    img.save(str(output_path), **save_kwargs)

    print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)})")


def generate_svg(output_path, width=1920, height=1080):
    """
    Generate a single test SVG with random color and geometric patterns.
    """
    seed = np.random.randint(0, 1000000)
    np.random.seed(seed)

    # Random base color
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)

    # Create SVG with random geometric shapes
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="{width}" height="{height}" fill="rgb({base_color[0]},{base_color[1]},{base_color[2]})"/>

'''

    # Add random shapes for visual variety
    num_shapes = np.random.randint(5, 15)
    for _ in range(num_shapes):
        shape_type = np.random.choice(['circle', 'rect', 'ellipse', 'polygon'])

        # Random color with some variation from base
        color_var = np.random.randint(-50, 50, 3)
        shape_color = np.clip(base_color.astype(np.int16) + color_var, 0, 255).astype(np.uint8)
        opacity = np.random.uniform(0.1, 0.7)

        if shape_type == 'circle':
            cx = np.random.randint(0, width)
            cy = np.random.randint(0, height)
            r = np.random.randint(20, min(width, height) // 4)
            svg_content += f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'

        elif shape_type == 'rect':
            x = np.random.randint(0, width - 100)
            y = np.random.randint(0, height - 100)
            w = np.random.randint(50, min(300, width - x))
            h = np.random.randint(50, min(300, height - y))
            svg_content += f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'

        elif shape_type == 'ellipse':
            cx = np.random.randint(0, width)
            cy = np.random.randint(0, height)
            rx = np.random.randint(20, min(width, height) // 6)
            ry = np.random.randint(20, min(width, height) // 6)
            svg_content += f'  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'

        elif shape_type == 'polygon':
            points = []
            num_points = np.random.randint(3, 8)
            for _ in range(num_points):
                px = np.random.randint(0, width)
                py = np.random.randint(0, height)
                points.append(f"{px},{py}")
            points_str = " ".join(points)
            svg_content += f'  <polygon points="{points_str}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'

    svg_content += '</svg>'

    # Write SVG file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"✓ Generated: {output_path.name} (Color: RGB{tuple(base_color)}, {num_shapes} shapes)")


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


def get_video_codec(codec_name):
    """
    Get the appropriate fourcc code and file extension for the specified codec.
    Returns (fourcc_code, recommended_extension, description)
    """
    codecs = {
        'h264': ('avc1', 'mp4', 'H.264/AVC'),
        'h265': ('hev1', 'mp4', 'H.265/HEVC'),
        'vp9': ('VP90', 'webm', 'VP9'),
        'av1': ('av01', 'mp4', 'AV1'),
        'mpeg4': ('mp4v', 'mp4', 'MPEG-4'),
        'mjpeg': ('MJPG', 'avi', 'Motion JPEG'),
        'xvid': ('XVID', 'avi', 'Xvid'),
    }

    codec_name = codec_name.lower()
    if codec_name not in codecs:
        # Default to mpeg4 if unknown
        return codecs['mpeg4']

    return codecs[codec_name]


def generate_triangle_wave(frequency, sample_rate, duration):
    """
    Generate a triangle wave at the specified frequency.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Triangle wave using sawtooth with width=0.5
    wave = scipy.signal.sawtooth(2 * np.pi * frequency * t, width=0.5)
    return wave


def generate_audio_data(frequency, duration, sample_rate=44100, channels=1,
                       bit_depth=16, max_freq=1000):
    """
    Generate audio data as numpy array (returns data ready for scipy.io.wavfile).
    This is used internally by other audio generation functions.
    """
    # Generate triangle wave
    wave = generate_triangle_wave(frequency, sample_rate, duration)

    # Apply low-pass filter
    cutoff = min(frequency * 2, max_freq)
    nyquist = sample_rate / 2
    normalized_cutoff = cutoff / nyquist

    b, a = scipy.signal.butter(4, normalized_cutoff, btype='low')
    wave = scipy.signal.filtfilt(b, a, wave)

    # Normalize to -12dBFS
    target_amplitude = 10 ** (-12 / 20)
    wave = wave / np.max(np.abs(wave)) * target_amplitude

    # Validate bit depth
    if bit_depth < 1 or bit_depth > 32:
        raise ValueError(f"Bit depth must be between 1 and 32, got {bit_depth}")

    # Determine container format
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
        dtype = np.int32
        is_unsigned = False
    else:
        container_bits = 32
        dtype = np.int32
        is_unsigned = False

    # Quantize
    if is_unsigned:
        offset = 2 ** (container_bits - 1)
        max_value = offset - 1
        quant_max = (2 ** bit_depth) // 2 - 1
        wave_quantized = np.round(wave * quant_max) / quant_max
        wave_scaled = np.clip(wave_quantized * max_value, -max_value, max_value).astype(dtype) + offset
    else:
        if container_bits == 16:
            container_max = 32767
        elif container_bits == 24:
            container_max = 8388607
        else:
            container_max = 2147483647

        quant_max = (2 ** bit_depth) // 2 - 1
        wave_quantized = np.round(wave * quant_max) / quant_max
        wave_scaled = np.clip(wave_quantized * container_max, -container_max, container_max).astype(dtype)

    # Create multi-channel audio if needed
    if channels == 1:
        audio_data = wave_scaled
    else:
        audio_data = np.zeros((len(wave_scaled), channels), dtype=dtype)
        for ch in range(channels):
            phase_shift = np.random.uniform(0, 0.1)
            ch_wave = generate_triangle_wave(frequency, sample_rate, duration + phase_shift)
            ch_wave = ch_wave[:len(wave)]
            ch_wave = scipy.signal.filtfilt(b, a, ch_wave)
            ch_wave = ch_wave / np.max(np.abs(ch_wave)) * target_amplitude

            if is_unsigned:
                ch_wave_quantized = np.round(ch_wave * quant_max) / quant_max
                audio_data[:, ch] = np.clip(ch_wave_quantized * max_value, -max_value, max_value).astype(dtype) + offset
            else:
                ch_wave_quantized = np.round(ch_wave * quant_max) / quant_max
                audio_data[:, ch] = np.clip(ch_wave_quantized * container_max, -container_max, container_max).astype(dtype)

    return audio_data, sample_rate


def generate_wav(output_path, frequency, duration=1, sample_rate=44100, channels=1,
                bit_depth=16, max_freq=1000):
    """
    Generate a WAV file with low-pass filtered triangle wave tone at -12dBFS.
    Supports arbitrary bit depths (1-32 bits). Non-standard bit depths are quantized
    and stored in the next larger standard container (8, 16, 24, or 32-bit).
    """
    audio_data, sample_rate = generate_audio_data(
        frequency, duration, sample_rate, channels, bit_depth, max_freq
    )

    # Write WAV file
    wavfile.write(str(output_path), sample_rate, audio_data)

    # Determine container bits for display
    if bit_depth <= 8:
        container_bits = 8
    elif bit_depth <= 16:
        container_bits = 16
    elif bit_depth <= 24:
        container_bits = 24
    else:
        container_bits = 32

    ch_desc = f"{channels}-channel" if channels > 2 else ("stereo" if channels == 2 else "mono")
    bit_desc = f"{bit_depth}-bit" if container_bits == bit_depth else f"{bit_depth}-bit (in {container_bits}-bit container)"
    print(f"✓ Generated: {output_path.name} ({ch_desc}, {bit_desc}, {frequency:.1f}Hz, -12dBFS)")


def generate_ogg(output_path, frequency, duration=1, sample_rate=44100, channels=1,
                bit_depth=16, max_freq=1000):
    """
    Generate an OGG file with low-pass filtered triangle wave tone at -12dBFS.
    Uses bundled ffmpeg (no external installation needed).
    """
    audio_data, sample_rate = generate_audio_data(
        frequency, duration, sample_rate, channels, bit_depth, max_freq
    )

    # Create temporary WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        tmp_wav_path = tmp_wav.name
        wavfile.write(tmp_wav_path, sample_rate, audio_data)

    try:
        # Convert WAV to OGG using bundled ffmpeg
        result = subprocess.run([
            FFMPEG_PATH, '-y', '-i', tmp_wav_path,
            '-c:a', 'libvorbis', '-q:a', '5',
            str(output_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"⚠ Error: Failed to generate OGG file (ffmpeg error).")
            print(f"   Error: {result.stderr}")
            return

        ch_desc = f"{channels}-channel" if channels > 2 else ("stereo" if channels == 2 else "mono")
        print(f"✓ Generated: {output_path.name} ({ch_desc}, OGG Vorbis, {frequency:.1f}Hz, -12dBFS)")
    finally:
        # Clean up temp file
        if os.path.exists(tmp_wav_path):
            os.remove(tmp_wav_path)


def generate_mp3(output_path, frequency, duration=1, sample_rate=44100, channels=1,
                bit_depth=16, max_freq=1000, bitrate='192k'):
    """
    Generate an MP3 file with low-pass filtered triangle wave tone at -12dBFS.
    Uses bundled ffmpeg (no external installation needed).
    """
    audio_data, sample_rate = generate_audio_data(
        frequency, duration, sample_rate, channels, bit_depth, max_freq
    )

    # Create temporary WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        tmp_wav_path = tmp_wav.name
        wavfile.write(tmp_wav_path, sample_rate, audio_data)

    try:
        # Convert WAV to MP3 using bundled ffmpeg
        result = subprocess.run([
            FFMPEG_PATH, '-y', '-i', tmp_wav_path,
            '-c:a', 'libmp3lame', '-b:a', bitrate,
            str(output_path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"⚠ Error: Failed to generate MP3 file (ffmpeg error).")
            print(f"   Error: {result.stderr}")
            return

        ch_desc = f"{channels}-channel" if channels > 2 else ("stereo" if channels == 2 else "mono")
        print(f"✓ Generated: {output_path.name} ({ch_desc}, MP3 {bitrate}, {frequency:.1f}Hz, -12dBFS)")
    finally:
        # Clean up temp file
        if os.path.exists(tmp_wav_path):
            os.remove(tmp_wav_path)


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
        choices=['mp4', 'jpg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'svg', 'wav', 'ogg', 'mp3'],
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

    # Video codec options
    parser.add_argument(
        '--codec',
        type=str,
        choices=['h264', 'h265', 'vp9', 'av1', 'mpeg4', 'mjpeg', 'xvid'],
        default='mpeg4',
        help='Video codec to use for MP4/video generation (default: mpeg4)'
    )

    # Audio options for videos (independent flags)
    parser.add_argument(
        '--embed-audio',
        action='store_true',
        help='Embed audio track into video files. Can be used independently or with --audio-file.'
    )
    parser.add_argument(
        '--audio-file',
        action='store_true',
        help='Generate standalone audio file alongside video. Can be used independently or with --embed-audio.'
    )
    parser.add_argument(
        '--audio-format',
        type=str,
        choices=['wav', 'ogg', 'mp3'],
        default='wav',
        help='Format for standalone audio files when using --audio-file (default: wav)'
    )
    parser.add_argument(
        '--mp3-bitrate',
        type=str,
        default='192k',
        help='Bitrate for MP3 files (default: 192k)'
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
    codec_desc = f', Codec: {args.codec.upper()}' if args.type == 'mp4' else ''
    audio_mode_desc = ''
    if args.type == 'mp4' and (args.embed_audio or args.audio_file):
        modes = []
        if args.embed_audio:
            modes.append('embedded')
        if args.audio_file:
            modes.append(f'file:{args.audio_format.upper()}')
        audio_mode_desc = f', Audio: {" + ".join(modes)}'

    media_type_desc = {
        'mp4': f'MP4 videos ({args.width}x{args.height}, {args.duration}s @ {args.fps}fps{codec_desc}{audio_mode_desc})',
        'jpg': f'JPG images ({args.width}x{args.height})',
        'png': f'PNG images ({args.width}x{args.height})',
        'webp': f'WebP images ({args.width}x{args.height})',
        'bmp': f'BMP images ({args.width}x{args.height})',
        'tiff': f'TIFF images ({args.width}x{args.height})',
        'svg': f'SVG vector graphics ({args.width}x{args.height})',
        'gif': f'GIF animations ({args.width}x{args.height}, {args.duration}s @ {args.fps}fps)',
        'wav': f'WAV audio ({args.channels}ch, {args.bit_depth}-bit, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'ogg': f'OGG audio ({args.channels}ch, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)',
        'mp3': f'MP3 audio ({args.channels}ch, {args.mp3_bitrate}, {args.sample_rate}Hz, {args.min_freq}-{args.max_freq}Hz, {args.duration}s)'
    }

    print(f"\n🎬 Generating {args.n} {args.type.upper()} files...")
    print(f"   Type: {media_type_desc[args.type]}")
    print(f"   Output: {output_dir}/\n")

    # Pre-calculate frequencies for audio files and videos with audio (evenly spaced)
    if args.type in ['wav', 'ogg', 'mp3'] or (args.type == 'mp4' and (args.embed_audio or args.audio_file)):
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
            # Determine if we need to generate audio for video
            audio_freq = frequencies[i] if (args.embed_audio or args.audio_file) else None

            generate_video(
                output_path,
                width=args.width,
                height=args.height,
                fps=args.fps,
                duration=args.duration,
                codec=args.codec,
                audio_frequency=audio_freq,
                audio_sample_rate=args.sample_rate,
                audio_channels=args.channels,
                audio_bit_depth=args.bit_depth,
                max_freq=args.max_freq,
                embed_audio=args.embed_audio,
                save_separate_audio=args.audio_file,
                audio_format=args.audio_format
            )
        elif args.type in ['jpg', 'png', 'webp', 'bmp', 'tiff']:
            generate_image(
                output_path,
                width=args.width,
                height=args.height,
                format=args.type
            )
        elif args.type == 'svg':
            generate_svg(
                output_path,
                width=args.width,
                height=args.height
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
        elif args.type == 'ogg':
            generate_ogg(
                output_path,
                frequency=frequencies[i],
                duration=args.duration,
                sample_rate=args.sample_rate,
                channels=args.channels,
                bit_depth=args.bit_depth,
                max_freq=args.max_freq
            )
        elif args.type == 'mp3':
            generate_mp3(
                output_path,
                frequency=frequencies[i],
                duration=args.duration,
                sample_rate=args.sample_rate,
                channels=args.channels,
                bit_depth=args.bit_depth,
                max_freq=args.max_freq,
                bitrate=args.mp3_bitrate
            )

    print(f"\n✅ Done! Generated {args.n} {args.type.upper()} files in '{output_dir}/'")


if __name__ == '__main__':
    main()
