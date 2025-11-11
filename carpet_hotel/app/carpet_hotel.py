#!/usr/bin/env python3
"""
Carpet Hotel - Main Entry Point
================================

Wrapper script for backwards compatibility.
Imports the core module for easy access.

For CLI: Use carpet_hotel_parser.py
For GUI: Use carpet_hotel_gui.py
"""

# Re-export main classes for backwards compatibility
from carpet_hotel_core import CarpetHotelCore, CarpetHotelLauncher

__all__ = ['CarpetHotelCore', 'CarpetHotelLauncher']
