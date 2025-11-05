#!/usr/bin/env python3
"""
Comprehensive test suite for media_generator package.
Tests all media types, formats, and parameter combinations.

Run from project root:
    python3 -m media_generator.test
"""

import sys
import shutil
from pathlib import Path
from typing import Callable
import numpy as np
from numpy.typing import NDArray

# Import from the package
from media_generator.audio import AudioConfig, MediaOutput, write_audio_file
from media_generator.video import VideoConfig, write_video_file, embed_audio_in_video
from media_generator.image import write_image_file, write_svg_file, write_gif_file


class TestRunner:
    """Test runner for media generator."""

    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.test_dir: Path = Path("test_output")

    def setup(self) -> None:
        """Setup test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

    def teardown(self) -> None:
        """Cleanup test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def verify_file_exists(self, filepath: Path) -> bool:
        """Check if file exists and has non-zero size."""
        path: Path = Path(filepath)
        return path.exists() and path.stat().st_size > 0

    def test(self, name: str, test_func: Callable[[], None]) -> None:
        """Run a single test."""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")

        try:
            test_func()
            self.passed += 1
            print(f"✅ PASSED")
        except Exception as e:
            self.failed += 1
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

    # =============================================================================
    # Audio Tests
    # =============================================================================

    def test_audio_wav_mono_16bit(self) -> None:
        """Test WAV generation - mono, 16-bit."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_mono_16bit.wav",
            format="wav"
        )
        config: AudioConfig = AudioConfig(
            frequency=440.0,
            duration=1.0,
            sample_rate=44100,
            channels=1,
            bit_depth=16
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "WAV file not created"
        assert "mono" in desc and "16-bit" in desc, "Description incorrect"

    def test_audio_wav_stereo_24bit(self) -> None:
        """Test WAV generation - stereo, 24-bit."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_stereo_24bit.wav",
            format="wav"
        )
        config: AudioConfig = AudioConfig(
            frequency=880.0,
            duration=1.0,
            sample_rate=48000,
            channels=2,
            bit_depth=24
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "WAV file not created"
        assert "stereo" in desc and "24-bit" in desc, "Description incorrect"

    def test_audio_ogg(self) -> None:
        """Test OGG Vorbis generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.ogg",
            format="ogg"
        )
        config: AudioConfig = AudioConfig(
            frequency=220.0,
            duration=1.0,
            sample_rate=44100,
            channels=1,
            bit_depth=16
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "OGG file not created"
        assert "Vorbis" in desc, "Description incorrect"

    def test_audio_mp3(self) -> None:
        """Test MP3 generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.mp3",
            format="mp3"
        )
        config: AudioConfig = AudioConfig(
            frequency=440.0,
            duration=1.0,
            sample_rate=44100,
            channels=2,
            bit_depth=16,
            bitrate='192k'
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "MP3 file not created"
        assert "192k" in desc, "Description incorrect"

    def test_audio_m4a(self) -> None:
        """Test M4A/AAC generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.m4a",
            format="m4a"
        )
        config: AudioConfig = AudioConfig(
            frequency=440.0,
            duration=1.0,
            sample_rate=44100,
            channels=1,
            bit_depth=16,
            bitrate='128k'
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "M4A file not created"

    def test_audio_flac(self) -> None:
        """Test FLAC generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.flac",
            format="flac"
        )
        config: AudioConfig = AudioConfig(
            frequency=440.0,
            duration=1.0,
            sample_rate=44100,
            channels=2,
            bit_depth=16
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "FLAC file not created"
        assert "lossless" in desc, "Description incorrect"

    def test_audio_custom_sample_rate(self) -> None:
        """Test audio with custom (decimal) sample rate."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_custom_rate.wav",
            format="wav"
        )
        config: AudioConfig = AudioConfig(
            frequency=440.0,
            duration=1.0,
            sample_rate=43124.3123,
            channels=1,
            bit_depth=16
        )
        desc: str = write_audio_file(output, config)
        assert self.verify_file_exists(output.path), "WAV file not created"

    # =============================================================================
    # Video Tests
    # =============================================================================

    def test_video_mpeg4(self) -> None:
        """Test MP4 video with MPEG-4 codec."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_mpeg4.mp4",
            format="mp4"
        )
        config: VideoConfig = VideoConfig(
            width=640,
            height=480,
            fps=30,
            duration=1,
            codec='mpeg4'
        )
        codec_desc: str
        base_color: NDArray[np.uint8]
        codec_desc, base_color = write_video_file(output, config)
        assert self.verify_file_exists(output.path), "MP4 file not created"
        assert codec_desc == "MPEG-4", f"Codec description incorrect: {codec_desc}"
        assert len(base_color) == 3, f"Base color invalid: {base_color}"

    def test_video_h264(self) -> None:
        """Test MP4 video with H.264 codec."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_h264.mp4",
            format="mp4"
        )
        config: VideoConfig = VideoConfig(
            width=1280,
            height=720,
            fps=30,
            duration=1,
            codec='h264'
        )
        codec_desc: str
        base_color: NDArray[np.uint8]
        codec_desc, base_color = write_video_file(output, config)
        assert self.verify_file_exists(output.path), "MP4 file not created"
        assert codec_desc == "H.264", "Codec description incorrect"

    def test_video_decimal_fps(self) -> None:
        """Test video with decimal frame rate."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_decimal_fps.mp4",
            format="mp4"
        )
        config: VideoConfig = VideoConfig(
            width=640,
            height=480,
            fps=23.976,
            duration=1,
            codec='mpeg4'
        )
        codec_desc: str
        base_color: NDArray[np.uint8]
        codec_desc, base_color = write_video_file(output, config)
        assert self.verify_file_exists(output.path), "MP4 file not created"

    def test_video_custom_resolution(self) -> None:
        """Test video with custom resolution."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_custom_res.mp4",
            format="mp4"
        )
        config: VideoConfig = VideoConfig(
            width=800,
            height=600,
            fps=60,
            duration=2,
            codec='mpeg4'
        )
        codec_desc: str
        base_color: NDArray[np.uint8]
        codec_desc, base_color = write_video_file(output, config)
        assert self.verify_file_exists(output.path), "MP4 file not created"

    def test_video_with_embedded_audio(self) -> None:
        """Test video with embedded audio."""
        # First create video
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_with_audio.mp4",
            format="mp4"
        )
        video_config: VideoConfig = VideoConfig(
            width=640,
            height=480,
            fps=30,
            duration=1,
            codec='mpeg4'
        )
        codec_desc: str
        base_color: NDArray[np.uint8]
        codec_desc, base_color = write_video_file(output, video_config)
        assert self.verify_file_exists(output.path), "MP4 file not created"

        # Embed audio
        audio_config: AudioConfig = AudioConfig(
            frequency=440.0,
            duration=1.0,
            sample_rate=44100,
            channels=2,
            bit_depth=16
        )
        success: bool = embed_audio_in_video(output.path, audio_config, 1.0)
        assert success, "Audio embedding failed"
        assert self.verify_file_exists(output.path), "MP4 file missing after audio embed"

    # =============================================================================
    # Image Tests
    # =============================================================================

    def test_image_jpg(self) -> None:
        """Test JPG image generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.jpg",
            format="jpg"
        )
        base_color: NDArray[np.uint8] = write_image_file(output, 1920, 1080)
        assert self.verify_file_exists(output.path), "JPG file not created"
        assert len(base_color) == 3, "Base color invalid"

    def test_image_png(self) -> None:
        """Test PNG image generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.png",
            format="png"
        )
        base_color: NDArray[np.uint8] = write_image_file(output, 800, 600)
        assert self.verify_file_exists(output.path), "PNG file not created"

    def test_image_webp(self) -> None:
        """Test WebP image generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.webp",
            format="webp"
        )
        base_color: NDArray[np.uint8] = write_image_file(output, 640, 480)
        assert self.verify_file_exists(output.path), "WebP file not created"

    def test_image_bmp(self) -> None:
        """Test BMP image generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.bmp",
            format="bmp"
        )
        base_color: NDArray[np.uint8] = write_image_file(output, 800, 600)
        assert self.verify_file_exists(output.path), "BMP file not created"

    def test_image_tiff(self) -> None:
        """Test TIFF image generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.tiff",
            format="tiff"
        )
        base_color: NDArray[np.uint8] = write_image_file(output, 1024, 768)
        assert self.verify_file_exists(output.path), "TIFF file not created"

    def test_image_svg(self) -> None:
        """Test SVG vector graphics generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.svg",
            format="svg"
        )
        base_color: NDArray[np.uint8] = write_svg_file(output, 800, 600)
        assert self.verify_file_exists(output.path), "SVG file not created"
        assert len(base_color) == 3, "Base color invalid"

        # Verify SVG content
        svg_content: str = output.path.read_text()
        assert '<?xml' in svg_content, "SVG header missing"
        assert '<svg' in svg_content, "SVG tag missing"

    # =============================================================================
    # GIF Animation Tests
    # =============================================================================

    def test_gif_animation(self) -> None:
        """Test GIF animation generation."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test.gif",
            format="gif"
        )
        config: VideoConfig = VideoConfig(
            width=480,
            height=360,
            fps=10,
            duration=1
        )
        base_color: NDArray[np.uint8] = write_gif_file(output, config)
        assert self.verify_file_exists(output.path), "GIF file not created"
        assert len(base_color) == 3, "Base color invalid"

    def test_gif_custom_params(self) -> None:
        """Test GIF with custom parameters."""
        output: MediaOutput = MediaOutput(
            path=self.test_dir / "test_custom.gif",
            format="gif"
        )
        config: VideoConfig = VideoConfig(
            width=640,
            height=480,
            fps=15,
            duration=2
        )
        base_color: NDArray[np.uint8] = write_gif_file(output, config)
        assert self.verify_file_exists(output.path), "GIF file not created"

    # =============================================================================
    # Run All Tests
    # =============================================================================

    def run_all_tests(self) -> bool:
        """Run all test cases."""
        self.setup()

        print("\n" + "="*70)
        print("MEDIA GENERATOR TEST SUITE")
        print("="*70)

        # Audio tests
        print("\n\n" + "="*70)
        print("AUDIO TESTS")
        print("="*70)
        self.test("WAV - Mono 16-bit", self.test_audio_wav_mono_16bit)
        self.test("WAV - Stereo 24-bit", self.test_audio_wav_stereo_24bit)
        self.test("OGG Vorbis", self.test_audio_ogg)
        self.test("MP3", self.test_audio_mp3)
        self.test("M4A/AAC", self.test_audio_m4a)
        self.test("FLAC", self.test_audio_flac)
        self.test("Custom Sample Rate", self.test_audio_custom_sample_rate)

        # Video tests
        print("\n\n" + "="*70)
        print("VIDEO TESTS")
        print("="*70)
        self.test("MP4 - MPEG-4 codec", self.test_video_mpeg4)
        self.test("MP4 - H.264 codec", self.test_video_h264)
        self.test("Decimal FPS (23.976)", self.test_video_decimal_fps)
        self.test("Custom Resolution", self.test_video_custom_resolution)
        self.test("Video with Embedded Audio", self.test_video_with_embedded_audio)

        # Image tests
        print("\n\n" + "="*70)
        print("IMAGE TESTS")
        print("="*70)
        self.test("JPG Image", self.test_image_jpg)
        self.test("PNG Image", self.test_image_png)
        self.test("WebP Image", self.test_image_webp)
        self.test("BMP Image", self.test_image_bmp)
        self.test("TIFF Image", self.test_image_tiff)
        self.test("SVG Vector Graphics", self.test_image_svg)

        # GIF tests
        print("\n\n" + "="*70)
        print("GIF ANIMATION TESTS")
        print("="*70)
        self.test("GIF Animation", self.test_gif_animation)
        self.test("GIF Custom Parameters", self.test_gif_custom_params)

        # Print summary
        self.print_summary()
        self.teardown()

        return self.failed == 0

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print("="*70)

        if self.failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed")


def main() -> None:
    """Main test entry point."""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
