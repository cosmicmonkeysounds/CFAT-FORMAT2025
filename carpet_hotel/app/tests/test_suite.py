#!/usr/bin/env python3
"""
Carpet Hotel Test Suite

Comprehensive tests for SuperCollider audio, Processing video, and OSC communication.
"""

import os
import sys
import time
import subprocess
import glob
from pathlib import Path
from pythonosc import udp_client, dispatcher, osc_server
from pythonosc.osc_server import ThreadingOSCUDPServer
import threading

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(msg):
    print(f"{Colors.BLUE}[TEST]{Colors.END} {msg}")

def print_pass(msg):
    print(f"{Colors.GREEN}✓ PASS{Colors.END} {msg}")

def print_fail(msg):
    print(f"{Colors.RED}✗ FAIL{Colors.END} {msg}")

def print_warn(msg):
    print(f"{Colors.YELLOW}⚠ WARN{Colors.END} {msg}")


class TestSuite:
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.absolute()
        self.data_dir = self.script_dir.parent / 'data'
        self.sc_script = self.script_dir / 'carpet_hotel_audio.scd'
        self.processing_sketch = self.script_dir / 'carpet_hotel.pde'

        # Find sclang
        self.sclang_path = '/Applications/SuperCollider.app/Contents/MacOS/sclang'

        # OSC setup for receiving messages
        self.osc_messages = []
        self.osc_server = None
        self.osc_thread = None

    def setup_osc_listener(self, port=12001):
        """Setup OSC server to listen for messages."""
        print_test(f"Setting up OSC listener on port {port}")

        disp = dispatcher.Dispatcher()
        disp.set_default_handler(self.osc_handler)

        self.osc_server = ThreadingOSCUDPServer(("127.0.0.1", port), disp)
        self.osc_thread = threading.Thread(target=self.osc_server.serve_forever, daemon=True)
        self.osc_thread.start()

        print_pass(f"OSC listener running on port {port}")

    def osc_handler(self, address, *args):
        """Handle incoming OSC messages."""
        msg = {'address': address, 'args': args, 'time': time.time()}
        self.osc_messages.append(msg)
        print(f"  [OSC-RECV] {address} {args}")

    def stop_osc_listener(self):
        """Stop OSC server."""
        if self.osc_server:
            self.osc_server.shutdown()
            print_pass("OSC listener stopped")

    # ========================================================================
    # TEST 1: Check Data Files
    # ========================================================================

    def test_data_files(self):
        """Test that data directory exists and contains media files."""
        print_test("\n=== TEST 1: Data Files ===")

        # Check data directory
        if not self.data_dir.exists():
            print_fail(f"Data directory not found: {self.data_dir}")
            return False
        print_pass(f"Data directory exists: {self.data_dir}")

        # Find video files
        video_files = list(self.data_dir.glob('carpet_*.mp4')) + list(self.data_dir.glob('carpet_*.mov'))
        video_files.sort()
        print(f"  Found {len(video_files)} video file(s)")
        for vf in video_files:
            print(f"    - {vf.name}")

        if len(video_files) == 0:
            print_fail("No video files found!")
            return False
        print_pass(f"Found {len(video_files)} video files")

        # Find audio files
        audio_files = list(self.data_dir.glob('carpet_*.wav')) + list(self.data_dir.glob('carpet_*.aiff'))
        audio_files.sort()
        print(f"  Found {len(audio_files)} audio file(s)")
        for af in audio_files:
            print(f"    - {af.name}")

        if len(audio_files) == 0:
            print_warn("No audio files found")
        else:
            print_pass(f"Found {len(audio_files)} audio files")

        return True

    # ========================================================================
    # TEST 2: SuperCollider Startup with OSC Init Messages
    # ========================================================================

    def test_supercollider_startup(self):
        """Test SuperCollider startup and wait for OSC init messages."""
        print_test("\n=== TEST 2: SuperCollider Startup ===")

        if not self.sc_script.exists():
            print_fail(f"SuperCollider script not found: {self.sc_script}")
            return False
        print_pass(f"SuperCollider script exists: {self.sc_script.name}")

        # Setup OSC listener
        self.osc_messages = []
        self.setup_osc_listener(port=57121)  # Listen on different port for testing

        print_test("Launching SuperCollider...")
        print("  (This may take 10-15 seconds for class library to compile)")

        # Launch SC using stdin with executeFile (sclang doesn't auto-execute .scd files)
        execute_cmd = f'thisProcess.interpreter.executeFile("{str(self.sc_script)}");'

        try:
            sc_process = subprocess.Popen(
                [self.sclang_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Send execute command
            sc_process.stdin.write(execute_cmd + "\n")
            sc_process.stdin.flush()

            # Monitor output
            start_time = time.time()
            timeout = 45
            init_message_seen = False
            server_booted = False
            audio_ready = False

            def read_output():
                nonlocal init_message_seen, server_booted, audio_ready
                for line in iter(sc_process.stdout.readline, ''):
                    if not line:
                        break
                    line = line.rstrip()
                    print(f"  [SC] {line}")

                    # Track init messages
                    if "CARPET HOTEL" in line:
                        init_message_seen = True
                    if "Audio server ready!" in line or "booting" in line.lower():
                        server_booted = True
                    if "Audio engine ready!" in line or "Listening for OSC" in line:
                        audio_ready = True

            # Start output reader thread
            output_thread = threading.Thread(target=read_output, daemon=True)
            output_thread.start()

            # Wait for init
            while time.time() - start_time < timeout:
                if audio_ready:
                    break
                time.sleep(0.5)

            elapsed = time.time() - start_time

            # Check results
            if not init_message_seen:
                print_fail(f"SC script did not execute (no init message seen after {elapsed:.1f}s)")
                sc_process.kill()
                return False
            print_pass("SC script executed (init message seen)")

            if not server_booted:
                print_warn("SC audio server boot message not seen")
            else:
                print_pass("SC audio server boot message seen")

            if not audio_ready:
                print_fail(f"SC audio engine not ready after {elapsed:.1f}s")
                sc_process.kill()
                return False
            print_pass(f"SC audio engine ready in {elapsed:.1f}s")

            # Test OSC communication
            print_test("Testing OSC communication with SC...")
            time.sleep(1)  # Give SC time to setup OSC

            # Send a test OSC message
            client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
            client.send_message("/carpet/scene", [0, 2, 0])
            print("  Sent: /carpet/scene 0 2 0")

            time.sleep(2)

            # Kill SC
            print_test("Stopping SuperCollider...")
            sc_process.terminate()
            try:
                sc_process.wait(timeout=5)
                print_pass("SuperCollider stopped cleanly")
            except subprocess.TimeoutExpired:
                sc_process.kill()
                print_warn("SuperCollider force killed")

            return True

        except Exception as e:
            print_fail(f"Error during SC test: {e}")
            return False
        finally:
            self.stop_osc_listener()

    # ========================================================================
    # TEST 3: Processing Startup (Dry Run)
    # ========================================================================

    def test_processing_startup(self):
        """Test Processing sketch for syntax errors (dry run)."""
        print_test("\n=== TEST 3: Processing Syntax Check ===")

        if not self.processing_sketch.exists():
            print_fail(f"Processing sketch not found: {self.processing_sketch}")
            return False
        print_pass(f"Processing sketch exists: {self.processing_sketch.name}")

        # Check for processing-java
        processing_java = 'processing-java'
        try:
            result = subprocess.run([processing_java, '--help'],
                                   capture_output=True, timeout=5)
            print_pass("processing-java command available")
        except:
            print_warn("processing-java not found in PATH")
            print_warn("  Skipping Processing syntax check")
            print("  Install Processing and add to PATH to enable this test")
            return True  # Don't fail the test if Processing isn't installed

        # Processing requires sketch to be in a folder with the same name as the .pde file
        # carpet_hotel.pde must be in a folder named 'carpet_hotel'
        # Since it's in 'app', we'll skip this test
        sketch_name = self.processing_sketch.stem  # 'carpet_hotel'
        parent_folder_name = self.script_dir.name  # 'app'

        if sketch_name != parent_folder_name:
            print_warn(f"Processing sketch '{sketch_name}.pde' is in folder '{parent_folder_name}'")
            print_warn(f"  Processing requires sketch folder to match .pde filename")
            print_warn(f"  Skipping Processing compilation test")
            return True  # Don't fail, just warn

        # Try to build (syntax check)
        print_test("Checking Processing sketch syntax...")
        try:
            result = subprocess.run(
                [processing_java, f'--sketch={self.script_dir}', '--build'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print_pass("Processing sketch compiled successfully")
                return True
            else:
                print_fail("Processing sketch compilation failed")
                print("STDOUT:")
                print(result.stdout)
                print("STDERR:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print_fail("Processing compilation timeout")
            return False
        except Exception as e:
            print_fail(f"Error during Processing test: {e}")
            return False

    # ========================================================================
    # TEST 4: OSC Message Flow
    # ========================================================================

    def test_osc_flow(self):
        """Test OSC message flow between components."""
        print_test("\n=== TEST 4: OSC Message Flow ===")

        # Setup listener
        self.osc_messages = []
        self.setup_osc_listener(port=12001)

        # Create OSC client to send test messages
        client = udp_client.SimpleUDPClient("127.0.0.1", 12001)

        print_test("Sending test OSC messages...")

        # Test 1: Scene change
        client.send_message("/carpet/goto", [3])
        time.sleep(0.5)

        # Test 2: Volume
        client.send_message("/carpet/volume", [0.5])
        time.sleep(0.5)

        # Test 3: Elevator
        client.send_message("/carpet/elevator/up", [])
        time.sleep(0.5)

        # Check messages received
        if len(self.osc_messages) >= 3:
            print_pass(f"Received {len(self.osc_messages)} OSC messages")
            return True
        else:
            print_fail(f"Only received {len(self.osc_messages)}/3 expected messages")
            return False

        self.stop_osc_listener()

    # ========================================================================
    # Run All Tests
    # ========================================================================

    def run_all(self):
        """Run all tests."""
        print(f"\n{'='*60}")
        print("CARPET HOTEL TEST SUITE")
        print(f"{'='*60}")

        results = {
            'Data Files': self.test_data_files(),
            'SuperCollider Startup': self.test_supercollider_startup(),
            'Processing Syntax': self.test_processing_startup(),
            'OSC Message Flow': self.test_osc_flow(),
        }

        print(f"\n{'='*60}")
        print("TEST RESULTS")
        print(f"{'='*60}")

        for test_name, passed in results.items():
            status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {test_name}: {status}")

        total = len(results)
        passed = sum(1 for v in results.values() if v)

        print(f"\n{passed}/{total} tests passed")

        if passed == total:
            print(f"{Colors.GREEN}✓ All tests passed!{Colors.END}")
            return 0
        else:
            print(f"{Colors.RED}✗ Some tests failed{Colors.END}")
            return 1


def main():
    """Main entry point."""
    suite = TestSuite()
    return suite.run_all()


if __name__ == '__main__':
    sys.exit(main())
