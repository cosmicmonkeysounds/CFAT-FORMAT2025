#!/usr/bin/env python3
"""
Standalone test for LED animation system.
Tests if animation loop runs and sends commands.
"""

import sys
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from components.utils.utils import find_arduino_port
from components.serial_broker import SerialBroker
from components.arduino import CarpetHotelArduino

def test_serial_broker_direct():
    """Test 1: Direct serial broker communication."""
    print("\n" + "="*60)
    print("TEST 1: Direct Serial Broker Communication")
    print("="*60)

    port = find_arduino_port()
    if not port:
        print("✗ No Arduino found")
        return False

    print(f"✓ Found Arduino on {port}")

    broker = SerialBroker(port)
    if not broker.connect():
        print("✗ Failed to connect")
        return False

    print("✓ Connected to Arduino")

    # Send test commands directly
    print("\nSending test LED commands...")
    for i in range(5):
        brightness = 50 + i * 50
        print(f"  [{i+1}/5] RED:{brightness}")
        broker.write_led("red", brightness)
        time.sleep(0.5)

    # Turn off
    print("  Turning off RED")
    broker.write_led("red", 0)
    time.sleep(0.5)

    broker.disconnect()
    print("✓ Test 1 PASSED - Broker can send LED commands\n")
    return True


def test_arduino_animation_thread():
    """Test 2: Arduino class animation thread."""
    print("\n" + "="*60)
    print("TEST 2: Arduino Animation Thread")
    print("="*60)

    arduino = CarpetHotelArduino(serial_port="auto")

    if not arduino.connect():
        print("✗ Failed to connect Arduino")
        return False

    print("✓ Arduino connected")

    # Check animation thread status
    print(f"\nAnimation thread status:")
    print(f"  animation_running: {arduino.animation_running}")
    print(f"  animation_thread: {arduino.animation_thread}")
    print(f"  animation_thread.is_alive(): {arduino.animation_thread.is_alive() if arduino.animation_thread else 'N/A'}")
    print(f"  animation_mode: {arduino.animation_mode}")

    if not arduino.animation_running:
        print("✗ Animation thread not running!")
        arduino.disconnect()
        return False

    print("✓ Animation thread is running")

    # Test mode changes
    print("\nTesting animation modes...")

    # Test STABLE mode
    print("\n  Setting mode: STABLE")
    arduino.set_led_animation_mode("STABLE")
    print(f"  Current mode: {arduino.animation_mode}")
    print("  Waiting 3 seconds to observe...")
    time.sleep(3)

    # Test TRANSITION_UP mode
    print("\n  Setting mode: TRANSITION_UP")
    arduino.set_led_animation_mode("TRANSITION", direction="up")
    print(f"  Current mode: {arduino.animation_mode}")
    print("  Waiting 2 seconds to observe...")
    time.sleep(2)

    # Back to STABLE
    print("\n  Setting mode: STABLE")
    arduino.set_led_animation_mode("STABLE")
    print(f"  Current mode: {arduino.animation_mode}")
    print("  Waiting 2 seconds to observe...")
    time.sleep(2)

    # Turn off
    print("\n  Setting mode: OFF")
    arduino.set_led_animation_mode("OFF")
    print(f"  Current mode: {arduino.animation_mode}")
    time.sleep(1)

    arduino.disconnect()
    print("\n✓ Test 2 PASSED - Animation thread can change modes\n")
    return True


def test_manual_led_control():
    """Test 3: Manual LED control through Arduino class."""
    print("\n" + "="*60)
    print("TEST 3: Manual LED Control")
    print("="*60)

    arduino = CarpetHotelArduino(serial_port="auto")

    if not arduino.connect():
        print("✗ Failed to connect Arduino")
        return False

    print("✓ Arduino connected")

    # Turn off animation to test manual control
    arduino.set_led_animation_mode("OFF")
    time.sleep(0.5)

    print("\nTesting manual LED control...")

    # Test each LED
    leds = ["red", "yellow", "green"]
    for led in leds:
        print(f"\n  Testing {led.upper()} LED...")
        for brightness in [0, 64, 128, 192, 255, 128, 64, 0]:
            print(f"    {led.upper()}:{brightness}")
            arduino.set_led(led, brightness)
            time.sleep(0.3)

    print("\n  All LEDs off")
    arduino.set_led("red", 0)
    arduino.set_led("yellow", 0)
    arduino.set_led("green", 0)
    time.sleep(0.5)

    arduino.disconnect()
    print("\n✓ Test 3 PASSED - Manual control works\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LED ANIMATION DIAGNOSTIC TESTS")
    print("="*60)
    print("\nThese tests will:")
    print("1. Test direct serial communication (bypassing Arduino class)")
    print("2. Test Arduino animation thread")
    print("3. Test manual LED control")
    print("\nWatch the LEDs on your Arduino!")
    print("="*60)

    input("\nPress ENTER to start...")

    results = []

    # Run tests
    try:
        results.append(("Serial Broker Direct", test_serial_broker_direct()))
        time.sleep(2)

        results.append(("Animation Thread", test_arduino_animation_thread()))
        time.sleep(2)

        results.append(("Manual LED Control", test_manual_led_control()))

    except KeyboardInterrupt:
        print("\n\n✗ Tests interrupted by user")
        return
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")
    print("="*60 + "\n")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("\nIf you saw LEDs changing during tests, the hardware works!")
        print("If LEDs didn't change, check:")
        print("  1. LED wiring (D3=GREEN, D5=YELLOW, D6=RED)")
        print("  2. Serial port selection")
        print("  3. Arduino code uploaded correctly")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nCheck the output above for details.")

    print()


if __name__ == "__main__":
    main()
