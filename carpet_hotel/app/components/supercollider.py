#!/usr/bin/env python3
"""
Carpet Hotel SuperCollider Module
==================================

Manages SuperCollider audio engine for Carpet Hotel.

Features:
- Launches sclang with carpet_hotel_sound.scd script
- Monitors OSC initialization messages
- Detects audio devices and sample rates
- Manages audio engine lifecycle
"""

import subprocess
import time
from typing import Optional, List
from pathlib import Path

from components.utils.utils import find_sclang, ProcessWrapper, get_app_dir, detect_audio_devices, detect_sample_rates


class CarpetHotelSuperCollider:
    """
    SuperCollider audio engine manager.

    Uses system default audio device - user should set this via macOS System Settings
    before running. See AUDIO_SETUP.md for configuration instructions.
    """

    def __init__(self):
        """
        Initialize SuperCollider manager.

        Audio device and sample rate are determined by macOS system defaults.
        """
        self.sclang_path = find_sclang()
        self.sc_script = get_app_dir() / "carpet_hotel_sound.scd"

        # ProcessWrapper with sclang pattern for forceful cleanup
        self.process = ProcessWrapper("SuperCollider", process_name_pattern="sclang")
        self.initialized = False

    def start(self, output_bus: int = 0) -> bool:
        """
        Start SuperCollider audio engine.

        Args:
            output_bus: Audio output bus offset (default: 0)

        Returns:
            True if started successfully
        """
        if not self.sclang_path:
            print("✗ sclang not found. Please install SuperCollider.")
            return False

        if not self.sc_script.exists():
            print(f"✗ SuperCollider script not found: {self.sc_script}")
            return False

        print(f"Starting SuperCollider...")
        print(f"  Using system default audio device")
        print(f"  Output bus offset: {output_bus}")

        # Build command with script path and bus argument
        # Pass bus as command-line argument so thisProcess.argv can access it
        cmd = [self.sclang_path, str(self.sc_script), str(output_bus)]

        # Start process - script will be loaded automatically with bus argument
        if not self.process.start(cmd):
            return False

        print(f"  ✓ SuperCollider script loading with bus argument")

        # Wait for initialization
        if not self.wait_for_init():
            print("✗ SuperCollider failed to initialize")
            self.stop()
            return False

        self.initialized = True
        print("✓ SuperCollider audio engine ready")
        return True

    def wait_for_compile(self, timeout: float = 15.0) -> bool:
        """
        Wait for SuperCollider class library to compile.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if compiled successfully
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self.process.is_alive():
                print("✗ SuperCollider process died during compilation")
                return False

            # Read output
            line = self.process.read_output(timeout=0.1)
            if line:
                # Don't print all compilation lines (too verbose)
                # Only print important messages
                if "compile done" in line.lower():
                    print("✓ Class library compiled")
                    # Wait a bit more for "Welcome to SuperCollider" message
                    time.sleep(0.5)
                    return True
                elif "error" in line.lower() and "class extension" not in line.lower():
                    # Print actual errors (but not class extension warnings)
                    print(f"  [SC] {line}")

            time.sleep(0.1)

        print("✗ Timeout waiting for class library compilation")
        return False

    def wait_for_init(self, timeout: float = 45.0) -> bool:
        """
        Wait for SuperCollider to initialize.
        This includes compilation time + script execution time.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if initialized successfully
        """
        print("Waiting for SuperCollider to initialize...")
        start_time = time.time()
        compile_done = False
        last_message = None
        repeat_count = 0

        # Use direct readline instead of select-based read_output
        # This ensures we don't miss any output
        if not self.process.process or not self.process.process.stdout:
            print("✗ No stdout available")
            return False

        while time.time() - start_time < timeout:
            if not self.process.is_alive():
                if repeat_count > 0:
                    print()  # New line after repeated message
                print("✗ SuperCollider process died")
                return False

            # Direct blocking readline with short timeout using select
            import select
            import sys
            try:
                ready, _, _ = select.select([self.process.process.stdout], [], [], 0.1)
                if not ready:
                    continue

                line = self.process.process.stdout.readline()
                if not line:
                    continue

                line = line.rstrip()

                # Determine what to print
                should_print = False
                message = None

                if not compile_done:
                    # During compilation, only print key messages
                    if "compile done" in line.lower():
                        message = "  ✓ Class library compiled"
                        should_print = True
                        compile_done = True
                    elif "error" in line.lower() and "class extension" not in line.lower():
                        message = f"  [SC] {line}"
                        should_print = True
                else:
                    # After compilation, print everything
                    message = f"  [SC] {line}"
                    should_print = True

                # Handle duplicate detection
                if should_print and message:
                    if message == last_message:
                        # Same message - increment counter and update line
                        repeat_count += 1
                        sys.stdout.write(f"\r{message} (x{repeat_count + 1})")
                        sys.stdout.flush()
                    else:
                        # Different message - print new line
                        if repeat_count > 0:
                            print()  # Finish the previous line
                        print(message)
                        last_message = message
                        repeat_count = 0

                # Check for initialization signals
                # Script prints "Audio server ready!" after successful boot
                # Also check for "Loading audio files..." which comes right after
                if "Audio server ready!" in line or "Loading audio files" in line:
                    if repeat_count > 0:
                        print()  # New line after repeated message
                    return True

            except Exception as e:
                if repeat_count > 0:
                    print()  # New line after repeated message
                print(f"  Warning: Error reading output: {e}")
                time.sleep(0.1)
                repeat_count = 0
                last_message = None

        if repeat_count > 0:
            print()  # New line after repeated message
        return False

    def stop(self) -> bool:
        """
        Stop SuperCollider audio engine.

        Returns:
            True if stopped successfully
        """
        print("[SuperCollider] Stopping...")
        self.initialized = False

        # Send Cmd+. (stop all sound) and quit to sclang via stdin
        if self.process.process and self.process.process.stdin:
            try:
                # Send the equivalent of Cmd+. in SuperCollider to stop synths
                self.process.process.stdin.write("CmdPeriod.run;\n")
                self.process.process.stdin.flush()
                time.sleep(0.2)

                # Send quit command
                self.process.process.stdin.write("0.exit;\n")
                self.process.process.stdin.flush()
                print("[SuperCollider] Sent stop and quit commands")
                time.sleep(0.3)

                # Close stdin to prevent further input
                self.process.process.stdin.close()
            except Exception as e:
                print(f"[SuperCollider] Could not send commands: {e}")

        # Stop the process (will use pkill as fallback)
        result = self.process.stop()

        # Extra aggressive cleanup - kill BOTH sclang and scsynth
        import subprocess
        for process_name in ["sclang", "scsynth"]:
            try:
                # Use killall which is more reliable than pkill for exact names
                subprocess.run(["killall", "-9", process_name],
                             capture_output=True, timeout=2)
                print(f"[SuperCollider] Sent kill signal to all {process_name} processes")
            except Exception as e:
                pass  # Process might not exist, which is fine

        # Verify processes are actually dead
        time.sleep(0.5)
        still_running = []
        for process_name in ["sclang", "scsynth"]:
            try:
                result = subprocess.run(["pgrep", process_name],
                                      capture_output=True, timeout=1)
                if result.returncode == 0:  # Process found
                    still_running.append(process_name)
            except:
                pass

        if still_running:
            print(f"⚠ Warning: {', '.join(still_running)} still running after kill attempts")
            # One final nuclear option
            for process_name in still_running:
                try:
                    subprocess.run(["pkill", "-9", "-f", process_name],
                                 capture_output=True, timeout=2)
                except:
                    pass
        else:
            print("✓ SuperCollider fully stopped (verified)")

        return True

    def is_running(self) -> bool:
        """
        Check if SuperCollider is running.

        Returns:
            True if running
        """
        return self.process.is_alive()

    @staticmethod
    def detect_devices() -> List[str]:
        """
        Detect available audio devices.

        Returns:
            List of device names
        """
        return detect_audio_devices()

    @staticmethod
    def detect_sample_rates() -> List[int]:
        """
        Get available sample rates.

        Returns:
            List of sample rates
        """
        return detect_sample_rates()


def main():
    """Standalone mode - test SuperCollider."""
    print("Carpet Hotel SuperCollider Audio Engine")
    print("=" * 50)
    print("\nUsing system default audio device.")
    print("Set your audio device via macOS System Settings.")
    print("See AUDIO_SETUP.md for configuration help.\n")

    sc = CarpetHotelSuperCollider()

    if sc.start():
        print("\nSuperCollider running. Press Ctrl+C to stop...")
        try:
            while sc.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            sc.stop()
    else:
        print("✗ Failed to start SuperCollider")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
