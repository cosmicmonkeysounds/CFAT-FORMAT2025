"""
Core generation logic and data models for media generator.
Uses functional programming style with immutable data classes.
"""

import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
import scipy.signal
import scipy.io.wavfile as wavfile
import tempfile
import subprocess
import os

try:
    from imageio_ffmpeg import get_ffmpeg_exe
    FFMPEG_PATH = get_ffmpeg_exe()
except ImportError:
    FFMPEG_PATH = 'ffmpeg'


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class AudioConfig:
    """Immutable configuration for audio generation."""
    frequency: float
    duration: float
    sample_rate: float = 44100
    channels: int = 1
    bit_depth: int = 16
    max_freq: float = 1000
    bitrate: str = '192k'  # For lossy formats


@dataclass(frozen=True)
class VideoConfig:
    """Immutable configuration for video generation."""
    width: int = 1920
    height: int = 1080
    fps: float = 30
    duration: float = 1
    codec: str = 'mpeg4'


@dataclass(frozen=True)
class MediaOutput:
    """Configuration for where and how to save media."""
    path: Path
    format: str


# =============================================================================
# Pure Audio Generation Functions
# =============================================================================

def generate_triangle_wave(frequency: float, sample_rate: float, duration: float) -> np.ndarray:
    """Generate a triangle wave at the specified frequency."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return scipy.signal.sawtooth(2 * np.pi * frequency * t, width=0.5)


def apply_lowpass_filter(wave: np.ndarray, cutoff: float, sample_rate: float) -> np.ndarray:
    """Apply Butterworth low-pass filter to audio wave."""
    nyquist = sample_rate / 2
    normalized_cutoff = cutoff / nyquist
    b, a = scipy.signal.butter(4, normalized_cutoff, btype='low')
    return scipy.signal.filtfilt(b, a, wave)


def normalize_to_dbfs(wave: np.ndarray, target_db: float = -12) -> np.ndarray:
    """Normalize audio wave to target dBFS."""
    target_amplitude = 10 ** (target_db / 20)
    return wave / np.max(np.abs(wave)) * target_amplitude


def quantize_audio(wave: np.ndarray, bit_depth: int, channels: int) -> np.ndarray:
    """Quantize audio to specified bit depth and convert to appropriate dtype."""
    if bit_depth < 1 or bit_depth > 32:
        raise ValueError(f"Bit depth must be between 1 and 32, got {bit_depth}")

    # Determine container format
    if bit_depth <= 8:
        container_bits, dtype, is_unsigned = 8, np.uint8, True
    elif bit_depth <= 16:
        container_bits, dtype, is_unsigned = 16, np.int16, False
    elif bit_depth <= 24:
        container_bits, dtype, is_unsigned = 24, np.int32, False
    else:
        container_bits, dtype, is_unsigned = 32, np.int32, False

    # Quantize
    if is_unsigned:
        offset = 2 ** (container_bits - 1)
        max_value = offset - 1
        quant_max = (2 ** bit_depth) // 2 - 1
        quantized = np.clip(wave * quant_max, -quant_max, quant_max)
        quantized = (quantized + offset).astype(dtype)
    else:
        max_value = 2 ** (container_bits - 1) - 1
        quant_max = (2 ** bit_depth) // 2 - 1
        quantized = np.clip(wave * quant_max, -quant_max, quant_max).astype(dtype)

        if container_bits == 24:
            quantized = quantized << (32 - 24)

    # Replicate for channels
    if channels > 1:
        quantized = np.tile(quantized.reshape(-1, 1), (1, channels))

    return quantized


def generate_audio_data(config: AudioConfig) -> Tuple[np.ndarray, float]:
    """
    Generate audio data from configuration.
    Returns (audio_data, actual_sample_rate) tuple.
    """
    # Generate and process wave
    wave = generate_triangle_wave(config.frequency, config.sample_rate, config.duration)
    cutoff = min(config.frequency * 2, config.max_freq)
    wave = apply_lowpass_filter(wave, cutoff, config.sample_rate)
    wave = normalize_to_dbfs(wave, -12)

    # Quantize
    audio_data = quantize_audio(wave, config.bit_depth, config.channels)

    return audio_data, config.sample_rate


# =============================================================================
# Audio File Writers
# =============================================================================

def write_wav(output: MediaOutput, config: AudioConfig) -> None:
    """Write audio data to WAV file."""
    audio_data, sample_rate = generate_audio_data(config)
    wavfile.write(str(output.path), int(sample_rate), audio_data)


def write_compressed_audio(output: MediaOutput, config: AudioConfig,
                          codec: str, codec_args: list) -> None:
    """Write compressed audio via ffmpeg (OGG, MP3, AAC, FLAC)."""
    audio_data, sample_rate = generate_audio_data(config)

    # Create temporary WAV
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
        tmp_wav_path = tmp_wav.name
        wavfile.write(tmp_wav_path, int(sample_rate), audio_data)

    try:
        # Convert via ffmpeg
        result = subprocess.run([
            FFMPEG_PATH, '-y', '-i', tmp_wav_path,
            *codec_args,
            '-t', str(config.duration),
            '-metadata', f'duration={config.duration}',
            str(output.path)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg encoding failed: {result.stderr}")
    finally:
        if os.path.exists(tmp_wav_path):
            os.remove(tmp_wav_path)


def get_codec_args(format: str, bitrate: str = '192k') -> list:
    """Get ffmpeg codec arguments for audio format."""
    codec_map = {
        'ogg': ['-c:a', 'libvorbis', '-q:a', '5'],
        'mp3': ['-c:a', 'libmp3lame', '-b:a', bitrate],
        'aac': ['-c:a', 'aac', '-b:a', bitrate],
        'm4a': ['-c:a', 'aac', '-b:a', bitrate],
        'flac': ['-c:a', 'flac'],
    }
    return codec_map.get(format, [])


def write_audio_file(output: MediaOutput, config: AudioConfig) -> str:
    """
    Write audio file in any supported format.
    Returns descriptive string about what was generated.
    """
    if output.format == 'wav':
        write_wav(output, config)
        container_bits = 8 if config.bit_depth <= 8 else (16 if config.bit_depth <= 16 else (24 if config.bit_depth <= 24 else 32))
        ch_desc = "mono" if config.channels == 1 else ("stereo" if config.channels == 2 else f"{config.channels}-channel")
        return f"{ch_desc}, {container_bits}-bit, {config.frequency:.1f}Hz, -12dBFS"
    else:
        codec_args = get_codec_args(output.format, config.bitrate)
        write_compressed_audio(output, config, output.format, codec_args)
        ch_desc = "mono" if config.channels == 1 else ("stereo" if config.channels == 2 else f"{config.channels}-channel")
        ext = output.format.upper()

        if output.format in ['ogg']:
            return f"{ch_desc}, {ext} Vorbis, {config.frequency:.1f}Hz, -12dBFS"
        elif output.format in ['mp3', 'aac', 'm4a']:
            return f"{ch_desc}, {ext} {config.bitrate}, {config.frequency:.1f}Hz, -12dBFS"
        elif output.format == 'flac':
            return f"{ch_desc}, FLAC lossless, {config.frequency:.1f}Hz, -12dBFS"
        else:
            return f"{ch_desc}, {config.frequency:.1f}Hz, -12dBFS"


# =============================================================================
# Video Generation Functions
# =============================================================================

def get_video_codec_info(codec: str) -> Tuple[str, str, str]:
    """Get fourcc string, file extension, and description for video codec."""
    codec_map = {
        'h264': ('avc1', 'mp4', 'H.264'),
        'h265': ('hev1', 'mp4', 'H.265/HEVC'),
        'vp9': ('vp09', 'webm', 'VP9'),
        'av1': ('av01', 'mp4', 'AV1'),
        'mpeg4': ('mp4v', 'mp4', 'MPEG-4'),
        'mjpeg': ('MJPG', 'avi', 'Motion JPEG'),
        'xvid': ('XVID', 'avi', 'Xvid'),
    }
    return codec_map.get(codec, ('mp4v', 'mp4', 'MPEG-4'))


def apply_random_effects(frame: np.ndarray, effect_intensity: float = 0.4) -> np.ndarray:
    """Apply random visual effects to a frame."""
    effect_type = np.random.choice(['noise', 'blur', 'gradient', 'none'], p=[0.3, 0.2, 0.3, 0.2])

    if effect_type == 'noise':
        noise = np.random.randint(-20, 20, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + (noise * effect_intensity).astype(np.int16), 0, 255).astype(np.uint8)
    elif effect_type == 'blur':
        kernel_size = np.random.choice([3, 5, 7])
        frame = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    elif effect_type == 'gradient':
        height, width = frame.shape[:2]
        gradient = np.linspace(0, 1, width).reshape(1, width, 1)
        gradient = np.repeat(gradient, height, axis=0)
        gradient = np.repeat(gradient, 3, axis=2)
        frame = (frame.astype(np.float32) * (0.7 + gradient * 0.3 * effect_intensity)).astype(np.uint8)

    return frame


def generate_video_frames(config: VideoConfig, seed: int) -> list:
    """Generate frames for a video with random color and effects."""
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)
    color_variance = np.random.randint(5, 30)
    total_frames = int(config.fps * config.duration)

    frames = []
    for frame_num in range(total_frames):
        np.random.seed(seed + frame_num)
        color = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
        color = np.clip(color, 0, 255).astype(np.uint8)
        frame = np.full((config.height, config.width, 3), color[::-1], dtype=np.uint8)
        frame = apply_random_effects(frame, effect_intensity=0.4)
        frames.append(frame)

    return frames, base_color


def write_video_file(output: MediaOutput, config: VideoConfig) -> Tuple[str, np.ndarray]:
    """
    Write video file without audio.
    Returns (codec_description, base_color) tuple.
    """
    fourcc_str, _, codec_desc = get_video_codec_info(config.codec)
    fourcc = cv2.VideoWriter_fourcc(*fourcc_str)

    seed = np.random.randint(0, 1000000)
    frames, base_color = generate_video_frames(config, seed)

    out = cv2.VideoWriter(str(output.path), fourcc, config.fps, (config.width, config.height))
    for frame in frames:
        out.write(frame)
    out.release()

    return codec_desc, base_color


def embed_audio_in_video(video_path: Path, audio_config: AudioConfig, duration: float) -> bool:
    """
    Add audio track to video file using ffmpeg.
    Returns True if successful.
    """
    audio_data, sample_rate = generate_audio_data(audio_config)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
        tmp_audio_path = tmp_audio.name
        wavfile.write(tmp_audio_path, int(sample_rate), audio_data)

    temp_video = video_path.with_suffix('.temp.mp4')

    try:
        result = subprocess.run([
            FFMPEG_PATH, '-y', '-i', str(video_path),
            '-i', tmp_audio_path,
            '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental',
            '-t', str(duration),
            '-shortest', str(temp_video)
        ], capture_output=True, text=True)

        if result.returncode == 0:
            os.remove(video_path)
            temp_video.rename(video_path)
            return True
        return False
    finally:
        if os.path.exists(tmp_audio_path):
            os.remove(tmp_audio_path)
        if temp_video.exists():
            os.remove(temp_video)


# =============================================================================
# Image Generation Functions
# =============================================================================

def generate_image_data(width: int, height: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate random image data with effects. Returns (frame, base_color)."""
    np.random.seed(seed)
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)
    color_variance = np.random.randint(5, 30)

    color = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
    color = np.clip(color, 0, 255).astype(np.uint8)
    frame = np.full((height, width, 3), color[::-1], dtype=np.uint8)
    frame = apply_random_effects(frame, effect_intensity=0.4)

    return frame, base_color


