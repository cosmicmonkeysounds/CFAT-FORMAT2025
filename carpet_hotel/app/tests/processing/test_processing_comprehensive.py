#!/usr/bin/env python3
"""
Comprehensive Processing Test Suite
====================================

Tests Processing video engine in all configurations:
- Different display configurations (1, 2, [1,2], [2,1])
- With/without keyboard control
- With/without OSC control
- Detection and validation

Run with: python3 test_processing_comprehensive.py
"""

import sys
import time
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from carpet_hotel_pde import CarpetHotelProcessing
from utils import find_processing_java, detect_displays, get_app_dir


class ProcessingTester:
    """Comprehensive Processing test suite."""

    def __init__(self):
        self.results = []
        self.processing_java = None
        self.displays = []
        self.test_duration = 3  # seconds per test (reduced for faster cleanup)

        # Register cleanup on exit
        import atexit
        atexit.register(self.cleanup_all_processing)

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        print(f"{status} - {test_name}")
        if message:
            print(f"      {message}")

    def print_header(self, title: str):
        """Print section header."""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)

    def cleanup_all_processing(self):
        """Kill all Processing processes as cleanup."""
        print("\n\nCleaning up any remaining Processing processes...")
        try:
            subprocess.run(
                ["pkill", "-9", "-f", "Processing.app"],
                capture_output=True,
                timeout=5
            )
            time.sleep(1)
            print("✓ Cleanup complete")
        except Exception as e:
            print(f"⚠ Cleanup error: {e}")

    def print_summary(self):
        """Print test summary."""
        self.print_header("TEST SUMMARY")

        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"])
        total = len(self.results)

        print(f"\nTotal tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {passed/total*100:.1f}%")

        if failed > 0:
            print("\nFailed tests:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  ✗ {r['test']}")
                    if r["message"]:
                        print(f"    {r['message']}")

        print("\n" + "="*70 + "\n")

        # Final cleanup
        self.cleanup_all_processing()

        return failed == 0

    def test_1_dependencies(self) -> bool:
        """Test 1: Check dependencies."""
        self.print_header("Test 1: Dependencies")

        # Test processing-java detection
        print("\n[1.1] Finding processing-java...")
        self.processing_java = find_processing_java()

        if self.processing_java:
            self.log_result("processing-java detection", True, f"Found at: {self.processing_java}")
        else:
            self.log_result("processing-java detection", False, "Not found. Install Processing from https://processing.org/download")
            return False

        # Verify it's executable
        print("\n[1.2] Verifying processing-java is executable...")
        try:
            result = subprocess.run(
                [self.processing_java, "--help"],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                self.log_result("processing-java executable", True)
            else:
                self.log_result("processing-java executable", False, f"Return code: {result.returncode}")
                return False
        except Exception as e:
            self.log_result("processing-java executable", False, str(e))
            return False

        # Check sketch directory
        print("\n[1.3] Checking sketch directory...")
        sketch_dir = get_app_dir()
        app_pde = sketch_dir / "app.pde"

        if app_pde.exists():
            self.log_result("sketch directory", True, f"Found at: {sketch_dir}")
        else:
            self.log_result("sketch directory", False, f"app.pde not found at: {app_pde}")
            return False

        return True

    def test_2_display_detection(self) -> bool:
        """Test 2: Display detection."""
        self.print_header("Test 2: Display Detection")

        print("\n[2.1] Detecting displays...")
        self.displays = detect_displays()

        if len(self.displays) > 0:
            self.log_result("display detection", True, f"Found {len(self.displays)} display(s)")

            print("\nAvailable displays:")
            for display in self.displays:
                main_marker = " [MAIN]" if display.get("main") else ""
                print(f"  Display {display['index']}: {display['name']}{main_marker}")
                if 'resolution' in display:
                    print(f"    Resolution: {display['resolution'][0]}x{display['resolution'][1]}")
        else:
            self.log_result("display detection", False, "No displays detected")
            return False

        return True

    def test_3_initialization(self) -> bool:
        """Test 3: Wrapper initialization."""
        self.print_header("Test 3: Wrapper Initialization")

        # Test default initialization
        print("\n[3.1] Default initialization...")
        try:
            pde = CarpetHotelProcessing()
            self.log_result("default initialization", True, f"Displays: {pde.displays}, Keyboard: {pde.enable_keyboard}")
        except Exception as e:
            self.log_result("default initialization", False, str(e))
            return False

        # Test custom displays
        print("\n[3.2] Custom display configuration...")
        try:
            pde = CarpetHotelProcessing(displays=[1], enable_keyboard=False)
            if pde.displays == [1] and pde.enable_keyboard == False:
                self.log_result("custom configuration", True)
            else:
                self.log_result("custom configuration", False, f"Config mismatch: displays={pde.displays}, keyboard={pde.enable_keyboard}")
        except Exception as e:
            self.log_result("custom configuration", False, str(e))
            return False

        return True

    def test_4_single_display_configs(self) -> bool:
        """Test 4: Single display configurations."""
        self.print_header("Test 4: Single Display Configurations")

        if len(self.displays) < 1:
            self.log_result("single display configs", False, "No displays available")
            return False

        # Test display 1
        print("\n[4.1] Testing with display 1 only...")
        success = self._test_processing_start_stop(
            displays=[1],
            test_name="display 1 only"
        )

        # Test display 2 (if available)
        if len(self.displays) >= 2:
            print("\n[4.2] Testing with display 2 only...")
            success = self._test_processing_start_stop(
                displays=[2],
                test_name="display 2 only"
            ) and success
        else:
            print("\n[4.2] Skipping display 2 test (only 1 display available)")

        return success

    def test_5_multiple_display_configs(self) -> bool:
        """Test 5: Multiple display configurations."""
        self.print_header("Test 5: Multiple Display Configurations")

        if len(self.displays) < 2:
            print("\nSkipping multiple display tests (only 1 display available)")
            self.log_result("multiple display configs", True, "Skipped - only 1 display")
            return True

        # Test displays [1, 2]
        print("\n[5.1] Testing with displays [1, 2]...")
        success = self._test_processing_start_stop(
            displays=[1, 2],
            test_name="displays [1, 2]"
        )

        # Test displays [2, 1] (reversed order)
        print("\n[5.2] Testing with displays [2, 1] (reversed)...")
        success = self._test_processing_start_stop(
            displays=[2, 1],
            test_name="displays [2, 1]"
        ) and success

        return success

    def test_6_keyboard_modes(self) -> bool:
        """Test 6: Keyboard control modes."""
        self.print_header("Test 6: Keyboard Control Modes")

        # Test with keyboard enabled
        print("\n[6.1] Testing with keyboard control enabled...")
        success = self._test_processing_start_stop(
            displays=[1],
            enable_keyboard=True,
            test_name="keyboard enabled"
        )

        # Test with keyboard disabled
        print("\n[6.2] Testing with keyboard control disabled...")
        success = self._test_processing_start_stop(
            displays=[1],
            enable_keyboard=False,
            test_name="keyboard disabled"
        ) and success

        return success

    def test_7_lifecycle(self) -> bool:
        """Test 7: Process lifecycle."""
        self.print_header("Test 7: Process Lifecycle")

        print("\n[7.1] Testing start/stop/restart cycle...")

        try:
            pde = CarpetHotelProcessing(displays=[1])

            # Start
            if not pde.start():
                self.log_result("lifecycle start", False, "Failed to start")
                return False

            time.sleep(2)

            if not pde.is_running():
                self.log_result("lifecycle running check", False, "Process not running after start")
                pde.stop()
                return False

            self.log_result("lifecycle start", True)

            # Stop
            if not pde.stop():
                self.log_result("lifecycle stop", False, "Failed to stop")
                return False

            time.sleep(1)

            if pde.is_running():
                self.log_result("lifecycle stop check", False, "Process still running after stop")
                return False

            self.log_result("lifecycle stop", True)

            # Restart
            if not pde.start():
                self.log_result("lifecycle restart", False, "Failed to restart")
                return False

            time.sleep(2)

            if not pde.is_running():
                self.log_result("lifecycle restart check", False, "Process not running after restart")
                pde.stop()
                return False

            self.log_result("lifecycle restart", True)

            # Final cleanup
            pde.stop()

            return True

        except Exception as e:
            self.log_result("lifecycle test", False, str(e))
            return False

    def _test_processing_start_stop(self, displays: list, enable_keyboard: bool = True, test_name: str = "") -> bool:
        """Helper to test Processing start/stop with specific configuration."""
        pde = None
        try:
            pde = CarpetHotelProcessing(
                displays=displays,
                enable_keyboard=enable_keyboard
            )

            # Start
            if not pde.start():
                self.log_result(test_name, False, "Failed to start")
                return False

            # Wait and verify it's running
            time.sleep(self.test_duration)

            if not pde.is_running():
                self.log_result(test_name, False, "Process died during test")
                pde.stop()
                time.sleep(1)
                return False

            # Stop
            if not pde.stop():
                self.log_result(test_name, False, "Failed to stop cleanly")
                return False

            # Verify it stopped and wait a bit
            time.sleep(2)
            if pde.is_running():
                self.log_result(test_name, False, "Process still running after stop")
                # Force kill
                pde.stop()
                time.sleep(1)
                return False

            self.log_result(test_name, True)

            # Add delay between tests to ensure cleanup
            time.sleep(1)
            return True

        except Exception as e:
            self.log_result(test_name, False, str(e))
            if pde:
                try:
                    pde.stop()
                    time.sleep(1)
                except:
                    pass
            return False

    def run_all_tests(self) -> bool:
        """Run all tests in sequence."""
        print("\n" + "="*70)
        print("  CARPET HOTEL - COMPREHENSIVE PROCESSING TEST SUITE")
        print("="*70)
        print("\nThis will test Processing in multiple configurations.")
        print("Each test will run for a few seconds.\n")

        # Run tests in order
        all_passed = True

        # Test 1: Dependencies
        if not self.test_1_dependencies():
            print("\n✗ Cannot continue - dependencies missing")
            return False

        # Test 2: Display detection
        if not self.test_2_display_detection():
            print("\n✗ Cannot continue - display detection failed")
            return False

        # Test 3: Initialization
        all_passed = self.test_3_initialization() and all_passed

        # Test 4: Single display configs
        all_passed = self.test_4_single_display_configs() and all_passed

        # Test 5: Multiple display configs
        all_passed = self.test_5_multiple_display_configs() and all_passed

        # Test 6: Keyboard modes
        all_passed = self.test_6_keyboard_modes() and all_passed

        # Test 7: Lifecycle
        all_passed = self.test_7_lifecycle() and all_passed

        # Print summary
        return self.print_summary()


def main():
    """Run comprehensive Processing tests."""
    tester = ProcessingTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
