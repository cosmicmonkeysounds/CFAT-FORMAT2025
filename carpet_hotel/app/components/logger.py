#!/usr/bin/env python3
"""
Carpet Hotel Logger
===================

Centralized logging with component prefixes and color support.
Reduces duplicate messages and provides clean, organized output.
"""

import sys
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

    def __init__(self, component: str = "Core", verbose: bool = True):
        """
        Initialize logger.

        Args:
            component: Component name for prefix
            verbose: If False, only show important messages
        """
        self.component = component
        self.verbose = verbose
        self.last_message = None
        self.repeat_count = 0

    def _print(self, prefix: str, message: str, force: bool = False):
        """
        Print message with duplicate suppression.

        Args:
            prefix: Message prefix (e.g., "✓", "✗", "→")
            message: Message content
            force: Force print even if duplicate
        """
        full_message = f"{prefix} {message}"

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


def get_logger(component: str, verbose: bool = True) -> Logger:
    """
    Get or create logger for component.

    Args:
        component: Component name
        verbose: Verbosity level

    Returns:
        Logger instance
    """
    if component not in _loggers:
        _loggers[component] = Logger(component, verbose)
    return _loggers[component]


def set_verbosity(verbose: bool):
    """Set verbosity for all loggers."""
    for logger in _loggers.values():
        logger.verbose = verbose


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
