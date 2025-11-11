#!/usr/bin/env python3
"""
Quick cleanup test - Start Processing once and verify it stops cleanly
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from carpet_hotel_pde import CarpetHotelProcessing

def test_cleanup():
    """Test that Processing starts and stops cleanly."""
    print("="*60)
    print("Testing Processing Cleanup")
    print("="*60)

    print("\n[1/3] Starting Processing...")
    pde = CarpetHotelProcessing(displays=[1])

    if not pde.start():
        print("✗ Failed to start")
        return False

    print("✓ Started")

    print("\n[2/3] Waiting 3 seconds...")
    time.sleep(3)

    if not pde.is_running():
        print("✗ Process died")
        return False

    print("✓ Still running")

    print("\n[3/3] Stopping...")
    if not pde.stop():
        print("✗ Failed to stop")
        return False

    time.sleep(2)

    if pde.is_running():
        print("✗ Still running after stop!")
        return False

    print("✓ Stopped cleanly")

    print("\n" + "="*60)
    print("✓ Cleanup test PASSED")
    print("="*60)

    return True

if __name__ == "__main__":
    success = test_cleanup()
    sys.exit(0 if success else 1)
