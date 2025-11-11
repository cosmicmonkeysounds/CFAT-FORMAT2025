#!/usr/bin/env python3
"""
Test script for the elevator control panel Arduino
"""

import serial
import serial.tools.list_ports
import time
import sys


def select_port():
    """Prompt user to select a serial port"""
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("No serial ports found!")
        return None

    print("\nAvailable serial ports:")
    print("="*60)
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port.device}: {port.description}")
    print("="*60)

    while True:
        try:
            choice = input("\nEnter port number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None

            port_num = int(choice)
            if 1 <= port_num <= len(ports):
                return ports[port_num - 1].device
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(ports)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return None


def test_elevator_control(port=None):
    """Test the elevator control panel"""

    if port is None:
        port = select_port()
        if port is None:
            print("No port selected.")
            return

    print(f"\nConnecting to Arduino on {port}...")

    try:
        # Open serial connection
        ser = serial.Serial(port, 115200, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset

        # Wait for READY message
        print("Waiting for Arduino READY message...")
        start_time = time.time()
        while time.time() - start_time < 5:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                print(f"Arduino: {line}")
                if line == "READY":
                    break

        print("\nArduino connected!")
        print("\nTest controls:")
        print("  Press UP or DOWN buttons on the hardware")
        print("  Type 'r', 'y', or 'g' to toggle RED, YELLOW, or GREEN LEDs")
        print("  Type 'q' to quit")
        print("\n" + "="*50 + "\n")

        # LED states
        led_states = {'RED': False, 'YELLOW': False, 'GREEN': False}

        # Non-blocking input setup
        import select

        while True:
            # Check for button presses from Arduino
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"Button pressed: {line.upper()}")

            # Check for keyboard input (Unix/Mac only)
            if sys.platform != 'win32':
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 'q':
                        break
                    elif key == 'r':
                        led_states['RED'] = not led_states['RED']
                        cmd = f"RED:{1 if led_states['RED'] else 0}\n"
                        ser.write(cmd.encode())
                        print(f"LED command sent: {cmd.strip()}")
                    elif key == 'y':
                        led_states['YELLOW'] = not led_states['YELLOW']
                        cmd = f"YELLOW:{1 if led_states['YELLOW'] else 0}\n"
                        ser.write(cmd.encode())
                        print(f"LED command sent: {cmd.strip()}")
                    elif key == 'g':
                        led_states['GREEN'] = not led_states['GREEN']
                        cmd = f"GREEN:{1 if led_states['GREEN'] else 0}\n"
                        ser.write(cmd.encode())
                        print(f"LED command sent: {cmd.strip()}")

            time.sleep(0.01)  # Small delay to prevent CPU spinning

        ser.close()
        print("\nDisconnected.")

    except serial.SerialException as e:
        print(f"Error: {e}")
        print("Make sure the Arduino is connected and the correct port is specified.")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_elevator_control(sys.argv[1])
    else:
        test_elevator_control()
