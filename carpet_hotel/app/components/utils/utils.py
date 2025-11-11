#!/usr/bin/env python3
"""
Carpet Hotel Utilities
======================

Common functionality for all Carpet Hotel components.
Includes subprocess management, device detection, and OSC utilities.
"""

import subprocess
import platform
import time
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import serial
import serial.tools.list_ports


# ============================================================================
# Path Resolution
# ============================================================================

def get_project_root() -> Path:
    """Get the project root directory (carpets/carpet_hotel/)."""
    # utils.py is in app/components/utils/, so go up 3 levels to project root
    return Path(__file__).parent.parent.parent.parent.absolute()


def get_app_dir() -> Path:
    """Get the app directory (carpets/carpet_hotel/app/)."""
    # utils.py is in app/components/utils/, so go up 2 levels to app/
    return Path(__file__).parent.parent.parent.absolute()


def get_data_dir() -> Path:
    """Get the data directory."""
    return get_project_root() / "data"


def get_config_dir() -> Path:
    """Get the config directory."""
    config_dir = get_app_dir() / "configs"
    config_dir.mkdir(exist_ok=True)
    return config_dir


# ============================================================================
# Display Detection (macOS)
# ============================================================================

def detect_displays() -> List[Dict[str, any]]:
    """
    Detect all connected displays with their properties.

    Returns:
        List of display dictionaries with keys:
        - index: Display index (0, 1, 2, ...)
        - name: Display name
        - resolution: (width, height) tuple
        - main: Boolean - True if main display
    """
    displays = []

    # Try screeninfo first (most reliable)
    try:
        from screeninfo import get_monitors
        monitors = get_monitors()

        for idx, monitor in enumerate(monitors):
            # Use monitor name if available, otherwise generic name
            name = monitor.name if monitor.name else f"Display {idx + 1}"
            if monitor.is_primary:
                name += " [Primary]"

            displays.append({
                "index": idx,
                "name": name,
                "resolution": (monitor.width, monitor.height),
                "main": monitor.is_primary
            })

        if displays:
            return displays

    except ImportError:
        print("Note: screeninfo not installed. Install with: pip install screeninfo")
    except Exception as e:
        print(f"Warning: Could not detect displays via screeninfo: {e}")

    # Fallback to system_profiler on macOS
    if platform.system() == "Darwin":  # macOS
        try:
            # Use system_profiler to get display info
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                # Parse display information
                display_index = 0
                for item in data.get("SPDisplaysDataType", []):
                    for display_key, display_data in item.items():
                        if isinstance(display_data, dict) and "spdisplays_ndrvs" in display_data:
                            for display in display_data["spdisplays_ndrvs"]:
                                name = display.get("_name", f"Display {display_index + 1}")

                                # Get resolution
                                resolution_str = display.get("_spdisplays_resolution", "")
                                width, height = parse_resolution(resolution_str)

                                # Check if main display (first one is usually main)
                                is_main = display_index == 0

                                displays.append({
                                    "index": display_index,
                                    "name": name,
                                    "resolution": (width, height),
                                    "main": is_main
                                })

                                display_index += 1

        except Exception as e:
            print(f"Warning: Could not detect displays via system_profiler: {e}")

    # Fallback: Return at least one default display
    if not displays:
        displays.append({
            "index": 0,
            "name": "Default Display",
            "resolution": (1920, 1080),
            "main": True
        })

    return displays


def parse_resolution(resolution_str: str) -> Tuple[int, int]:
    """Parse resolution string like '1920 x 1080' to (width, height)."""
    try:
        parts = resolution_str.replace("x", " ").split()
        if len(parts) >= 2:
            return (int(parts[0]), int(parts[1]))
    except:
        pass
    return (1920, 1080)  # Default


# ============================================================================
# Audio Device Detection
# ============================================================================

