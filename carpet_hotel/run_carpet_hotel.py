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

try:
    from pythonosc import osc_message_builder
    from pythonosc import udp_client
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import ThreadingOSCUDPServer
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False
    print("Warning: python-osc not installed. OSC control mode will not be available.")
    print("  Install with: pip install python-osc")

class CarpetHotelLauncher:
    def __init__(self, audio_device=None, test_mode=False, osc_control=False, displays=None):
        self.sc_process = None
        self.processing_process = None
        self.script_dir = Path(__file__).parent.absolute()
        self.platform = platform.system()  # 'Darwin' (macOS), 'Windows', 'Linux'
        self.audio_device = audio_device
        self.test_mode = test_mode
        self.osc_control = osc_control
        self.displays = displays or [1, 2]

        # OSC configuration
        self.osc_client = None
        self.osc_server = None
        self.osc_thread = None
        self.processing_send_port = 12000  # Send to Processing
        self.processing_recv_port = 12001  # Receive from Processing
        self.current_state = "unknown"

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

    def kill_all_supercollider(self):
        """Kill all SuperCollider processes."""
        try:
            if self.platform == 'Darwin' or self.platform == 'Linux':
                subprocess.run(['pkill', '-9', 'sclang'], capture_output=True)
                subprocess.run(['pkill', '-9', 'scsynth'], capture_output=True)
            elif self.platform == 'Windows':
                subprocess.run(['taskkill', '/F', '/IM', 'sclang.exe'], capture_output=True)
                subprocess.run(['taskkill', '/F', '/IM', 'scsynth.exe'], capture_output=True)
        except Exception:
            pass

    def launch_supercollider(self):
        """Launch SuperCollider using command-line interpreter (sclang) with retry logic."""
        self.log(f"\n=== Launching SuperCollider ({self.platform}) ===")
        self.log(f"Script: {self.sc_script}")
        self.log(f"Using sclang: {self.sclang_path}")
        if self.audio_device:
            self.log(f"Audio device: {self.audio_device}")

        # Kill any existing SuperCollider processes first
        self.log("  Ensuring no SuperCollider processes are running...")
        self.kill_all_supercollider()
        time.sleep(1)

        # Try up to 3 times with progressive delays
        max_attempts = 3
        wait_times = [2, 5, 8]  # Seconds to wait between attempts

        for attempt in range(max_attempts):
            if attempt > 0:
                self.log(f"\n  Retry attempt {attempt + 1}/{max_attempts}...")
                self.log(f"  Killing all SuperCollider processes...")
                self.kill_all_supercollider()
                wait_time = wait_times[attempt - 1]
                self.log(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

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
                        if attempt < max_attempts - 1:
                            # Will retry
                            self.log(f"  Attempt {attempt + 1} failed, will retry...")
                            break
                        else:
                            # Final attempt failed
                            self.log("\n❌ SuperCollider audio server FAILED to boot after all attempts!")
                            self.log("  Check the error messages above.")
                            if "could not initialize audio" in '\n'.join(output_lines):
                                self.log("\n  HINT: Try a different audio device:")
                                self.log("    python run_carpet_hotel.py --audio-device \"Multi-Output Device\"")
                            return False
                    time.sleep(0.2)

                # Check if we timed out
                if not success_marker:
                    if attempt < max_attempts - 1:
                        # Timeout but we have retries left
                        self.log(f"  Attempt {attempt + 1} timed out, will retry...")
                    else:
                        # Final timeout
                        self.log("❌ SuperCollider boot timed out after all attempts")
                        return False

            except Exception as e:
                if attempt < max_attempts - 1:
                    self.log(f"  Attempt {attempt + 1} failed: {e}")
                else:
                    self.log(f"❌ Failed to launch SuperCollider after all attempts: {e}")
                    return False

        # Should not reach here, but just in case
        return False

    def launch_processing(self):
        """Launch Processing sketch."""
        self.log(f"\n=== Launching Processing ({self.platform}) ===")
        self.log(f"Sketch: {self.processing_sketch}")
        self.log(f"Displays: {self.displays}")
        self.log(f"Test mode: {self.test_mode}")
        self.log(f"OSC control: {self.osc_control}")

        try:
            # Build command with arguments
            cmd = [self.processing_java, '--sketch=' + str(self.script_dir), '--run']

            # Add Processing command line arguments
            if self.test_mode:
                cmd.append('--test-mode')
            if self.osc_control:
                cmd.append('--osc-control')
            if self.displays:
                displays_str = ','.join(map(str, self.displays))
                cmd.append(f'--displays={displays_str}')

            self.processing_process = subprocess.Popen(
                cmd,
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

    def setup_osc(self):
        """Setup OSC communication with Processing."""
        if not OSC_AVAILABLE or not self.osc_control:
            return

        self.log("\n=== Setting up OSC control ===")

        # Create OSC client to send to Processing
        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", self.processing_send_port)

        # Create OSC server to receive from Processing
        dispatcher = Dispatcher()
        dispatcher.map("/carpet/state", self.handle_processing_state)
        self.osc_server = ThreadingOSCUDPServer(("127.0.0.1", self.processing_recv_port), dispatcher)

        # Start OSC server in background thread
        self.osc_thread = threading.Thread(target=self.osc_server.serve_forever, daemon=True)
        self.osc_thread.start()

        self.log(f"✓ OSC control enabled")
        self.log(f"  Sending to Processing on port {self.processing_send_port}")
        self.log(f"  Receiving from Processing on port {self.processing_recv_port}")

    def handle_processing_state(self, address, *args):
        """Handle state updates from Processing."""
        state = args[0] if args else "unknown"
        self.current_state = state
        if state == "entering_scene":
            scene = args[1] if len(args) > 1 else "?"
            print(f"\n[Processing] Entered scene {scene}")
        elif state == "entering_transition":
            from_scene = args[1] if len(args) > 1 else "?"
            to_scene = args[2] if len(args) > 2 else "?"
            print(f"\n[Processing] Transitioning {from_scene} -> {to_scene}")
        elif state == "transition_started":
            from_scene = args[1] if len(args) > 1 else "?"
            to_scene = args[2] if len(args) > 2 else "?"
            print(f"\n[Processing] Transition started: {from_scene} -> {to_scene}")
        elif state == "error":
            error = args[1] if len(args) > 1 else "Unknown error"
            print(f"\n[Processing] ERROR: {error}")

    def send_scene_command(self, scene):
        """Send scene transition command to Processing via OSC."""
        if not self.osc_client:
            print("OSC control not enabled!")
            return False

        try:
            self.osc_client.send_message("/carpet/goto", scene)
            print(f"[Python] Sent: goto scene {scene}")
            return True
        except Exception as e:
            print(f"Error sending OSC: {e}")
            return False

    def interactive_control(self):
        """Interactive terminal for controlling scenes."""
        print("\n" + "="*60)
        print("  INTERACTIVE CONTROL MODE")
        print("="*60)
        print("\nCommands:")
        print("  <number>  - Go to scene (e.g., 0, 1, 2)")
        print("  q, quit   - Exit")
        print("  help      - Show this help")
        print()

        while True:
            try:
                cmd = input("Scene > ").strip().lower()

                if not cmd:
                    continue
                elif cmd in ['q', 'quit', 'exit']:
                    break
                elif cmd == 'help':
                    print("\nCommands:")
                    print("  <number>  - Go to scene")
                    print("  q, quit   - Exit")
                    print("  help      - Show this help")
                else:
                    try:
                        scene = int(cmd)
                        self.send_scene_command(scene)
                    except ValueError:
                        print(f"Unknown command: {cmd}")

            except (EOFError, KeyboardInterrupt):
                break

        print("\nExiting interactive mode...")

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

        # Setup OSC if enabled
        if self.osc_control:
            time.sleep(2)  # Give Processing time to start OSC
            self.setup_osc()
            time.sleep(1)

        # Enter interactive mode if OSC control is enabled
        if self.osc_control:
            try:
                self.interactive_control()
            except KeyboardInterrupt:
                print("\n\nShutting down...")
        else:
            print("Press Ctrl+C to stop both processes.\n")
            try:
                self.monitor_processing()
            except KeyboardInterrupt:
                print("\n\nShutting down...")

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

        # Stop OSC server
        if self.osc_server:
            try:
                print("Stopping OSC server...")
                self.osc_server.shutdown()
                print("✓ OSC server stopped")
            except Exception as e:
                print(f"  Warning: {e}")

        print("\n✓ Shutdown complete\n")

def guided_setup():
    """Interactive guided setup for all configuration options."""
    print("\n" + "="*60)
    print("  CARPET HOTEL - GUIDED SETUP")
    print("="*60 + "\n")

    print("This wizard will help you configure Carpet Hotel.\n")

    config = {
        'audio_device': None,
        'test_mode': False,
        'osc_control': False,
        'displays': None
    }

    # === Audio Device Selection ===
    print("\n" + "-"*60)
    print("  1. AUDIO DEVICE")
    print("-"*60)
    print("\nRecommended audio devices (known to work well):")

    recommended_devices = [
        "MacBook Pro Speakers",
        "Built-in Output",
        "Multi-Output Device"
    ]

    for i, device in enumerate(recommended_devices, 1):
        print(f"  {i}. {device}")

    print(f"  {len(recommended_devices) + 1}. Custom device name")
    print(f"  {len(recommended_devices) + 2}. Use SuperCollider's default")

    choice = input(f"\nSelect device [1-{len(recommended_devices) + 2}]: ").strip()

    try:
        idx = int(choice)
        if 1 <= idx <= len(recommended_devices):
            config['audio_device'] = recommended_devices[idx - 1]
            print(f"✓ Selected: {config['audio_device']}")
        elif idx == len(recommended_devices) + 1:
            custom = input("Enter device name: ").strip()
            config['audio_device'] = custom if custom else None
            if config['audio_device']:
                print(f"✓ Using custom device: {config['audio_device']}")
        else:
            print("✓ Using SuperCollider's default device")
    except ValueError:
        print("✓ Using SuperCollider's default device")

    # === Display Configuration ===
    print("\n" + "-"*60)
    print("  2. DISPLAY CONFIGURATION")
    print("-"*60)
    print("\nConfigure which monitors show which floors.")
    print("NOTE: Order matters! First number = floor N, second = floor N+1, etc.")
    print("\nExamples:")
    print("  1,2     - Monitor 1 shows floor N, Monitor 2 shows floor N+1")
    print("  2,1     - Monitor 2 shows floor N, Monitor 1 shows floor N+1")
    print("  1,2,3   - Three monitors showing consecutive floors")
    print("  3,1,2,4 - Four monitors in custom order")
    print("\nQuick presets:")
    print("  1. Single display: [1]")
    print("  2. Two displays: [1, 2] [DEFAULT]")
    print("  3. Three displays: [1, 2, 3]")
    print("  4. Custom configuration")

    choice = input("\nSelect [1-4] or press Enter for default: ").strip()

    try:
        if not choice or choice == '2':
            config['displays'] = [1, 2]
            print("✓ Two displays: [1, 2]")
        elif choice == '1':
            config['displays'] = [1]
            print("✓ Single display: [1]")
        elif choice == '3':
            config['displays'] = [1, 2, 3]
            print("✓ Three displays: [1, 2, 3]")
            print("⚠ Warning: Using 3+ displays may impact performance")
        elif choice == '4':
            custom = input("\nEnter display numbers (comma-separated, e.g., 2,1,3,4):\n  > ").strip()
            if custom:
                config['displays'] = [int(d.strip()) for d in custom.split(',')]
                print(f"✓ Custom configuration: {config['displays']}")
                if len(config['displays']) > 3:
                    print(f"⚠ Warning: Using {len(config['displays'])} displays may impact performance")
                    print("   Consider using fewer windows for smoother playback")
            else:
                config['displays'] = [1, 2]
                print("✓ Using default: [1, 2]")
        else:
            idx = int(choice)
            if idx == 1:
                config['displays'] = [1]
                print("✓ Single display: [1]")
            elif idx == 2:
                config['displays'] = [1, 2]
                print("✓ Two displays: [1, 2]")
            elif idx == 3:
                config['displays'] = [1, 2, 3]
                print("✓ Three displays: [1, 2, 3]")
                print("⚠ Warning: Using 3+ displays may impact performance")
            else:
                config['displays'] = [1, 2]
                print("✓ Using default: [1, 2]")
    except (ValueError, IndexError):
        config['displays'] = [1, 2]
        print("✓ Using default: [1, 2]")

    # === Input Modes ===
    print("\n" + "-"*60)
    print("  3. SCENE CONTROL INPUT METHODS")
    print("-"*60)
    print("\nHow do you want to control scene transitions in Processing?")
    print("(Note: Processing -> SuperCollider audio sync happens automatically)")
    print("\n  1. No direct control (external OSC only)")
    print("  2. Keyboard & mouse (test mode)")
    print("      - Keys: 1-9 for scenes, UP/DOWN for next/prev")
    print("      - Mouse: scroll wheel for volume")
    print("  3. Python terminal (OSC control mode)")
    print("      - Interactive terminal to send scene commands")
    print("  4. Both keyboard/mouse AND Python terminal")

    choice = input("\nSelect [1-4]: ").strip()

    try:
        idx = int(choice)
        if idx == 1:
            print("✓ No direct control (waiting for external OSC)")
        elif idx == 2:
            config['test_mode'] = True
            print("✓ Test mode enabled")
            print("  Controls: 1-9 (scenes), arrows (next/prev), scroll (volume)")
        elif idx == 3:
            config['osc_control'] = True
            if not OSC_AVAILABLE:
                print("⚠ Warning: python-osc not installed!")
                print("  Install with: pip install python-osc")
            else:
                print("✓ OSC control mode enabled")
                print("  You'll get an interactive 'Scene >' prompt")
        elif idx == 4:
            config['test_mode'] = True
            config['osc_control'] = True
            if not OSC_AVAILABLE:
                print("⚠ Warning: python-osc not installed!")
                print("  Install with: pip install python-osc")
            else:
                print("✓ Both control modes enabled")
                print("  Keyboard/mouse in Processing + Python terminal")
    except (ValueError, IndexError):
        print("✓ No direct control")

    # === Summary ===
    print("\n" + "="*60)
    print("  CONFIGURATION SUMMARY")
    print("="*60)
    print(f"Audio device:     {config['audio_device'] or 'Default'}")
    print(f"Displays:         {config['displays']}")
    print(f"Test mode:        {'Yes' if config['test_mode'] else 'No'}")
    print(f"OSC control:      {'Yes' if config['osc_control'] else 'No'}")
    print("="*60 + "\n")

    confirm = input("Proceed with this configuration? [Y/n]: ").strip().lower()
    if confirm and confirm not in ['y', 'yes']:
        print("\nSetup cancelled.")
        sys.exit(0)

    print("\n✓ Configuration confirmed!\n")
    return config

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
    parser.add_argument('--test-mode', action='store_true',
                       help='Enable test mode (keyboard/mouse input in Processing)')
    parser.add_argument('--osc-control', action='store_true',
                       help='Enable OSC control mode (control from Python terminal)')
    parser.add_argument('--displays', type=str,
                       help='Display numbers for windows (e.g., "1,2,3")')

    args = parser.parse_args()

    # List devices mode
    if args.list_devices:
        print("\nTo list available audio devices, run SuperCollider and execute:")
        print("  ServerOptions.devices")
        print("\nOr run with --audio-device to specify a device.")
        sys.exit(0)

    # Check if any config arguments were provided
    has_config_args = any([
        args.audio_device,
        args.test_mode,
        args.osc_control,
        args.displays
    ])

    # Guide mode - run interactive setup if no config args provided and not building
    if not has_config_args and not args.build and not args.sc_only:
        config = guided_setup()
        audio_device = config['audio_device']
        test_mode = config['test_mode']
        osc_control = config['osc_control']
        displays = config['displays']
    else:
        # Use command line arguments
        audio_device = args.audio_device
        test_mode = args.test_mode
        osc_control = args.osc_control
        displays = None
        if args.displays:
            displays = [int(d.strip()) for d in args.displays.split(',')]

    launcher = CarpetHotelLauncher(
        audio_device=audio_device,
        test_mode=test_mode,
        osc_control=osc_control,
        displays=displays
    )

    if args.build:
        success = launcher.build_processing()
        sys.exit(0 if success else 1)
    else:
        success = launcher.run(sc_only=args.sc_only)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
