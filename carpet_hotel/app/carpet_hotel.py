#!/usr/bin/env python3
"""
Carpet Hotel Core
=================

Minimal core coordinator that manages the three main components:
- SuperCollider (audio engine)
- Processing (video display)
- Arduino (elevator control)

This module ONLY coordinates between components. All component-specific
logic lives in the wrapper modules (carpet_hotel_scd, carpet_hotel_pde,
carpet_hotel_arduino).
"""

from typing import Optional, List
from pathlib import Path
import signal
import atexit
import sys
import threading
import time

# Import wrapper modules
from carpet_hotel_scd import CarpetHotelSuperCollider
from carpet_hotel_pde import CarpetHotelProcessing
from carpet_hotel_arduino import CarpetHotelArduino


class CarpetHotelCore:
    """
    Core coordinator for Carpet Hotel system.

    Manages lifecycle of all three components:
    - SuperCollider audio engine
    - Processing video display
    - Arduino elevator control
    """

    def __init__(self):
        """Initialize core coordinator."""
        # Component instances
        self.supercollider: Optional[CarpetHotelSuperCollider] = None
        self.processing: Optional[CarpetHotelProcessing] = None
        self.arduino: Optional[CarpetHotelArduino] = None

        # Component running states
        self.sc_running = False
        self.pde_running = False
        self.arduino_running = False

        # Process monitoring
        self._monitor_thread = None
        self._monitor_running = False

        # Register cleanup handlers
        atexit.register(self._cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle termination signals gracefully."""
        print(f"\n\nReceived signal {signum}, shutting down...")
        self.stop_all()
        sys.exit(0)

    def _cleanup(self):
        """Cleanup handler called on exit."""
        # Stop monitoring thread
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)

        if self.is_running():
            print("\nCleaning up running processes...")
            self.stop_all()

    def _monitor_processes(self):
        """Monitor processes and update state when they exit."""
        while self._monitor_running:
            # Check Processing
            if self.pde_running and self.processing:
                if not self.processing.is_running():
                    print("\n⚠ Processing exited unexpectedly")
                    self.pde_running = False
                    self.processing = None

            # Check SuperCollider
            if self.sc_running and self.supercollider:
                # SC doesn't have is_running check yet, could add if needed
                pass

            time.sleep(0.5)  # Check every 500ms

    def _start_monitoring(self):
        """Start process monitoring thread."""
        if not self._monitor_running:
            self._monitor_running = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_processes,
                daemon=True
            )
            self._monitor_thread.start()

    def start_supercollider(self) -> bool:
        """
        Start SuperCollider audio engine.

        Uses system default audio device. User should configure audio device
        via macOS System Settings before running.

        Returns:
            True if started successfully
        """
        if self.sc_running:
            print("⚠ SuperCollider already running")
            return True

        self.supercollider = CarpetHotelSuperCollider()

        if self.supercollider.start():
            self.sc_running = True
            return True

        return False

    def stop_supercollider(self) -> bool:
        """
        Stop SuperCollider audio engine.

        Returns:
            True if stopped successfully
        """
        if not self.sc_running or not self.supercollider:
            return True

        if self.supercollider.stop():
            self.sc_running = False
            return True

        return False

    def start_processing(self, displays: Optional[List[int]] = None,
                        enable_keyboard: bool = False) -> bool:
        """
        Start Processing video display.

        Args:
            displays: List of display indices to use
            enable_keyboard: Enable keyboard control

        Returns:
            True if started successfully
        """
        if self.pde_running:
            print("⚠ Processing already running")
            return True

        self.processing = CarpetHotelProcessing(
            displays=displays,
            enable_keyboard=enable_keyboard
        )

        if self.processing.start():
            self.pde_running = True
            # Start monitoring thread to detect unexpected exits
            self._start_monitoring()
            return True

        return False

    def stop_processing(self) -> bool:
        """
        Stop Processing video display.

        Returns:
            True if stopped successfully
        """
        if not self.pde_running or not self.processing:
            return True

        if self.processing.stop():
            self.pde_running = False
            return True

        return False

    def start_arduino(self, serial_port: Optional[str] = None) -> bool:
        """
        Start Arduino elevator control.

        Args:
            serial_port: Serial port (None or "auto" for auto-detect)

        Returns:
            True if started successfully
        """
        if self.arduino_running:
            print("⚠ Arduino already running")
            return True

        self.arduino = CarpetHotelArduino(serial_port=serial_port)

        if self.arduino.connect():
            self.arduino_running = True
            return True

        return False

    def stop_arduino(self) -> bool:
        """
        Stop Arduino elevator control.

        Returns:
            True if stopped successfully
        """
        if not self.arduino_running or not self.arduino:
            return True

        self.arduino.disconnect()
        self.arduino_running = False
        return True

    def start_all(self, displays: Optional[List[int]] = None,
                  enable_keyboard: bool = False,
                  serial_port: Optional[str] = None,
                  enable_arduino: bool = True) -> bool:
        """
        Start all components.

        Args:
            displays: Display list for Processing
            enable_keyboard: Enable keyboard control in Processing
            serial_port: Arduino serial port
            enable_arduino: Whether to start Arduino

        Returns:
            True if all started successfully
        """
        print("\n" + "="*60)
        print("Starting Carpet Hotel")
        print("="*60 + "\n")

        # Start SuperCollider first (takes longest to initialize)
        print("[1/3] Starting SuperCollider...")
        if not self.start_supercollider():
            print("✗ Failed to start SuperCollider")
            return False

        # Start Processing
        print("\n[2/3] Starting Processing...")
        if not self.start_processing(displays, enable_keyboard):
            print("✗ Failed to start Processing")
            self.stop_supercollider()
            return False

        # Start Arduino (optional)
        if enable_arduino:
            print("\n[3/3] Starting Arduino...")
            if not self.start_arduino(serial_port):
                print("⚠ Arduino not available (continuing without it)")
        else:
            print("\n[3/3] Arduino disabled")

        print("\n" + "="*60)
        print("✓ Carpet Hotel Started")
        print("="*60 + "\n")

        return True

    def stop_all(self) -> bool:
        """
        Stop all running components.

        Returns:
            True if all stopped successfully
        """
        print("\n" + "="*60)
        print("Stopping Carpet Hotel")
        print("="*60 + "\n")

        success = True

        if self.arduino_running:
            print("Stopping Arduino...")
            if not self.stop_arduino():
                success = False

        if self.pde_running:
            print("Stopping Processing...")
            if not self.stop_processing():
                success = False

        if self.sc_running:
            print("Stopping SuperCollider...")
            if not self.stop_supercollider():
                success = False

        if success:
            print("\n✓ All components stopped")
        else:
            print("\n⚠ Some components failed to stop cleanly")

        return success

    def is_running(self) -> bool:
        """
        Check if any component is running.

        Returns:
            True if at least one component is running
        """
        return self.sc_running or self.pde_running or self.arduino_running

    def get_status(self) -> dict:
        """
        Get status of all components.

        Returns:
            Dictionary with component statuses
        """
        return {
            "supercollider": self.sc_running,
            "processing": self.pde_running,
            "arduino": self.arduino_running
        }


# For backward compatibility with old code
CarpetHotelLauncher = CarpetHotelCore


def main():
    """Simple test of the core."""
    import time

    core = CarpetHotelCore()

    print("Testing Carpet Hotel Core")
    print("="*60)

    # Start all
    if core.start_all(enable_arduino=False):
        print("\nAll systems running. Press Ctrl+C to stop...")

        try:
            while core.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nInterrupted by user")

    # Stop all
    core.stop_all()


if __name__ == "__main__":
    main()
