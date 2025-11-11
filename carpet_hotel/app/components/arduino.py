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

import serial
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

        self.serial_conn: Optional[serial.Serial] = None
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

        # Connect to serial
        if not self.setup_serial():
            return False

        # Setup OSC
        if not self.setup_osc():
            self.cleanup_serial()
            return False

        # Start OSC server
        self.start_osc_server()

        # Start LED animation thread
        self.start_animation_thread()

        self.running = True
        print(f"✓ Arduino connected and ready")
        return True

    def setup_serial(self) -> bool:
        """
        Setup serial connection to Arduino.

        Returns:
            True if successful
        """
        try:
            print(f"Connecting to Arduino on {self.serial_port}...")
            self.serial_conn = serial.Serial(self.serial_port, 115200, timeout=0.1)
            time.sleep(2)  # Wait for Arduino to reset

            # Wait for READY message
            print("Waiting for Arduino READY message...")
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    print(f"  Arduino: {line}")
                    if line == "READY":
                        print("✓ Arduino serial connected")
                        return True

            print("⚠ Arduino did not send READY message, but continuing...")
            return True

        except serial.SerialException as e:
            print(f"✗ Could not connect to Arduino: {e}")
            return False

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
        if args and self.serial_conn:
            state = int(args[0])
            cmd = f"RED:{state}\n"
            self.serial_conn.write(cmd.encode())
            print(f"[OSC→Serial] {address} {state} → Arduino: {cmd.strip()}")

    def handle_led_yellow(self, address, *args):
        """Handle yellow LED OSC message."""
        if args and self.serial_conn:
            state = int(args[0])
            cmd = f"YELLOW:{state}\n"
            self.serial_conn.write(cmd.encode())
            print(f"[OSC→Serial] {address} {state} → Arduino: {cmd.strip()}")

    def handle_led_green(self, address, *args):
        """Handle green LED OSC message."""
        if args and self.serial_conn:
            state = int(args[0])
            cmd = f"GREEN:{state}\n"
            self.serial_conn.write(cmd.encode())
            print(f"[OSC→Serial] {address} {state} → Arduino: {cmd.strip()}")

    def process_serial_messages(self):
        """Process messages from Arduino serial (call in loop)."""
        if not self.serial_conn or not self.serial_conn.in_waiting:
            return

        try:
            line = self.serial_conn.readline().decode('utf-8').strip()
            if not line or line == "READY":
                return

            # Convert serial messages to OSC (Arduino sends uppercase UP/DOWN)
            line_upper = line.upper()
            if line_upper == "UP":
                self.osc_client.send_message("/carpet/elevator/up", [])
                self.log.success("Button UP pressed")
                self._notify("✓ Button UP pressed")
            elif line_upper == "DOWN":
                self.osc_client.send_message("/carpet/elevator/down", [])
                self.log.success("Button DOWN pressed")
                self._notify("✓ Button DOWN pressed")
            else:
                self.log.warning(f"Unknown message: {line}")
                self._notify(f"⚠ Unknown: {line}")

        except Exception as e:
            self.log.error(f"Error processing serial: {e}")

    def set_led(self, color: str, value: int):
        """
        Set LED brightness using PWM.

        Args:
            color: 'red', 'yellow', or 'green'
            value: 0-255 (PWM brightness), or 0/1 for legacy compatibility
        """
        if not self.serial_conn:
            self.log.error("Arduino not connected")
            return

        # Convert legacy 0/1 to 0/255
        if value == 1:
            value = 255

        # Clamp to valid range
        value = max(0, min(255, value))

        cmd = f"{color.upper()}:{value}\n"
        try:
            self.serial_conn.write(cmd.encode())
            self.log.debug(f"LED {color.upper()} → {value}")
            self._notify(f"LED {color.upper()}: {value}")
        except Exception as e:
            self.log.error(f"Failed to set LED: {e}")
            self._notify(f"✗ LED error: {e}")

    def set_led_animation_mode(self, mode: str, direction: str = "up"):
        """
        Set LED animation mode.

        Args:
            mode: 'STABLE', 'TRANSITION', or 'OFF'
            direction: 'up' or 'down' (for TRANSITION mode)
        """
        self.log.info(f"LED animation mode: {mode} (direction: {direction})")

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

    def start_animation_thread(self):
        """Start the LED animation thread."""
        if self.animation_running:
            return

        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
        self.animation_thread.start()
        self.log.info("LED animation thread started")

    def _animation_loop(self):
        """Main LED animation loop (runs in background thread)."""
        start_time = time.time()

        while self.animation_running and self.running:
            elapsed = time.time() - start_time

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

    def _animate_stable(self, elapsed: float):
        """
        Stable animation: Slow sin-wave pulsing of green LED between 60% to 80%.

        Args:
            elapsed: Time elapsed since animation start (seconds)
        """
        # Very slow oscillation - 5 second period
        period = 5.0
        phase = (elapsed % period) / period * 2 * math.pi

        # Sin wave oscillates between -1 and 1
        # Map to 60% (153) to 80% (204)
        min_brightness = int(255 * 0.60)  # 153
        max_brightness = int(255 * 0.80)  # 204
        brightness_range = max_brightness - min_brightness

        # Calculate brightness using sin wave
        sin_value = math.sin(phase)  # -1 to 1
        normalized = (sin_value + 1) / 2  # 0 to 1
        brightness = int(min_brightness + normalized * brightness_range)

        # Set green LED, keep others off
        self.set_led("red", 0)
        self.set_led("yellow", 0)
        self.set_led("green", brightness)

    def _animate_transition_up(self, elapsed: float):
        """
        Transition UP animation: Flicker red → yellow → green quickly.
        Random brightnesses: 0%-20% for "off", 80%-100% for "on".

        Args:
            elapsed: Time elapsed since animation start (seconds)
        """
        # Quick flicker - change every 100ms
        flicker_period = 0.1
        step = int(elapsed / flicker_period) % 3  # 0, 1, 2 (red, yellow, green)

        # Random brightness for the active LED (80%-100%)
        on_brightness = random.randint(int(255 * 0.80), 255)
        # Random brightness for inactive LEDs (0%-20%)
        off_brightness = random.randint(0, int(255 * 0.20))

        if step == 0:  # Red
            self.set_led("red", on_brightness)
            self.set_led("yellow", off_brightness)
            self.set_led("green", off_brightness)
        elif step == 1:  # Yellow
            self.set_led("red", off_brightness)
            self.set_led("yellow", on_brightness)
            self.set_led("green", off_brightness)
        else:  # Green
            self.set_led("red", off_brightness)
            self.set_led("yellow", off_brightness)
            self.set_led("green", on_brightness)

    def _animate_transition_down(self, elapsed: float):
        """
        Transition DOWN animation: Flicker green → yellow → red quickly.
        Random brightnesses: 0%-20% for "off", 80%-100% for "on".

        Args:
            elapsed: Time elapsed since animation start (seconds)
        """
        # Quick flicker - change every 100ms
        flicker_period = 0.1
        step = int(elapsed / flicker_period) % 3  # 0, 1, 2 (green, yellow, red)

        # Random brightness for the active LED (80%-100%)
        on_brightness = random.randint(int(255 * 0.80), 255)
        # Random brightness for inactive LEDs (0%-20%)
        off_brightness = random.randint(0, int(255 * 0.20))

        if step == 0:  # Green
            self.set_led("red", off_brightness)
            self.set_led("yellow", off_brightness)
            self.set_led("green", on_brightness)
        elif step == 1:  # Yellow
            self.set_led("red", off_brightness)
            self.set_led("yellow", on_brightness)
            self.set_led("green", off_brightness)
        else:  # Red
            self.set_led("red", on_brightness)
            self.set_led("yellow", off_brightness)
            self.set_led("green", off_brightness)

    def run_forever(self):
        """
        Run processing loop forever (blocking).
        Call process_serial_messages() in a loop.
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
                self.process_serial_messages()
                time.sleep(0.01)  # 10ms loop

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

        self.cleanup_serial()

    def cleanup_serial(self):
        """Cleanup serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            # Turn off all LEDs
            try:
                self.serial_conn.write(b"RED:0\n")
                self.serial_conn.write(b"YELLOW:0\n")
                self.serial_conn.write(b"GREEN:0\n")
            except:
                pass

            self.serial_conn.close()
            print("✓ Serial connection closed")


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
