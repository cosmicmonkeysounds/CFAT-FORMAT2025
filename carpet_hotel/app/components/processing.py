#!/usr/bin/env python3
"""
Carpet Hotel Processing Module
===============================

Manages Processing video display for Carpet Hotel.

Features:
- Launches Processing sketch with carpet_hotel_video.pde
- Manages display configuration (multiple screens)
- Detects available displays
- Manages video engine lifecycle
"""

import subprocess
import time
import threading
from typing import Optional, List, Dict
from pathlib import Path

from components.utils.utils import find_processing_java, ProcessWrapper, get_app_dir, detect_displays, get_data_dir
from components.logger import get_logger


class CarpetHotelProcessing:
    """
    Processing video engine manager.
    """

    def __init__(self, displays: Optional[List[int]] = None,
                 enable_keyboard: bool = True):
        """
        Initialize Processing manager.

        Args:
            displays: List of display indices to use (None for default [1, 2])
            enable_keyboard: Enable keyboard control in Processing (default: True)
        """
        self.displays = displays or [1, 2]
        self.enable_keyboard = enable_keyboard

        self.processing_java = find_processing_java()
        self.sketch_dir = get_app_dir()

        # Use process_name_pattern to kill all Processing instances
        self.process = ProcessWrapper("Processing", process_name_pattern="Processing.app")
        self.initialized = False

        # Output monitoring
        self._output_thread = None
        self._output_running = False

        # Logger
        self.log = get_logger("Processing", verbose=False)

    def start(self) -> bool:
        """
        Start Processing video engine.

        Returns:
            True if started successfully
        """
        if not self.processing_java:
            print("✗ processing-java not found. Please install Processing.")
            return False

        # Build command
        cmd = [
            self.processing_java,
            f"--sketch={self.sketch_dir}",
            "--run"
        ]

        # Add command line arguments for Processing sketch
        if self.enable_keyboard:
            cmd.append("--test-mode")

        # Add OSC control mode (always enabled for Python control)
        cmd.append("--osc-control")

        # Display configuration now read from video_config.json by Processing
        # Only pass if explicitly provided (otherwise Processing reads from config)
        # This parameter is deprecated - displays should be configured in video_config.json
        if self.displays and self.displays != [1, 2]:  # Only override if non-default
            displays_str = ','.join(map(str, self.displays))
            cmd.append(f"--displays={displays_str}")
            print(f"  ⚠ Using command-line displays override (prefer video_config.json)")

        # Pass video files as arguments
        video_files = self._get_video_files()
        if video_files:
            print(f"  Passing {len(video_files)} video file(s) to Processing")
            for video_file in video_files:
                cmd.append(f"--video={video_file}")
        else:
            print("  ⚠ No video files found in data directory")

        print(f"Starting Processing...")
        print(f"  Displays: {self.displays}")
        print(f"  Keyboard: {self.enable_keyboard}")

        # Start process
        if not self.process.start(cmd):
            return False

        # Start output monitoring thread (CRITICAL - prevents buffer blocking)
        self._start_output_monitor()

        # Give Processing time to start
        time.sleep(2)

        if not self.process.is_alive():
            self.log.error("Processing process died")
            return False

        self.initialized = True
        self.log.success("Processing video engine ready")
        return True

    def _get_video_files(self) -> List[Path]:
        """Get list of video files from data directory."""
        data_dir = get_data_dir()
        video_files = []

        # Find video files
        for pattern in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
            video_files.extend(data_dir.glob(pattern))

        # Sort by name
        return sorted(video_files)

    def stop(self) -> bool:
        """
        Stop Processing video engine.

        Returns:
            True if stopped successfully
        """
        self.initialized = False

        # Stop output monitoring thread
        self._output_running = False
        if self._output_thread and self._output_thread.is_alive():
            self._output_thread.join(timeout=1)

        return self.process.stop()

    def _start_output_monitor(self):
        """
        Start thread to monitor and drain Processing stdout/stderr.

        CRITICAL: Processing writes to stdout. If we don't read it, the buffer
        fills up and Processing blocks, causing the entire system to freeze.
        """
        if self._output_running:
            return

        self._output_running = True
        self._output_thread = threading.Thread(
            target=self._monitor_output,
            daemon=True
        )
        self._output_thread.start()

    def _monitor_output(self):
        """
        Monitor Processing output and drain buffer.

        Reads stdout continuously to prevent buffer from filling.
        Only logs important messages to keep console clean.
        """
        if not self.process.process or not self.process.process.stdout:
            return

        important_keywords = ["error", "exception", "warning", "failed"]

        while self._output_running and self.process.is_alive():
            try:
                # Non-blocking read with timeout
                line = self.process.read_output(timeout=0.1)

                if line:
                    # Only log important messages
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in important_keywords):
                        self.log.warning(line)
                    # Silently drain all other output to prevent blocking

            except Exception as e:
                if self._output_running:  # Only log if we're still supposed to be running
                    self.log.debug(f"Output monitor error: {e}")
                break

            time.sleep(0.01)  # Small delay to prevent CPU spinning

    def is_running(self) -> bool:
        """
        Check if Processing is running.

        Returns:
            True if running
        """
        return self.process.is_alive()

    @staticmethod
    def detect_displays() -> List[Dict[str, any]]:
        """
        Detect available displays.

        Returns:
            List of display info dictionaries
        """
        return detect_displays()

    @staticmethod
    def get_display_count() -> int:
        """
        Get number of available displays.

        Returns:
            Number of displays
        """
        return len(detect_displays())


def main():
    """Standalone mode - test Processing."""
    import argparse

    parser = argparse.ArgumentParser(description='Carpet Hotel Processing')
    parser.add_argument('--displays', help='Display numbers (comma-separated)')
    parser.add_argument('--keyboard', action='store_true', help='Enable keyboard control')
    parser.add_argument('--list-displays', action='store_true', help='List displays')

    args = parser.parse_args()

    if args.list_displays:
        print("Available displays:")
        for display in CarpetHotelProcessing.detect_displays():
            main_marker = " [MAIN]" if display["main"] else ""
            print(f"  {display['index']}: {display['name']}{main_marker}")
            print(f"     Resolution: {display['resolution'][0]}x{display['resolution'][1]}")
        return

    displays = None
    if args.displays:
        displays = [int(d.strip()) for d in args.displays.split(',')]

    pde = CarpetHotelProcessing(
        displays=displays,
        enable_keyboard=args.keyboard
    )

    if pde.start():
        print("\nProcessing running. Press Ctrl+C to stop...")
        try:
            while pde.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            pde.stop()
    else:
        print("✗ Failed to start Processing")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
