#!/usr/bin/env python3
"""
Carpet Hotel Logger
===================

Centralized logging with component prefixes and color support.
Reduces duplicate messages and provides clean, organized output.
Logs to both console and files in logs/ folder.
"""

import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class Logger:
    """
    Centralized logger for Carpet Hotel.

    Features:
    - Component-based prefixes [SC], [Processing], [Core], etc.
    - Automatic duplicate suppression
    - Clean formatted output
    - Optional verbosity control
    """

    def __init__(self, component: str = "Core", verbose: bool = True, log_file: Optional[str] = None, clear_on_start: bool = False):
        """
        Initialize logger.

        Args:
            component: Component name for prefix
            verbose: If False, only show important messages
            log_file: Optional log file path (auto-determined if None)
            clear_on_start: If True, clear log file on initialization
        """
        self.component = component
        self.verbose = verbose
        self.last_message = None
        self.repeat_count = 0

        # Set up file logging
        self.log_file = log_file
        if self.log_file is None:
            # Auto-determine log file based on component
            self.log_file = self._get_log_file_path(component)

        # Ensure logs directory exists
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

            # Clear log file if requested
            if clear_on_start:
                try:
                    with open(self.log_file, 'w') as f:
                        f.write('')  # Clear file
                except Exception:
                    pass  # Fail silently

    def _get_log_file_path(self, component: str) -> str:
        """Get log file path for component."""
        # Map components to log files
        log_mapping = {
            "Processing": "video.log",
            "SuperCollider": "sound.log",
            "Arduino": "arduino.log",
            "SerialBroker": "arduino.log",
            "Core": "core.log",
        }

        # Default to core.log for unknown components
        log_filename = log_mapping.get(component, "core.log")

        # Get app directory (where logger.py is in components/)
        from pathlib import Path
        app_dir = Path(__file__).parent.parent.absolute()  # Go from components/logger.py to app/
        return str(app_dir / "logs" / log_filename)

    def _print(self, prefix: str, message: str, force: bool = False):
        """
        Print message with duplicate suppression and log to file.

        Args:
            prefix: Message prefix (e.g., "✓", "✗", "→")
            message: Message content
            force: Force print even if duplicate
        """
        full_message = f"{prefix} {message}"

        # Always write to file (without duplicate suppression)
        if self.log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            try:
                with open(self.log_file, 'a') as f:
                    f.write(f"[{timestamp}] {full_message}\n")
            except Exception as e:
                # Fail silently to not disrupt the program
                pass

        # Console output with duplicate suppression
        if full_message == self.last_message and not force:
            # Same message - increment counter
            self.repeat_count += 1
            sys.stdout.write(f"\r{full_message} (x{self.repeat_count + 1})")
            sys.stdout.flush()
        else:
            # Different message - print new line
            if self.repeat_count > 0:
                print()  # Finish previous line
                self.repeat_count = 0

            print(full_message)
            self.last_message = full_message

    def info(self, message: str):
        """Log info message."""
        if self.verbose:
            self._print(f"[{self.component}]", message)

    def success(self, message: str):
        """Log success message."""
        self._print(f"[{self.component}] ✓", message)

    def error(self, message: str):
        """Log error message."""
        self._print(f"[{self.component}] ✗", message, force=True)

    def warning(self, message: str):
        """Log warning message."""
        self._print(f"[{self.component}] ⚠", message)

    def debug(self, message: str):
        """Log debug message (only if verbose)."""
        if self.verbose:
            self._print(f"[{self.component}] •", message)

    def osc_send(self, address: str, args: list):
        """Log OSC send message."""
        args_str = " ".join(str(a) for a in args)
        self._print(f"[{self.component}] →", f"{address} {args_str}")

    def osc_recv(self, address: str, args: list):
        """Log OSC receive message."""
        args_str = " ".join(str(a) for a in args)
        self._print(f"[{self.component}] ←", f"{address} {args_str}")

    def section(self, title: str):
        """Print section header."""
        if self.repeat_count > 0:
            print()  # Finish previous line
            self.repeat_count = 0

        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
        self.last_message = None

    def subsection(self, title: str):
        """Print subsection header."""
        if self.repeat_count > 0:
            print()  # Finish previous line
            self.repeat_count = 0

        print(f"\n[{self.component}] === {title} ===")
        self.last_message = None

    def finish_line(self):
        """Finish current line (if repeating)."""
        if self.repeat_count > 0:
            print()
            self.repeat_count = 0
            self.last_message = None


# Global logger instances
_loggers = {}


def get_logger(component: str, verbose: bool = True, clear_on_start: bool = False) -> Logger:
    """
    Get or create logger for component.

    Args:
        component: Component name
        verbose: Verbosity level
        clear_on_start: If True, clear log file on first creation

    Returns:
        Logger instance
    """
    if component not in _loggers:
        _loggers[component] = Logger(component, verbose, clear_on_start=clear_on_start)
    return _loggers[component]


def set_verbosity(verbose: bool):
    """Set verbosity for all loggers."""
    for logger in _loggers.values():
        logger.verbose = verbose


def clear_all_logs():
    """Clear all log files in the logs directory."""
    from pathlib import Path
    try:
        # Get app directory
        app_dir = Path(__file__).parent.parent.absolute()
        logs_dir = app_dir / "logs"

        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                try:
                    with open(log_file, 'w') as f:
                        f.write('')  # Clear file
                except Exception:
                    pass  # Fail silently
    except Exception:
        pass  # Fail silently


# Convenience function
def log(component: str, message: str, level: str = "info"):
    """
    Quick logging function.

    Args:
        component: Component name
        message: Message to log
        level: "info", "success", "error", "warning", "debug"
    """
    logger = get_logger(component)

    if level == "success":
        logger.success(message)
    elif level == "error":
        logger.error(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "debug":
        logger.debug(message)
    else:
        logger.info(message)
