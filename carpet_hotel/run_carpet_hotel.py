#!/usr/bin/env python3
"""
CARPET HOTEL - Launcher Script (Cross-Platform)
=================================================

Coordinates launching both SuperCollider audio engine and Processing sketch.
Uses SuperCollider's command-line interpreter (sclang) for reliable execution.

Supports: macOS, Windows, Linux

Requirements:
    None! (Just SuperCollider and Processing installed)

Usage:
    python run_carpet_hotel.py              # Run both SC and Processing
    python run_carpet_hotel.py --build      # Build Processing executable
    python run_carpet_hotel.py --sc-only    # Run SuperCollider only
    python run_carpet_hotel.py --help       # Show help
"""

import subprocess
import time
import os
import sys
import signal
import argparse
import platform
import threading
from pathlib import Path

class CarpetHotelLauncher:
    def __init__(self, audio_device=None):
        self.sc_process = None
        self.processing_process = None
        self.script_dir = Path(__file__).parent.absolute()
        self.platform = platform.system()  # 'Darwin' (macOS), 'Windows', 'Linux'
        self.audio_device = audio_device

        # Paths
        self.sc_script = self.script_dir / "carpet_hotel_audio.scd"
        self.processing_sketch = self.script_dir / "carpet_hotel.pde"
        self.log_file = self.script_dir / "carpet_hotel.log"

        # Initialize log file (wipe existing content)
        self.init_log_file()

        # Platform-specific paths
        self.setup_platform_paths()

    def init_log_file(self):
        """Initialize/wipe the log file."""
        with open(self.log_file, 'w') as f:
            f.write("=== CARPET HOTEL LOG ===\n")
            f.write(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Platform: {self.platform}\n")
            f.write("="*60 + "\n\n")
        print(f"✓ Log file created: {self.log_file}")

    def log(self, message):
        """Write message to both console and log file."""
        print(message)
        with open(self.log_file, 'a') as f:
            f.write(message + "\n")

    def setup_platform_paths(self):
        """Setup platform-specific paths."""
        if self.platform == 'Darwin':  # macOS
            self.sc_app = "/Applications/SuperCollider.app"
            self.sclang_path = "/Applications/SuperCollider.app/Contents/MacOS/sclang"
            self.processing_java = os.environ.get('PROCESSING_JAVA', 'processing-java')
        elif self.platform == 'Windows':
            self.sc_app = None
            # Check common Windows install locations for sclang
            self.sclang_paths = [
                r"C:\Program Files\SuperCollider\sclang.exe",
                r"C:\Program Files (x86)\SuperCollider\sclang.exe",
                os.environ.get('SCLANG_PATH', '')
            ]
            self.sclang_path = self.find_sclang_windows()
            self.processing_java = os.environ.get('PROCESSING_JAVA', 'processing-java')
        else:  # Linux
            self.sc_app = None
            self.sclang_path = os.environ.get('SCLANG_PATH', '/usr/bin/sclang')
            self.processing_java = os.environ.get('PROCESSING_JAVA', 'processing-java')

    def find_sclang_windows(self):
        """Find sclang executable on Windows."""
        for path in self.sclang_paths:
            if path and os.path.exists(path):
                return path
        return None

    def check_dependencies(self):
        """Check if SuperCollider and Processing are installed."""
        print(f"=== Checking dependencies ({self.platform}) ===")

        # Check SuperCollider (sclang)
        if self.platform == 'Darwin':
            if not os.path.exists(self.sclang_path):
                print(f"❌ sclang not found at: {self.sclang_path}")
                print(f"   Make sure SuperCollider is installed at: {self.sc_app}")
                return False
            print(f"✓ SuperCollider (sclang) found: {self.sclang_path}")
        elif self.platform == 'Windows':
            if not self.sclang_path:
                print(f"❌ sclang.exe not found")
                print("   Expected locations:")
                for path in self.sclang_paths[:2]:
                    print(f"     {path}")
                print("   Or set SCLANG_PATH environment variable")
                return False
            print(f"✓ SuperCollider (sclang) found: {self.sclang_path}")
        else:  # Linux
            if not self.sclang_path or not os.path.exists(self.sclang_path):
                print(f"❌ sclang not found")
                print(f"   Set SCLANG_PATH environment variable")
                return False
            print(f"✓ SuperCollider (sclang) found: {self.sclang_path}")

        # Check Processing
        try:
            result = subprocess.run([self.processing_java, '--help'],
                                  capture_output=True, text=True, timeout=5)
            print(f"✓ Processing command-line tool found: {self.processing_java}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"❌ processing-java not found")
            if self.platform == 'Darwin':
                print('   Add to PATH: export PATH="/Applications/Processing.app/Contents/MacOS:$PATH"')
            else:
                print("   Add Processing to PATH or set PROCESSING_JAVA environment variable")
            return False

        # Check audio script exists
        if not self.sc_script.exists():
            print(f"❌ SuperCollider script not found: {self.sc_script}")
            return False
        print(f"✓ Audio script found: {self.sc_script}")

        # Check Processing sketch exists
        if not self.processing_sketch.exists():
            print(f"❌ Processing sketch not found: {self.processing_sketch}")
            return False
        print(f"✓ Processing sketch found: {self.processing_sketch}")

        print()
        return True

    def stream_output(self, process, prefix, log_file):
        """Stream process output to both console and log file."""
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                message = f"[{prefix}] {line}"
                print(message)
                with open(log_file, 'a') as f:
                    f.write(message + "\n")
        except Exception as e:
            print(f"[{prefix}] Stream error: {e}")

    def launch_supercollider(self):
        """Launch SuperCollider using command-line interpreter (sclang)."""
        self.log(f"\n=== Launching SuperCollider ({self.platform}) ===")
        self.log(f"Script: {self.sc_script}")
        self.log(f"Using sclang: {self.sclang_path}")
        if self.audio_device:
            self.log(f"Audio device: {self.audio_device}")

        try:
            # Launch sclang with the audio script
            # sclang will execute the .scd file and keep running
            self.log("  Starting SuperCollider audio engine...")

            # Build command with optional audio device argument
            cmd = [self.sclang_path, str(self.sc_script)]
            if self.audio_device:
                cmd.append(self.audio_device)

            self.sc_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1
            )

            # Monitor output for success/failure indicators
            self.log("  Waiting for audio server to boot...")
            success_marker = False
            failure_marker = False
            start_time = time.time()
            timeout = 15  # seconds

            # Create a list to collect output
            output_lines = []

            def collect_output():
                nonlocal success_marker, failure_marker
                try:
                    for line in iter(self.sc_process.stdout.readline, ''):
                        if not line:
                            break
                        line = line.rstrip()
                        output_lines.append(line)
                        message = f"[SC] {line}"
                        print(message)
                        with open(self.log_file, 'a') as f:
                            f.write(message + "\n")

                        # Check for success/failure markers
                        if "Audio engine ready!" in line or "Listening for OSC" in line:
                            success_marker = True
                        if "could not initialize audio" in line or "Server 'localhost' exited" in line:
                            failure_marker = True
                except Exception as e:
                    print(f"[SC] Stream error: {e}")

            # Start background thread to collect output
            sc_thread = threading.Thread(target=collect_output, daemon=True)
            sc_thread.start()

            # Wait for success or failure
            while time.time() - start_time < timeout:
                if success_marker:
                    self.log("✓ SuperCollider audio engine launched successfully")
                    self.log("  Audio server booted and ready for OSC")
                    return True
                if failure_marker or self.sc_process.poll() is not None:
                    self.log("\n❌ SuperCollider audio server FAILED to boot!")
                    self.log("  Check the error messages above.")
                    if "could not initialize audio" in '\n'.join(output_lines):
                        self.log("\n  HINT: Try a different audio device:")
                        self.log("    python run_carpet_hotel.py --audio-device \"Multi-Output Device\"")
                    return False
                time.sleep(0.2)

            # Timeout
            self.log("❌ SuperCollider boot timed out (no success confirmation)")
            return False

        except Exception as e:
            self.log(f"❌ Failed to launch SuperCollider: {e}")
            return False

    def launch_processing(self):
        """Launch Processing sketch."""
        self.log(f"\n=== Launching Processing ({self.platform}) ===")
        self.log(f"Sketch: {self.processing_sketch}")

        try:
            self.processing_process = subprocess.Popen(
                [self.processing_java, '--sketch=' + str(self.script_dir), '--run'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1
            )

            # Start background thread to stream output
            processing_thread = threading.Thread(
                target=self.stream_output,
                args=(self.processing_process, "PROC", self.log_file),
                daemon=True
            )
            processing_thread.start()

            self.log("✓ Processing sketch launched")
            return True

        except Exception as e:
            self.log(f"❌ Failed to launch Processing: {e}")
            return False

    def build_processing(self):
        """Build Processing executable."""
        print(f"\n=== Building Processing Executable ({self.platform}) ===")
        print(f"Sketch: {self.script_dir}")

        build_dir = self.script_dir / "build"
        build_dir.mkdir(exist_ok=True)

        # Platform-specific build
        if self.platform == 'Darwin':
            platform_flag = 'macosx'
            extension = '.app'
        elif self.platform == 'Windows':
            platform_flag = 'windows'
            extension = '.exe'
        else:
            platform_flag = 'linux'
            extension = ''

        try:
            print(f"Building for {self.platform}...")
            result = subprocess.run(
                [self.processing_java,
                 '--sketch=' + str(self.script_dir),
                 '--output=' + str(build_dir),
                 '--export',
                 f'--platform={platform_flag}',
                 '--force'],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print("✓ Build successful!")
                print(f"  Output: {build_dir}")

                # Find the executable
                if extension:
                    exe_files = list(build_dir.glob(f"*{extension}"))
                    if exe_files:
                        print(f"  Executable: {exe_files[0]}")
                        if self.platform == 'Darwin':
                            print(f'\n  To run: open "{exe_files[0]}"')
                        else:
                            print(f'\n  To run: {exe_files[0]}')
                        print(f"  Remember: SuperCollider must be running separately!")

                return True
            else:
                print("❌ Build failed")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("❌ Build timed out")
            return False
        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False

    def run(self, sc_only=False):
        """Run the complete system."""
        print("\n" + "="*60)
        print(f"  CARPET HOTEL LAUNCHER ({self.platform})")
        print("="*60 + "\n")

        if not self.check_dependencies():
            return False

        if not self.launch_supercollider():
            return False

        if sc_only:
            print("\n=== SuperCollider Only Mode ===")
            print("Audio engine running in SuperCollider IDE.")
            print("Press Ctrl+C when done.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nDone.")
            return True

        print("\nWaiting for audio engine to stabilize...")
        time.sleep(3)

        if not self.launch_processing():
            self.cleanup()
            return False

        print("\n" + "="*60)
        print("  ✓ SYSTEM RUNNING")
        print("="*60)
        print("\nBoth SuperCollider and Processing are running.")
        print("Press Ctrl+C to stop both processes.\n")

        try:
            self.monitor_processing()
        except KeyboardInterrupt:
            print("\n\nShutting down Processing...")
        finally:
            self.cleanup()

        return True

    def monitor_processing(self):
        """Monitor Processing process."""
        while True:
            if self.processing_process and self.processing_process.poll() is not None:
                print("\n⚠ Processing exited")
                break
            time.sleep(0.5)

    def cleanup(self):
        """Clean up both Processing and SuperCollider processes."""
        print("\n=== Cleaning up ===")

        if self.processing_process:
            try:
                print("Stopping Processing...")
                self.processing_process.terminate()
                self.processing_process.wait(timeout=5)
                print("✓ Processing stopped")
            except subprocess.TimeoutExpired:
                print("  Force killing Processing...")
                self.processing_process.kill()
            except Exception as e:
                print(f"  Warning: {e}")

        if self.sc_process:
            try:
                print("Stopping SuperCollider...")
                self.sc_process.terminate()
                self.sc_process.wait(timeout=5)
                print("✓ SuperCollider stopped")
            except subprocess.TimeoutExpired:
                print("  Force killing SuperCollider...")
                self.sc_process.kill()
            except Exception as e:
                print(f"  Warning: {e}")

        # Kill any remaining SuperCollider/sclang processes
        try:
            print("Killing any remaining SuperCollider processes...")
            if self.platform == 'Darwin' or self.platform == 'Linux':
                subprocess.run(['pkill', '-9', 'sclang'], capture_output=True)
                subprocess.run(['pkill', '-9', 'scsynth'], capture_output=True)
            elif self.platform == 'Windows':
                subprocess.run(['taskkill', '/F', '/IM', 'sclang.exe'], capture_output=True)
                subprocess.run(['taskkill', '/F', '/IM', 'scsynth.exe'], capture_output=True)
            print("✓ All SuperCollider processes terminated")
        except Exception as e:
            print(f"  Warning: {e}")

        print("\n✓ Shutdown complete\n")

def select_audio_device():
    """Interactive guide mode for selecting audio device."""
    print("\n" + "="*60)
    print("  AUDIO DEVICE SELECTION - GUIDE MODE")
    print("="*60 + "\n")

    print("Detecting available audio devices...\n")

    # Common working devices for macOS
    recommended_devices = [
        "MacBook Pro Speakers",
        "Built-in Output",
        "Multi-Output Device"
    ]

    print("Recommended devices (known to work well):")
    for i, device in enumerate(recommended_devices, 1):
        print(f"  {i}. {device}")

    print(f"\nOr enter a custom device name")
    print("(Leave empty to use SuperCollider's default)\n")

    choice = input("Select device [1-3 or custom name]: ").strip()

    if not choice:
        print("Using SuperCollider's default device")
        return None

    try:
        idx = int(choice)
        if 1 <= idx <= len(recommended_devices):
            device = recommended_devices[idx - 1]
            print(f"\nSelected: {device}")
            return device
        else:
            print("Invalid selection, using default")
            return None
    except ValueError:
        # User entered a custom device name
        print(f"\nUsing custom device: {choice}")
        return choice

def main():
    parser = argparse.ArgumentParser(
        description='Carpet Hotel - Launch coordinator for SuperCollider and Processing (Cross-Platform)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_carpet_hotel.py                  # Run everything
  python run_carpet_hotel.py --build          # Build executable
  python run_carpet_hotel.py --sc-only        # Run SuperCollider only

Requirements:
  SuperCollider and Processing installed

Environment Variables:
  SCLANG_PATH       Path to sclang executable
  PROCESSING_JAVA   Path to processing-java command
        """
    )

    parser.add_argument('--build', action='store_true',
                       help='Build Processing executable instead of running')
    parser.add_argument('--sc-only', action='store_true',
                       help='Run SuperCollider only (for testing)')
    parser.add_argument('--audio-device', type=str,
                       help='Audio device name for SuperCollider (e.g. "MacBook Pro Speakers")')
    parser.add_argument('--list-devices', action='store_true',
                       help='List available audio devices and exit')

    args = parser.parse_args()

    # List devices mode
    if args.list_devices:
        print("\nTo list available audio devices, run SuperCollider and execute:")
        print("  ServerOptions.devices")
        print("\nOr run with --audio-device to specify a device.")
        sys.exit(0)

    # Guide mode - select audio device if not specified
    audio_device = args.audio_device
    if not audio_device and not args.build:
        audio_device = select_audio_device()

    launcher = CarpetHotelLauncher(audio_device=audio_device)

    if args.build:
        success = launcher.build_processing()
        sys.exit(0 if success else 1)
    else:
        success = launcher.run(sc_only=args.sc_only)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
