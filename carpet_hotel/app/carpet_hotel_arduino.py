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
from typing import Optional
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

from utils import find_arduino_port, detect_serial_ports


class CarpetHotelArduino:
    """
    Arduino/Elevator control panel manager.
    """

    def __init__(self, serial_port: Optional[str] = None,
                 osc_send_host: str = "127.0.0.1",
                 osc_send_port: int = 12000,
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

            # Convert serial messages to OSC
            if line == "up":
                self.osc_client.send_message("/carpet/elevator/up", [])
                print(f"[Serial→OSC] Button UP → /carpet/elevator/up")
            elif line == "down":
                self.osc_client.send_message("/carpet/elevator/down", [])
                print(f"[Serial→OSC] Button DOWN → /carpet/elevator/down")
            else:
                print(f"[Serial] Unknown message: {line}")

        except Exception as e:
            print(f"✗ Error processing serial message: {e}")

    def set_led(self, color: str, state: int):
        """
        Set LED state directly.

        Args:
            color: 'red', 'yellow', or 'green'
            state: 0 (off) or 1 (on)
        """
        if not self.serial_conn:
            print("✗ Arduino not connected")
            return

        cmd = f"{color.upper()}:{state}\n"
        self.serial_conn.write(cmd.encode())

    def set_led_animation_mode(self, mode: str):
        """
        Set LED animation mode.

        Args:
            mode: 'STABLE', 'TRANSITION', or 'OFF'
        """
        # Map modes to LED states
        if mode == "STABLE":
            # Green on, others off
            self.set_led("red", 0)
            self.set_led("yellow", 0)
            self.set_led("green", 1)
        elif mode == "TRANSITION":
            # Yellow blinking
            self.set_led("red", 0)
            self.set_led("yellow", 1)
            self.set_led("green", 0)
        elif mode == "OFF":
            # All off
            self.set_led("red", 0)
            self.set_led("yellow", 0)
            self.set_led("green", 0)

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
