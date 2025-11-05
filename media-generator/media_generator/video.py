"""
Video generation module.
Handles video file generation with various codecs and optional audio embedding.
"""

import cv2
import numpy as np
import tempfile
import subprocess
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple
import scipy.io.wavfile as wavfile

from media_generator.audio import AudioConfig, MediaOutput, generate_audio_data, FFMPEG_PATH


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class VideoConfig:
    """Immutable configuration for video generation."""
    width: int = 1920
    height: int = 1080
    fps: float = 30
    duration: float = 1
    codec: str = 'mpeg4'


# =============================================================================
# Video Codec Functions
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


# =============================================================================
# Video Effect Functions
# =============================================================================

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


# =============================================================================
# Video Frame Generation
# =============================================================================

def generate_video_frames(config: VideoConfig, seed: int) -> Tuple[list, np.ndarray]:
    """Generate frames for a video with random color and effects. Returns (frames, base_color)."""
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


# =============================================================================
# Video File Writers
# =============================================================================

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
