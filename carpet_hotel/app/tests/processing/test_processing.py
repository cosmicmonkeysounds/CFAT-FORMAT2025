#!/usr/bin/env python3
"""
Test Processing wrapper
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.processing import CarpetHotelProcessing
from components.utils.utils import find_processing_java, detect_displays

def main():
    print("="*60)
    print("Testing Processing Wrapper")
    print("="*60 + "\n")

    # Test 1: Find processing-java
    print("[1/3] Finding processing-java...")
    processing_java = find_processing_java()
    if processing_java:
        print(f"✓ Found: {processing_java}")
    else:
        print("✗ processing-java not found!")
        print("  Install Processing from https://processing.org/download")
        return False

    # Test 2: Detect displays
    print("\n[2/3] Detecting displays...")
    displays = detect_displays()
    print(f"✓ Found {len(displays)} display(s):")
    for display in displays:
        main_marker = " [MAIN]" if display.get("main") else ""
        print(f"  {display['index']}: {display['name']}{main_marker}")
        if 'resolution' in display:
            print(f"     Resolution: {display['resolution'][0]}x{display['resolution'][1]}")

    # Test 3: Initialize wrapper
    print("\n[3/3] Initializing Processing wrapper...")
    try:
        pde = CarpetHotelProcessing()
        print("✓ Processing wrapper initialized")
        print(f"  Displays: {pde.displays}")
        print(f"  Keyboard: {pde.enable_keyboard}")
        print(f"  Sketch dir: {pde.sketch_dir}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False

    print("\n" + "="*60)
    print("✓ All Processing tests passed!")
    print("="*60)
    print("\nNOTE: To test video display, you need:")
    print("  1. carpet_hotel_video.pde in the app directory")
    print("  2. Video files in data/ folder")
    print("  3. Run: cd app && processing-java --sketch=. --run")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
