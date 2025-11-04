#!/usr/bin/env python3
"""
Generate n unique 1920x1080 MP4 videos with random colors and effects for testing.
Each video is 1 second long with randomized visual noise/distortion.
"""

import cv2
import numpy as np
import argparse
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser(
        description='Generate n unique test videos with random colors and effects'
    )
    parser.add_argument(
        'n',
        type=int,
        help='Number of videos to generate'
    )
    parser.add_argument(
        '-o', '--output-dir',
        type=str,
        default='test_videos',
        help='Output directory (default: test_videos)'
    )
    parser.add_argument(
        '-w', '--width',
        type=int,
        default=1920,
        help='Video width (default: 1920)'
    )
    parser.add_argument(
        '-H', '--height',
        type=int,
        default=1080,
        help='Video height (default: 1080)'
    )
    parser.add_argument(
        '-f', '--fps',
        type=int,
        default=30,
        help='Frames per second (default: 30)'
    )
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=1,
        help='Duration in seconds (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n🎬 Generating {args.n} test videos...")
    print(f"   Resolution: {args.width}x{args.height}")
    print(f"   Duration: {args.duration}s @ {args.fps}fps")
    print(f"   Output: {output_dir}/\n")
    
    # Generate videos
    for i in range(args.n):
        output_path = output_dir / f"test_video_{i+1:04d}.mp4"
        generate_video(
            output_path,
            width=args.width,
            height=args.height,
            fps=args.fps,
            duration=args.duration
        )
    
    print(f"\n✅ Done! Generated {args.n} videos in '{output_dir}/'")


if __name__ == '__main__':
    main()
