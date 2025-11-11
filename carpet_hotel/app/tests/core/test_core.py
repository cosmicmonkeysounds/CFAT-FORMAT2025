#!/usr/bin/env python3
"""
Test Core Coordinator
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from carpet_hotel_core import CarpetHotelCore

def main():
    print("="*60)
    print("Testing Core Coordinator")
    print("="*60 + "\n")

    # Test 1: Initialize core
    print("[1/3] Initializing core coordinator...")
    try:
        core = CarpetHotelCore()
        print("✓ Core initialized")
        status = core.get_status()
        print(f"  SuperCollider: {status['supercollider']}")
        print(f"  Processing: {status['processing']}")
        print(f"  Arduino: {status['arduino']}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 2: Check status
    print("\n[2/3] Checking core status...")
    try:
        is_running = core.is_running()
        print(f"✓ Core running status: {is_running}")
        assert not is_running, "Core should not be running yet"
    except Exception as e:
        print(f"✗ Status check failed: {e}")
        return False

    # Test 3: Verify methods exist
    print("\n[3/3] Verifying core methods...")
    try:
        assert hasattr(core, 'start_supercollider'), "Missing start_supercollider"
        assert hasattr(core, 'start_processing'), "Missing start_processing"
        assert hasattr(core, 'start_arduino'), "Missing start_arduino"
        assert hasattr(core, 'start_all'), "Missing start_all"
        assert hasattr(core, 'stop_all'), "Missing stop_all"
        print("✓ All core methods present")
    except AssertionError as e:
        print(f"✗ Method check failed: {e}")
        return False

    print("\n" + "="*60)
    print("✓ All core tests passed!")
    print("="*60)
    print("\nNOTE: This only tests initialization and API.")
    print("To test full integration:")
    print("  1. Configure audio device (see AUDIO_SETUP.md)")
    print("  2. Ensure video files are in data/")
    print("  3. Run: python3 carpet_hotel.py")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
