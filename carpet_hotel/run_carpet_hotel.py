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

class CarpetHotelLauncher:
    def __init__(self, audio_device=None, enable_keyboard=True, enable_python_terminal=True,
                 enable_osc_external=True, displays=None, arduino_port="auto"):
        self.sc_process = None
        self.processing_process = None
        self.script_dir = Path(__file__).parent.absolute()
        self.platform = platform.system()  # 'Darwin' (macOS), 'Windows', 'Linux'
        self.audio_device = audio_device

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

        # Paths
        self.sc_script = self.script_dir / "carpet_hotel_audio.scd"
        self.processing_sketch = self.script_dir / "carpet_hotel.pde"
        self.log_file = self.script_dir / "carpet_hotel.log"

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
                        # print(f"[SC] Stream error: {e}")
                        pass

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

    def count_video_files(self):
        """Count video files in the data directory to determine number of scenes."""
        import os
        import glob

        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, 'data')

        # Count video files (mp4, mov, avi, etc.)
        video_extensions = ['*.mp4', '*.mov', '*.avi', '*.m4v']
        video_files = []
        for ext in video_extensions:
            pattern = os.path.join(data_dir, ext)
            video_files.extend(glob.glob(pattern))

        num_videos = len(video_files)
        if num_videos == 0:
            print(f"[WARNING] No video files found in {data_dir}, using default of 9 scenes")
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

            # Initialize LED animations
            print("[Arduino] Initializing LED animations...")
            self.log("[Arduino] Initializing LED animations...")
            time.sleep(0.5)  # Give thread time to start
            self.send_arduino_period(400)  # 400ms per LED in transition mode
            time.sleep(0.1)
            self.send_arduino_animation("STABLE")  # Start in stable mode

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
                            self.send_arduino_animation("TRANSITION")

                            if self.osc_client:
                                print(f"[Arduino] DEBUG: Sending OSC /carpet/goto {next_scene}")
                                try:
                                    self.osc_client.send_message("/carpet/goto", next_scene)
                                    # Update internal state immediately
                                    self.current_scene = next_scene
                                    print(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")
                                    self.log(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")

                                    # Schedule return to stable mode after transition (3 seconds)
                                    def back_to_stable():
                                        time.sleep(3.0)
                                        if self.arduino_serial and self.arduino_running:
                                            self.send_arduino_animation("STABLE")

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
                            self.send_arduino_animation("TRANSITION")

                            if self.osc_client:
                                print(f"[Arduino] DEBUG: Sending OSC /carpet/goto {prev_scene}")
                                try:
                                    self.osc_client.send_message("/carpet/goto", prev_scene)
                                    # Update internal state immediately
                                    self.current_scene = prev_scene
                                    print(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")
                                    self.log(f"[Arduino] DEBUG: OSC sent, current_scene updated to {self.current_scene}")

                                    # Schedule return to stable mode after transition (3 seconds)
                                    def back_to_stable():
                                        time.sleep(3.0)
                                        if self.arduino_serial and self.arduino_running:
                                            self.send_arduino_animation("STABLE")

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

    def send_arduino_animation(self, mode):
        """Send animation command to Arduino via serial.

        Args:
            mode: "STABLE", "TRANSITION", or "OFF"
        """
        if not self.arduino_serial:
            return

        try:
            cmd = f"ANIM:{mode.upper()}\n"
            self.arduino_serial.write(cmd.encode())
            print(f"[Arduino] Animation: {cmd.strip()}")
            self.log(f"[Arduino] Animation: {cmd.strip()}")
        except Exception as e:
            self.log(f"[Arduino] Error sending animation command: {e}")

    def send_arduino_period(self, period_ms):
        """Send animation period to Arduino via serial.

        Args:
            period_ms: Period in milliseconds
        """
        if not self.arduino_serial:
            return

        try:
            cmd = f"PERIOD:{period_ms}\n"
            self.arduino_serial.write(cmd.encode())
            print(f"[Arduino] Period: {cmd.strip()}")
            self.log(f"[Arduino] Period: {cmd.strip()}")
        except Exception as e:
            self.log(f"[Arduino] Error sending period command: {e}")

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
                self.arduino_running = False
                # Turn off all LED animations before disconnecting
                self.send_arduino_animation("OFF")
                time.sleep(0.1)
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

def detect_screens():
    """Detect available screens using screeninfo library."""
    screens = []

    if SCREENINFO_AVAILABLE:
        try:
            monitors = get_monitors()
            for i, monitor in enumerate(monitors):
                # Get the monitor name - this is the REAL name like "MacBook Built-In", "Samsung Odyssey G9", etc.
                display_name = getattr(monitor, 'name', None)

                # Handle None or empty name
                if not display_name:
                    display_name = f'Display {i + 1}'
                elif display_name.startswith('\\\\'):
                    # Windows device path - extract friendly name
                    display_name = f'Display {i + 1}'

                # Mark primary display
                if i == 0 or getattr(monitor, 'is_primary', False):
                    if 'Primary' not in display_name:
                        display_name = f'{display_name} (Primary)'

                screens.append({
                    'index': i + 1,
                    'name': display_name,
                    'width': monitor.width,
                    'height': monitor.height,
                    'x': monitor.x,
                    'y': monitor.y,
                    'is_primary': getattr(monitor, 'is_primary', i == 0)
                })
        except Exception as e:
            print(f"Warning: Could not detect screens: {e}")
            # Fallback to default
            screens = [
                {'index': 1, 'name': 'Display 1 (Primary)', 'width': 1920, 'height': 1080, 'x': 0, 'y': 0, 'is_primary': True}
            ]
    else:
        # screeninfo not available - provide default options
        screens = [
            {'index': 1, 'name': 'Display 1 (Primary)', 'width': 1920, 'height': 1080, 'x': 0, 'y': 0, 'is_primary': True},
            {'index': 2, 'name': 'Display 2', 'width': 1920, 'height': 1080, 'x': 1920, 'y': 0, 'is_primary': False},
            {'index': 3, 'name': 'Display 3', 'width': 1920, 'height': 1080, 'x': 3840, 'y': 0, 'is_primary': False},
            {'index': 4, 'name': 'Display 4', 'width': 1920, 'height': 1080, 'x': 5760, 'y': 0, 'is_primary': False}
        ]

    return screens

def load_settings():
    """Load last saved settings from config file."""
    config_file = Path(__file__).parent / ".carpet_hotel_config.json"
    default_settings = {
        'audio_device': None,
        'enable_keyboard': True,
        'enable_python_terminal': True,
        'enable_osc_external': True,
        'displays': [1, 2],
        'arduino_port': 'auto'
    }

    try:
        if config_file.exists():
            with open(config_file, 'r') as f:
                settings = json.load(f)
                # Merge with defaults in case new settings were added
                return {**default_settings, **settings}
    except Exception as e:
        print(f"Warning: Could not load settings: {e}")

    return default_settings

def save_settings(settings):
    """Save settings to config file."""
    config_file = Path(__file__).parent / ".carpet_hotel_config.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print(f"✓ Settings saved to {config_file}")
        print(f"  arduino_port: {settings.get('arduino_port', 'not set')}")
    except Exception as e:
        print(f"Warning: Could not save settings: {e}")

def guided_setup_gui():
    """Persistent GUI control panel for configuration and control."""
    result = {'cancelled': True}

    root = tk.Tk()
    root.title("Carpet Hotel - Control Panel")
    root.geometry("700x600")
    root.resizable(False, False)

    # Load previous settings
    saved_settings = load_settings()

    # State management
    launcher_instance = [None]  # Use list to allow modification in nested functions
    launcher_thread = [None]
    is_running = [False]
    is_paused = [False]

    # Configuration storage
    config = {
        'audio_device': saved_settings.get('audio_device'),
        'enable_keyboard': saved_settings.get('enable_keyboard', True),
        'enable_python_terminal': saved_settings.get('enable_python_terminal', True),
        'enable_osc_external': saved_settings.get('enable_osc_external', True),
        'displays': saved_settings.get('displays', [1, 2])
    }

    current_page = [0]  # Use list to allow modification in nested functions
    preview_windows = {}  # Store preview windows for cleanup

    # Create notebook for wizard pages
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)

    # ===== PAGE 1: Audio Device =====
    page1 = ttk.Frame(notebook)
    notebook.add(page1, text="1. Audio")

    ttk.Label(page1, text="Audio Output Device", font=('Arial', 14, 'bold')).pack(pady=10)
    ttk.Label(page1, text="Choose where you want the audio to play from:").pack(pady=5)

    # Initialize audio selection from saved settings
    saved_audio = config.get('audio_device')
    if saved_audio in ["MacBook Pro Speakers", "Built-in Output", "Multi-Output Device"]:
        audio_var = tk.StringVar(value=saved_audio)
        audio_custom = tk.StringVar()
    elif saved_audio:
        audio_var = tk.StringVar(value="custom")
        audio_custom = tk.StringVar(value=saved_audio)
    else:
        audio_var = tk.StringVar(value="default")
        audio_custom = tk.StringVar()

    ttk.Radiobutton(page1, text="MacBook Pro Speakers (recommended)",
                    variable=audio_var, value="MacBook Pro Speakers").pack(anchor='w', padx=40, pady=5)
    ttk.Radiobutton(page1, text="Built-in Output",
                    variable=audio_var, value="Built-in Output").pack(anchor='w', padx=40, pady=5)
    ttk.Radiobutton(page1, text="Multi-Output Device",
                    variable=audio_var, value="Multi-Output Device").pack(anchor='w', padx=40, pady=5)

    custom_frame = ttk.Frame(page1)
    custom_frame.pack(anchor='w', padx=40, pady=5)
    ttk.Radiobutton(custom_frame, text="Custom:",
                    variable=audio_var, value="custom").pack(side='left')
    ttk.Entry(custom_frame, textvariable=audio_custom, width=25).pack(side='left', padx=5)

    ttk.Radiobutton(page1, text="Automatic (let SuperCollider choose)",
                    variable=audio_var, value="default").pack(anchor='w', padx=40, pady=5)

    # ===== PAGE 2: Displays =====
    page2 = ttk.Frame(notebook)
    notebook.add(page2, text="2. Displays")

    ttk.Label(page2, text="Display Configuration", font=('Arial', 14, 'bold')).pack(pady=10)
    ttk.Label(page2, text="Select which displays to use (order matters!)").pack(pady=5)

    # Detect available screens
    available_screens = detect_screens()

    # Create two-column layout for lists
    lists_frame = ttk.Frame(page2)
    lists_frame.pack(fill='both', expand=True, padx=20, pady=10)

    # Left side: Available displays
    left_frame = ttk.Frame(lists_frame)
    left_frame.pack(side='left', fill='both', expand=True, padx=5)

    ttk.Label(left_frame, text="Available Displays:", font=('Arial', 10, 'bold')).pack()
    ttk.Label(left_frame, text="(hover to preview)", foreground='gray', font=('Arial', 8)).pack()

    available_listbox = tk.Listbox(left_frame, height=8, selectmode=tk.SINGLE, font=('Arial', 10))
    available_listbox.pack(fill='both', expand=True, pady=5)

    # Get saved display selection
    saved_displays = config.get('displays', [1, 2])

    # Populate available displays (initially all displays except saved ones)
    for screen in available_screens:
        screen_name = screen.get('name', f"Display {screen['index']}")
        if screen['index'] not in saved_displays:
            available_listbox.insert(tk.END, screen_name)

    # Right side: Selected displays
    right_frame = ttk.Frame(lists_frame)
    right_frame.pack(side='left', fill='both', expand=True, padx=5)

    ttk.Label(right_frame, text="Selected Displays:", font=('Arial', 10, 'bold')).pack()
    ttk.Label(right_frame, text="(in order)", foreground='gray', font=('Arial', 8)).pack()

    selected_listbox = tk.Listbox(right_frame, height=8, selectmode=tk.SINGLE, font=('Arial', 10))
    selected_listbox.pack(fill='both', expand=True, pady=5)

    # Pre-populate with saved displays (in order)
    for display_num in saved_displays:
        for screen in available_screens:
            if screen['index'] == display_num:
                selected_listbox.insert(tk.END, screen.get('name', f'Display {display_num}'))
                break

    # Helper function to get display number from name
    def get_display_number(display_name):
        for screen in available_screens:
            if screen.get('name', f"Display {screen['index']}") == display_name:
                return screen['index']
        # Fallback: extract number from name
        import re
        match = re.search(r'\d+', display_name)
        return int(match.group()) if match else 1

    # Helper function to show preview window
    def show_preview(display_name):
        display_num = get_display_number(display_name)

        # Don't create duplicate previews
        if display_num in preview_windows:
            return

        # Find the actual screen info for this display
        screen_info = None
        for screen in available_screens:
            if screen['index'] == display_num:
                screen_info = screen
                break

        if not screen_info:
            return  # Can't show preview if we don't know where the screen is

        # Create a preview window
        preview = tk.Toplevel(root)
        preview.title(f"{screen_info['name']}")
        preview.attributes('-alpha', 0.7)  # Semi-transparent
        preview.attributes('-topmost', True)  # Always on top

        # Create colored label with screen name
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        color = colors[(display_num - 1) % len(colors)]

        text = f"DISPLAY {display_num}\n{screen_info['name']}\n{screen_info['width']}x{screen_info['height']}"
        label = tk.Label(preview, text=text, font=('Arial', 24, 'bold'),
                        bg=color, fg='white')
        label.pack(fill='both', expand=True)

        # Position on the ACTUAL screen using real coordinates
        preview_width = 500
        preview_height = 350

        # Center the preview on the target screen
        x = screen_info['x'] + (screen_info['width'] - preview_width) // 2
        y = screen_info['y'] + (screen_info['height'] - preview_height) // 2

        preview.geometry(f"{preview_width}x{preview_height}+{x}+{y}")

        preview_windows[display_num] = preview

    # Helper function to hide preview window
    def hide_preview(display_name):
        display_num = get_display_number(display_name)
        if display_num in preview_windows:
            preview_windows[display_num].destroy()
            del preview_windows[display_num]

    # Helper function to cleanup all previews
    def cleanup_previews():
        for preview in list(preview_windows.values()):
            preview.destroy()
        preview_windows.clear()

    # Hover handlers for available list
    def on_available_hover(event):
        index = available_listbox.nearest(event.y)
        if index >= 0 and index < available_listbox.size():
            display_name = available_listbox.get(index)
            show_preview(display_name)

    def on_available_leave(event):
        cleanup_previews()

    # Hover handlers for selected list
    def on_selected_hover(event):
        index = selected_listbox.nearest(event.y)
        if index >= 0 and index < selected_listbox.size():
            display_name = selected_listbox.get(index)
            show_preview(display_name)

    def on_selected_leave(event):
        cleanup_previews()

    # Bind hover events
    available_listbox.bind('<Motion>', on_available_hover)
    available_listbox.bind('<Leave>', on_available_leave)
    selected_listbox.bind('<Motion>', on_selected_hover)
    selected_listbox.bind('<Leave>', on_selected_leave)

    # Double-click to move from available to selected
    def move_to_selected(event):
        cleanup_previews()
        selection = available_listbox.curselection()
        if selection:
            index = selection[0]
            display_name = available_listbox.get(index)
            selected_listbox.insert(tk.END, display_name)
            available_listbox.delete(index)

    # Double-click to move from selected to available
    def move_to_available(event):
        cleanup_previews()
        selection = selected_listbox.curselection()
        if selection:
            index = selection[0]
            display_name = selected_listbox.get(index)
            available_listbox.insert(tk.END, display_name)
            selected_listbox.delete(index)

    available_listbox.bind('<Double-Button-1>', move_to_selected)
    selected_listbox.bind('<Double-Button-1>', move_to_available)

    ttk.Label(page2, text="Double-click to move displays between lists\nOrder in 'Selected' determines floor assignment",
              foreground='gray', justify='center').pack(pady=5)

    # ===== PAGE 3: Controls =====
    page3 = ttk.Frame(notebook)
    notebook.add(page3, text="3. Controls")

    ttk.Label(page3, text="Input Methods", font=('Arial', 14, 'bold')).pack(pady=10)
    ttk.Label(page3, text="Select which control methods to enable (at least one):").pack(pady=5)
    ttk.Label(page3, text="Mouse wheel volume control is always available.", foreground='gray', font=('Arial', 9)).pack(pady=(0, 10))

    # Checkbox variables - initialize from saved settings
    keyboard_var = tk.BooleanVar(value=config.get('enable_keyboard', True))
    python_terminal_var = tk.BooleanVar(value=config.get('enable_python_terminal', True))
    external_osc_var = tk.BooleanVar(value=config.get('enable_osc_external', True))

    # Keyboard control checkbox
    ttk.Checkbutton(page3, text="Keyboard Control (in Processing)",
                    variable=keyboard_var).pack(anchor='w', padx=40, pady=5)
    ttk.Label(page3, text="    • Press 1-9 to jump to scenes\n    • Up/Down arrows for next/previous scene",
              foreground='gray', justify='left').pack(anchor='w', padx=60)

    # Python terminal checkbox
    ttk.Checkbutton(page3, text="Python Terminal",
                    variable=python_terminal_var).pack(anchor='w', padx=40, pady=(10, 5))
    ttk.Label(page3, text="    • Type scene numbers in terminal\n    • For manual control during testing",
              foreground='gray', justify='left').pack(anchor='w', padx=60)

    # External OSC checkbox (Arduino)
    ttk.Checkbutton(page3, text="External OSC (Arduino Elevator Controller)",
                    variable=external_osc_var).pack(anchor='w', padx=40, pady=(10, 5))
    ttk.Label(page3, text="    • Receive OSC messages from Arduino\n    • Python script brokers messages to/from Processing",
              foreground='gray', justify='left').pack(anchor='w', padx=60)

    if not OSC_AVAILABLE:
        ttk.Label(page3, text="\n⚠ Python terminal and external OSC require 'python-osc'\nInstall with: pip install python-osc",
                  foreground='orange').pack(pady=10)

    # ===== PAGE 4: Arduino Port Selection =====
    page4 = ttk.Frame(notebook)
    notebook.add(page4, text="4. Arduino")

    ttk.Label(page4, text="Arduino Elevator Control", font=('Arial', 14, 'bold')).pack(pady=10)
    ttk.Label(page4, text="Select the USB port for your Arduino (if connected):").pack(pady=5)

    # Arduino port selection variable
    saved_arduino_port = config.get('arduino_port', 'auto')
    arduino_port_var = tk.StringVar(value=saved_arduino_port)
    arduino_custom_port = tk.StringVar(value="" if saved_arduino_port == "auto" else saved_arduino_port)

    # Auto-detect option
    ttk.Radiobutton(page4, text="Auto-detect Arduino (recommended)",
                    variable=arduino_port_var, value="auto").pack(anchor='w', padx=40, pady=5)
    ttk.Label(page4, text="    Automatically finds Adafruit/Arduino boards",
              foreground='gray').pack(anchor='w', padx=60)

    # Available ports list
    ttk.Label(page4, text="\nAvailable Serial Ports:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=40, pady=(15, 5))

    ports_frame = ttk.Frame(page4)
    ports_frame.pack(padx=40, pady=5, fill='x')

    # Listbox for ports
    ports_listbox_frame = ttk.Frame(ports_frame)
    ports_listbox_frame.pack(side='left', fill='both', expand=True)

    ports_listbox = tk.Listbox(ports_listbox_frame, height=6, font=('Courier', 12))
    ports_listbox.pack(side='left', fill='both', expand=True)

    ports_scrollbar = ttk.Scrollbar(ports_listbox_frame, orient='vertical', command=ports_listbox.yview)
    ports_scrollbar.pack(side='right', fill='y')
    ports_listbox.configure(yscrollcommand=ports_scrollbar.set)

    # Refresh button
    def refresh_ports():
        ports_listbox.delete(0, tk.END)
        if SERIAL_AVAILABLE:
            try:
                import serial.tools.list_ports
                ports = list(serial.tools.list_ports.comports())
                if ports:
                    for port in ports:
                        # Mark Arduino boards (including Nano with CH340/FTDI chips)
                        desc_lower = port.description.lower()
                        is_arduino = any(keyword in desc_lower for keyword in ['arduino', 'adafruit', 'ch340', 'ch341', 'ftdi', 'nano'])
                        marker = " ⭐" if is_arduino else ""
                        ports_listbox.insert(tk.END, f"{port.device}{marker}: {port.description}")
                else:
                    ports_listbox.insert(tk.END, "No serial ports found")
            except Exception as e:
                ports_listbox.insert(tk.END, f"Error: {e}")
        else:
            ports_listbox.insert(tk.END, "pyserial not installed")
            ports_listbox.insert(tk.END, "Install with: pip install pyserial")

    def on_port_select(event):
        selection = ports_listbox.curselection()
        if selection:
            selected_text = ports_listbox.get(selection[0])
            # Extract port name (everything before the colon)
            port_name = selected_text.split(':')[0].replace(" ⭐", "").strip()
            arduino_port_var.set("custom")
            arduino_custom_port.set(port_name)

    ports_listbox.bind('<<ListboxSelect>>', on_port_select)

    refresh_button = ttk.Button(ports_frame, text="🔄 Refresh", command=refresh_ports)
    refresh_button.pack(side='left', padx=(10, 0))

    # Initial port list
    refresh_ports()

    # Manual entry option
    ttk.Label(page4, text="\nOr enter manually:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=40, pady=(15, 5))
    custom_port_frame = ttk.Frame(page4)
    custom_port_frame.pack(anchor='w', padx=40, pady=5)
    ttk.Radiobutton(custom_port_frame, text="Custom port:",
                    variable=arduino_port_var, value="custom").pack(side='left')
    ttk.Entry(custom_port_frame, textvariable=arduino_custom_port, width=30).pack(side='left', padx=5)
    ttk.Label(page4, text="    Example: /dev/cu.usbmodem14201 (macOS) or COM3 (Windows)",
              foreground='gray').pack(anchor='w', padx=60)

    if not SERIAL_AVAILABLE:
        ttk.Label(page4, text="\n⚠ Arduino control requires 'pyserial'\nInstall with: pip install pyserial",
                  foreground='orange').pack(pady=10)

    # ===== PAGE 5: Summary =====
    page5 = ttk.Frame(notebook)
    notebook.add(page5, text="5. Review")

    ttk.Label(page5, text="Configuration Summary", font=('Arial', 14, 'bold')).pack(pady=10)
    summary_text = tk.Text(page5, height=15, width=60, wrap='word', font=('Courier', 10))
    summary_text.pack(pady=10, padx=20)

    def update_summary():
        summary_text.delete('1.0', 'end')
        summary_text.config(state='normal')

        # Audio
        audio = audio_var.get()
        if audio == "custom":
            audio = audio_custom.get() or "Default"
        elif audio == "default":
            audio = "Automatic"
        summary_text.insert('end', f"Audio Output:\n  {audio}\n\n")

        # Displays - read from selected listbox
        selected_displays = []
        for i in range(selected_listbox.size()):
            display_name = selected_listbox.get(i)
            display_num = get_display_number(display_name)
            selected_displays.append(display_num)

        if selected_displays:
            disp_list = ", ".join(str(d) for d in selected_displays)
            summary_text.insert('end', f"Display(s):\n  {disp_list}\n")
            summary_text.insert('end', f"  ({len(selected_displays)} display{'s' if len(selected_displays) != 1 else ''})\n\n")
        else:
            summary_text.insert('end', f"Display(s):\n  None selected!\n\n")

        # Control methods (checkboxes)
        control_methods = []
        if keyboard_var.get():
            control_methods.append("Keyboard (Processing)")
        if python_terminal_var.get():
            control_methods.append("Python Terminal")
        if external_osc_var.get():
            control_methods.append("External OSC (Arduino)")

        if control_methods:
            control_desc = "\n  ".join(control_methods)
            summary_text.insert('end', f"Input Methods:\n  {control_desc}\n")
            summary_text.insert('end', f"  + Mouse wheel (volume, always on)\n\n")
        else:
            summary_text.insert('end', f"Input Methods:\n  NONE SELECTED!\n\n")

        # Arduino port
        if external_osc_var.get():
            arduino_port = arduino_port_var.get()
            if arduino_port == "auto":
                summary_text.insert('end', f"Arduino Port:\n  Auto-detect\n\n")
            else:
                port_value = arduino_custom_port.get() or "Not specified"
                summary_text.insert('end', f"Arduino Port:\n  {port_value}\n\n")

        summary_text.insert('end', "═" * 50 + "\n\n")
        summary_text.insert('end', "Click 'Start' to launch Carpet Hotel\nwith these settings.")
        summary_text.config(state='disabled')

    def on_page_changed(event):
        if notebook.index(notebook.select()) == 4:  # Summary page (now page 5, index 4)
            update_summary()

    notebook.bind('<<NotebookTabChanged>>', on_page_changed)

    # ===== Status Label =====
    status_frame = ttk.Frame(root)
    status_frame.pack(fill='x', padx=10, pady=(0, 5))
    status_label = ttk.Label(status_frame, text="Ready to start", font=('Arial', 9), foreground='gray')
    status_label.pack()

    # ===== Bottom Buttons =====
    button_frame = ttk.Frame(root)
    button_frame.pack(fill='x', padx=10, pady=10)

    # Create button references that we'll update dynamically
    cancel_button = ttk.Button(button_frame, text="Quit")
    back_button = ttk.Button(button_frame, text="◀ Back", command=lambda: notebook.select(max(0, notebook.index(notebook.select()) - 1)))
    next_button = ttk.Button(button_frame, text="Next ▶", command=lambda: notebook.select(min(4, notebook.index(notebook.select()) + 1)))
    start_button = ttk.Button(button_frame, text="Start")
    stop_button = ttk.Button(button_frame, text="Stop")
    pause_button = ttk.Button(button_frame, text="Pause")

    def update_button_state():
        """Update button visibility and commands based on running state."""
        # Clear all buttons
        for widget in button_frame.winfo_children():
            widget.pack_forget()

        if is_running[0]:
            # Running state: show Stop and Pause/Resume
            stop_button.pack(side='right', padx=5)
            if is_paused[0]:
                pause_button.config(text="Resume", command=on_resume)
            else:
                pause_button.config(text="Pause", command=on_pause)
            pause_button.pack(side='right')
        else:
            # Initial state: show Cancel, Back, Next, Start
            cancel_button.pack(side='left')
            back_button.pack(side='left', padx=5)
            next_button.pack(side='left')
            start_button.pack(side='right')

    def disable_config_ui():
        """Disable configuration UI while running."""
        notebook.tab(0, state='disabled')
        notebook.tab(1, state='disabled')
        notebook.tab(2, state='disabled')

    def enable_config_ui():
        """Enable configuration UI when stopped."""
        notebook.tab(0, state='normal')
        notebook.tab(1, state='normal')
        notebook.tab(2, state='normal')

    def run_launcher_thread():
        """Run launcher in background thread."""
        try:
            launcher = launcher_instance[0]
            if launcher:
                # Start the launcher (non-blocking)
                success = launcher.start()
                if not success:
                    def on_failure():
                        status_label.config(text="Failed to start", foreground='red')
                        is_running[0] = False
                        enable_config_ui()
                        update_button_state()
                    root.after(0, on_failure)
                else:
                    # Monitor Processing in background
                    while is_running[0]:
                        if launcher.processing_process and launcher.processing_process.poll() is not None:
                            print("\n⚠ Processing has exited - stopping...")
                            root.after(0, on_stop)
                            break
                        time.sleep(0.5)
        except Exception as e:
            print(f"Error in launcher thread: {e}")
            import traceback
            traceback.print_exc()
            def on_error():
                status_label.config(text=f"Error: {e}", foreground='red')
                is_running[0] = False
                enable_config_ui()
                update_button_state()
            root.after(0, on_error)

    def on_quit():
        """Quit the application."""
        if is_running[0]:
            if messagebox.askokcancel("Quit", "Stop Carpet Hotel and quit?"):
                cleanup_previews()
                if launcher_instance[0]:
                    launcher_instance[0].stop()
                root.destroy()
        else:
            if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
                cleanup_previews()
                root.destroy()

    def on_start():
        """Start Carpet Hotel in background thread."""
        # Cleanup preview windows
        cleanup_previews()

        # Validate and save configuration

        # Audio
        audio = audio_var.get()
        if audio == "custom":
            config['audio_device'] = audio_custom.get().strip() or None
        elif audio == "default":
            config['audio_device'] = None
        else:
            config['audio_device'] = audio

        # Displays - read from selected listbox
        selected_displays = []
        for i in range(selected_listbox.size()):
            display_name = selected_listbox.get(i)
            display_num = get_display_number(display_name)
            selected_displays.append(display_num)

        if not selected_displays:
            messagebox.showerror("No Displays Selected", "Please select at least one display.")
            return

        config['displays'] = selected_displays

        # Input methods (checkboxes)
        config['enable_keyboard'] = keyboard_var.get()
        config['enable_python_terminal'] = python_terminal_var.get()
        config['enable_osc_external'] = external_osc_var.get()

        # Arduino port
        arduino_port = arduino_port_var.get()
        if arduino_port == "custom":
            arduino_port = arduino_custom_port.get() or "auto"
        config['arduino_port'] = arduino_port

        # Validate: at least one control method must be enabled
        if not (config['enable_keyboard'] or config['enable_python_terminal'] or config['enable_osc_external']):
            messagebox.showerror("No Control Methods", "Please enable at least one input method.")
            return

        # Check if OSC is needed but not available
        needs_osc = config['enable_python_terminal'] or config['enable_osc_external']
        if needs_osc and not OSC_AVAILABLE:
            if not messagebox.askyesno("Missing Dependency",
                                        "Python OSC library is not installed.\n\n"
                                        "Python terminal and external OSC will not work.\n\n"
                                        "Continue with keyboard control only?"):
                return

        # Save settings for next time
        save_settings(config)

        # Create launcher instance
        launcher_instance[0] = CarpetHotelLauncher(
            audio_device=config['audio_device'],
            enable_keyboard=config['enable_keyboard'],
            enable_python_terminal=config['enable_python_terminal'],
            enable_osc_external=config['enable_osc_external'],
            displays=config['displays'],
            arduino_port=config.get('arduino_port', 'auto')
        )

        # Update state
        is_running[0] = True
        is_paused[0] = False
        status_label.config(text="Starting Carpet Hotel...", foreground='blue')
        disable_config_ui()
        update_button_state()

        # Start launcher in background thread
        launcher_thread[0] = threading.Thread(target=run_launcher_thread, daemon=True)
        launcher_thread[0].start()

        # Update status after a moment
        root.after(2000, lambda: status_label.config(text="Running", foreground='green'))

    def on_stop():
        """Stop Carpet Hotel but keep GUI open."""
        status_label.config(text="Stopping...", foreground='orange')
        if launcher_instance[0]:
            launcher_instance[0].stop()
        is_running[0] = False
        is_paused[0] = False
        launcher_instance[0] = None
        enable_config_ui()
        update_button_state()
        status_label.config(text="Stopped - Ready to start", foreground='gray')

    def on_pause():
        """Pause Carpet Hotel."""
        status_label.config(text="Pausing...", foreground='orange')
        if launcher_instance[0]:
            launcher_instance[0].pause()
        is_paused[0] = True
        update_button_state()
        status_label.config(text="Paused", foreground='orange')

    def on_resume():
        """Resume Carpet Hotel."""
        status_label.config(text="Resuming...", foreground='blue')
        if launcher_instance[0]:
            launcher_instance[0].resume()
        is_paused[0] = False
        update_button_state()
        status_label.config(text="Running", foreground='green')

    # Set button commands
    cancel_button.config(command=on_quit)
    start_button.config(command=on_start)
    stop_button.config(command=on_stop)

    # Initialize button state
    update_button_state()

    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")

    # Handle window close button
    def on_window_close():
        if is_running[0]:
            if messagebox.askokcancel("Quit", "Stop Carpet Hotel and quit?"):
                cleanup_previews()
                if launcher_instance[0]:
                    launcher_instance[0].stop()
                root.destroy()
        else:
            cleanup_previews()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_window_close)

    # Run main loop - this keeps the GUI open permanently
    root.mainloop()

    # When GUI closes, we're done
    # The GUI doesn't return anything anymore - it's persistent

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

    # GUI mode - run persistent control panel if no config args provided and not building
    if not has_config_args and not args.build and not args.sc_only:
        # Run the persistent GUI - it handles everything internally
        guided_setup_gui()
        # When GUI closes, we're done
        sys.exit(0)
    else:
        # Use command line arguments (legacy support for old flags)
        audio_device = args.audio_device
        # Map old flags to new structure
        enable_keyboard = args.test_mode
        enable_python_terminal = args.osc_control
        enable_osc_external = args.osc_control  # External OSC shares the same flag
        displays = None
        if args.displays:
            displays = [int(d.strip()) for d in args.displays.split(',')]

        launcher = CarpetHotelLauncher(
            audio_device=audio_device,
            enable_keyboard=enable_keyboard,
            enable_python_terminal=enable_python_terminal,
            enable_osc_external=enable_osc_external,
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
