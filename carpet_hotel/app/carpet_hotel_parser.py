#!/usr/bin/env python3
"""
Carpet Hotel Parser - Entry Point
==================================

Wrapper script for backwards compatibility and easy CLI access.
Actual implementation is in components/parser.py
"""

from components.parser import main, parse_arguments

__all__ = ['main', 'parse_arguments']

if __name__ == '__main__':
    main()
