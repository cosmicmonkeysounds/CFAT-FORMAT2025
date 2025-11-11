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
from components.supercollider import CarpetHotelSuperCollider
from components.processing import CarpetHotelProcessing
from components.arduino import CarpetHotelArduino
from components.logger import get_logger

# OSC forwarding
try:
    from pythonosc import udp_client
    from pythonosc.dispatcher import Dispatcher
    from pythonosc.osc_server import ThreadingOSCUDPServer
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False
    _log = get_logger("Core")
    _log.warning("python-osc not installed - OSC forwarding disabled")
    _log.info("  Install with: pip install python-osc")


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

        # Arduino serial polling
        self._arduino_thread = None
        self._arduino_running = False

        # OSC communication
        self.osc_server = None
        self.osc_thread = None
        self.sc_client = None
        self.processing_recv_port = 12001  # Receive from Processing
        self.sc_send_port = 57120          # Send to SuperCollider

        # Global state (brain manages all state)
        self.current_scene = 0
        self.master_volume = 0.7
        self.num_displays = 2
        self.is_animating = False

        # Logger
        self.log = get_logger("Core")

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
        # Stop Arduino polling thread
        self._arduino_running = False
        if self._arduino_thread and self._arduino_thread.is_alive():
            self._arduino_thread.join(timeout=1)

        # Stop monitoring thread
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1)

        # Stop OSC server
        if self.osc_server:
            try:
                self.osc_server.shutdown()
            except:
                pass

        if self.is_running():
            print("\nCleaning up running processes...")
            self.stop_all()

    def _monitor_processes(self):
        """Monitor processes and update state when they exit."""
        while self._monitor_running:
            # Check Processing
            if self.pde_running and self.processing:
                if not self.processing.is_running():
                    self.log.warning("Processing exited unexpectedly")
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

    def _poll_arduino_serial(self):
        """Poll Arduino serial messages continuously."""
        while self._arduino_running:
            if self.arduino and self.arduino_running:
                try:
                    self.arduino.process_serial_messages()
                except Exception as e:
                    self.log.error(f"Arduino serial error: {e}")
            time.sleep(0.01)  # 10ms poll rate (same as Arduino standalone)

    def _start_arduino_polling(self):
        """Start Arduino serial polling thread."""
        if not self._arduino_running:
            self._arduino_running = True
            self._arduino_thread = threading.Thread(
                target=self._poll_arduino_serial,
                daemon=True
            )
            self._arduino_thread.start()
            self.log.debug("Arduino serial polling started")

    # ========================================================================
    # OSC Communication (Brain manages all state and routing)
    # ========================================================================

    def setup_osc(self) -> bool:
        """
        Setup OSC communication as central hub.

        Core receives messages from Processing and forwards to SuperCollider.
        Core manages all global state.

        Returns:
            True if setup successful
        """
        if not OSC_AVAILABLE:
            self.log.warning("OSC not available - audio control disabled")
            return False

        self.log.subsection("OSC Communication")
        self.log.info("Architecture: Processing ↔ Core (Brain) ↔ SuperCollider")

        # Create OSC client to send to SuperCollider
        self.sc_client = udp_client.SimpleUDPClient("127.0.0.1", self.sc_send_port)
        self.log.success(f"OSC client → SuperCollider (port {self.sc_send_port})")

        # Create OSC server to receive from Processing and Arduino
        dispatcher = Dispatcher()
        dispatcher.map("/carpet/scene", self._handle_scene)
        dispatcher.map("/carpet/transition", self._handle_transition)
        dispatcher.map("/carpet/volume", self._handle_volume)
        dispatcher.map("/carpet/state", self._handle_state)
        dispatcher.map("/carpet/elevator/up", self._handle_elevator_up)
        dispatcher.map("/carpet/elevator/down", self._handle_elevator_down)

        self.osc_server = ThreadingOSCUDPServer(
            ("127.0.0.1", self.processing_recv_port),
            dispatcher
        )

        # Start OSC server in background thread
        self.osc_thread = threading.Thread(target=self.osc_server.serve_forever, daemon=True)
        self.osc_thread.start()

        self.log.success(f"OSC server ← Processing (port {self.processing_recv_port})")
        self.log.success("OSC communication ready")

        return True

    def _handle_scene(self, address, *args):
        """Handle scene change from Processing."""
        if len(args) >= 3:
            scene = args[0]
            num_windows = args[1]
            is_animating = args[2]

            # Update global state
            self.current_scene = scene
            self.num_displays = num_windows
            self.is_animating = (is_animating != 0)

            # Forward to SuperCollider
            if self.sc_client and self.sc_running:
                self.sc_client.send_message("/carpet/scene", args)
                self.log.info(f"Scene {scene} → SuperCollider")

    def _handle_transition(self, address, *args):
        """Handle transition from Processing."""
        # Forward directly to SuperCollider (don't spam console)
        if self.sc_client and self.sc_running:
            self.sc_client.send_message("/carpet/transition", args)

    def _handle_volume(self, address, *args):
        """Handle volume change from Processing."""
        if len(args) >= 1:
            volume = float(args[0])

            # Update global state
            self.master_volume = volume

            # Forward to SuperCollider
            if self.sc_client and self.sc_running:
                self.sc_client.send_message("/carpet/volume", [volume])
                self.log.info(f"Volume {int(volume * 100)}% → SuperCollider")

    def _handle_state(self, address, *args):
        """Handle state updates from Processing."""
        if len(args) >= 1:
            state = args[0]
            self.log.debug(f"Processing state: {state}")

    def _handle_elevator_up(self, address, *args):
        """Handle UP button press from Arduino."""
        # Trigger transition animation (UP direction)
        if self.arduino and self.arduino_running:
            self.arduino.set_led_animation_mode("TRANSITION", direction="up")

        # Increment scene
        max_scene = self.get_max_scene()
        self.current_scene = (self.current_scene + 1) % (max_scene + 1)

        self.log.info(f"Arduino UP → Scene {self.current_scene}")

        # Send goto command to Processing
        if self.pde_running:
            processing_client = udp_client.SimpleUDPClient("127.0.0.1", 12000)
            processing_client.send_message("/carpet/goto", [self.current_scene])

        # After a delay, switch to stable animation (transition takes ~2 seconds)
        import threading
        def switch_to_stable():
            time.sleep(2.0)  # Wait for transition to complete
            if self.arduino and self.arduino_running:
                self.arduino.set_led_animation_mode("STABLE")
        threading.Thread(target=switch_to_stable, daemon=True).start()

    def _handle_elevator_down(self, address, *args):
        """Handle DOWN button press from Arduino."""
        # Trigger transition animation (DOWN direction)
        if self.arduino and self.arduino_running:
            self.arduino.set_led_animation_mode("TRANSITION", direction="down")

        # Decrement scene
        max_scene = self.get_max_scene()
        self.current_scene = (self.current_scene - 1) % (max_scene + 1)

        self.log.info(f"Arduino DOWN → Scene {self.current_scene}")

        # Send goto command to Processing
        if self.pde_running:
            processing_client = udp_client.SimpleUDPClient("127.0.0.1", 12000)
            processing_client.send_message("/carpet/goto", [self.current_scene])

        # After a delay, switch to stable animation (transition takes ~2 seconds)
        import threading
        def switch_to_stable():
            time.sleep(2.0)  # Wait for transition to complete
            if self.arduino and self.arduino_running:
                self.arduino.set_led_animation_mode("STABLE")
        threading.Thread(target=switch_to_stable, daemon=True).start()

    def get_max_scene(self) -> int:
        """Calculate maximum scene index based on video files and displays."""
        num_clips = self.get_num_video_clips()

        # Formula: max_scene = num_clips - num_displays
        # - 1 display, 10 clips: max_scene = 10 - 1 = 9 (scenes 0-9)
        # - 2 displays, 10 clips: max_scene = 10 - 2 = 8 (scenes 0-8)
        max_scene = num_clips - self.num_displays

        return max(0, max_scene)

    def get_num_video_clips(self) -> int:
        """Count number of video files in data folder."""
        from pathlib import Path
        data_dir = Path(__file__).parent.parent / "data"
        video_files = list(data_dir.glob("*.mp4"))
        return len(video_files)

    def send_initial_scene(self):
        """Send initial scene to SuperCollider to start audio."""
        if self.sc_client and self.sc_running:
            # Send scene 0 with current number of displays
            self.sc_client.send_message("/carpet/scene", [
                self.current_scene,
                self.num_displays,
                0  # not animating
            ])
            self.log.success(f"Initial scene {self.current_scene} → SuperCollider")

            # Send initial volume
            self.sc_client.send_message("/carpet/volume", [self.master_volume])
            self.log.success(f"Initial volume {int(self.master_volume * 100)}% → SuperCollider")

    # ========================================================================
    # Component Management
    # ========================================================================

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

            # Setup OSC if not already done
            if not self.osc_server and OSC_AVAILABLE:
                self.setup_osc()

            # Send initial scene/volume to SC immediately (independent startup)
            if self.osc_server:
                self.log.success("SuperCollider ready - sending initial state...")
                time.sleep(1)  # Give SC time to init OSC
                self.send_initial_scene()

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

        # Update num_displays state
        if displays:
            self.num_displays = len(displays)

        self.processing = CarpetHotelProcessing(
            displays=displays,
            enable_keyboard=enable_keyboard
        )

        if self.processing.start():
            self.pde_running = True

            # Setup OSC communication if not already done
            if not self.osc_server and OSC_AVAILABLE:
                self.setup_osc()

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
            # Start background thread to poll serial messages
            self._start_arduino_polling()

            # Set initial LED animation to stable
            time.sleep(0.5)  # Give Arduino time to initialize
            self.arduino.set_led_animation_mode("STABLE")

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

        # Stop polling thread first
        self._arduino_running = False
        if self._arduino_thread and self._arduino_thread.is_alive():
            self._arduino_thread.join(timeout=1)

        # Disconnect Arduino
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
