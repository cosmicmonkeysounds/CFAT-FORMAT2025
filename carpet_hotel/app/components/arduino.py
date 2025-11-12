#!/usr/bin/env python3
"""
Carpet Hotel Arduino Module
============================

Manages Arduino/Elevator control panel communication via serial and OSC.

Features:
- Serial communication with Arduino
- Converts button presses to OSC messages
- Receives OSC LED control commands
- Auto-detection of Arduino port
"""

import time
import threading
import math
import random
from typing import Optional
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

from components.utils.utils import find_arduino_port, detect_serial_ports
from components.logger import get_logger
from components.serial_broker import SerialBroker


class CarpetHotelArduino:
    """
    Arduino/Elevator control panel manager.
    """

    def __init__(self, serial_port: Optional[str] = None,
                 osc_send_host: str = "127.0.0.1",
                 osc_send_port: int = 12001,  # Send to Python core, not Processing
                 osc_recv_port: int = 12002):
        """
        Initialize Arduino manager.

        Args:
            serial_port: Serial port for Arduino (auto-detect if None)
            osc_send_host: Host to send OSC messages to
            osc_send_port: Port to send OSC messages to (Processing)
            osc_recv_port: Port to receive OSC LED control messages
        """
        self.serial_port = serial_port
        self.osc_send_host = osc_send_host
        self.osc_send_port = osc_send_port
        self.osc_recv_port = osc_recv_port

        # Serial broker (single source of truth for serial I/O)
        self.broker: Optional[SerialBroker] = None

        self.osc_client: Optional[udp_client.SimpleUDPClient] = None
        self.osc_server: Optional[ThreadingOSCUDPServer] = None
        self.osc_thread: Optional[threading.Thread] = None
        self.running = False

        # Logger
        self.log = get_logger("Arduino")

        # Message callback for GUI logging
        self.message_callback = None

        # LED Animation
        self.animation_mode = "OFF"  # 'OFF', 'STABLE', 'TRANSITION_UP', 'TRANSITION_DOWN'
        self.animation_thread: Optional[threading.Thread] = None
        self.animation_running = False

    def set_message_callback(self, callback):
        """
        Set callback function for message logging.

        Args:
            callback: Function that takes (message: str) parameter
        """
        self.message_callback = callback

    def _notify(self, message: str):
        """Send message to callback if set."""
        if self.message_callback:
            try:
                self.message_callback(message)
            except Exception as e:
                self.log.error(f"Callback error: {e}")

    def connect(self) -> bool:
        """
        Connect to Arduino and setup OSC.

        Returns:
            True if connection successful
        """
        # Find Arduino port if not specified
        if self.serial_port is None or self.serial_port == "auto":
            self.serial_port = find_arduino_port()
            if self.serial_port is None:
                print("✗ No Arduino found. Available ports:")
                for port in detect_serial_ports():
                    print(f"  {port['device']}: {port['description']}")
                return False

        # Create and connect serial broker
        self.broker = SerialBroker(self.serial_port)
        if not self.broker.connect():
            return False

        # Register callback for incoming serial messages
        self.broker.register_message_callback(self._handle_serial_message)

        # Setup OSC
        if not self.setup_osc():
            self.broker.disconnect()
            return False

        # Start OSC server
        self.start_osc_server()

        # IMPORTANT: Set running=True BEFORE starting animation thread
        # Otherwise the thread will exit immediately
        self.running = True

        # Start LED animation thread
        self.start_animation_thread()

        print(f"✓ Arduino connected and ready")
        return True

    def _handle_serial_message(self, message: str):
        """
        Handle incoming serial message from broker.

        Args:
            message: Message from Arduino
        """
        # Convert serial messages to OSC (Arduino sends uppercase UP/DOWN)
        message_upper = message.upper()

        if message_upper == "UP":
            if self.osc_client:
                self.osc_client.send_message("/carpet/elevator/up", [])
            self.log.success("Button UP pressed")
            self._notify("✓ Button UP pressed")

        elif message_upper == "DOWN":
            if self.osc_client:
                self.osc_client.send_message("/carpet/elevator/down", [])
            self.log.success("Button DOWN pressed")
            self._notify("✓ Button DOWN pressed")

        else:
            # Unknown message - might be debug output
            if message:  # Ignore empty lines
                self.log.debug(f"Arduino: {message}")

    def setup_osc(self) -> bool:
        """
        Setup OSC client and server.

        Returns:
            True if successful
        """
        try:
            # OSC client to send button presses
            self.osc_client = udp_client.SimpleUDPClient(
                self.osc_send_host, self.osc_send_port
            )
            print(f"✓ OSC client ready (sending to {self.osc_send_host}:{self.osc_send_port})")

            # OSC server to receive LED control messages
            dispatcher = Dispatcher()
            dispatcher.map("/carpet/elevator/led/red", self.handle_led_red)
            dispatcher.map("/carpet/elevator/led/yellow", self.handle_led_yellow)
            dispatcher.map("/carpet/elevator/led/green", self.handle_led_green)
            dispatcher.map("/carpet/led/red", self.handle_led_red)
            dispatcher.map("/carpet/led/yellow", self.handle_led_yellow)
            dispatcher.map("/carpet/led/green", self.handle_led_green)

            self.osc_server = ThreadingOSCUDPServer(
                ("127.0.0.1", self.osc_recv_port), dispatcher
            )
            print(f"✓ OSC server ready (receiving on port {self.osc_recv_port})")

            return True

        except Exception as e:
            print(f"✗ Could not setup OSC: {e}")
            return False

    def start_osc_server(self):
        """Start OSC server in background thread."""
        if self.osc_server:
            self.osc_thread = threading.Thread(target=self.osc_server.serve_forever)
            self.osc_thread.daemon = True
            self.osc_thread.start()

    def handle_led_red(self, address, *args):
        """Handle red LED OSC message."""
        if args and self.broker:
            state = int(args[0])
            self.broker.write_led("red", state)
            print(f"[OSC→Serial] {address} {state} → Arduino RED")

    def handle_led_yellow(self, address, *args):
        """Handle yellow LED OSC message."""
        if args and self.broker:
            state = int(args[0])
            self.broker.write_led("yellow", state)
            print(f"[OSC→Serial] {address} {state} → Arduino YELLOW")

    def handle_led_green(self, address, *args):
        """Handle green LED OSC message."""
        if args and self.broker:
            state = int(args[0])
            self.broker.write_led("green", state)
            print(f"[OSC→Serial] {address} {state} → Arduino GREEN")


    def set_led(self, color: str, value: int):
        """
        Set LED brightness using PWM.

        Args:
            color: 'red', 'yellow', or 'green'
            value: 0-255 (PWM brightness), or 0/1 for legacy compatibility
        """
        if not self.broker:
            print(f"[Arduino] ERROR: set_led({color}, {value}) called but broker is None!")
            self.log.error(f"set_led({color}, {value}) - broker is None")
            return

        if not self.broker.is_connected():
            print(f"[Arduino] ERROR: set_led({color}, {value}) called but broker not connected!")
            self.log.error(f"set_led({color}, {value}) - broker not connected")
            return

        # Convert legacy 0/1 to 0/255
        if value == 1:
            value = 255

        # Log occasionally for debugging
        if random.randint(0, 50) == 0:
            print(f"[Arduino] set_led({color}, {value}) - sending to broker")

        # Use broker for thread-safe write
        self.broker.write_led(color, value)

    def set_led_animation_mode(self, mode: str, direction: str = "up"):
        """
        Set LED animation mode.

        Args:
            mode: 'STABLE', 'TRANSITION', or 'OFF'
            direction: 'up' or 'down' (for TRANSITION mode)
        """
        old_mode = self.animation_mode

        # Update animation mode
        if mode == "STABLE":
            self.animation_mode = "STABLE"
        elif mode == "TRANSITION":
            self.animation_mode = f"TRANSITION_{direction.upper()}"
        elif mode == "OFF":
            self.animation_mode = "OFF"
            # Turn off all LEDs
            self.set_led("red", 0)
            self.set_led("yellow", 0)
            self.set_led("green", 0)

        self.log.info(f"Animation mode: {old_mode} → {self.animation_mode}")
        print(f"[Arduino] Animation mode changed: {old_mode} → {self.animation_mode}")

    def start_animation_thread(self):
        """Start the LED animation thread."""
        if self.animation_running:
            self.log.warning("Animation thread already running")
            return

        self.log.info("Starting LED animation thread...")
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        self.log.success("LED animation thread started")
        print("✓ LED animation thread started")

    def _animation_loop(self):
        """Main LED animation loop (runs in background thread)."""
        self.log.info("Animation loop starting")
        print("[Animation] Loop started")
        print(f"[Animation] Initial state: running={self.running}, animation_running={self.animation_running}, broker_connected={self.broker.is_connected() if self.broker else False}")
        start_time = time.time()
        last_mode = None
        iteration = 0

        while self.animation_running and self.running:
            elapsed = time.time() - start_time
            iteration += 1

            # Log mode changes
            if self.animation_mode != last_mode:
                self.log.info(f"Animation mode changed: {last_mode} → {self.animation_mode}")
                print(f"[Animation] Mode changed: {last_mode} → {self.animation_mode}")
                print(f"[Animation] Broker status: {self.broker.is_connected() if self.broker else 'No broker'}")
                last_mode = self.animation_mode

            # Debug: Log every 100 iterations to show loop is running
            if iteration % 100 == 0:
                self.log.debug(f"Loop alive - iteration {iteration}, mode={self.animation_mode}")
                print(f"[Animation] Loop alive - mode={self.animation_mode}, iteration={iteration}, broker_connected={self.broker.is_connected() if self.broker else False}")

            if self.animation_mode == "STABLE":
                self._animate_stable(elapsed)
            elif self.animation_mode == "TRANSITION_UP":
                self._animate_transition_up(elapsed)
            elif self.animation_mode == "TRANSITION_DOWN":
                self._animate_transition_down(elapsed)
            elif self.animation_mode == "OFF":
                # Do nothing, LEDs are already off
                pass

            time.sleep(0.05)  # 20 FPS animation

        self.log.info("Animation loop stopped")
        print("[Animation] Loop stopped")

    def _animate_stable(self, elapsed: float):
        """
        Stable animation: Slow pulsing of green LED (0 and 127 for dimmer look).

        Args:
            elapsed: Time elapsed since animation start (seconds)
        """
        # Simple on/off pulsing - 1 second period
        period = 1.0
        phase = (elapsed % period) / period  # 0.0 to 1.0

        # Simple threshold: on for first half, off for second half
        brightness = 127 if phase < 0.5 else 0

        # Debug output (frequently at first, then less often)
        if elapsed < 5.0 or (int(elapsed) % 5 == 0 and (elapsed % 5) < 0.1):
            self.log.debug(f"STABLE animation - Green: {brightness}, elapsed: {elapsed:.1f}s, phase: {phase:.2f}")
            print(f"[Animation] STABLE - Green brightness: {brightness}, elapsed: {elapsed:.1f}s")

        # Set green LED, keep others off
        self.set_led("red", 0)
        self.set_led("yellow", 0)
        self.set_led("green", brightness)

    def _animate_transition_up(self, elapsed: float):
        """
        Transition UP animation: Flicker red → yellow → green quickly.
        Using 0 and 127 for dimmer look.

        Args:
            elapsed: Time elapsed since animation start (seconds)
        """
        # Quick flicker - change every 100ms
        flicker_period = 0.1
        step = int(elapsed / flicker_period) % 3  # 0, 1, 2 (red, yellow, green)

        if step == 0:  # Red
            self.set_led("red", 127)
            self.set_led("yellow", 0)
            self.set_led("green", 0)
        elif step == 1:  # Yellow
            self.set_led("red", 0)
            self.set_led("yellow", 127)
            self.set_led("green", 0)
        else:  # Green
            self.set_led("red", 0)
            self.set_led("yellow", 0)
            self.set_led("green", 127)

    def _animate_transition_down(self, elapsed: float):
        """
        Transition DOWN animation: Flicker green → yellow → red quickly.
        Using 0 and 127 for dimmer look.

        Args:
            elapsed: Time elapsed since animation start (seconds)
        """
        # Quick flicker - change every 100ms
        flicker_period = 0.1
        step = int(elapsed / flicker_period) % 3  # 0, 1, 2 (green, yellow, red)

        if step == 0:  # Green
            self.set_led("red", 0)
            self.set_led("yellow", 0)
            self.set_led("green", 127)
        elif step == 1:  # Yellow
            self.set_led("red", 0)
            self.set_led("yellow", 127)
            self.set_led("green", 0)
        else:  # Red
            self.set_led("red", 127)
            self.set_led("yellow", 0)
            self.set_led("green", 0)

    def run_forever(self):
        """
        Run forever (blocking).
        Broker handles serial I/O in background threads.
        """
        print("\n" + "="*60)
        print("Arduino Bridge Running")
        print("="*60)
        print(f"Serial: {self.serial_port}")
        print(f"OSC Send: {self.osc_send_host}:{self.osc_send_port}")
        print(f"OSC Recv: 127.0.0.1:{self.osc_recv_port}")
        print("\nPress Ctrl+C to stop")
        print("="*60 + "\n")

        try:
            while self.running:
                time.sleep(0.1)  # Just keep alive

        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.disconnect()

    def disconnect(self):
        """Disconnect and cleanup resources."""
        self.running = False
        self.animation_running = False

        # Wait for animation thread to stop
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1)

        if self.osc_server:
            self.osc_server.shutdown()
            print("✓ OSC server stopped")

        # Disconnect broker (handles LED cleanup and serial close)
        if self.broker:
            self.broker.disconnect()


def main():
    """Standalone mode - run Arduino bridge."""
    import argparse

    parser = argparse.ArgumentParser(description='Carpet Hotel Arduino Bridge')
    parser.add_argument('--port', '-p', help='Serial port (auto-detect if not specified)')
    parser.add_argument('--list-ports', action='store_true',
                        help='List available serial ports and exit')

    args = parser.parse_args()

    if args.list_ports:
        print("Available serial ports:")
        for port in detect_serial_ports():
            arduino_marker = " [Arduino]" if port["is_arduino"] else ""
            print(f"  {port['device']}: {port['description']}{arduino_marker}")
        return

    arduino = CarpetHotelArduino(serial_port=args.port)

    if arduino.connect():
        arduino.run_forever()
    else:
        print("✗ Failed to connect to Arduino")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
