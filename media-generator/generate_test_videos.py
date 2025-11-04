#!/usr/bin/env python3
"""
Generate n unique 1920x1080 MP4 videos with random colors and effects for testing.
Each video is 1 second long with randomized visual noise/distortion.
"""

import cv2
import numpy as np
import argparse
import re
from pathlib import Path


def find_existing_videos(output_dir, base_name):
    """
    Find existing videos matching the naming pattern and return the highest number.
    Returns None if no matching files found.
    """
    pattern = re.compile(rf'^{re.escape(base_name)}_(\d+)\.mp4$')
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


def prompt_conflict_resolution(output_dir, base_name, max_existing):
    """
    Prompt user to decide how to handle existing files.
    Returns (start_number, overwrite_mode)
    """
    print(f"\n⚠️  Found existing videos matching pattern '{base_name}_*.mp4'")
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
        '-n', '--name',
        type=str,
        default='test_video',
        help='Base name for video files (default: test_video)'
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
    
    # Check for existing files and handle conflicts
    max_existing = find_existing_videos(output_dir, args.name)
    start_num = 1
    
    if max_existing is not None:
        start_num, overwrite = prompt_conflict_resolution(output_dir, args.name, max_existing)
        if overwrite:
            print(f"\n🔄 Will overwrite existing files starting from 1")
        else:
            print(f"\n➕ Continuing from number {start_num}")
    
    print(f"\n🎬 Generating {args.n} test videos...")
    print(f"   Resolution: {args.width}x{args.height}")
    print(f"   Duration: {args.duration}s @ {args.fps}fps")
    print(f"   Output: {output_dir}/\n")
    
    # Generate videos
    for i in range(args.n):
        video_num = start_num + i
        output_path = output_dir / f"{args.name}_{video_num}.mp4"
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
