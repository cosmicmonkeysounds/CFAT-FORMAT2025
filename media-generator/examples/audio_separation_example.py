#!/usr/bin/env python3
"""
Example script demonstrating the audio separator module.
"""

from pathlib import Path
from media_generator.audio_separator import (
    separate_audio_batch,
    separate_audio_from_directory,
    SeparationConfig,
    AudioFormat,
    check_ffmpeg_available
)


def example_1_single_file():
    """Extract audio from a single video file."""
    print("Example 1: Extract audio from a single video file")
    print("-" * 60)

    video_file = Path('test_media/test_media_1.mp4')

    if not video_file.exists():
        print(f"Video file not found: {video_file}")
        return

    config = SeparationConfig(
        output_format=AudioFormat.WAV,
    )

    results = separate_audio_batch([video_file], config, verbose=True)

    print(f"\nResult: {'Success' if results[0].success else 'Failed'}")
    if results[0].success:
        print(f"Audio saved to: {results[0].audio_path}")
    print()


def example_2_multiple_formats():
    """Extract audio in multiple formats from the same video."""
    print("Example 2: Extract audio in multiple formats")
    print("-" * 60)

    video_file = Path('test_media/test_media_1.mp4')

    if not video_file.exists():
        print(f"Video file not found: {video_file}")
        return

    formats = [AudioFormat.WAV, AudioFormat.MP3, AudioFormat.FLAC]
    output_dir = Path('test_media/multi_format_output')
    output_dir.mkdir(exist_ok=True)

    for fmt in formats:
        config = SeparationConfig(
            output_format=fmt,
            bitrate='256k',
            output_dir=output_dir
        )

        results = separate_audio_batch([video_file], config, verbose=False)

        if results[0].success:
            print(f"✓ {fmt.value.upper()}: {results[0].audio_path}")
        else:
            print(f"✗ {fmt.value.upper()}: {results[0].error}")

    print()


def example_3_directory_processing():
    """Process all videos in a directory."""
    print("Example 3: Process all videos in a directory")
    print("-" * 60)

    video_dir = Path('test_media')

    if not video_dir.exists():
        print(f"Directory not found: {video_dir}")
        return

    config = SeparationConfig(
        output_format=AudioFormat.MP3,
        bitrate='192k',
        prefix='audio_',
        output_dir=Path('test_media/extracted')
    )

    results = separate_audio_from_directory(
        video_dir,
        config=config,
        recursive=False,
        verbose=True
    )

    successful = sum(1 for r in results if r.success)
    print(f"\nProcessed {len(results)} files, {successful} successful")
    print()


def example_4_custom_audio_settings():
    """Extract audio with custom settings (mono, specific sample rate)."""
    print("Example 4: Extract with custom audio settings")
    print("-" * 60)

    video_file = Path('test_media/test_media_1.mp4')

    if not video_file.exists():
        print(f"Video file not found: {video_file}")
        return

    config = SeparationConfig(
        output_format=AudioFormat.WAV,
        channels=1,  # Mono
        sample_rate=22050,  # Lower sample rate
        suffix='_mono_22k'
    )

    results = separate_audio_batch([video_file], config, verbose=True)

    if results[0].success:
        print(f"\n✓ Mono audio saved: {results[0].audio_path}")
    print()


def example_5_error_handling():
    """Demonstrate error handling for missing files."""
    print("Example 5: Error handling")
    print("-" * 60)

    # Try to process non-existent files
    video_files = [
        Path('nonexistent1.mp4'),
        Path('nonexistent2.mp4'),
    ]

    config = SeparationConfig(output_format=AudioFormat.WAV)

    results = separate_audio_batch(video_files, config, verbose=False)

    for result in results:
        if result.success:
            print(f"✓ {result.video_path.name}: Success")
        else:
            print(f"✗ {result.video_path.name}: {result.error}")

    print()


def main():
    """Run all examples."""
    print("=" * 60)
    print("Audio Separator Examples")
    print("=" * 60)
    print()

    # Check FFmpeg availability first
    if not check_ffmpeg_available():
        print("Error: FFmpeg is not available. Please install FFmpeg first.")
        return

    print("✓ FFmpeg is available")
    print()

    # Run examples
    try:
        example_1_single_file()
    except Exception as e:
        print(f"Example 1 error: {e}\n")

    try:
        example_2_multiple_formats()
    except Exception as e:
        print(f"Example 2 error: {e}\n")

    try:
        example_3_directory_processing()
    except Exception as e:
        print(f"Example 3 error: {e}\n")

    try:
        example_4_custom_audio_settings()
    except Exception as e:
        print(f"Example 4 error: {e}\n")

    try:
        example_5_error_handling()
    except Exception as e:
        print(f"Example 5 error: {e}\n")

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
