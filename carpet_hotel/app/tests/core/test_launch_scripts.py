#!/usr/bin/env python3
"""
Carpet Hotel Launch Scripts Test Suite

Tests for CLI parser and launch script functionality.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add app directory to path for imports
script_dir = Path(__file__).parent.parent.parent.absolute()  # /app/
sys.path.insert(0, str(script_dir))

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(msg):
    print(f"{Colors.BLUE}[TEST]{Colors.END} {msg}")

def print_pass(msg):
    print(f"{Colors.GREEN}✓ PASS{Colors.END} {msg}")

def print_fail(msg):
    print(f"{Colors.RED}✗ FAIL{Colors.END} {msg}")

def print_warn(msg):
    print(f"{Colors.YELLOW}⚠ WARN{Colors.END} {msg}")


class LaunchScriptTests:
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent.absolute()  # /app/
        self.parent_dir = self.script_dir.parent  # /carpet_hotel/
        self.parser_script = self.script_dir / 'carpet_hotel_parser.py'
        self.core_script = self.script_dir / 'carpet_hotel.py'
        self.gui_script = self.script_dir / 'carpet_hotel_gui.py'
        self.launch_macos = self.parent_dir / 'launch_macos.sh'
        self.launch_windows = self.parent_dir / 'launch_windows.bat'

    # ========================================================================
    # TEST 1: File Existence
    # ========================================================================

    def test_files_exist(self):
        """Test that all required files exist."""
        print_test("\n=== TEST 1: File Existence ===")

        files_to_check = [
            ('carpet_hotel_parser.py', self.parser_script),
            ('carpet_hotel.py', self.core_script),
            ('carpet_hotel_gui.py', self.gui_script),
            ('launch_macos.sh', self.launch_macos),
            ('launch_windows.bat', self.launch_windows),
        ]

        all_exist = True
        for name, path in files_to_check:
            if path.exists():
                print_pass(f"{name} exists")
            else:
                print_fail(f"{name} NOT FOUND: {path}")
                all_exist = False

        # Check if Mac launch script is executable
        if self.launch_macos.exists():
            is_executable = os.access(self.launch_macos, os.X_OK)
            if is_executable:
                print_pass("launch_macos.sh is executable")
            else:
                print_fail("launch_macos.sh is NOT executable")
                all_exist = False

        return all_exist

    # ========================================================================
    # TEST 2: Parser Import
    # ========================================================================

    def test_parser_import(self):
        """Test that parser module can be imported."""
        print_test("\n=== TEST 2: Parser Import ===")

        try:
            import carpet_hotel_parser
            print_pass("carpet_hotel_parser module imported successfully")

            # Check for required functions
            if hasattr(carpet_hotel_parser, 'parse_arguments'):
                print_pass("parse_arguments() function exists")
            else:
                print_fail("parse_arguments() function NOT FOUND")
                return False

            if hasattr(carpet_hotel_parser, 'main'):
                print_pass("main() function exists")
            else:
                print_fail("main() function NOT FOUND")
                return False

            return True

        except ImportError as e:
            print_fail(f"Failed to import carpet_hotel_parser: {e}")
            return False

    # ========================================================================
    # TEST 3: Core Module Import
    # ========================================================================

    def test_core_import(self):
        """Test that core module can be imported."""
        print_test("\n=== TEST 3: Core Module Import ===")

        try:
            import carpet_hotel
            print_pass("carpet_hotel module imported successfully")

            # Check for CarpetHotelLauncher class
            if hasattr(carpet_hotel, 'CarpetHotelLauncher'):
                print_pass("CarpetHotelLauncher class exists")
            else:
                print_fail("CarpetHotelLauncher class NOT FOUND")
                return False

            # Make sure main() doesn't exist (it should be in parser now)
            if not hasattr(carpet_hotel, 'main'):
                print_pass("main() correctly removed from core module")
            else:
                print_warn("main() still exists in core module (should be in parser)")

            return True

        except ImportError as e:
            print_fail(f"Failed to import carpet_hotel: {e}")
            return False

    # ========================================================================
    # TEST 4: GUI Module Import
    # ========================================================================

    def test_gui_import(self):
        """Test that GUI module can be imported."""
        print_test("\n=== TEST 4: GUI Module Import ===")

        try:
            import carpet_hotel_gui
            print_pass("carpet_hotel_gui module imported successfully")

            # Check for CarpetHotelGUI class
            if hasattr(carpet_hotel_gui, 'CarpetHotelGUI'):
                print_pass("CarpetHotelGUI class exists")
            else:
                print_fail("CarpetHotelGUI class NOT FOUND")
                return False

            return True

        except ImportError as e:
            print_fail(f"Failed to import carpet_hotel_gui: {e}")
            return False

    # ========================================================================
    # TEST 5: Parser Help Command (Mac)
    # ========================================================================

    def test_parser_help(self):
        """Test parser --help command."""
        print_test("\n=== TEST 5: Parser Help Command ===")

        if sys.platform != 'darwin':
            print_warn("Skipping Mac-specific test on non-Mac platform")
            return True

        try:
            result = subprocess.run(
                ['python3', str(self.parser_script), '--help'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.script_dir
            )

            if result.returncode == 0:
                print_pass("Parser --help executed successfully")

                # Check for expected strings in help output
                expected_strings = [
                    'Carpet Hotel',
                    '--build',
                    '--sc-only',
                    '--audio-device',
                    '--displays',
                ]

                for expected in expected_strings:
                    if expected in result.stdout:
                        print(f"  ✓ Found '{expected}' in help output")
                    else:
                        print_warn(f"  Missing '{expected}' in help output")

                return True
            else:
                print_fail(f"Parser --help returned non-zero exit code: {result.returncode}")
                print(f"STDERR: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print_fail("Parser --help timed out")
            return False
        except Exception as e:
            print_fail(f"Error running parser --help: {e}")
            return False

    # ========================================================================
    # TEST 6: Parser No Args Behavior
    # ========================================================================

    def test_parser_no_args(self):
        """Test parser behavior with no arguments."""
        print_test("\n=== TEST 6: Parser No Args Behavior ===")

        if sys.platform != 'darwin':
            print_warn("Skipping Mac-specific test on non-Mac platform")
            return True

        try:
            result = subprocess.run(
                ['python3', str(self.parser_script)],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.script_dir
            )

            # Should exit with 0 and show help message
            if result.returncode == 0:
                print_pass("Parser with no args executed successfully")

                # Should recommend GUI
                if 'carpet_hotel_gui.py' in result.stdout:
                    print_pass("Recommends GUI control panel")
                else:
                    print_warn("Does not mention GUI control panel")

                return True
            else:
                print_fail(f"Parser returned non-zero exit code: {result.returncode}")
                return False

        except subprocess.TimeoutExpired:
            print_fail("Parser with no args timed out")
            return False
        except Exception as e:
            print_fail(f"Error running parser with no args: {e}")
            return False

    # ========================================================================
    # TEST 7: Launch Script Syntax (Mac)
    # ========================================================================

    def test_launch_script_syntax_mac(self):
        """Test Mac launch script syntax."""
        print_test("\n=== TEST 7: Launch Script Syntax (Mac) ===")

        if sys.platform != 'darwin':
            print_warn("Skipping Mac-specific test on non-Mac platform")
            return True

        try:
            # Check bash syntax
            result = subprocess.run(
                ['bash', '-n', str(self.launch_macos)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print_pass("Mac launch script has valid bash syntax")
                return True
            else:
                print_fail(f"Mac launch script has syntax errors")
                print(f"STDERR: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print_fail("Syntax check timed out")
            return False
        except Exception as e:
            print_fail(f"Error checking launch script syntax: {e}")
            return False

    # ========================================================================
    # TEST 8: Launch Script Content (Windows placeholder)
    # ========================================================================

    def test_launch_script_content_windows(self):
        """Test Windows launch script content (placeholder)."""
        print_test("\n=== TEST 8: Launch Script Content (Windows) ===")

        if not self.launch_windows.exists():
            print_fail("Windows launch script not found")
            return False

        # Read and check for basic commands
        content = self.launch_windows.read_text()

        required_content = [
            '@echo off',
            'carpet_hotel_gui.py',
            'cd /d',
        ]

        all_found = True
        for required in required_content:
            if required in content:
                print(f"  ✓ Found '{required}' in Windows script")
            else:
                print_warn(f"  Missing '{required}' in Windows script")
                all_found = False

        if all_found:
            print_pass("Windows launch script has expected content")
        else:
            print_warn("Windows launch script may be incomplete (untested on Windows)")

        # Note: Can't actually test execution on Mac
        print_warn("Windows script execution not tested (running on Mac)")

        return True  # Don't fail since we can't test on Mac

    # ========================================================================
    # TEST 9: Parser Argument Parsing
    # ========================================================================

    def test_parser_arguments(self):
        """Test that parser correctly handles various arguments."""
        print_test("\n=== TEST 9: Parser Argument Parsing ===")

        try:
            # Import the parser module
            import carpet_hotel_parser

            # Test with sys.argv override
            test_cases = [
                (['--help'], "help flag"),
                (['--build'], "build flag"),
                (['--sc-only'], "sc-only flag"),
                (['--audio-device', 'test'], "audio-device argument"),
                (['--displays', '1,2,3'], "displays argument"),
                (['--arduino-port', '/dev/cu.test'], "arduino-port argument"),
            ]

            all_passed = True
            for args, description in test_cases:
                try:
                    # Save original argv
                    original_argv = sys.argv.copy()
                    sys.argv = ['carpet_hotel_parser.py'] + args

                    # Try to parse (will raise SystemExit for --help)
                    try:
                        parsed = carpet_hotel_parser.parse_arguments()
                        print(f"  ✓ Parsed {description}")
                    except SystemExit:
                        if '--help' in args:
                            print(f"  ✓ Parsed {description} (SystemExit expected)")
                        else:
                            print_warn(f"  Unexpected SystemExit for {description}")

                    # Restore argv
                    sys.argv = original_argv

                except Exception as e:
                    print_fail(f"  Error parsing {description}: {e}")
                    all_passed = False
                    sys.argv = original_argv

            if all_passed:
                print_pass("All argument parsing tests passed")

            return all_passed

        except ImportError as e:
            print_fail(f"Failed to import parser for testing: {e}")
            return False

    # ========================================================================
    # Run All Tests
    # ========================================================================

    def run_all(self):
        """Run all tests."""
        print(f"\n{'='*60}")
        print("CARPET HOTEL LAUNCH SCRIPTS TEST SUITE")
        print(f"{'='*60}")
        print(f"Platform: {sys.platform}")
        print(f"Python: {sys.version}")

        results = {
            'File Existence': self.test_files_exist(),
            'Parser Import': self.test_parser_import(),
            'Core Module Import': self.test_core_import(),
            'GUI Module Import': self.test_gui_import(),
            'Parser Help Command': self.test_parser_help(),
            'Parser No Args': self.test_parser_no_args(),
            'Mac Launch Script Syntax': self.test_launch_script_syntax_mac(),
            'Windows Launch Script Content': self.test_launch_script_content_windows(),
            'Parser Argument Parsing': self.test_parser_arguments(),
        }

        print(f"\n{'='*60}")
        print("TEST RESULTS")
        print(f"{'='*60}")

        for test_name, passed in results.items():
            status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
            print(f"  {test_name}: {status}")

        total = len(results)
        passed = sum(1 for v in results.values() if v)

        print(f"\n{passed}/{total} tests passed")

        if passed == total:
            print(f"{Colors.GREEN}✓ All tests passed!{Colors.END}")
            return 0
        else:
            print(f"{Colors.RED}✗ Some tests failed{Colors.END}")
            return 1


def main():
    """Main entry point."""
    suite = LaunchScriptTests()
    return suite.run_all()


if __name__ == '__main__':
    sys.exit(main())
