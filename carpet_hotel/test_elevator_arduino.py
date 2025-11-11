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
        print("  Type '1' for STABLE animation (green pulse)")
        print("  Type '2' for TRANSITION animation (RGB cycle)")
        print("  Type '0' to turn OFF all LEDs")
        print("  Type 'p' followed by number to set period (e.g., 'p500')")
        print("  Type 'q' to quit")
        print("\n" + "="*50 + "\n")

        # Animation state
        period_input = ""

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
                    elif key == '1':
                        cmd = "ANIM:STABLE\n"
                        ser.write(cmd.encode())
                        print(f"Animation command sent: {cmd.strip()}")
                    elif key == '2':
                        cmd = "ANIM:TRANSITION\n"
                        ser.write(cmd.encode())
                        print(f"Animation command sent: {cmd.strip()}")
                    elif key == '0':
                        cmd = "ANIM:OFF\n"
                        ser.write(cmd.encode())
                        print(f"Animation command sent: {cmd.strip()}")
                    elif key == 'p':
                        period_input = ""
                        print("Enter period in ms (then press Enter): ", end='', flush=True)
                    elif key.isdigit() and period_input is not None:
                        period_input += key
                        print(key, end='', flush=True)
                    elif key == '\n' and period_input:
                        try:
                            period = int(period_input)
                            cmd = f"PERIOD:{period}\n"
                            ser.write(cmd.encode())
                            print(f"\nPeriod command sent: {cmd.strip()}")
                        except ValueError:
                            print("\nInvalid period")
                        period_input = ""

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
