#!/usr/bin/env python3
"""
Test Process Monitoring - Verify core detects when Processing exits
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from carpet_hotel import CarpetHotelCore

def test_monitoring():
    """Test that core detects when Processing exits unexpectedly."""
    print("="*60)
    print("Testing Process Monitoring")
    print("="*60)

    core = CarpetHotelCore()

    print("\n[1/4] Starting Processing...")
    if not core.start_processing(displays=[1], enable_keyboard=True):
        print("✗ Failed to start")
        return False

    print("✓ Started")
    print(f"Core state: pde_running={core.pde_running}")

    print("\n[2/4] Waiting 3 seconds...")
    time.sleep(3)

    if not core.is_running():
        print("✗ Processing died immediately")
        return False

    print("✓ Still running")
    print(f"Core state: pde_running={core.pde_running}")

    print("\n[3/4] Close the Processing window now (press ESC or close window)")
    print("     Waiting up to 10 seconds for detection...")

    # Poll for up to 10 seconds
    detected = False
    for i in range(20):  # 20 * 0.5s = 10s
        time.sleep(0.5)
        if not core.pde_running:
            print(f"\n✓ Core detected Processing exit after {(i+1)*0.5:.1f}s")
            detected = True
            break
        if i % 2 == 0:
            print(".", end="", flush=True)

    if not detected:
        print("\n✗ Core did not detect Processing exit")
        print("   Stopping manually...")
        core.stop_processing()
        return False

    print(f"\nCore state: pde_running={core.pde_running}")
    print(f"Process alive: {core.processing.is_running() if core.processing else 'N/A'}")

    print("\n[4/4] Cleanup...")
    core.stop_all()

    print("\n" + "="*60)
    print("✓ Process monitoring test PASSED")
    print("="*60)

    return True

if __name__ == "__main__":
    try:
        success = test_monitoring()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
