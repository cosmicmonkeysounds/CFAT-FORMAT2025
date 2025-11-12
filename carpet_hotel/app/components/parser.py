#!/usr/bin/env python3
"""
Carpet Hotel CLI Parser
=======================

Command-line argument parsing for Carpet Hotel launcher.
Separated from core logic to keep code modular.

Usage:
    python carpet_hotel_parser.py [options]

Or import and use:
    from carpet_hotel_parser import main
    main()
"""

import sys
import argparse
from carpet_hotel_core import CarpetHotelCore
from components.supercollider import CarpetHotelSuperCollider


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Carpet Hotel - Launch coordinator for SuperCollider and Processing (Cross-Platform)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python components/parser.py                    # Show help
  python components/parser.py --build            # Build Processing executable
  python components/parser.py --sc-only          # Run SuperCollider only
  python components/gui.py                       # Launch GUI control panel (recommended)

Requirements:
  SuperCollider and Processing installed

Environment Variables:
  SCLANG_PATH       Path to sclang executable
  PROCESSING_JAVA   Path to processing-java command
        """
    )

    parser.add_argument('--build', action='store_true',
                       help='Build Processing executable instead of running')
    parser.add_argument('--sc-only', action='store_true',
                       help='Run SuperCollider only (for testing)')
    parser.add_argument('--audio-device', type=str,
                       help='Audio device name for SuperCollider (e.g. "MacBook Pro Speakers")')
    parser.add_argument('--sample-rate', type=int,
                       help='Audio sample rate in Hz (e.g. 44100, 48000, 96000). Auto-detected if not specified.')
    parser.add_argument('--list-devices', action='store_true',
                       help='List available audio devices and exit')
    parser.add_argument('--test-mode', action='store_true',
                       help='Enable test mode (keyboard/mouse input in Processing)')
    parser.add_argument('--osc-control', action='store_true',
                       help='Enable OSC control mode (control from Python terminal)')
    parser.add_argument('--displays', type=str,
                       help='Display numbers for windows (e.g., "1,2,3")')
    parser.add_argument('--arduino-port', type=str,
                       help='Arduino serial port (e.g., "/dev/cu.usbmodem..." or "auto")')

    return parser.parse_args()


def main():
    """Main entry point for CLI."""
    args = parse_arguments()

    # List devices mode
    if args.list_devices:
        print("\nAvailable audio devices:")
        for device in CarpetHotelSuperCollider.detect_devices():
            print(f"  - {device}")
        sys.exit(0)

    # No GUI mode - if no args provided, show help
    has_config_args = any([
        args.audio_device,
        args.test_mode,
        args.osc_control,
        args.displays,
        args.build,
        args.sc_only,
        args.arduino_port
    ])

    if not has_config_args:
        print("\n" + "="*60)
        print("  CARPET HOTEL")
        print("="*60)
        print("\nFor graphical control panel, run:")
        print("  python components/gui.py")
        print("\nFor command-line operation, use:")
        print("  python components/parser.py --help")
        print()
        sys.exit(0)

    # Parse configuration from arguments
    audio_device = args.audio_device
    sample_rate = args.sample_rate if hasattr(args, 'sample_rate') else None

    # Map flags to configuration
    enable_keyboard = args.test_mode
    enable_python_terminal = args.osc_control
    enable_osc_external = args.osc_control  # External OSC shares the same flag

    # Parse displays
    displays = None
    if args.displays:
        try:
            displays = [int(d.strip()) for d in args.displays.split(',')]
        except ValueError:
            print(f"Error: Invalid display format '{args.displays}'. Use comma-separated numbers like '1,2,3'")
            sys.exit(1)

    # Arduino port
    arduino_port = args.arduino_port if args.arduino_port else 'auto'
    enable_arduino = not args.sc_only  # Disable Arduino in SC-only mode

    # Create core instance
    core = CarpetHotelCore()

    # Execute requested action
    try:
        if args.build:
            print("Build mode not yet implemented in new architecture")
            sys.exit(1)

        # SC-only mode
        if args.sc_only:
            print("Starting SuperCollider only...")
            if core.start_supercollider(audio_device, sample_rate):
                print("\nSuperCollider running. Press Ctrl+C to stop...")
                import time
                try:
                    while core.sc_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            success = core.stop_supercollider()

        # Full mode
        else:
            success = core.start_all(
                audio_device=audio_device,
                sample_rate=sample_rate,
                displays=displays,
                enable_keyboard=enable_keyboard,
                serial_port=arduino_port,
                enable_arduino=enable_arduino
            )

            if success:
                print("\nCarpet Hotel running. Press Ctrl+C to stop...")
                import time
                try:
                    while core.is_running():
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass

            core.stop_all()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        core.stop_all()
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        core.stop_all()
        sys.exit(1)


if __name__ == '__main__':
    main()
