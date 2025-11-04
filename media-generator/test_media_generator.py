#!/usr/bin/env python3
"""
Comprehensive test suite for media_generator package.
Tests all major permutations and cases for media generation.
"""

import subprocess
import sys
from pathlib import Path
import shutil


class TestRunner:
    """Test runner for media generator"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_dir = Path("test_output_suite")
        self.module_path = Path(__file__).parent / "media_generator" / "__main__.py"

    def setup(self):
        """Setup test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

    def teardown(self):
        """Cleanup test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def run_command(self, args, expected_success=True):
        """Run media generator command"""
        cmd = [sys.executable, str(self.module_path)] + args
        result = subprocess.run(cmd, capture_output=True, text=True)

        if expected_success:
            return result.returncode == 0, result
        else:
            return result.returncode != 0, result

    def verify_file_exists(self, filepath):
        """Check if file exists and has non-zero size"""
        path = Path(filepath)
        return path.exists() and path.stat().st_size > 0

    def test(self, name, args, expected_files, expected_success=True):
        """Run a single test"""
        print(f"\n{'='*70}")
        print(f"TEST: {name}")
        print(f"CMD: {' '.join(args)}")

        # Clean test directory before each test to avoid conflicts
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        success, result = self.run_command(args, expected_success)

        if not success:
            self.failed += 1
            print(f"❌ FAILED: Command execution {'failed' if expected_success else 'succeeded unexpectedly'}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return

        # Check expected files
        all_files_exist = True
        for expected_file in expected_files:
            file_path = self.test_dir / expected_file
            if not self.verify_file_exists(file_path):
                all_files_exist = False
                print(f"❌ FAILED: Expected file not found or empty: {expected_file}")

        if all_files_exist:
            self.passed += 1
            print(f"✅ PASSED")
        else:
            self.failed += 1

    def run_all_tests(self):
        """Run all test cases"""
        self.setup()

        print("\n" + "="*70)
        print("MEDIA GENERATOR TEST SUITE")
        print("="*70)

        # ===== IMAGE FORMAT TESTS =====
        print("\n\n" + "="*70)
        print("IMAGE FORMAT TESTS")
        print("="*70)

        self.test(
            "Generate JPG images",
            ["2", "-t", "jpg", "-o", str(self.test_dir), "-w", "640", "-H", "480"],
            ["test_media_1.jpg", "test_media_2.jpg"]
        )

        self.test(
            "Generate PNG images",
            ["2", "-t", "png", "-o", str(self.test_dir), "-w", "800", "-H", "600"],
            ["test_media_1.png", "test_media_2.png"]
        )

        self.test(
            "Generate WebP images",
            ["2", "-t", "webp", "-o", str(self.test_dir), "-w", "640", "-H", "480"],
            ["test_media_1.webp", "test_media_2.webp"]
        )

        self.test(
            "Generate BMP images",
            ["2", "-t", "bmp", "-o", str(self.test_dir), "-w", "640", "-H", "480"],
            ["test_media_1.bmp", "test_media_2.bmp"]
        )

        self.test(
            "Generate TIFF images",
            ["2", "-t", "tiff", "-o", str(self.test_dir), "-w", "640", "-H", "480"],
            ["test_media_1.tiff", "test_media_2.tiff"]
        )

        self.test(
            "Generate SVG images",
            ["2", "-t", "svg", "-o", str(self.test_dir), "-w", "800", "-H", "600"],
            ["test_media_1.svg", "test_media_2.svg"]
        )

        # ===== ANIMATION TESTS =====
        print("\n\n" + "="*70)
        print("ANIMATION TESTS")
        print("="*70)

        self.test(
            "Generate GIF animations",
            ["2", "-t", "gif", "-o", str(self.test_dir), "-d", "1", "-f", "10"],
            ["test_media_1.gif", "test_media_2.gif"]
        )

        # ===== AUDIO FORMAT TESTS =====
        print("\n\n" + "="*70)
        print("AUDIO FORMAT TESTS")
        print("="*70)

        self.test(
            "Generate WAV audio",
            ["2", "-t", "wav", "-o", str(self.test_dir), "-d", "1"],
            ["test_media_1.wav", "test_media_2.wav"]
        )

        self.test(
            "Generate OGG audio",
            ["2", "-t", "ogg", "-o", str(self.test_dir), "-d", "1"],
            ["test_media_1.ogg", "test_media_2.ogg"]
        )

        self.test(
            "Generate MP3 audio",
            ["2", "-t", "mp3", "-o", str(self.test_dir), "-d", "1", "--mp3-bitrate", "128k"],
            ["test_media_1.mp3", "test_media_2.mp3"]
        )

        # ===== VIDEO CODEC TESTS =====
        print("\n\n" + "="*70)
        print("VIDEO CODEC TESTS")
        print("="*70)

        self.test(
            "Generate MP4 video with MPEG-4 codec",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--codec", "mpeg4"],
            ["test_media_1.mp4"]
        )

        self.test(
            "Generate MP4 video with H.264 codec",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--codec", "h264"],
            ["test_media_1.mp4"]
        )

        # ===== VIDEO AUDIO EMBEDDING TESTS =====
        print("\n\n" + "="*70)
        print("VIDEO AUDIO EMBEDDING TESTS")
        print("="*70)

        self.test(
            "Generate video with embedded audio only",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--embed-audio"],
            ["test_media_1.mp4"]
        )

        self.test(
            "Generate video with separate audio file only (WAV)",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--audio-file", "--audio-format", "wav"],
            ["test_media_1.mp4", "test_media_1.wav"]
        )

        self.test(
            "Generate video with separate audio file only (OGG)",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--audio-file", "--audio-format", "ogg"],
            ["test_media_1.mp4", "test_media_1.ogg"]
        )

        self.test(
            "Generate video with separate audio file only (MP3)",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--audio-file", "--audio-format", "mp3"],
            ["test_media_1.mp4", "test_media_1.mp3"]
        )

        self.test(
            "Generate video with BOTH embedded and separate audio (WAV)",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--embed-audio", "--audio-file", "--audio-format", "wav"],
            ["test_media_1.mp4", "test_media_1.wav"]
        )

        self.test(
            "Generate video with BOTH embedded and separate audio (OGG)",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--embed-audio", "--audio-file", "--audio-format", "ogg"],
            ["test_media_1.mp4", "test_media_1.ogg"]
        )

        self.test(
            "Generate video with BOTH embedded and separate audio (MP3)",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--embed-audio", "--audio-file", "--audio-format", "mp3"],
            ["test_media_1.mp4", "test_media_1.mp3"]
        )

        # ===== MULTI-FILE TESTS =====
        print("\n\n" + "="*70)
        print("MULTI-FILE GENERATION TESTS")
        print("="*70)

        self.test(
            "Generate multiple videos with audio",
            ["3", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "--embed-audio", "--min-freq", "200", "--max-freq", "800"],
            ["test_media_1.mp4", "test_media_2.mp4", "test_media_3.mp4"]
        )

        self.test(
            "Generate multiple images with custom dimensions",
            ["5", "-t", "jpg", "-o", str(self.test_dir), "-w", "1024", "-H", "768"],
            [f"test_media_{i}.jpg" for i in range(1, 6)]
        )

        # ===== AUDIO PARAMETER TESTS =====
        print("\n\n" + "="*70)
        print("AUDIO PARAMETER TESTS")
        print("="*70)

        self.test(
            "Generate stereo audio",
            ["1", "-t", "wav", "-o", str(self.test_dir), "-d", "1", "--channels", "2"],
            ["test_media_1.wav"]
        )

        self.test(
            "Generate audio with custom sample rate",
            ["1", "-t", "wav", "-o", str(self.test_dir), "-d", "1", "--sample-rate", "48000"],
            ["test_media_1.wav"]
        )

        self.test(
            "Generate audio with custom bit depth",
            ["1", "-t", "wav", "-o", str(self.test_dir), "-d", "1", "--bit-depth", "24"],
            ["test_media_1.wav"]
        )

        self.test(
            "Generate audio with custom frequency range",
            ["3", "-t", "wav", "-o", str(self.test_dir), "-d", "1", "--min-freq", "440", "--max-freq", "880"],
            ["test_media_1.wav", "test_media_2.wav", "test_media_3.wav"]
        )

        # ===== VIDEO PARAMETER TESTS =====
        print("\n\n" + "="*70)
        print("VIDEO PARAMETER TESTS")
        print("="*70)

        self.test(
            "Generate video with custom FPS",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "-f", "60"],
            ["test_media_1.mp4"]
        )

        self.test(
            "Generate video with custom duration",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "3"],
            ["test_media_1.mp4"]
        )

        self.test(
            "Generate video with custom dimensions",
            ["1", "-t", "mp4", "-o", str(self.test_dir), "-d", "1", "-w", "1280", "-H", "720"],
            ["test_media_1.mp4"]
        )

        # ===== CUSTOM NAMING TESTS =====
        print("\n\n" + "="*70)
        print("CUSTOM NAMING TESTS")
        print("="*70)

        self.test(
            "Generate files with custom base name",
            ["2", "-t", "jpg", "-o", str(self.test_dir), "-n", "custom_name"],
            ["custom_name_1.jpg", "custom_name_2.jpg"]
        )

        # Print summary
        self.print_summary()
        self.teardown()

        return self.failed == 0

    def print_summary(self):
        """Print test summary"""
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


def main():
    """Main test entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
