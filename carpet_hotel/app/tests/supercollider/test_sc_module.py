#!/usr/bin/env python3
"""
Simple test to verify SuperCollider module works.
Starts SC, waits for init, then stops.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from carpet_hotel_scd import CarpetHotelSuperCollider

def main():
    print("\n" + "="*60)
    print("Testing SuperCollider Module")
    print("="*60 + "\n")

    # Create instance
    sc = CarpetHotelSuperCollider()

    # Start
    print("Starting SuperCollider...")
    if sc.start():
        print("\n✓ SuperCollider started successfully!")

        # Let it run for a few seconds
        print("\nRunning for 5 seconds...")
        for i in range(5):
            time.sleep(1)
            if not sc.is_running():
                print(f"✗ SuperCollider died after {i+1} seconds!")
                return False
            print(f"  {i+1}/5 - Still running...")

        # Stop
        print("\nStopping SuperCollider...")
        if sc.stop():
            print("✓ Stopped cleanly")
        else:
            print("✗ Failed to stop cleanly")

        print("\n" + "="*60)
        print("✓ Test Passed")
        print("="*60 + "\n")
        return True
    else:
        print("\n✗ Failed to start SuperCollider")
        print("\n" + "="*60)
        print("✗ Test Failed")
        print("="*60 + "\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
