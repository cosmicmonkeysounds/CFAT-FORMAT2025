"""
Audio generation module.
Pure functional audio generation with immutable configurations.
"""

import numpy as np
import scipy.signal
import scipy.io.wavfile as wavfile
import tempfile
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple

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
