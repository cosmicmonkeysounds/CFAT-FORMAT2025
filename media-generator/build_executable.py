#!/usr/bin/env python3
"""
Build script for creating standalone executables using PyInstaller.

Usage:
    python3 build_executable.py

This will create executables for your current platform in the dist/ directory.
"""

import sys
import platform
import subprocess
from pathlib import Path


def build_executable():
    """Build standalone executable using PyInstaller."""

    print("=" * 70)
    print("Media Generator - Executable Build Script")
    print("=" * 70)
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version.split()[0]}")
    print()

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller not found!")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

    # Determine executable name based on platform
    system = platform.system()
    if system == "Windows":
        exe_name = "media-generator.exe"
    else:
        exe_name = "media-generator"

    print(f"\nBuilding executable: {exe_name}")
    print("-" * 70)

    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable file
        "--name", exe_name.replace(".exe", ""),  # Output name
        "--clean",  # Clean cache before building
        "--noconfirm",  # Replace output directory without confirmation
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "cv2",
        "--hidden-import", "numpy",
        "--hidden-import", "PIL",
        "--hidden-import", "scipy.signal",
        "--hidden-import", "scipy.io.wavfile",
        # Entry point
        "media_generator/__main__.py",
    ]

    # Add console flag (no console window on Windows for GUI apps - but we want console)
    # By default PyInstaller shows console, which is what we want

    print(f"Running: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True)

        print("\n" + "=" * 70)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 70)
        print(f"\nExecutable location:")
        print(f"  dist/{exe_name}")
        print(f"\nYou can now distribute this file to users.")
        print(f"They don't need Python or any dependencies installed.")
        print()

        if system == "Darwin":  # macOS
            print("macOS Note:")
            print("  Users may need to allow the app in System Preferences > Security")
            print("  Or run: xattr -cr dist/media-generator")
            print()
        elif system == "Linux":
            print("Linux Note:")
            print("  Make executable: chmod +x dist/media-generator")
            print()

        print("To create executables for other platforms:")
        print("  - Run this script on each target platform (Windows, macOS, Linux)")
        print("  - Or use GitHub Actions / CI for automated cross-platform builds")
        print()

    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 70)
        print("❌ BUILD FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Make sure we're in the right directory
    script_dir = Path(__file__).parent
    if script_dir != Path.cwd():
        print(f"Changing to script directory: {script_dir}")
        import os
        os.chdir(script_dir)

    build_executable()