def write_image_file(output: MediaOutput, width: int, height: int) -> np.ndarray:
    """Write image file (JPG, PNG, WebP, BMP, TIFF). Returns base_color."""
    from PIL import Image

    seed = np.random.randint(0, 1000000)
    frame, base_color = generate_image_data(width, height, seed)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)

    save_kwargs = {}
    if output.format == 'jpg':
        save_kwargs['quality'] = 95
    elif output.format == 'webp':
        save_kwargs['quality'] = 90
        save_kwargs['method'] = 6

    img.save(str(output.path), **save_kwargs)
    return base_color


def generate_svg_content(width: int, height: int, base_color: np.ndarray) -> str:
    """Generate SVG content with random geometric shapes."""
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="rgb({base_color[0]},{base_color[1]},{base_color[2]})"/>

'''

    num_shapes = np.random.randint(5, 15)
    for _ in range(num_shapes):
        shape_type = np.random.choice(['circle', 'rect', 'ellipse', 'polygon'])
        color_var = np.random.randint(-50, 50, 3)
        shape_color = np.clip(base_color.astype(np.int16) + color_var, 0, 255).astype(np.uint8)
        opacity = np.random.uniform(0.1, 0.7)

        if shape_type == 'circle':
            cx, cy = np.random.randint(0, width), np.random.randint(0, height)
            r = np.random.randint(20, min(width, height) // 4)
            svg += f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'
        elif shape_type == 'rect':
            x, y = np.random.randint(0, width - 100), np.random.randint(0, height - 100)
            w, h = np.random.randint(50, min(300, width - x)), np.random.randint(50, min(300, height - y))
            svg += f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'
        elif shape_type == 'ellipse':
            cx, cy = np.random.randint(0, width), np.random.randint(0, height)
            rx, ry = np.random.randint(20, min(width, height) // 6), np.random.randint(20, min(width, height) // 6)
            svg += f'  <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'
        elif shape_type == 'polygon':
            points = [f"{np.random.randint(0, width)},{np.random.randint(0, height)}"
                     for _ in range(np.random.randint(3, 8))]
            svg += f'  <polygon points="{" ".join(points)}" fill="rgb({shape_color[0]},{shape_color[1]},{shape_color[2]})" opacity="{opacity:.2f}"/>\n'

    svg += '</svg>'
    return svg


def write_svg_file(output: MediaOutput, width: int, height: int) -> np.ndarray:
    """Write SVG file. Returns base_color."""
    seed = np.random.randint(0, 1000000)
    np.random.seed(seed)
    base_color = np.random.randint(0, 256, 3, dtype=np.uint8)

    svg_content = generate_svg_content(width, height, base_color)
    output.path.write_text(svg_content)
    return base_color


def write_gif_file(output: MediaOutput, config: VideoConfig) -> np.ndarray:
    """Write animated GIF. Returns base_color."""
    from PIL import Image

    seed = np.random.randint(0, 1000000)
    frames, base_color = generate_video_frames(config, seed)

    pil_frames = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames]
    duration_ms = int((config.duration / len(frames)) * 1000)

    pil_frames[0].save(
        str(output.path),
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0
    )

    return base_color