def detect_audio_devices() -> List[str]:
    """
    Detect available audio devices.

    Returns:
        List of audio device names
    """
    devices = []

    if platform.system() == "Darwin":  # macOS
        try:
            # Use system_profiler for audio devices
            result = subprocess.run(
                ["system_profiler", "SPAudioDataType", "-json"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)

                for item in data.get("SPAudioDataType", []):
                    name = item.get("_name", "")
                    if name:
                        devices.append(name)

        except Exception as e:
            print(f"Warning: Could not detect audio devices: {e}")

    # Add default options
    if not devices:
        devices = ["Built-in Output", "Built-in Speakers"]

    return devices


def detect_sample_rates() -> List[int]:
    """
    Get common sample rates for audio.

    Returns:
        List of sample rate options
    """
    return [44100, 48000, 88200, 96000, 176400, 192000]


# ============================================================================
# Serial Port Detection (Arduino)
# ============================================================================

def detect_serial_ports() -> List[Dict[str, str]]:
    """
    Detect available serial ports.

    Returns:
        List of port dictionaries with keys:
        - device: Port device path
        - description: Port description
        - is_arduino: Boolean - True if likely an Arduino
    """
    ports = []

    try:
        for port in serial.tools.list_ports.comports():
            is_arduino = (
                'Adafruit' in port.description or
                'Arduino' in port.description or
                'USB Serial' in port.description
            )

            ports.append({
                "device": port.device,
                "description": port.description,
                "is_arduino": is_arduino
            })

    except Exception as e:
        print(f"Warning: Could not detect serial ports: {e}")

    return ports


def find_arduino_port() -> Optional[str]:
    """
    Find Arduino port automatically.

    Returns:
        Port device path or None if not found
    """
    ports = detect_serial_ports()

    for port in ports:
        if port["is_arduino"]:
            return port["device"]

    return None


# ============================================================================
# Process Management
# ============================================================================

class ProcessWrapper:
    """
    Wrapper for managing external processes with lifecycle tracking.
    """

    def __init__(self, name: str, process_name_pattern: Optional[str] = None):
        """
        Initialize process wrapper.

        Args:
            name: Name of the process (for logging)
            process_name_pattern: Pattern to match process name for cleanup (e.g., "Processing")
        """
        self.name = name
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.process_name_pattern = process_name_pattern

    def start(self, cmd: List[str], cwd: Optional[str] = None,
              env: Optional[Dict[str, str]] = None,
              stdin=subprocess.PIPE,
              stdout=subprocess.PIPE,
              stderr=subprocess.STDOUT) -> bool:
        """
        Start the process.

        Args:
            cmd: Command and arguments list
            cwd: Working directory
            env: Environment variables
            stdin: stdin configuration
            stdout: stdout configuration
            stderr: stderr configuration

        Returns:
            True if started successfully
        """
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                text=True,
                bufsize=1
            )
            self.running = True
            print(f"✓ {self.name} started (PID: {self.process.pid})")
            return True

        except Exception as e:
            print(f"✗ Failed to start {self.name}: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop the process gracefully, then forcefully if needed.

        Returns:
            True if stopped successfully
        """
        if not self.process:
            # Even if we don't have a process reference, try to kill by name
            if self.process_name_pattern:
                self._kill_by_name()
            return True

        try:
            pid = self.process.pid

            # Try graceful termination first
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
                print(f"✓ {self.name} stopped gracefully")
                self.running = False
                return True
            except subprocess.TimeoutExpired:
                pass

            # Try forceful kill
            self.process.kill()
            try:
                self.process.wait(timeout=2)
                print(f"✓ {self.name} stopped (force killed)")
                self.running = False
            except subprocess.TimeoutExpired:
                print(f"⚠ {self.name} did not respond to kill signal")

            # Kill by name pattern as last resort
            if self.process_name_pattern:
                self._kill_by_name()

            self.running = False
            return True

        except Exception as e:
            print(f"✗ Failed to stop {self.name}: {e}")

            # Try to kill by name as fallback
            if self.process_name_pattern:
                self._kill_by_name()

            self.running = False
            return False

    def _kill_by_name(self):
        """Kill all processes matching the name pattern."""
        if not self.process_name_pattern:
            return

        try:
            if platform.system() == "Darwin":  # macOS
                # Kill all matching processes
                subprocess.run(
                    ["pkill", "-9", "-f", self.process_name_pattern],
                    capture_output=True,
                    timeout=5
                )
                print(f"✓ Killed all {self.process_name_pattern} processes")
            elif platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/IM", f"{self.process_name_pattern}.exe"],
                    capture_output=True,
                    timeout=5
                )
                print(f"✓ Killed all {self.process_name_pattern} processes")
        except Exception as e:
            print(f"⚠ Could not kill {self.process_name_pattern} processes: {e}")

    def is_alive(self) -> bool:
        """
        Check if process is still alive.

        Returns:
            True if process is running
        """
        if not self.process:
            return False

        return self.process.poll() is None

    def read_output(self, timeout: float = 0.1) -> Optional[str]:
        """
        Read a line from process output (non-blocking).

        Args:
            timeout: Maximum time to wait for output

        Returns:
            Output line or None if no output available
        """
        if not self.process or not self.process.stdout:
            return None

        try:
            import select

            # Check if data is available
            ready, _, _ = select.select([self.process.stdout], [], [], timeout)

            if ready:
                line = self.process.stdout.readline()
                return line.rstrip() if line else None

        except Exception as e:
            print(f"Warning: Error reading output from {self.name}: {e}")

        return None


# ============================================================================
# File Detection
# ============================================================================

def detect_video_files() -> List[Path]:
    """
    Detect all video files in the data directory.

    Returns:
        List of video file paths, sorted
    """
    data_dir = get_data_dir()
    video_files = []

    # Look for common video formats
    for pattern in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
        video_files.extend(data_dir.glob(pattern))

    return sorted(video_files)


def detect_audio_files() -> List[Path]:
    """
    Detect all audio files in the data directory.

    Returns:
        List of audio file paths, sorted
    """
    data_dir = get_data_dir()
    audio_files = []

    # Look for common audio formats
    for pattern in ["*.wav", "*.aiff", "*.mp3", "*.flac"]:
        audio_files.extend(data_dir.glob(pattern))

    return sorted(audio_files)


# ============================================================================
# SuperCollider Utilities
# ============================================================================

def find_sclang() -> Optional[str]:
    """
    Find sclang executable.

    Returns:
        Path to sclang or None if not found
    """
    # Check environment variable
    if "SCLANG_PATH" in sys.path:
        return sys.path["SCLANG_PATH"]

    # Platform-specific locations
    if platform.system() == "Darwin":  # macOS
        default_path = "/Applications/SuperCollider.app/Contents/MacOS/sclang"
        if Path(default_path).exists():
            return default_path

    elif platform.system() == "Windows":
        # Check common Windows locations
        for path in [
            r"C:\Program Files\SuperCollider\sclang.exe",
            r"C:\Program Files (x86)\SuperCollider\sclang.exe"
        ]:
            if Path(path).exists():
                return path

    # Try to find in PATH
    import shutil
    sclang = shutil.which("sclang")
    if sclang:
        return sclang

    return None


# ============================================================================
# Processing Utilities
# ============================================================================

def find_processing_java() -> Optional[str]:
    """
    Find processing-java executable.

    Returns:
        Path to processing-java or None if not found
    """
    # Check environment variable
    if "PROCESSING_JAVA" in sys.path:
        return sys.path["PROCESSING_JAVA"]

    # Platform-specific locations
    if platform.system() == "Darwin":  # macOS
        default_path = "/Applications/Processing.app/Contents/MacOS/processing-java"
        if Path(default_path).exists():
            return default_path

    elif platform.system() == "Windows":
        # Check common Windows locations
        for path in [
            r"C:\Program Files\Processing\processing-java.exe",
            r"C:\Program Files (x86)\Processing\processing-java.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "Processing" / "processing-java.exe"
        ]:
            if Path(path).exists():
                return str(path)

    # Try to find in PATH
    import shutil
    processing_java = shutil.which("processing-java")
    if processing_java:
        return processing_java

    return None


# ============================================================================
# Validation
# ============================================================================

def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies are available.

    Returns:
        Dictionary of dependency name -> available (bool)
    """
    deps = {}

    # SuperCollider
    deps["sclang"] = find_sclang() is not None

    # Processing
    deps["processing-java"] = find_processing_java() is not None

    # Python packages
    try:
        import pythonosc
        deps["python-osc"] = True
    except ImportError:
        deps["python-osc"] = False

    try:
        import serial
        deps["pyserial"] = True
    except ImportError:
        deps["pyserial"] = False

    return deps
