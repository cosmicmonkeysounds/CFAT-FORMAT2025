#!/usr/bin/env python3
"""
Test OSC Audio Flow - Verify Processing → Core → SuperCollider communication

This test verifies the complete OSC chain:
1. SuperCollider starts and loads audio
2. Processing starts and sends OSC to Core
3. Core receives and forwards to SuperCollider
4. Audio should play!
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from carpet_hotel import CarpetHotelCore

def test_audio_osc():
    """Test complete audio OSC flow."""
    print("="*70)
    print("  AUDIO OSC FLOW TEST")
    print("="*70)
    print("\nThis test verifies:")
    print("  1. SuperCollider starts and boots audio server")
    print("  2. Processing starts with OSC enabled")
    print("  3. Core sets up OSC routing (Processing ↔ Core ↔ SC)")
    print("  4. Core sends initial scene to SC")
    print("  5. Audio should play!")
    print()

    core = CarpetHotelCore()

    # Step 1: Start SuperCollider
    print("[1/4] Starting SuperCollider...")
    if not core.start_supercollider():
        print("✗ Failed to start SuperCollider")
        return False

    print("✓ SuperCollider running")
    print(f"   State: sc_running={core.sc_running}")
    print()

    # Step 2: Start Processing
    print("[2/4] Starting Processing...")
    if not core.start_processing(displays=[1], enable_keyboard=True):
        print("✗ Failed to start Processing")
        core.stop_supercollider()
        return False

    print("✓ Processing running")
    print(f"   State: pde_running={core.pde_running}")
    print()

    # Step 3: Verify OSC setup
    print("[3/4] Verifying OSC communication...")
    if core.osc_server:
        print("✓ OSC server running (listening from Processing)")
    else:
        print("✗ OSC server not running")
        core.stop_all()
        return False

    if core.sc_client:
        print("✓ OSC client ready (sending to SuperCollider)")
    else:
        print("✗ OSC client not ready")
        core.stop_all()
        return False

    print(f"   Core state: scene={core.current_scene}, volume={int(core.master_volume*100)}%")
    print()

    # Step 4: Audio should be playing
    print("[4/4] Audio test")
    print("✓ All systems running!")
    print()
    print("🎵 AUDIO SHOULD BE PLAYING NOW 🎵")
    print()
    print("You should hear the audio piece playing.")
    print("The carpet audio loops should be audible.")
    print()
    print("Press Ctrl+C to stop when ready...")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")

    # Cleanup
    print("\nCleaning up...")
    core.stop_all()

    print()
    print("="*70)
    print("  TEST COMPLETE")
    print("="*70)
    print()
    print("Did you hear audio? If yes, the OSC flow is working!")
    print("If no audio, check:")
    print("  - SuperCollider audio device settings")
    print("  - System audio output is not muted")
    print("  - Check SuperCollider console for errors")
    print()

    return True

if __name__ == "__main__":
    try:
        test_audio_osc()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
