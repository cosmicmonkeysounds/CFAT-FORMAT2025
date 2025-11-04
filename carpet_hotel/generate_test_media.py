#!/usr/bin/env python3
"""
Generate test media files for the media-generator Processing sketch.
Creates video files with specified naming patterns and handles conflicts.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def get_existing_files(output_dir, base_name):
    """Find all existing files with the given base name pattern."""
    existing = []
    for file in os.listdir(output_dir):
        if file.startswith(base_name) and file.endswith('.mp4'):
            try:
                # Extract number from filename (e.g., "carpet1.mp4" -> 1)
                num_str = file[len(base_name):-4]
                num = int(num_str)
                existing.append(num)
            except ValueError:
                continue
    return sorted(existing)


def prompt_conflict_resolution(existing_files, base_name):
    """Ask user how to handle existing files."""
    print(f"\nFound {len(existing_files)} existing {base_name} file(s): {base_name}{min(existing_files)}.mp4 to {base_name}{max(existing_files)}.mp4")
    print("\nHow do you want to proceed?")
    print("  1. Overwrite existing files (start from 1)")
    print("  2. Continue from last number (start from {})".format(max(existing_files) + 1))
    print("  3. Cancel")

    while True:
        choice = input("\nEnter your choice (1/2/3): ").strip()
        if choice == '1':
            return 'overwrite', 1
        elif choice == '2':
            return 'continue', max(existing_files) + 1
        elif choice == '3':
            print("Operation cancelled.")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def generate_test_video(output_path, width=1280, height=720, duration=10, color=None):
    """
    Generate a test video using ffmpeg.

    Args:
        output_path: Path where the video will be saved
        width: Video width in pixels
        height: Video height in pixels
        duration: Video duration in seconds
        color: Hex color (e.g., "FF0000" for red), or None for random
    """
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not in PATH.")
        print("Install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)

    # Generate random color if not specified
    if color is None:
        import random
        color = "{:06x}".format(random.randint(0, 0xFFFFFF))

    # Create a test pattern video with color and text
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c=0x{color}:s={width}x{height}:d={duration}',
        '-vf', f"drawtext=text='{Path(output_path).name}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-y',  # Overwrite without asking
        output_path
    ]

    print(f"Generating: {output_path} ({width}x{height}, {duration}s, color=#{color})")

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"✓ Created: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create {output_path}")
        print(f"Error: {e.stderr.decode()}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate test media files for media-generator Processing sketch',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -n 5                    # Generate carpet1.mp4 to carpet5.mp4
  %(prog)s -n 10 -b video          # Generate video1.mp4 to video10.mp4
  %(prog)s -n 3 -b test -d 15      # Generate test1.mp4 to test3.mp4 (15s each)
  %(prog)s -n 5 -w 1920 -h 1080    # Generate HD videos
        '''
    )

    parser.add_argument('-n', '--count', type=int, default=5,
                        help='Number of video files to generate (default: 5)')
    parser.add_argument('-b', '--basename', type=str, default='carpet',
                        help='Base name for generated files (default: carpet)')
    parser.add_argument('-o', '--output', type=str, default='./data',
                        help='Output directory (default: ./data)')
    parser.add_argument('-w', '--width', type=int, default=1280,
                        help='Video width in pixels (default: 1280)')
    parser.add_argument('-h', '--height', type=int, default=720,
                        help='Video height in pixels (default: 720)')
    parser.add_argument('-d', '--duration', type=int, default=10,
                        help='Video duration in seconds (default: 10)')
    parser.add_argument('--random-colors', action='store_true',
                        help='Use random colors for each video')
    parser.add_argument('--force', action='store_true',
                        help='Overwrite existing files without prompting')

    # Handle the -h conflict with argparse's default help
    if '-h' in sys.argv and '--height' not in sys.argv:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Media Generator - Test File Creator")
    print(f"=" * 50)

    # Check for existing files
    existing_files = get_existing_files(output_dir, args.basename)
    start_number = 1

    if existing_files and not args.force:
        mode, start_number = prompt_conflict_resolution(existing_files, args.basename)
        if mode == 'overwrite':
            print(f"\nOverwriting existing files...")
    elif existing_files and args.force:
        print(f"\nForce mode: Overwriting existing files...")

    # Generate videos
    print(f"\nGenerating {args.count} video(s) starting from {args.basename}{start_number}.mp4\n")

    success_count = 0
    for i in range(args.count):
        # No leading zeros - just use the number directly
        file_number = start_number + i
        filename = f"{args.basename}{file_number}.mp4"
        output_path = output_dir / filename

        # Generate random color for each video if requested
        color = None if args.random_colors else "808080"  # Default gray

        if generate_test_video(
            str(output_path),
            width=args.width,
            height=args.height,
            duration=args.duration,
            color=color
        ):
            success_count += 1

    print(f"\n" + "=" * 50)
    print(f"Generated {success_count}/{args.count} video file(s) in {output_dir}")
    print(f"\nFiles: {args.basename}{start_number}.mp4 to {args.basename}{start_number + args.count - 1}.mp4")


if __name__ == '__main__':
    main()
