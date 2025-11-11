#!/usr/bin/env python3
"""
Elevator Control Panel OSC Bridge

Bridges between Arduino serial messages and OSC messages for the carpet_hotel system.
Converts button presses to OSC messages and OSC LED commands to serial.

OSC Messages:
  Sent (when buttons pressed):
    /carpet/elevator/up
    /carpet/elevator/down

  Received (LED control):
    /carpet/elevator/led/red [0 or 1]
    /carpet/elevator/led/yellow [0 or 1]
    /carpet/elevator/led/green [0 or 1]
"""

import serial
import serial.tools.list_ports
import time
import sys
import argparse
import threading
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


class ElevatorOSCBridge:
    def __init__(self, serial_port, osc_send_host="127.0.0.1", osc_send_port=12000,
                 osc_recv_port=12002):
        """
        Initialize the elevator OSC bridge

        Args:
            serial_port: Serial port for Arduino (e.g., '/dev/cu.usbmodem14201' or 'COM3')
            osc_send_host: Host to send OSC messages to (default: localhost)
            osc_send_port: Port to send OSC messages to (default: 12000 - Processing)
            osc_recv_port: Port to receive OSC messages on (default: 12002)
        """
        self.serial_port = serial_port
        self.osc_send_host = osc_send_host
        self.osc_send_port = osc_send_port
        self.osc_recv_port = osc_recv_port

        self.serial_conn = None
        self.osc_client = None
        self.osc_server = None
        self.osc_thread = None
        self.running = False

    def find_arduino_port(self):
        """Find the Arduino port automatically"""
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if 'Adafruit' in port.description or 'Arduino' in port.description:
                return port.device
        return None

    def setup_serial(self):
        """Set up serial connection to Arduino"""
        if self.serial_port is None:
            self.serial_port = self.find_arduino_port()
            if self.serial_port is None:
                print("ERROR: No Arduino found. Available ports:")
                for p in serial.tools.list_ports.comports():
                    print(f"  {p.device}: {p.description}")
                return False

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
                        print("✓ Arduino connected and ready")
                        return True

            print("WARNING: Arduino did not send READY message, but continuing...")
            return True

        except serial.SerialException as e:
            print(f"ERROR: Could not connect to Arduino: {e}")
            return False

    def setup_osc(self):
        """Set up OSC client and server"""
        try:
            # OSC client to send messages
            self.osc_client = udp_client.SimpleUDPClient(
                self.osc_send_host, self.osc_send_port
            )
            print(f"✓ OSC client ready (sending to {self.osc_send_host}:{self.osc_send_port})")

            # OSC server to receive messages
            dispatcher = Dispatcher()
            dispatcher.map("/carpet/elevator/led/red", self.handle_led_red)
            dispatcher.map("/carpet/elevator/led/yellow", self.handle_led_yellow)
            dispatcher.map("/carpet/elevator/led/green", self.handle_led_green)
            dispatcher.map("/carpet/elevator/led/*", self.handle_led_all)  # Catch-all

            self.osc_server = ThreadingOSCUDPServer(
                ("127.0.0.1", self.osc_recv_port), dispatcher
            )
            print(f"✓ OSC server ready (receiving on port {self.osc_recv_port})")

            return True

        except Exception as e:
            print(f"ERROR: Could not set up OSC: {e}")
            return False

    def handle_led_red(self, address, *args):
        """Handle red LED OSC message"""
        if args and self.serial_conn:
            state = int(args[0])
            cmd = f"RED:{state}\n"
            self.serial_conn.write(cmd.encode())
            print(f"[OSC→Serial] {address} {state} → Arduino: {cmd.strip()}")

    def handle_led_yellow(self, address, *args):
        """Handle yellow LED OSC message"""
        if args and self.serial_conn:
            state = int(args[0])
            cmd = f"YELLOW:{state}\n"
            self.serial_conn.write(cmd.encode())
            print(f"[OSC→Serial] {address} {state} → Arduino: {cmd.strip()}")

    def handle_led_green(self, address, *args):
        """Handle green LED OSC message"""
        if args and self.serial_conn:
            state = int(args[0])
            cmd = f"GREEN:{state}\n"
            self.serial_conn.write(cmd.encode())
            print(f"[OSC→Serial] {address} {state} → Arduino: {cmd.strip()}")

    def handle_led_all(self, address, *args):
        """Catch-all handler for LED messages"""
        print(f"[OSC] Unhandled LED message: {address} {args}")

    def process_serial_messages(self):
        """Process messages from Arduino serial"""
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
            print(f"ERROR processing serial message: {e}")

    def run(self):
        """Main run loop"""
        if not self.setup_serial():
            return False

        if not self.setup_osc():
            return False

        # Start OSC server in background thread
        self.osc_thread = threading.Thread(target=self.osc_server.serve_forever)
        self.osc_thread.daemon = True
        self.osc_thread.start()

        print("\n" + "="*60)
        print("Elevator OSC Bridge Running")
        print("="*60)
        print(f"Serial: {self.serial_port} (115200 baud)")
        print(f"OSC Send: {self.osc_send_host}:{self.osc_send_port}")
        print(f"OSC Recv: 127.0.0.1:{self.osc_recv_port}")
        print("\nButton presses will be sent as OSC messages:")
        print("  UP button   → /carpet/elevator/up")
        print("  DOWN button → /carpet/elevator/down")
        print("\nLED control via OSC messages:")
        print("  /carpet/elevator/led/red [0/1]")
        print("  /carpet/elevator/led/yellow [0/1]")
        print("  /carpet/elevator/led/green [0/1]")
        print("\nPress Ctrl+C to stop")
        print("="*60 + "\n")

        self.running = True

        try:
            while self.running:
                self.process_serial_messages()
                time.sleep(0.01)  # 10ms loop

        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.running = False

        if self.osc_server:
            self.osc_server.shutdown()
            print("✓ OSC server stopped")

        if self.serial_conn and self.serial_conn.is_open:
            # Turn off all LEDs
            self.serial_conn.write(b"RED:0\n")
            self.serial_conn.write(b"YELLOW:0\n")
            self.serial_conn.write(b"GREEN:0\n")
            self.serial_conn.close()
            print("✓ Serial connection closed")


def main():
    parser = argparse.ArgumentParser(description='Elevator Control Panel OSC Bridge')
    parser.add_argument('--port', '-p', help='Serial port (auto-detect if not specified)')
    parser.add_argument('--osc-host', default='127.0.0.1',
                        help='OSC destination host (default: 127.0.0.1)')
    parser.add_argument('--osc-send-port', type=int, default=12000,
                        help='OSC destination port (default: 12000)')
    parser.add_argument('--osc-recv-port', type=int, default=12002,
                        help='OSC receive port (default: 12002)')
    parser.add_argument('--list-ports', action='store_true',
                        help='List available serial ports and exit')

    args = parser.parse_args()

    if args.list_ports:
        print("Available serial ports:")
        for port in serial.tools.list_ports.comports():
            print(f"  {port.device}: {port.description}")
        return

    bridge = ElevatorOSCBridge(
        serial_port=args.port,
        osc_send_host=args.osc_host,
        osc_send_port=args.osc_send_port,
        osc_recv_port=args.osc_recv_port
    )

    bridge.run()


if __name__ == "__main__":
    main()
