#!/usr/bin/env python3
"""
Carpet Hotel GUI - Entry Point
===============================

Wrapper script for backwards compatibility and easy GUI access.
Actual implementation is in components/gui.py
"""

from components.gui import main, CarpetHotelGUI

__all__ = ['main', 'CarpetHotelGUI']

if __name__ == '__main__':
    main()
