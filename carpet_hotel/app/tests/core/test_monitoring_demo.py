#!/usr/bin/env python3
"""
Demo: Process monitoring automatically detects when Processing exits

This demo shows that the core monitoring thread works.
Start Processing, then close it, and watch the core detect it.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from carpet_hotel_core import CarpetHotelCore

def demo():
    """Demo process monitoring."""
    print("="*70)
    print("  PROCESS MONITORING DEMO")
    print("="*70)
    print("\nThis demo shows that the core automatically detects")
    print("when Processing exits (via ESC, window close, or crash).")
    print()

    core = CarpetHotelCore()

    print("[1] Starting Processing...")
    if not core.start_processing(displays=[1], enable_keyboard=True):
        print("✗ Failed to start")
        return

    print(f"✓ Processing started (monitoring enabled)")
    print(f"   Core state: pde_running = {core.pde_running}")
    print()

    print("[2] Processing is running. You can:")
    print("    - Press ESC in the Processing window")
    print("    - Click the window close button (X)")
    print("    - Force quit (Cmd+Q)")
    print()
    print("    The core will detect the exit automatically!")
    print()
    print("    Watching for exit (will check for 60 seconds)...")
    print()

    # Monitor for exit
    start_time = time.time()
    last_check = time.time()

    while time.time() - start_time < 60:
        time.sleep(0.5)

        # Print dot every 2 seconds to show we're alive
        if time.time() - last_check >= 2:
            print(".", end="", flush=True)
            last_check = time.time()

        # Check if Processing exited
        if not core.pde_running:
            elapsed = time.time() - start_time
            print(f"\n\n✓ Core detected Processing exit after {elapsed:.1f} seconds!")
            print(f"   Core state: pde_running = {core.pde_running}")
            print()
            print("This is exactly what the GUI sees when polling state.")
            print("The GUI will update within 0.5 seconds of this detection.")
            print()
            print("="*70)
            print("  DEMO COMPLETE - Monitoring works!")
            print("="*70)
            return

    print("\n\nTimeout - Processing still running after 60 seconds")
    print("Stopping manually...")
    core.stop_processing()

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted")
        sys.exit(0)
