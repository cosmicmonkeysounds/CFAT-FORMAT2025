#!/usr/bin/env python3
"""
Settings Manager for Carpet Hotel GUI
======================================

Handles persistence of GUI settings to configs/ folder.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class SettingsManager:
    """Manage GUI settings persistence."""

    def __init__(self, config_file: str = "gui_settings.json"):
        """
        Initialize settings manager.

        Args:
            config_file: Name of config file in configs/ folder
        """
        self.config_dir = Path(__file__).parent.parent / "configs"
        self.config_file = self.config_dir / config_file
        self.settings: Dict[str, Any] = {}

        # Ensure configs directory exists
        self.config_dir.mkdir(exist_ok=True)

        # Load existing settings
        self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load settings from file.

        Returns:
            Dictionary of settings
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
                print(f"✓ Settings loaded from {self.config_file.name}")
            except Exception as e:
                print(f"⚠ Could not load settings: {e}")
                self.settings = {}
        else:
            print(f"No saved settings found, using defaults")
            self.settings = {}

        return self.settings

    def save(self):
        """Save current settings to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            print(f"✓ Settings saved to {self.config_file.name}")
        except Exception as e:
            print(f"✗ Could not save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value

    def get_all(self) -> Dict[str, Any]:
        """
        Get all settings.

        Returns:
            Dictionary of all settings
        """
        return self.settings.copy()

    def update(self, updates: Dict[str, Any]):
        """
        Update multiple settings.

        Args:
            updates: Dictionary of settings to update
        """
        self.settings.update(updates)


# Default settings
DEFAULT_SETTINGS = {
    # Audio settings
    "audio_device": "Default",
    "master_volume": 0.7,

    # Video settings
    "active_displays": [],  # List of active display dicts
    "inactive_displays": [],  # List of inactive display dicts
    "enable_keyboard": True,

    # Hardware settings
    "serial_port": "",  # Empty = not selected

    # Window settings
    "window_width": 1000,
    "window_height": 900,
    "window_x": None,
    "window_y": None,
}
