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
import atexit
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

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

try:
    from screeninfo import get_monitors
    SCREENINFO_AVAILABLE = True
except ImportError:
    SCREENINFO_AVAILABLE = False
    print("Warning: screeninfo not installed. Screen detection will be limited.")
    print("  Install with: pip install screeninfo")

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Arduino elevator control will not be available.")
    print("  Install with: pip install pyserial")

def detect_audio_sample_rate(audio_device=None):
    """
    Detect the sample rate of the audio device.
    Returns the detected sample rate or 48000 as a safe default.
    """
    system = platform.system()

    # Try common sample rates in order of likelihood
    common_rates = [48000, 44100, 96000, 88200, 192000]

    if system == "Darwin":  # macOS
        try:
            # Use system_profiler to get audio info
            result = subprocess.run(
                ['system_profiler', 'SPAudioDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # Look for sample rate in output
            # Format: "      Default Sample Rate: 48000"
            for line in result.stdout.split('\n'):
                if 'Sample Rate' in line or 'sample rate' in line:
                    # Extract number
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        rate = int(match.group(1))
                        if rate in common_rates:
                            print(f"[Audio] Detected sample rate: {rate} Hz")
                            return rate
        except Exception as e:
            print(f"[Audio] Could not auto-detect sample rate: {e}")

    # Default to 48000 Hz (most common on modern systems)
    default_rate = 48000
    print(f"[Audio] Using default sample rate: {default_rate} Hz")
    return default_rate

class CarpetHotelLauncher:
    def __init__(self, audio_device=None, sample_rate=None, enable_keyboard=True, enable_python_terminal=True,
                 enable_osc_external=True, displays=None, arduino_port="auto"):
        self.sc_process = None
        self.processing_process = None
        self.script_dir = Path(__file__).parent.absolute()
        self.platform = platform.system()  # 'Darwin' (macOS), 'Windows', 'Linux'
        self.audio_device = audio_device

        # Auto-detect sample rate if not provided
        if sample_rate is None:
            self.sample_rate = detect_audio_sample_rate(audio_device)
        else:
            self.sample_rate = sample_rate
            print(f"[Audio] Using specified sample rate: {self.sample_rate} Hz")

        # Input modes
        self.enable_keyboard = enable_keyboard          # Keyboard control in Processing
        self.enable_python_terminal = enable_python_terminal  # Python terminal interface
        self.enable_osc_external = enable_osc_external  # Arduino/external OSC control
        self.displays = displays or [1, 2]

        # OSC configuration
        self.osc_client = None  # Send to Processing
        self.osc_server = None  # Receive from Processing
        self.osc_thread = None
        self.sc_osc_client = None  # Send to SuperCollider
        self.sc_osc_server = None  # Receive from SuperCollider
        self.sc_osc_thread = None
        self.processing_send_port = 12000  # Send to Processing
        self.processing_recv_port = 12001  # Receive from Processing
        self.sc_send_port = 57120  # Send to SuperCollider
        self.sc_recv_port = 57121  # Receive from SuperCollider (if needed)
        self.current_state = "unknown"
        self.is_paused = False  # Track pause state

        # Scene tracking for Arduino control
        self.current_scene = 0
        self.total_scenes = self.count_video_files()  # Count video files in data directory

        # Arduino elevator control
        self.arduino_serial = None
        self.arduino_thread = None
        self.arduino_port_config = arduino_port  # "auto" or specific port path
        self.arduino_port = None  # Will be set during setup
        self.arduino_running = False
        self.led_animation_thread = None
        self.led_animation_mode = "OFF"  # OFF, STABLE, TRANSITION
        self.led_animation_running = False

        # SuperCollider status tracking
        self.sc_init_received = False
        self.sc_server_booted = False
        self.sc_ready = False

        # Paths
        self.sc_script = self.script_dir / "carpet_hotel_audio.scd"
        self.processing_sketch = self.script_dir / "carpet_hotel_video.pde"
        self.log_file = self.script_dir / "logs" / "carpet_hotel.log"

        # Initialize log file (wipe existing content)
        self.init_log_file()

        # Platform-specific paths
        self.setup_platform_paths()

        # Register cleanup handlers - CRITICAL: ensure SuperCollider always dies
        atexit.register(self.emergency_cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        if hasattr(signal, 'SIGBREAK'):  # Windows
            signal.signal(signal.SIGBREAK, self.signal_handler)

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
        """Stream process output to log file only (not console)."""
        try:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                message = f"[{prefix}] {line}"

                # Write to log file only (not console)
                # This keeps the terminal clean for user interaction
                with open(log_file, 'a') as f:
                    f.write(message + "\n")
        except Exception as e:
            # Only log errors to file
            with open(log_file, 'a') as f:
                f.write(f"[{prefix}] Stream error: {e}\n")

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
        self.log("  Waiting 5 seconds for processes to terminate...")
        time.sleep(5)

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
                # Reset OSC status flags for this attempt
                self.sc_init_received = False
                self.sc_server_booted = False
                self.sc_ready = False

                # Launch sclang with the audio script
                # Simple approach: just pass audio device as arg, let SC scan data/ directory
                self.log("  Starting SuperCollider audio engine...")

                # Build command - use heredoc to execute the script
                # SC's sclang doesn't auto-execute .scd files, need to use executeFile
                # Note: The SC script handles missing arguments gracefully, using defaults
                execute_cmd = f'thisProcess.interpreter.executeFile("{str(self.sc_script)}");'

                self.log(f"  Executing: {execute_cmd}")

                self.sc_process = subprocess.Popen(
                    [self.sclang_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # Send the execute command to stdin
                try:
                    self.sc_process.stdin.write(execute_cmd + "\n")
                    self.sc_process.stdin.flush()
                    # Keep stdin open so SC doesn't exit
                except Exception as e:
                    self.log(f"  Error writing to SC stdin: {e}")

                # Monitor output and wait for OSC status messages
                self.log("  Waiting for SuperCollider to initialize via OSC...")
                failure_marker = False
                start_time = time.time()
                timeout = 45  # seconds (increased for class library compilation + OSC init)

                # Create a list to collect output
                output_lines = []

                def collect_output():
                    nonlocal failure_marker
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

                            # Check for failure markers
                            if "could not initialize audio" in line or "Server 'localhost' exited" in line or "ERROR: Audio device" in line:
                                failure_marker = True
                    except Exception as e:
                        # Silently handle stream errors
                        pass

                # Start background thread to collect output
                sc_thread = threading.Thread(target=collect_output, daemon=True)
                sc_thread.start()

                # Wait for OSC status messages instead of text parsing
                init_seen = False
                server_seen = False
                ready_seen = False

                while time.time() - start_time < timeout:
                    # Check OSC status flags (set by OSC handlers)
                    if self.sc_init_received and not init_seen:
                        self.log("  ✓ SC script started (received /sc/init)")
                        init_seen = True

                    if self.sc_server_booted and not server_seen:
                        self.log("  ✓ SC audio server booted (received /sc/server)")
                        server_seen = True

                    if self.sc_ready and not ready_seen:
                        self.log("  ✓ SC audio engine ready (received /sc/ready)")
                        ready_seen = True

                    # Success: All OSC messages received
                    if self.sc_ready:
                        self.log("✓ SuperCollider audio engine launched successfully (confirmed via OSC)")
                        self.log("  Waiting 2 seconds for final initialization...")
                        time.sleep(2)
                        return True

                    # Failure: Process died or error detected
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

                    time.sleep(0.1)

                # Check if we timed out
                if not self.sc_ready:
                    if attempt < max_attempts - 1:
                        # Timeout but we have retries left
                        self.log(f"  Attempt {attempt + 1} timed out (OSC messages not received), will retry...")
                        self.log(f"    Status: init={self.sc_init_received}, server={self.sc_server_booted}, ready={self.sc_ready}")
                    else:
                        # Final timeout
                        self.log("❌ SuperCollider boot timed out after all attempts (OSC ready message not received)")
                        self.log(f"  Final status: init={self.sc_init_received}, server={self.sc_server_booted}, ready={self.sc_ready}")
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
        self.log(f"Keyboard control: {self.enable_keyboard}")
        self.log(f"Python terminal: {self.enable_python_terminal}")
        self.log(f"External OSC: {self.enable_osc_external}")

        try:
            # Build command with arguments
            cmd = [self.processing_java, '--sketch=' + str(self.script_dir), '--run']

            # Add Processing command line arguments
            # Enable keyboard control in Processing if requested
            if self.enable_keyboard:
                cmd.append('--test-mode')

            # Enable OSC control if either Python terminal or external OSC is enabled
            if self.enable_python_terminal or self.enable_osc_external:
                cmd.append('--osc-control')

            # Display configuration
            if self.displays:
                displays_str = ','.join(map(str, self.displays))
                cmd.append(f'--displays={displays_str}')

            # Add video files as arguments
            video_files = self.get_video_files()
            if video_files:
                self.log(f"  Passing {len(video_files)} video file(s) to Processing")
                for video_file in video_files:
                    cmd.append(f'--video={video_file}')

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
        """Setup OSC communication with Processing and SuperCollider."""
        if not OSC_AVAILABLE:
            self.log("OSC setup skipped: python-osc not available")
            return

        if not (self.enable_python_terminal or self.enable_osc_external):
            self.log("OSC setup skipped: no OSC-requiring features enabled")
            return

        self.log("\n=== Setting up OSC control ===")

        # Create OSC client to send to Processing
        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", self.processing_send_port)
        self.log(f"✓ OSC client created: {self.osc_client}")

        # Create OSC client to send to SuperCollider
        self.sc_osc_client = udp_client.SimpleUDPClient("127.0.0.1", self.sc_send_port)
        self.log(f"✓ SC OSC client created: {self.sc_osc_client}")

        # Create OSC server to receive from Processing
        dispatcher = Dispatcher()
        dispatcher.map("/carpet/state", self.handle_processing_state)
        # Forward audio commands from Processing to SuperCollider
        dispatcher.map("/carpet/scene", self.forward_to_sc)
        dispatcher.map("/carpet/transition", self.forward_to_sc)
        dispatcher.map("/carpet/volume", self.forward_to_sc)
        # SuperCollider init status messages
        dispatcher.map("/sc/init", self.handle_sc_init)
        dispatcher.map("/sc/server", self.handle_sc_server)
        dispatcher.map("/sc/ready", self.handle_sc_ready)
        # Arduino elevator LED control
        dispatcher.map("/carpet/elevator/led/red", self.handle_elevator_led_red)
        dispatcher.map("/carpet/elevator/led/yellow", self.handle_elevator_led_yellow)
        dispatcher.map("/carpet/elevator/led/green", self.handle_elevator_led_green)
        self.osc_server = ThreadingOSCUDPServer(("127.0.0.1", self.processing_recv_port), dispatcher)

        # Start OSC server in background thread
        self.osc_thread = threading.Thread(target=self.osc_server.serve_forever, daemon=True)
        self.osc_thread.start()

        self.log(f"✓ OSC control enabled")
        self.log(f"  Processing: send={self.processing_send_port}, recv={self.processing_recv_port}")
        self.log(f"  SuperCollider: send={self.sc_send_port}")
        self.log(f"  Python is now the OSC bus (Processing ↔ Python ↔ SuperCollider)")

        # Send a test message to Processing to verify connection
        try:
            self.log("DEBUG: Sending test OSC message to Processing...")
            self.osc_client.send_message("/carpet/test", [])
            self.log("DEBUG: Test message sent")
        except Exception as e:
            self.log(f"DEBUG: Error sending test message: {e}")

    def forward_to_sc(self, address, *args):
        """Forward OSC messages to SuperCollider."""
        if self.sc_osc_client and not self.is_paused:
            try:
                self.sc_osc_client.send_message(address, args)
                # self.log(f"[OSC-FWD] {address} {args} → SuperCollider")
            except Exception as e:
                # self.log(f"[OSC-ERR] Failed to forward to SC: {e}")
                pass

    def handle_processing_state(self, address, *args):
        """Handle state updates from Processing."""
        state = args[0] if args else "unknown"
        self.current_state = state

        # Track current scene for Arduino control
        if state == "entering_scene":
            scene = args[1] if len(args) > 1 else None
            if scene is not None:
                try:
                    self.current_scene = int(scene)
                    self.log(f"[Scene] Now on scene {self.current_scene}")
                except (ValueError, TypeError):
                    pass
        # if state == "entering_scene":
        #     scene = args[1] if len(args) > 1 else "?"
        #     print(f"\n[Processing] Entered scene {scene}")
        # elif state == "entering_transition":
        #     from_scene = args[1] if len(args) > 1 else "?"
        #     to_scene = args[2] if len(args) > 2 else "?"
        #     print(f"\n[Processing] Transitioning {from_scene} -> {to_scene}")
        # elif state == "transition_started":
        #     from_scene = args[1] if len(args) > 1 else "?"
        #     to_scene = args[2] if len(args) > 2 else "?"
        #     print(f"\n[Processing] Transition started: {from_scene} -> {to_scene}")
        # elif state == "error":
        #     error = args[1] if len(args) > 1 else "Unknown error"
        #     print(f"\n[Processing] ERROR: {error}")

    def handle_sc_init(self, address, *args):
        """Handle SuperCollider init message."""
        status = args[0] if args else "unknown"
        self.sc_init_received = True
        self.log(f"[SC-INIT] {status}")
        print(f"[SC-INIT] {status}")

    def handle_sc_server(self, address, *args):
        """Handle SuperCollider server boot message."""
        status = args[0] if args else "unknown"
        self.sc_server_booted = True
        self.log(f"[SC-SERVER] {status}")
        print(f"[SC-SERVER] {status}")

    def handle_sc_ready(self, address, *args):
        """Handle SuperCollider ready message."""
        status = args[0] if args else "unknown"
        self.sc_ready = True
        self.log(f"[SC-READY] {status}")
        print(f"[SC-READY] ✓ Audio engine ready!")

    def send_scene_command(self, scene):
        """Send scene transition command to Processing via OSC."""
        if not self.osc_client:
            # print("OSC control not enabled!")
            return False

        try:
            self.osc_client.send_message("/carpet/goto", scene)
            # print(f"[Python] Sent: goto scene {scene}")
            return True
        except Exception as e:
            # print(f"Error sending OSC: {e}")
            return False

    # ============================================================================
    # ARDUINO ELEVATOR CONTROL
    # ============================================================================

    def get_video_files(self):
        """Get list of video files in the data directory."""
        import os
        import glob

        # Get the directory where this script is located (app/)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # data/ is in parent directory (carpet_hotel/)
        data_dir = os.path.join(os.path.dirname(script_dir), 'data')

        # Find video files (mp4, mov, avi, etc.)
        video_extensions = ['*.mp4', '*.mov', '*.avi', '*.m4v']
        video_files = []
        for ext in video_extensions:
            pattern = os.path.join(data_dir, ext)
            video_files.extend(glob.glob(pattern))

        # Sort files to ensure consistent ordering
        video_files.sort()
        return video_files

    def get_audio_files(self):
        """Get list of audio files in the data directory."""
        import os
        import glob

        # Get the directory where this script is located (app/)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # data/ is in parent directory (carpet_hotel/)
        data_dir = os.path.join(os.path.dirname(script_dir), 'data')

        # Find audio files (wav, aiff, mp3, etc.)
        audio_extensions = ['*.wav', '*.aiff', '*.aif', '*.mp3', '*.m4a']
        audio_files = []
        for ext in audio_extensions:
            pattern = os.path.join(data_dir, ext)
            audio_files.extend(glob.glob(pattern))

        # Sort files to ensure consistent ordering
        audio_files.sort()
        return audio_files

    def count_video_files(self):
        """Count video files in the data directory to determine number of scenes."""
        video_files = self.get_video_files()
        num_videos = len(video_files)

        if num_videos == 0:
            print(f"[WARNING] No video files found in data directory, using default of 9 scenes")
            return 9  # Default fallback

        print(f"[INFO] Found {num_videos} video file(s) in data directory → {num_videos} scenes")
        return num_videos

    def find_arduino_port(self):
        """Find the Arduino port automatically."""
        if not SERIAL_AVAILABLE:
            return None

        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            # Look for Arduino boards (including Nano with CH340/FTDI chips)
            desc_lower = port.description.lower()
            if any(keyword in desc_lower for keyword in ['arduino', 'adafruit', 'ch340', 'ch341', 'ftdi', 'nano']):
                return port.device
        return None

    def setup_arduino(self):
        """Setup Arduino elevator control via serial."""
        print("\n=== Setting up Arduino elevator control ===", flush=True)
        if not SERIAL_AVAILABLE:
            print("Arduino control skipped: pyserial not installed", flush=True)
            self.log("Arduino control skipped: pyserial not installed")
            return False

        if not self.enable_osc_external:
            print("Arduino control skipped: enable_osc_external=False", flush=True)
            return False

        print("=== Setting up Arduino elevator control ===", flush=True)
        self.log("\n=== Setting up Arduino elevator control ===")

        # Determine Arduino port
        if self.arduino_port_config == "auto":
            print("Searching for Arduino (auto-detect)...")
            self.arduino_port = self.find_arduino_port()
            if not self.arduino_port:
                print("⚠ No Arduino found (auto-detect) - elevator control disabled")
                print("  Available ports:")
                self.log("⚠ No Arduino found (auto-detect) - elevator control disabled")
                self.log("  Available ports:")
                for p in serial.tools.list_ports.comports():
                    print(f"    {p.device}: {p.description}")
                    self.log(f"    {p.device}: {p.description}")
                return False
            print(f"✓ Found Arduino at: {self.arduino_port}")
        else:
            # Use user-specified port
            self.arduino_port = self.arduino_port_config
            print(f"Using specified Arduino port: {self.arduino_port}")
            self.log(f"Using specified Arduino port: {self.arduino_port}")

        # Close any existing serial connections to this port
        print(f"Closing any existing connections to {self.arduino_port}...")
        self.log(f"Closing any existing connections to {self.arduino_port}...")
        try:
            # Try to identify and kill processes using the serial port
            if self.platform == 'Darwin' or self.platform == 'Linux':
                # Kill any processes using the serial port
                subprocess.run(['fuser', '-k', self.arduino_port],
                              capture_output=True, timeout=2)
                time.sleep(0.5)
        except Exception as e:
            self.log(f"  (Could not check for existing connections: {e})")

        # Connect to Arduino (using same settings as test_elevator_arduino.py)
        try:
            self.log(f"Connecting to Arduino on {self.arduino_port}...")
            self.arduino_serial = serial.Serial(self.arduino_port, 115200, timeout=1)
            self.log(f"✓ Serial port opened: {self.arduino_serial}")
            time.sleep(2)  # Wait for Arduino to reset

            # Wait for READY message
            self.log("Waiting for Arduino READY message...")
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.arduino_serial.in_waiting:
                    line = self.arduino_serial.readline().decode('utf-8').strip()
                    self.log(f"  Arduino: {line}")
                    if line == "READY":
                        self.log("✓ Arduino connected and ready")
                        break

            # Start monitoring thread
            self.arduino_running = True
            self.arduino_thread = threading.Thread(target=self.monitor_arduino, daemon=True)
            self.arduino_thread.start()

            # Start LED animation thread
            print("[Arduino] Starting LED animation thread...")
            self.log("[Arduino] Starting LED animation thread...")
            self.led_animation_running = True
            self.led_animation_thread = threading.Thread(target=self.led_animation_loop, daemon=True)
            self.led_animation_thread.start()
            time.sleep(0.2)  # Give thread time to start
            self.set_led_animation_mode("STABLE")  # Start in stable mode

            print("✓ Arduino elevator control enabled")
            self.log("✓ Arduino elevator control enabled")
            self.log(f"  Total scenes: {self.total_scenes} (scenes 0-{self.total_scenes-1})")
            self.log(f"  Button presses will trigger scene changes")
            return True

        except serial.SerialException as e:
            self.log(f"⚠ Failed to connect to Arduino: {e}")
            return False

    def monitor_arduino(self):
        """Monitor Arduino serial port for button presses."""
        # Print to BOTH terminal and log
        print("[Arduino] Monitor thread started")
        self.log("[Arduino] Monitor thread started")
        print(f"[Arduino] DEBUG: Serial port: {self.arduino_serial}")
        self.log(f"[Arduino] DEBUG: Serial port: {self.arduino_serial}")
        print(f"[Arduino] DEBUG: Serial port name: {self.arduino_serial.port}")
        self.log(f"[Arduino] DEBUG: Serial port name: {self.arduino_serial.port}")
        print(f"[Arduino] DEBUG: Serial is_open: {self.arduino_serial.is_open}")
        self.log(f"[Arduino] DEBUG: Serial is_open: {self.arduino_serial.is_open}")
        print(f"[Arduino] DEBUG: Serial baudrate: {self.arduino_serial.baudrate}")
        self.log(f"[Arduino] DEBUG: Serial baudrate: {self.arduino_serial.baudrate}")
        print(f"[Arduino] DEBUG: Serial timeout: {self.arduino_serial.timeout}")
        self.log(f"[Arduino] DEBUG: Serial timeout: {self.arduino_serial.timeout}")
        print(f"[Arduino] DEBUG: osc_client = {self.osc_client}")
        self.log(f"[Arduino] DEBUG: osc_client = {self.osc_client}")
        print(f"[Arduino] DEBUG: current_scene = {self.current_scene}, total_scenes = {self.total_scenes}")
        self.log(f"[Arduino] DEBUG: current_scene = {self.current_scene}, total_scenes = {self.total_scenes}")

        # Test read immediately
        print("[Arduino] DEBUG: Checking for immediate data...")
        self.log("[Arduino] DEBUG: Checking for immediate data...")
        if self.arduino_serial.in_waiting:
            print(f"[Arduino] DEBUG: {self.arduino_serial.in_waiting} bytes waiting immediately!")
            self.log(f"[Arduino] DEBUG: {self.arduino_serial.in_waiting} bytes waiting immediately!")
        else:
            print("[Arduino] DEBUG: No data waiting immediately")
            self.log("[Arduino] DEBUG: No data waiting immediately")

        # Use exact same approach as test_elevator_arduino.py
        loop_count = 0
        while self.arduino_running and self.arduino_serial:
            try:
                loop_count += 1
                if loop_count % 100 == 0:  # Log every 100 loops to show it's running
                    self.log(f"[Arduino] Loop #{loop_count}, in_waiting={self.arduino_serial.in_waiting}")

                # Check for button presses from Arduino (same as test script)
                if self.arduino_serial.in_waiting:
                    line = self.arduino_serial.readline().decode('utf-8').strip()
                    print(f"[Arduino] Raw received: '{line}' (len={len(line)})")
                    self.log(f"[Arduino] Raw received: '{line}' (len={len(line)})")

                    if not line:
                        continue

                    if line == "READY":
                        print("[Arduino] Received READY message")
                        self.log("[Arduino] Received READY message")
                        continue

                    # Handle button presses - increment/decrement scene
                    if line == "up":
                        print(f"[Arduino] DEBUG: Handling UP - current_scene={self.current_scene}")
                        next_scene = min(self.current_scene + 1, self.total_scenes - 1)
                        print(f"[Arduino] DEBUG: Calculated next_scene={next_scene}")

                        if next_scene != self.current_scene:
                            print(f"[Arduino] UP button → scene {self.current_scene} → {next_scene}")
                            self.log(f"[Arduino] UP button → scene {self.current_scene} → {next_scene}")

                            # Start transition animation
                            self.set_led_animation_mode("TRANSITION")

                            if self.osc_client:
                                print(f"[Arduino] DEBUG: Sending OSC /carpet/goto {next_scene}")
                                try:
                                    self.osc_client.send_message("/carpet/goto", next_scene)
                                    # Update internal state immediately
                                    self.current_scene = next_scene
                                    print(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")
                                    self.log(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")

                                    # Schedule return to stable mode after transition (1 second)
                                    def back_to_stable():
                                        time.sleep(1.0)  # Reduced from 3.0 to 1.0 for faster feedback
                                        if self.arduino_serial and self.arduino_running:
                                            self.set_led_animation_mode("STABLE")

                                    threading.Thread(target=back_to_stable, daemon=True).start()

                                except Exception as e:
                                    print(f"[Arduino] ERROR sending OSC: {e}")
                                    self.log(f"[Arduino] ERROR sending OSC: {e}")
                            else:
                                print("[Arduino] ERROR: OSC client is None!")
                                self.log("[Arduino] ERROR: OSC client is None!")
                        else:
                            print(f"[Arduino] UP button → already at max scene {self.current_scene}")

                    elif line == "down":
                        print(f"[Arduino] DEBUG: Handling DOWN - current_scene={self.current_scene}")
                        prev_scene = max(self.current_scene - 1, 0)
                        print(f"[Arduino] DEBUG: Calculated prev_scene={prev_scene}")

                        if prev_scene != self.current_scene:
                            print(f"[Arduino] DOWN button → scene {self.current_scene} → {prev_scene}")
                            self.log(f"[Arduino] DOWN button → scene {self.current_scene} → {prev_scene}")

                            # Start transition animation
                            self.set_led_animation_mode("TRANSITION")

                            if self.osc_client:
                                print(f"[Arduino] DEBUG: Sending OSC /carpet/goto {prev_scene}")
                                try:
                                    self.osc_client.send_message("/carpet/goto", prev_scene)
                                    # Update internal state immediately
                                    self.current_scene = prev_scene
                                    print(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")
                                    self.log(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")

                                    # Schedule return to stable mode after transition (1 second)
                                    def back_to_stable():
                                        time.sleep(1.0)  # Reduced from 3.0 to 1.0 for faster feedback
                                        if self.arduino_serial and self.arduino_running:
                                            self.set_led_animation_mode("STABLE")

                                    threading.Thread(target=back_to_stable, daemon=True).start()

                                except Exception as e:
                                    print(f"[Arduino] ERROR sending OSC: {e}")
                                    self.log(f"[Arduino] ERROR sending OSC: {e}")
                            else:
                                print("[Arduino] ERROR: OSC client is None!")
                                self.log("[Arduino] ERROR: OSC client is None!")
                        else:
                            print(f"[Arduino] DOWN button → already at min scene {self.current_scene}")

                    else:
                        print(f"[Arduino] Unknown message: '{line}'")
                        self.log(f"[Arduino] Unknown message: '{line}'")

                time.sleep(0.01)  # Small delay to prevent CPU spinning

            except Exception as e:
                if self.arduino_running:  # Only log if we haven't deliberately shut down
                    self.log(f"[Arduino] Error reading serial: {e}")
                break

        self.log("[Arduino] Monitor thread stopped")

    def set_led_animation_mode(self, mode):
        """Set LED animation mode (OFF, STABLE, TRANSITION).

        Args:
            mode: "OFF", "STABLE", or "TRANSITION"
        """
        self.led_animation_mode = mode.upper()
        print(f"[Arduino] LED animation mode: {self.led_animation_mode}")
        self.log(f"[Arduino] LED animation mode: {self.led_animation_mode}")

    def led_animation_loop(self):
        """Thread that controls LED animations with 60FPS tick system."""
        print("[Arduino] LED animation thread started (60 FPS)")
        self.log("[Arduino] LED animation thread started (60 FPS)")

        # Animation state
        frame = 0  # Frame counter
        fps = 60
        frame_time = 1.0 / fps  # ~16.67ms per frame

        # Pattern state
        stable_blink_frames = int(0.15 * fps)  # 150ms = 9 frames at 60fps
        transition_cycle_frames = int(0.1 * fps)  # 100ms = 6 frames at 60fps

        # LED state cache to avoid redundant serial writes
        led_state = {"RED": None, "YELLOW": None, "GREEN": None}

        def set_led_if_changed(led_name, new_state):
            """Only send LED command if state actually changed."""
            if led_state[led_name] != new_state:
                self.send_arduino_led(led_name, new_state)
                led_state[led_name] = new_state

        while self.led_animation_running and self.arduino_serial:
            loop_start = time.time()

            try:
                if self.led_animation_mode == "OFF":
                    # All LEDs off
                    set_led_if_changed("RED", False)
                    set_led_if_changed("YELLOW", False)
                    set_led_if_changed("GREEN", False)
                    frame = 0  # Reset frame counter when OFF

                elif self.led_animation_mode == "STABLE":
                    # Green LED blinks at 150ms intervals
                    blink_on = (frame // stable_blink_frames) % 2 == 0
                    set_led_if_changed("RED", False)
                    set_led_if_changed("YELLOW", False)
                    set_led_if_changed("GREEN", blink_on)

                elif self.led_animation_mode == "TRANSITION":
                    # Cycle through RED -> YELLOW -> GREEN at 100ms intervals
                    cycle_position = (frame // transition_cycle_frames) % 3
                    set_led_if_changed("RED", cycle_position == 0)
                    set_led_if_changed("YELLOW", cycle_position == 1)
                    set_led_if_changed("GREEN", cycle_position == 2)

                frame += 1

            except Exception as e:
                self.log(f"[Arduino] LED animation error: {e}")

            # Sleep for remaining frame time to maintain 60 FPS
            elapsed = time.time() - loop_start
            sleep_time = max(0, frame_time - elapsed)
            time.sleep(sleep_time)

        # Turn off all LEDs when thread stops
        try:
            self.send_arduino_led("RED", False)
            self.send_arduino_led("YELLOW", False)
            self.send_arduino_led("GREEN", False)
        except:
            pass

        print("[Arduino] LED animation thread stopped")
        self.log("[Arduino] LED animation thread stopped")

    def send_arduino_led(self, led_name, state):
        """Send LED command to Arduino via serial (legacy - now using animations)."""
        if not self.arduino_serial:
            return

        try:
            cmd = f"{led_name.upper()}:{1 if state else 0}\n"
            self.arduino_serial.write(cmd.encode())
            self.log(f"[Arduino] LED command: {cmd.strip()}")
        except Exception as e:
            self.log(f"[Arduino] Error sending LED command: {e}")

    def handle_elevator_led_red(self, address, *args):
        """Handle red LED OSC message."""
        if args:
            state = int(args[0])
            self.send_arduino_led("RED", state)

    def handle_elevator_led_yellow(self, address, *args):
        """Handle yellow LED OSC message."""
        if args:
            state = int(args[0])
            self.send_arduino_led("YELLOW", state)

    def handle_elevator_led_green(self, address, *args):
        """Handle green LED OSC message."""
        if args:
            state = int(args[0])
            self.send_arduino_led("GREEN", state)

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

        # Start background thread to monitor Processing
        def monitor_proc():
            while True:
                if self.processing_process and self.processing_process.poll() is not None:
                    print("\n\n⚠ Processing has exited - shutting down...")
                    # Trigger exit by simulating EOF
                    os.kill(os.getpid(), signal.SIGINT)
                    break
                time.sleep(0.5)

        monitor_thread = threading.Thread(target=monitor_proc, daemon=True)
        monitor_thread.start()

        while True:
            try:
                # Check if Processing has exited
                if self.processing_process and self.processing_process.poll() is not None:
                    print("\n\n⚠ Processing has exited - shutting down...")
                    break

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

    def start(self):
        """Start the system (non-blocking, for GUI mode)."""
        print("\n" + "="*60)
        print(f"  CARPET HOTEL LAUNCHER ({self.platform})")
        print("="*60 + "\n")

        if not self.check_dependencies():
            return False

        if not self.launch_supercollider():
            return False

        print("\nWaiting for audio engine to stabilize...")
        time.sleep(3)

        if not self.launch_processing():
            self.cleanup()
            return False

        print("\n" + "="*60)
        print("  ✓ SYSTEM RUNNING")
        print("="*60)
        print("\nBoth SuperCollider and Processing are running.")

        # Setup OSC if Python terminal or external OSC is enabled
        if self.enable_python_terminal or self.enable_osc_external:
            print("\n" + "="*60)
            print("  OSC MODE ENABLED")
            print("="*60)
            print(f"\nKeyboard control: {'✓' if self.enable_keyboard else '✗'}")
            print(f"Python terminal: {'✓' if self.enable_python_terminal else '✗'}")
            print(f"External OSC (Arduino): {'✓' if self.enable_osc_external else '✗'}")
            print(f"\nLog output is being written to: {self.log_file}")
            print("(Terminal output from SC/PROC is suppressed for clean interface)\n")
            print("Waiting for Processing to initialize OSC...")
            time.sleep(5)  # Give Processing more time to start OSC server
            self.setup_osc()
            print("Waiting for OSC to stabilize...")
            time.sleep(2)
            print(f"\n[DEBUG] enable_osc_external = {self.enable_osc_external}")
            if self.enable_osc_external:
                print("[DEBUG] About to call setup_arduino()...")
                try:
                    self.setup_arduino()
                    print("[DEBUG] setup_arduino() returned")
                except Exception as e:
                    print(f"[ERROR] Exception in setup_arduino(): {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("[DEBUG] Skipping Arduino setup (enable_osc_external=False)")
            time.sleep(1)

        print("\n✓ Startup complete - GUI controls are active\n")
        print(f"Check log for output: {self.log_file}\n")

        return True

    def run(self, sc_only=False):
        """Run the complete system (blocking, for CLI mode)."""
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

        # Setup OSC if Python terminal or external OSC is enabled
        if self.enable_python_terminal or self.enable_osc_external:
            print("\n" + "="*60)
            print("  OSC MODE ENABLED")
            print("="*60)
            print(f"\nKeyboard control: {'✓' if self.enable_keyboard else '✗'}")
            print(f"Python terminal: {'✓' if self.enable_python_terminal else '✗'}")
            print(f"External OSC (Arduino): {'✓' if self.enable_osc_external else '✗'}")
            print(f"\nLog output is being written to: {self.log_file}")
            print("(Terminal output from SC/PROC is suppressed for clean interface)\n")
            print("Waiting for Processing to initialize OSC...")
            time.sleep(5)  # Give Processing more time to start OSC server
            self.setup_osc()
            print("Waiting for OSC to stabilize...")
            time.sleep(2)
            print(f"\n[DEBUG] enable_osc_external = {self.enable_osc_external}")
            if self.enable_osc_external:
                print("[DEBUG] About to call setup_arduino()...")
                try:
                    self.setup_arduino()
                    print("[DEBUG] setup_arduino() returned")
                except Exception as e:
                    print(f"[ERROR] Exception in setup_arduino(): {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("[DEBUG] Skipping Arduino setup (enable_osc_external=False)")
            time.sleep(1)

        # Enter interactive mode if Python terminal is enabled
        if self.enable_python_terminal:
            try:
                self.interactive_control()
            except KeyboardInterrupt:
                print("\n\nShutting down...")
        else:
            print("Press Ctrl+C to stop both processes.\n")
            print(f"Check log for output: {self.log_file}\n")
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
                print("\n\n⚠ Processing has exited - shutting down...")
                break
            time.sleep(0.5)

    def signal_handler(self, signum, frame):
        """Handle signals (SIGINT, SIGTERM, etc.) - ensure SuperCollider dies."""
        print(f"\n\nReceived signal {signum} - forcing cleanup...")
        self.emergency_cleanup()
        sys.exit(0)

    def emergency_cleanup(self):
        """Emergency cleanup - ALWAYS kill SuperCollider no matter what."""
        # This runs on exit, signals, crashes, etc.
        # Be aggressive - make sure SuperCollider DIES
        try:
            if self.platform == 'Darwin' or self.platform == 'Linux':
                subprocess.run(['pkill', '-9', 'sclang'], capture_output=True, timeout=2)
                subprocess.run(['pkill', '-9', 'scsynth'], capture_output=True, timeout=2)
            elif self.platform == 'Windows':
                subprocess.run(['taskkill', '/F', '/IM', 'sclang.exe'], capture_output=True, timeout=2)
                subprocess.run(['taskkill', '/F', '/IM', 'scsynth.exe'], capture_output=True, timeout=2)
        except:
            pass  # Fail silently on emergency cleanup

    def stop(self):
        """Stop all processes but keep launcher instance alive."""
        print("\n=== Stopping Carpet Hotel ===")
        self.cleanup()
        print("✓ All processes stopped (launcher still active)\n")

    def pause(self):
        """Pause playback - mute SC, pause videos, disable OSC inputs."""
        print("\n=== Pausing Carpet Hotel ===")
        self.is_paused = True

        # Mute SuperCollider by setting volume to 0
        if self.sc_osc_client:
            try:
                self.sc_osc_client.send_message("/carpet/volume", [0.0])
                print("  ✓ SuperCollider muted")
            except Exception as e:
                print(f"  Warning: Failed to mute SC: {e}")

        # Send pause command to Processing (if it supports it)
        if self.osc_client:
            try:
                self.osc_client.send_message("/carpet/pause", [1])
                print("  ✓ Processing paused")
            except Exception as e:
                print(f"  Warning: Failed to pause Processing: {e}")

        print("✓ Paused (OSC forwarding disabled)\n")

    def resume(self):
        """Resume playback - unmute SC, resume videos, enable OSC inputs."""
        print("\n=== Resuming Carpet Hotel ===")
        self.is_paused = False

        # Unmute SuperCollider by setting volume to default (0.7)
        if self.sc_osc_client:
            try:
                self.sc_osc_client.send_message("/carpet/volume", [0.7])
                print("  ✓ SuperCollider unmuted")
            except Exception as e:
                print(f"  Warning: Failed to unmute SC: {e}")

        # Send resume command to Processing (if it supports it)
        if self.osc_client:
            try:
                self.osc_client.send_message("/carpet/pause", [0])
                print("  ✓ Processing resumed")
            except Exception as e:
                print(f"  Warning: Failed to resume Processing: {e}")

        print("✓ Resumed (OSC forwarding enabled)\n")

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
                # Close stdin to signal shutdown
                if self.sc_process.stdin:
                    self.sc_process.stdin.close()
                self.sc_process.terminate()
                self.sc_process.wait(timeout=5)
                print("✓ SuperCollider stopped")
            except subprocess.TimeoutExpired:
                print("  Force killing SuperCollider...")
                self.sc_process.kill()
            except Exception as e:
                print(f"  Warning: {e}")

        # CRITICAL: Kill any remaining SuperCollider/sclang processes
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

        # Stop OSC servers
        if self.osc_server:
            try:
                print("Stopping Processing OSC server...")
                self.osc_server.shutdown()
                print("✓ Processing OSC server stopped")
            except Exception as e:
                print(f"  Warning: {e}")

        if self.sc_osc_server:
            try:
                print("Stopping SuperCollider OSC server...")
                self.sc_osc_server.shutdown()
                print("✓ SuperCollider OSC server stopped")
            except Exception as e:
                print(f"  Warning: {e}")

        # Stop Arduino
        if self.arduino_serial:
            try:
                print("Stopping Arduino elevator control...")
                # Stop LED animation thread first
                if self.led_animation_thread:
                    self.led_animation_running = False
                    self.led_animation_thread.join(timeout=1.0)
                # Turn off all LEDs before disconnecting
                self.set_led_animation_mode("OFF")
                time.sleep(0.2)
                self.arduino_running = False
                self.arduino_serial.close()
                print("✓ Arduino disconnected")
            except Exception as e:
                print(f"  Warning: {e}")

        # Reset process and client references
        self.sc_process = None
        self.processing_process = None
        self.osc_client = None
        self.osc_server = None
        self.sc_osc_client = None
        self.sc_osc_server = None
        self.arduino_serial = None
        self.arduino_running = False

        print("\n✓ Shutdown complete\n")

# GUI code has been moved to carpet_hotel_gui.py
# Run 'python carpet_hotel_gui.py' to launch the graphical interface


