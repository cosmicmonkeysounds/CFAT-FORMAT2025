#!/usr/bin/env python3
"""
Test the SC execution mechanism with a minimal script.
"""

import sys
import time
import subprocess
from pathlib import Path

def main():
    print("\n" + "="*60)
    print("Testing SuperCollider Execution Mechanism")
    print("="*60 + "\n")

    sclang_path = "/Applications/SuperCollider.app/Contents/MacOS/sclang"
    script_path = Path(__file__).parent / "test_inline.scd"

    print(f"sclang: {sclang_path}")
    print(f"script: {script_path}")

    # Start sclang
    print("\nStarting sclang...")
    proc = subprocess.Popen(
        [sclang_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    print(f"✓ Process started (PID: {proc.pid})")

    # Send execute command
    execute_cmd = f'thisProcess.interpreter.executeFile("{str(script_path)}");\n'
    print(f"\nSending command: {execute_cmd.strip()}")

    try:
        proc.stdin.write(execute_cmd)
        proc.stdin.flush()
        print("✓ Command sent")
    except Exception as e:
        print(f"✗ Failed to send command: {e}")
        proc.kill()
        return False

    # Monitor output
    print("\n--- SuperCollider Output ---")
    found_init = False
    start_time = time.time()
    timeout = 30

    try:
        while time.time() - start_time < timeout:
            if proc.poll() is not None:
                print(f"\n✗ Process exited with code {proc.returncode}")
                break

            line = proc.stdout.readline()
            if line:
                line = line.rstrip()
                print(f"[SC] {line}")

                if "Audio server ready!" in line:
                    found_init = True
                    print("\n✓ Found initialization marker!")
                    break

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    # Cleanup
    print("\nCleaning up...")
    proc.terminate()
    time.sleep(1)
    if proc.poll() is None:
        proc.kill()

    print("\n" + "="*60)
    if found_init:
        print("✓ Test PASSED")
    else:
        print("✗ Test FAILED")
    print("="*60 + "\n")

    return found_init

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
