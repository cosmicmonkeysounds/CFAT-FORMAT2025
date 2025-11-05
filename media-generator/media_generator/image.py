"""
Image and animation generation module.
Handles static images (JPG, PNG, WebP, BMP, TIFF, SVG) and animated GIFs.
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, List, Any

from media_generator.audio import MediaOutput
from media_generator.video import VideoConfig, apply_random_effects, generate_video_frames


# =============================================================================
# Image Generation Functions
# =============================================================================

def generate_image_data(width: int, height: int, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate random image data with effects. Returns (frame, base_color)."""
    np.random.seed(seed)
    base_color: np.ndarray = np.random.randint(0, 256, 3, dtype=np.uint8)
    color_variance: int = np.random.randint(5, 30)

    color: np.ndarray = base_color + np.random.randint(-color_variance, color_variance, 3, dtype=np.int16)
    color = np.clip(color, 0, 255).astype(np.uint8)
    frame: np.ndarray = np.full((height, width, 3), color[::-1], dtype=np.uint8)
    frame = apply_random_effects(frame, effect_intensity=0.4)

    return frame, base_color


def write_image_file(output: MediaOutput, width: int, height: int) -> np.ndarray:
    """Write image file (JPG, PNG, WebP, BMP, TIFF). Returns base_color."""
    seed: int = np.random.randint(0, 1000000)
    frame: np.ndarray
    base_color: np.ndarray
    frame, base_color = generate_image_data(width, height, seed)

    frame_rgb: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img: Image.Image = Image.fromarray(frame_rgb)

    save_kwargs: dict[str, Any] = {}
    if output.format == 'jpg':
        save_kwargs['quality'] = 95
    elif output.format == 'webp':
        save_kwargs['quality'] = 90
        save_kwargs['method'] = 6

    img.save(str(output.path), **save_kwargs)
    return base_color


# =============================================================================
# SVG Generation Functions
# =============================================================================

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
    seed: int = np.random.randint(0, 1000000)
    np.random.seed(seed)
    base_color: np.ndarray = np.random.randint(0, 256, 3, dtype=np.uint8)

    svg_content: str = generate_svg_content(width, height, base_color)
    output.path.write_text(svg_content)
    return base_color


# =============================================================================
# GIF Animation Functions
# =============================================================================

def write_gif_file(output: MediaOutput, config: VideoConfig) -> np.ndarray:
    """Write animated GIF. Returns base_color."""
    seed: int = np.random.randint(0, 1000000)
    frames: List[np.ndarray]
    base_color: np.ndarray
    frames, base_color = generate_video_frames(config, seed)

    pil_frames: List[Image.Image] = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames]
    duration_ms: int = int((config.duration / len(frames)) * 1000)

    pil_frames[0].save(
        str(output.path),
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0
    )

    return base_color
