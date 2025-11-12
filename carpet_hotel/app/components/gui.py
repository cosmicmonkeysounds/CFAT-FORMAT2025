#!/usr/bin/env python3
"""
Carpet Hotel GUI - Complete Redesign
=====================================

Modern GUI with full display detection, device management, and modular control.

Features:
- Video Tab: Display detection, active/inactive management, drag-drop reordering
- Audio Tab: Device and sample rate dropdowns with auto-detection
- Hardware Tab: Arduino connection management
- Command Tab: Raw OSC command interface
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from typing import Optional, List, Dict

# Import core and wrapper modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from carpet_hotel_core import CarpetHotelCore
from components.supercollider import CarpetHotelSuperCollider
from components.processing import CarpetHotelProcessing
from components.arduino import CarpetHotelArduino
from components.utils.utils import detect_displays, detect_serial_ports
from components.settings_manager import SettingsManager, DEFAULT_SETTINGS

# Check for OSC
try:
    from pythonosc import udp_client
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False


class CarpetHotelGUI:
    """Main GUI application for Carpet Hotel."""

    def __init__(self):
        """Initialize the GUI."""
        self.root = tk.Tk()
        self.root.title("Carpet Hotel - Control Panel")
        self.root.geometry("1000x900")

        # Core instance
        self.core = CarpetHotelCore()

        # Settings manager
        self.settings = SettingsManager()

        # Component running states
        self.video_running = False
        self.audio_running = False
        self.hardware_running = False

        # Display management
        self.all_displays = []
        self.active_displays = []
        self.inactive_displays = []

        # Display hover preview
        self.preview_window = None
        self.preview_display_index = None
        self.preview_timer = None

        # Create GUI
        self.create_gui()

        # Initial setup
        self.refresh_displays()
        self.refresh_audio_devices()
        self.refresh_serial_ports()

        # Start status polling
        self._poll_status()

        # Load saved settings and apply them
        self.load_settings()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_gui(self):
        """Create all GUI elements."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=(10, 5))

        # Create tabs
        self.create_video_tab(notebook)
        self.create_audio_tab(notebook)
        self.create_hardware_tab(notebook)
        self.create_command_tab(notebook)
        self.create_video_config_tab(notebook)

        # Global controls at bottom
        self.create_global_controls()

    # ========================================================================
    # VIDEO TAB
    # ========================================================================

    def create_video_tab(self, notebook):
        """Create Video/Processing tab with display management."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Video")

        # Header
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(header_frame, text="Video System (Processing)",
                 font=('Arial', 16, 'bold')).pack(side='left')

        # Refresh button
        ttk.Button(header_frame, text="↻ Refresh Displays",
                  command=self.refresh_displays, width=15).pack(side='right', padx=5)

        # Status
        status_frame = ttk.LabelFrame(tab, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=5)

        self.video_status_label = ttk.Label(status_frame, text="● Stopped",
                                           foreground='red', font=('Arial', 14, 'bold'))
        self.video_status_label.pack()

        # Control buttons
        control_frame = ttk.Frame(tab)
        control_frame.pack(pady=10)

        self.video_start_btn = ttk.Button(control_frame, text="▶ Start Video",
                                         command=self.start_video, width=20)
        self.video_start_btn.pack(side='left', padx=5)

        self.video_stop_btn = ttk.Button(control_frame, text="■ Stop Video",
                                        command=self.stop_video, width=20, state='disabled')
        self.video_stop_btn.pack(side='left', padx=5)

        # Display management section
        display_frame = ttk.LabelFrame(tab, text="Display Management", padding=10)
        display_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Help text
        help_text = "Drag displays between Active and Inactive lists. Active displays are used in order."
        ttk.Label(display_frame, text=help_text, foreground='gray',
                 font=('Arial', 9)).pack(anchor='w', pady=(0,10))

        # Two-column layout for Active/Inactive
        columns_frame = ttk.Frame(display_frame)
        columns_frame.pack(fill='both', expand=True)

        # Inactive Displays (left)
        inactive_frame = ttk.Frame(columns_frame)
        inactive_frame.pack(side='left', fill='both', expand=True, padx=(0,5))

        ttk.Label(inactive_frame, text="Inactive Displays",
                 font=('Arial', 12, 'bold')).pack()

        self.inactive_listbox = tk.Listbox(inactive_frame, height=8,
                                          selectmode=tk.SINGLE)
        self.inactive_listbox.pack(fill='both', expand=True, pady=5)
        self.inactive_listbox.bind('<Double-Button-1>', self.move_to_active)
        self.inactive_listbox.bind('<Motion>', lambda e: self.on_listbox_hover(e, self.inactive_listbox, self.inactive_displays))
        self.inactive_listbox.bind('<Leave>', self.hide_display_preview)

        # Active Displays (right)
        active_frame = ttk.Frame(columns_frame)
        active_frame.pack(side='left', fill='both', expand=True, padx=(5,0))

        ttk.Label(active_frame, text="Active Displays (Processing Order)",
                 font=('Arial', 12, 'bold')).pack()

        self.active_listbox = tk.Listbox(active_frame, height=8,
                                        selectmode=tk.SINGLE)
        self.active_listbox.pack(fill='both', expand=True, pady=5)
        self.active_listbox.bind('<Double-Button-1>', self.move_to_inactive)
        self.active_listbox.bind('<Motion>', lambda e: self.on_listbox_hover(e, self.active_listbox, self.active_displays))
        self.active_listbox.bind('<Leave>', self.hide_display_preview)

        # Reorder buttons below active list
        reorder_frame = ttk.Frame(active_frame)
        reorder_frame.pack(fill='x')

        ttk.Button(reorder_frame, text="▲ Move Up",
                  command=self.move_display_up, width=12).pack(side='left', padx=2)
        ttk.Button(reorder_frame, text="▼ Move Down",
                  command=self.move_display_down, width=12).pack(side='left', padx=2)

        # Keyboard control option (always enabled by default)
        self.video_keyboard_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="Enable keyboard control in Processing",
                       variable=self.video_keyboard_var).pack(anchor='w', pady=10)

        # Log output
        ttk.Label(tab, text="Log Output:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=20)
        self.video_log = scrolledtext.ScrolledText(tab, height=6, width=80, state='disabled')
        self.video_log.pack(fill='x', padx=20, pady=5)

    def refresh_displays(self):
        """Refresh display detection."""
        self.all_displays = detect_displays()

        # Initialize active displays if empty (auto-add all available displays)
        if not self.active_displays:
            if len(self.all_displays) >= 2:
                # Use first two displays by default
                self.active_displays = self.all_displays[:2]
                self.inactive_displays = self.all_displays[2:]
            elif len(self.all_displays) == 1:
                # Use the one display available
                self.active_displays = self.all_displays[:1]
                self.inactive_displays = []
            else:
                # No displays found
                self.active_displays = []
                self.inactive_displays = []

        self.update_display_lists()

    def update_display_lists(self):
        """Update the display listboxes."""
        # Clear lists
        self.inactive_listbox.delete(0, tk.END)
        self.active_listbox.delete(0, tk.END)

        # Populate inactive
        for display in self.inactive_displays:
            label = f"Display {display['index']}: {display['name']} ({display['resolution'][0]}x{display['resolution'][1]})"
            self.inactive_listbox.insert(tk.END, label)

        # Populate active
        for i, display in enumerate(self.active_displays):
            label = f"[{i+1}] Display {display['index']}: {display['name']} ({display['resolution'][0]}x{display['resolution'][1]})"
            self.active_listbox.insert(tk.END, label)

    def move_to_active(self, event=None):
        """Move selected display from inactive to active."""
        selection = self.inactive_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        display = self.inactive_displays.pop(idx)
        self.active_displays.append(display)
        self.update_display_lists()

    def move_to_inactive(self, event=None):
        """Move selected display from active to inactive."""
        selection = self.active_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        display = self.active_displays.pop(idx)
        self.inactive_displays.append(display)
        self.update_display_lists()

    def move_display_up(self):
        """Move selected display up in active list."""
        selection = self.active_listbox.curselection()
        if not selection or selection[0] == 0:
            return

        idx = selection[0]
        self.active_displays[idx], self.active_displays[idx-1] = \
            self.active_displays[idx-1], self.active_displays[idx]
        self.update_display_lists()
        self.active_listbox.selection_set(idx-1)

    def move_display_down(self):
        """Move selected display down in active list."""
        selection = self.active_listbox.curselection()
        if not selection or selection[0] == len(self.active_displays) - 1:
            return

        idx = selection[0]
        self.active_displays[idx], self.active_displays[idx+1] = \
            self.active_displays[idx+1], self.active_displays[idx]
        self.update_display_lists()
        self.active_listbox.selection_set(idx+1)

    def on_listbox_hover(self, event, listbox, display_list):
        """Show preview window when hovering over a display in the listbox."""
        # Get the item under cursor
        index = listbox.nearest(event.y)
        if index < 0 or index >= len(display_list):
            self.hide_display_preview()
            return

        display = display_list[index]
        display_index = display['index']

        # Only show if hovering over a different display
        if self.preview_display_index == display_index:
            return

        # Cancel any pending timer
        if self.preview_timer:
            self.root.after_cancel(self.preview_timer)

        # Show preview after short delay (500ms)
        self.preview_timer = self.root.after(500,
            lambda: self.show_display_preview(display))

    def show_display_preview(self, display):
        """Show a preview window on the specified display."""
        # Close existing preview
        self.hide_display_preview()

        # Create a new top-level window
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.attributes('-topmost', True)
        self.preview_window.overrideredirect(True)  # No window decorations

        # Get display info
        display_index = display['index']
        display_name = display['name']
        resolution = display['resolution']

        # Try to position window on the target display
        # Note: Tkinter doesn't have perfect multi-monitor support, so we approximate
        try:
            # Use screeninfo to get monitor geometry if available
            from screeninfo import get_monitors
            monitors = get_monitors()
            if display_index < len(monitors):
                monitor = monitors[display_index]
                x = monitor.x + (monitor.width // 2) - 200
                y = monitor.y + (monitor.height // 2) - 75
            else:
                # Fallback: just center on main display
                x = 300
                y = 300
        except:
            # If screeninfo not available, estimate based on display index
            x = display_index * 1920 + 600  # Assume displays are side-by-side
            y = 400

        # Position and size the window
        self.preview_window.geometry(f"400x150+{x}+{y}")

        # Set background
        self.preview_window.configure(bg='#2c3e50')

        # Add display info
        frame = tk.Frame(self.preview_window, bg='#2c3e50', padx=30, pady=30)
        frame.pack(fill='both', expand=True)

        # Display number (large)
        tk.Label(frame,
                text=f"Display {display_index}",
                font=('Arial', 32, 'bold'),
                bg='#2c3e50',
                fg='#ecf0f1').pack()

        # Display name
        tk.Label(frame,
                text=display_name,
                font=('Arial', 16),
                bg='#2c3e50',
                fg='#95a5a6').pack(pady=(10, 0))

        # Resolution
        tk.Label(frame,
                text=f"{resolution[0]} × {resolution[1]}",
                font=('Arial', 12),
                bg='#2c3e50',
                fg='#7f8c8d').pack()

        self.preview_display_index = display_index

    def hide_display_preview(self, event=None):
        """Hide the display preview window."""
        # Cancel any pending timer
        if self.preview_timer:
            self.root.after_cancel(self.preview_timer)
            self.preview_timer = None

        # Close preview window
        if self.preview_window:
            try:
                self.preview_window.destroy()
            except:
                pass
            self.preview_window = None
            self.preview_display_index = None

    def start_video(self):
        """Start Processing video system."""
        if self.video_running:
            return

        if not self.active_displays:
            self.log_to_widget(self.video_log, "✗ No active displays selected")
            messagebox.showwarning("No Displays", "Please add at least one display to the Active list.")
            return

        # Get display indices in order
        display_indices = [d['index'] for d in self.active_displays]

        self.log_to_widget(self.video_log, "Starting Processing video system...")
        self.log_to_widget(self.video_log, f"  Active displays: {display_indices}")
        self.log_to_widget(self.video_log, f"  Keyboard enabled: {self.video_keyboard_var.get()}")

        def start_thread():
            success = self.core.start_processing(
                displays=display_indices,
                enable_keyboard=self.video_keyboard_var.get()
            )

            if success:
                self.video_running = True
                self.root.after(0, self.update_video_ui, True)
                self.log_to_widget(self.video_log, "✓ Processing started")
            else:
                self.log_to_widget(self.video_log, "✗ Failed to start Processing")
                self.root.after(0, self.update_video_ui, False)

        threading.Thread(target=start_thread, daemon=True).start()

    def stop_video(self):
        """Stop Processing video system."""
        if not self.video_running:
            return

        self.log_to_widget(self.video_log, "Stopping Processing...")

        def stop_thread():
            if self.core.stop_processing():
                self.video_running = False
                self.log_to_widget(self.video_log, "✓ Processing stopped")
            else:
                self.log_to_widget(self.video_log, "✗ Failed to stop Processing")

            self.root.after(0, self.update_video_ui, False)

        threading.Thread(target=stop_thread, daemon=True).start()

    def update_video_ui(self, running: bool):
        """Update video UI based on running state."""
        if running:
            self.video_status_label.config(text="● Running", foreground='green')
            self.video_start_btn.config(state='disabled')
            self.video_stop_btn.config(state='normal')
        else:
            self.video_status_label.config(text="● Stopped", foreground='red')
            self.video_start_btn.config(state='normal')
            self.video_stop_btn.config(state='disabled')

    # ========================================================================
    # AUDIO TAB
    # ========================================================================

    def create_audio_tab(self, notebook):
        """Create Audio/SuperCollider tab with device dropdowns."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Audio")

        # Header
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(header_frame, text="Audio System (SuperCollider)",
                 font=('Arial', 16, 'bold')).pack(side='left')

        # Refresh button
        ttk.Button(header_frame, text="↻ Refresh Devices",
                  command=self.refresh_audio_devices, width=15).pack(side='right', padx=5)

        # Status
        status_frame = ttk.LabelFrame(tab, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=5)

        self.audio_status_label = ttk.Label(status_frame, text="● Stopped",
                                           foreground='red', font=('Arial', 14, 'bold'))
        self.audio_status_label.pack()

        # Control buttons
        control_frame = ttk.Frame(tab)
        control_frame.pack(pady=10)

        self.audio_start_btn = ttk.Button(control_frame, text="▶ Start Audio",
                                         command=self.start_audio, width=20)
        self.audio_start_btn.pack(side='left', padx=5)

        self.audio_stop_btn = ttk.Button(control_frame, text="■ Stop Audio",
                                        command=self.stop_audio, width=20, state='disabled')
        self.audio_stop_btn.pack(side='left', padx=5)

        # Configuration
        config_frame = ttk.LabelFrame(tab, text="Audio Configuration", padding=10)
        config_frame.pack(fill='x', padx=20, pady=10)

        # Audio device dropdown
        device_frame = ttk.Frame(config_frame)
        device_frame.pack(fill='x', pady=5)

        ttk.Label(device_frame, text="Audio Device:", width=15).pack(side='left', padx=5)
        self.audio_device_var = tk.StringVar(value="Default")
        self.audio_device_dropdown = ttk.Combobox(device_frame,
                                                  textvariable=self.audio_device_var,
                                                  state='readonly', width=40)
        self.audio_device_dropdown.pack(side='left', padx=5)

        # Volume control
        volume_frame = ttk.Frame(config_frame)
        volume_frame.pack(fill='x', pady=5)

        ttk.Label(volume_frame, text="Master Volume:", width=15).pack(side='left', padx=5)
        self.volume_var = tk.DoubleVar(value=0.7)
        self.volume_slider = tk.Scale(volume_frame, from_=0.0, to=1.0, resolution=0.01,
                                      orient='horizontal', variable=self.volume_var,
                                      command=self.on_volume_change, length=300)
        self.volume_slider.pack(side='left', padx=5)
        self.volume_label = ttk.Label(volume_frame, text="70%", width=6)
        self.volume_label.pack(side='left', padx=5)

        # Log output
        ttk.Label(tab, text="Log Output:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=20, pady=(10,0))
        self.audio_log = scrolledtext.ScrolledText(tab, height=10, width=80, state='disabled')
        self.audio_log.pack(fill='both', expand=True, padx=20, pady=5)

    def refresh_audio_devices(self):
        """Refresh audio device detection."""
        devices = CarpetHotelSuperCollider.detect_devices()
        devices = ["Default"] + devices
        self.audio_device_dropdown['values'] = devices
        self.log_to_widget(self.audio_log, f"Found {len(devices)} audio devices")

    def on_volume_change(self, value):
        """Handle volume slider change."""
        volume = float(value)
        # Update label
        self.volume_label.config(text=f"{int(volume * 100)}%")

        # Update core state
        if self.core:
            self.core.master_volume = volume

        # Save setting
        self.settings.set("master_volume", volume)

        # Send to SuperCollider if running
        if self.audio_running and OSC_AVAILABLE:
            try:
                client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
                client.send_message("/carpet/volume", [volume])
                self.log_to_widget(self.audio_log, f"Volume: {int(volume * 100)}%")
            except Exception as e:
                self.log_to_widget(self.audio_log, f"✗ Error setting volume: {e}")

    def start_audio(self):
        """Start SuperCollider audio system."""
        if self.audio_running:
            return

        self.log_to_widget(self.audio_log, "Starting SuperCollider audio system...")
        self.log_to_widget(self.audio_log, "(Using macOS system default audio device)")

        def start_thread():
            success = self.core.start_supercollider()

            if success:
                self.audio_running = True
                self.root.after(0, self.update_audio_ui, True)
                self.log_to_widget(self.audio_log, "✓ SuperCollider started")
            else:
                self.log_to_widget(self.audio_log, "✗ Failed to start SuperCollider")
                self.log_to_widget(self.audio_log, "  See AUDIO_SETUP.md for configuration help")
                self.root.after(0, self.update_audio_ui, False)

        threading.Thread(target=start_thread, daemon=True).start()

    def stop_audio(self):
        """Stop SuperCollider audio system."""
        if not self.audio_running:
            return

        self.log_to_widget(self.audio_log, "Stopping SuperCollider...")

        def stop_thread():
            if self.core.stop_supercollider():
                self.audio_running = False
                self.log_to_widget(self.audio_log, "✓ SuperCollider stopped")
            else:
                self.log_to_widget(self.audio_log, "✗ Failed to stop SuperCollider")

            self.root.after(0, self.update_audio_ui, False)

        threading.Thread(target=stop_thread, daemon=True).start()

    def update_audio_ui(self, running: bool):
        """Update audio UI based on running state."""
        if running:
            self.audio_status_label.config(text="● Running", foreground='green')
            self.audio_start_btn.config(state='disabled')
            self.audio_stop_btn.config(state='normal')
        else:
            self.audio_status_label.config(text="● Stopped", foreground='red')
            self.audio_start_btn.config(state='normal')
            self.audio_stop_btn.config(state='disabled')

    # ========================================================================
    # HARDWARE TAB
    # ========================================================================

    def create_hardware_tab(self, notebook):
        """Create Hardware/Arduino tab with connect button."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Hardware")

        # Header
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(header_frame, text="Hardware System (Arduino)",
                 font=('Arial', 16, 'bold')).pack(side='left')

        # Refresh button
        ttk.Button(header_frame, text="↻ Refresh Ports",
                  command=self.refresh_serial_ports, width=15).pack(side='right', padx=5)

        # Status
        status_frame = ttk.LabelFrame(tab, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=5)

        self.hardware_status_label = ttk.Label(status_frame, text="● Disconnected",
                                              foreground='red', font=('Arial', 14, 'bold'))
        self.hardware_status_label.pack()

        # Control buttons
        control_frame = ttk.Frame(tab)
        control_frame.pack(pady=10)

        self.hardware_connect_btn = ttk.Button(control_frame, text="▶ Connect",
                                              command=self.connect_hardware, width=20)
        self.hardware_connect_btn.pack(side='left', padx=5)

        self.hardware_disconnect_btn = ttk.Button(control_frame, text="■ Disconnect",
                                                 command=self.disconnect_hardware,
                                                 width=20, state='disabled')
        self.hardware_disconnect_btn.pack(side='left', padx=5)

        # Serial port configuration
        config_frame = ttk.LabelFrame(tab, text="Serial Port Configuration", padding=10)
        config_frame.pack(fill='x', padx=20, pady=10)

        port_frame = ttk.Frame(config_frame)
        port_frame.pack(fill='x', pady=5)

        ttk.Label(port_frame, text="Serial Port:", width=15).pack(side='left', padx=5)
        self.serial_port_var = tk.StringVar(value="")
        self.serial_port_dropdown = ttk.Combobox(port_frame,
                                                textvariable=self.serial_port_var,
                                                state='readonly', width=40)
        self.serial_port_dropdown.pack(side='left', padx=5)

        # LED Controls
        led_frame = ttk.LabelFrame(tab, text="LED Control", padding=10)
        led_frame.pack(fill='x', padx=20, pady=10)

        # Individual LEDs
        ttk.Label(led_frame, text="Individual LEDs:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(5,2))
        led_btn_frame = ttk.Frame(led_frame)
        led_btn_frame.pack(fill='x', pady=5)

        for color in [('Red', 'red'), ('Yellow', 'yellow'), ('Green', 'green')]:
            frame = ttk.Frame(led_btn_frame)
            frame.pack(side='left', padx=10)
            ttk.Label(frame, text=f"{color[0]}:", width=8).pack(side='left')
            ttk.Button(frame, text="ON",
                      command=lambda c=color[1]: self.set_led(c, 255),
                      width=6).pack(side='left', padx=2)
            ttk.Button(frame, text="OFF",
                      command=lambda c=color[1]: self.set_led(c, 0),
                      width=6).pack(side='left', padx=2)

        # LED Animations
        ttk.Label(led_frame, text="LED Animations:", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(10,2))
        anim_frame = ttk.Frame(led_frame)
        anim_frame.pack(fill='x', pady=5)

        ttk.Button(anim_frame, text="Stable Mode",
                  command=lambda: self.set_led_animation('STABLE'),
                  width=15).pack(side='left', padx=5)
        ttk.Button(anim_frame, text="Transition Mode",
                  command=lambda: self.set_led_animation('TRANSITION'),
                  width=15).pack(side='left', padx=5)
        ttk.Button(anim_frame, text="Off",
                  command=lambda: self.set_led_animation('OFF'),
                  width=15).pack(side='left', padx=5)

        # Log output
        ttk.Label(tab, text="Log Output:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=20, pady=(10,0))
        self.hardware_log = scrolledtext.ScrolledText(tab, height=10, width=80, state='disabled')
        self.hardware_log.pack(fill='both', expand=True, padx=20, pady=5)

    def refresh_serial_ports(self):
        """Refresh serial port detection."""
        ports = detect_serial_ports()
        port_labels = []

        for port in ports:
            label = f"{port['device']}"
            if port['is_arduino']:
                label += " [Arduino]"
            label += f" - {port['description']}"
            port_labels.append(label)

        self.serial_port_dropdown['values'] = port_labels

        # Auto-select first Arduino port if found
        for i, label in enumerate(port_labels):
            if "[Arduino]" in label:
                self.serial_port_var.set(label)
                break

        self.log_to_widget(self.hardware_log, f"Found {len(ports)} serial ports")

    def connect_hardware(self):
        """Connect to Arduino."""
        if self.hardware_running:
            return

        port = self.serial_port_var.get()
        if not port:
            self.log_to_widget(self.hardware_log, "✗ Please select a serial port")
            return

        # Extract just the device path
        port = port.split()[0]

        self.log_to_widget(self.hardware_log, "Connecting to Arduino...")

        def connect_thread():
            success = self.core.start_arduino(port)

            if success:
                # Set message callback for logging
                if self.core.arduino:
                    def arduino_message_callback(msg):
                        self.root.after(0, lambda: self.log_to_widget(self.hardware_log, msg))

                    self.core.arduino.set_message_callback(arduino_message_callback)

                self.hardware_running = True
                self.root.after(0, self.update_hardware_ui, True)
                self.log_to_widget(self.hardware_log, "✓ Arduino connected")
            else:
                self.log_to_widget(self.hardware_log, "✗ Failed to connect to Arduino")
                self.root.after(0, self.update_hardware_ui, False)

        threading.Thread(target=connect_thread, daemon=True).start()

    def disconnect_hardware(self):
        """Disconnect from Arduino."""
        if not self.hardware_running:
            return

        self.log_to_widget(self.hardware_log, "Disconnecting Arduino...")

        def disconnect_thread():
            if self.core.stop_arduino():
                self.hardware_running = False
                self.log_to_widget(self.hardware_log, "✓ Arduino disconnected")
            else:
                self.log_to_widget(self.hardware_log, "✗ Failed to disconnect Arduino")

            self.root.after(0, self.update_hardware_ui, False)

        threading.Thread(target=disconnect_thread, daemon=True).start()

    def update_hardware_ui(self, running: bool):
        """Update hardware UI based on running state."""
        if running:
            self.hardware_status_label.config(text="● Connected", foreground='green')
            self.hardware_connect_btn.config(state='disabled')
            self.hardware_disconnect_btn.config(state='normal')
        else:
            self.hardware_status_label.config(text="● Disconnected", foreground='red')
            self.hardware_connect_btn.config(state='normal')
            self.hardware_disconnect_btn.config(state='disabled')

    # ========================================================================
    # COMMAND TAB
    # ========================================================================

    def create_command_tab(self, notebook):
        """Create Control tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Control")

        # Header
        ttk.Label(tab, text="System Control",
                 font=('Arial', 16, 'bold')).pack(pady=10)

        # Main container frame
        container_frame = ttk.Frame(tab)
        container_frame.pack(fill='both', expand=True, padx=20, pady=5)

        # Controls frame (scrollable)
        canvas = tk.Canvas(container_frame)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Elevator Controls
        elevator_frame = ttk.LabelFrame(scrollable_frame, text="Elevator Control", padding=10)
        elevator_frame.pack(fill='x', padx=20, pady=5)

        btn_frame = ttk.Frame(elevator_frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="▲ UP", command=self.scene_up,
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="▼ DOWN", command=self.scene_down,
                  width=15).pack(side='left', padx=5)

        # Scene Selection
        scene_frame = ttk.LabelFrame(scrollable_frame, text="Scene Selection", padding=10)
        scene_frame.pack(fill='x', padx=20, pady=5)

        scene_select_frame = ttk.Frame(scene_frame)
        scene_select_frame.pack(fill='x', pady=5)

        ttk.Label(scene_select_frame, text="Go to Scene:", width=12).pack(side='left', padx=5)

        # Dropdown for scenes (dynamically calculated based on video files and displays)
        self.scene_var = tk.StringVar(value="0")
        self.scene_dropdown = ttk.Combobox(scene_select_frame, textvariable=self.scene_var,
                                           state='readonly', width=10)
        self.scene_dropdown.pack(side='left', padx=5)
        self.update_scene_dropdown()  # Populate with correct number of scenes

        ttk.Button(scene_select_frame, text="Go",
                  command=lambda: self.send_osc_command('/carpet/goto', [int(self.scene_var.get())]),
                  width=10).pack(side='left', padx=5)

        # Raw OSC Command section
        osc_frame = ttk.LabelFrame(scrollable_frame, text="Custom OSC Command", padding=10)
        osc_frame.pack(fill='x', padx=20, pady=5)

        ttk.Label(osc_frame, text="Send any OSC command directly", foreground='gray').pack(anchor='w')

        input_frame = ttk.Frame(osc_frame)
        input_frame.pack(fill='x', pady=5)

        ttk.Label(input_frame, text="Address:", width=10).pack(side='left', padx=5)
        self.osc_address_var = tk.StringVar(value="/carpet/")
        ttk.Entry(input_frame, textvariable=self.osc_address_var, width=25).pack(side='left', padx=5)

        ttk.Label(input_frame, text="Args:", width=6).pack(side='left', padx=5)
        self.osc_args_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.osc_args_var, width=20).pack(side='left', padx=5)

        ttk.Button(input_frame, text="Send", command=self.send_raw_osc, width=10).pack(side='left', padx=5)

        ttk.Label(osc_frame, text='Example: /carpet/volume 0.5  or  /carpet/scene 0 2 0',
                 foreground='gray', font=('Arial', 9)).pack(anchor='w', padx=5)

        # Pack canvas and scrollbar in container
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Command log below controls
        log_frame = ttk.Frame(tab)
        log_frame.pack(fill='x', padx=20, pady=(10,10))

        ttk.Label(log_frame, text="Control Log:", font=('Arial', 10, 'bold')).pack(anchor='w')
        self.command_log = scrolledtext.ScrolledText(log_frame, height=8, width=80, state='disabled')
        self.command_log.pack(fill='both', expand=True)

    # ========================================================================
    # VIDEO CONFIG TAB
    # ========================================================================

    def create_video_config_tab(self, notebook):
        """Create Video Config tab for editing Processing parameters."""
        import json
        from pathlib import Path

        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Video Config")

        # Header
        header_frame = ttk.Frame(tab)
        header_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(header_frame, text="Video Configuration",
                 font=('Arial', 16, 'bold')).pack(side='left')

        # Buttons
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side='right')

        ttk.Button(btn_frame, text="↻ Reload", command=self.reload_video_config,
                  width=12).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="💾 Save", command=self.save_video_config,
                  width=12).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="⟲ Reset", command=self.reset_video_config,
                  width=12).pack(side='left', padx=2)

        # Main scrollable area
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Config storage for widgets
        self.video_config_vars = {}

        # ===== ANIMATION SECTION =====
        anim_frame = ttk.LabelFrame(scrollable_frame, text="Animation", padding=10)
        anim_frame.pack(fill='x', padx=20, pady=5)

        self._add_float_slider(anim_frame, "Speed", "animation.speed", 0.01, 1.0, 0.1)
        self._add_string_dropdown(anim_frame, "Easing Curve", "animation.easing_curve",
                                  ["linear", "sine", "quad", "cubic", "quart", "quint"], "sine")
        self._add_float_slider(anim_frame, "Distance Multiplier", "animation.distance_multiplier", 0.5, 2.0, 1.0)

        # ===== EFFECTS SECTION =====
        effects_frame = ttk.LabelFrame(scrollable_frame, text="Effects", padding=10)
        effects_frame.pack(fill='x', padx=20, pady=5)

        # Chromatic Aberration
        chrom_frame = ttk.Frame(effects_frame)
        chrom_frame.pack(fill='x', pady=5)
        ttk.Label(chrom_frame, text="Chromatic Aberration",
                 font=('Arial', 11, 'bold')).pack(anchor='w')

        self._add_checkbox(chrom_frame, "Enabled", "effects.chromatic_aberration.enabled", True)
        self._add_float_slider(chrom_frame, "Intensity", "effects.chromatic_aberration.intensity", 0.0, 20.0, 8.0)
        self._add_int_slider(chrom_frame, "Red Alpha", "effects.chromatic_aberration.red_alpha", 0, 255, 200)
        self._add_int_slider(chrom_frame, "Green Alpha", "effects.chromatic_aberration.green_alpha", 0, 255, 200)
        self._add_int_slider(chrom_frame, "Blue Alpha", "effects.chromatic_aberration.blue_alpha", 0, 255, 200)

        ttk.Separator(effects_frame, orient='horizontal').pack(fill='x', pady=10)

        # Motion Blur
        blur_frame = ttk.Frame(effects_frame)
        blur_frame.pack(fill='x', pady=5)
        ttk.Label(blur_frame, text="Motion Blur",
                 font=('Arial', 11, 'bold')).pack(anchor='w')

        self._add_checkbox(blur_frame, "Enabled", "effects.motion_blur.enabled", True)
        self._add_int_slider(blur_frame, "Samples", "effects.motion_blur.samples", 1, 10, 3)
        self._add_float_slider(blur_frame, "Intensity", "effects.motion_blur.intensity", 0.0, 30.0, 15.0)
        self._add_int_slider(blur_frame, "Alpha Divisor", "effects.motion_blur.alpha_divisor", 1, 10, 2)

        ttk.Separator(effects_frame, orient='horizontal').pack(fill='x', pady=10)

        # Bloom
        bloom_frame = ttk.Frame(effects_frame)
        bloom_frame.pack(fill='x', pady=5)
        ttk.Label(bloom_frame, text="Bloom",
                 font=('Arial', 11, 'bold')).pack(anchor='w')

        self._add_checkbox(bloom_frame, "Enabled", "effects.bloom.enabled", True)
        self._add_float_slider(bloom_frame, "Intensity", "effects.bloom.intensity", 0.0, 150.0, 80.0)

        ttk.Separator(effects_frame, orient='horizontal').pack(fill='x', pady=10)

        # General Effect Settings
        self._add_float_slider(effects_frame, "Max Effect Intensity", "effects.max_effect_intensity", 0.0, 1.0, 0.8)
        self._add_float_slider(effects_frame, "Effect Threshold", "effects.effect_threshold", 0.0, 0.5, 0.05)

        # ===== TIMING SECTION =====
        timing_frame = ttk.LabelFrame(scrollable_frame, text="Timing", padding=10)
        timing_frame.pack(fill='x', padx=20, pady=5)

        self._add_string_dropdown(timing_frame, "Velocity Curve", "timing.velocity_curve",
                                  ["linear", "sine_ease", "quad_ease", "smooth"], "sine_ease")
        self._add_float_slider(timing_frame, "Acceleration Phase", "timing.acceleration_phase", 0.0, 1.0, 0.3)
        self._add_float_slider(timing_frame, "Deceleration Phase", "timing.deceleration_phase", 0.0, 1.0, 0.7)

        # ===== ADVANCED SECTION =====
        adv_frame = ttk.LabelFrame(scrollable_frame, text="Advanced", padding=10)
        adv_frame.pack(fill='x', padx=20, pady=5)

        self._add_float_slider(adv_frame, "Floor Spacing Multiplier", "advanced.floor_spacing_multiplier", 0.5, 2.0, 1.0)
        self._add_float_slider(adv_frame, "Transition Smoothness", "advanced.transition_smoothness", 0.1, 2.0, 1.0)
        self._add_string_dropdown(adv_frame, "Effect Intensity Curve", "advanced.effect_intensity_curve",
                                  ["linear", "sine", "quad", "exponential"], "sine")

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(20,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        # Load current config
        self.reload_video_config()

    def _add_checkbox(self, parent, label, config_key, default_value):
        """Add a checkbox to the config UI."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)

        var = tk.BooleanVar(value=default_value)
        self.video_config_vars[config_key] = var

        cb = ttk.Checkbutton(frame, text=label, variable=var)
        cb.pack(anchor='w', padx=20)

    def _add_float_slider(self, parent, label, config_key, min_val, max_val, default_val):
        """Add a float slider to the config UI."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)

        label_frame = ttk.Frame(frame)
        label_frame.pack(fill='x')

        ttk.Label(label_frame, text=label, width=25).pack(side='left', padx=20)

        var = tk.DoubleVar(value=default_val)
        value_label = ttk.Label(label_frame, text=f"{default_val:.2f}", width=8)
        value_label.pack(side='right', padx=20)

        slider = ttk.Scale(frame, from_=min_val, to=max_val, orient='horizontal',
                          variable=var, command=lambda v: value_label.config(text=f"{float(v):.2f}"))
        slider.pack(fill='x', padx=20)

        self.video_config_vars[config_key] = var

    def _add_int_slider(self, parent, label, config_key, min_val, max_val, default_val):
        """Add an integer slider to the config UI."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)

        label_frame = ttk.Frame(frame)
        label_frame.pack(fill='x')

        ttk.Label(label_frame, text=label, width=25).pack(side='left', padx=20)

        var = tk.IntVar(value=default_val)
        value_label = ttk.Label(label_frame, text=str(default_val), width=8)
        value_label.pack(side='right', padx=20)

        slider = ttk.Scale(frame, from_=min_val, to=max_val, orient='horizontal',
                          variable=var, command=lambda v: value_label.config(text=str(int(float(v)))))
        slider.pack(fill='x', padx=20)

        self.video_config_vars[config_key] = var

    def _add_string_dropdown(self, parent, label, config_key, options, default_val):
        """Add a string dropdown to the config UI."""
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=2)

        ttk.Label(frame, text=label, width=25).pack(side='left', padx=20)

        var = tk.StringVar(value=default_val)
        dropdown = ttk.Combobox(frame, textvariable=var, values=options,
                               state='readonly', width=15)
        dropdown.pack(side='left', padx=5)

        self.video_config_vars[config_key] = var

    def reload_video_config(self):
        """Reload video config from JSON file."""
        import json
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "configs" / "video_config.json"

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Update all variables from config
            for key, var in self.video_config_vars.items():
                keys = key.split('.')
                value = config
                for k in keys:
                    value = value.get(k, None)
                    if value is None:
                        break

                if value is not None:
                    var.set(value)

            messagebox.showinfo("Config Loaded", "Video configuration reloaded from file")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_video_config(self):
        """Save video config to JSON file."""
        import json
        from pathlib import Path

        config_path = Path(__file__).parent.parent / "configs" / "video_config.json"

        try:
            # Build config dict from variables
            config = {
                "animation": {
                    "speed": self.video_config_vars["animation.speed"].get(),
                    "easing_curve": self.video_config_vars["animation.easing_curve"].get(),
                    "distance_multiplier": self.video_config_vars["animation.distance_multiplier"].get()
                },
                "effects": {
                    "chromatic_aberration": {
                        "enabled": self.video_config_vars["effects.chromatic_aberration.enabled"].get(),
                        "intensity": self.video_config_vars["effects.chromatic_aberration.intensity"].get(),
                        "red_alpha": self.video_config_vars["effects.chromatic_aberration.red_alpha"].get(),
                        "green_alpha": self.video_config_vars["effects.chromatic_aberration.green_alpha"].get(),
                        "blue_alpha": self.video_config_vars["effects.chromatic_aberration.blue_alpha"].get()
                    },
                    "motion_blur": {
                        "enabled": self.video_config_vars["effects.motion_blur.enabled"].get(),
                        "samples": self.video_config_vars["effects.motion_blur.samples"].get(),
                        "intensity": self.video_config_vars["effects.motion_blur.intensity"].get(),
                        "alpha_divisor": self.video_config_vars["effects.motion_blur.alpha_divisor"].get()
                    },
                    "bloom": {
                        "enabled": self.video_config_vars["effects.bloom.enabled"].get(),
                        "intensity": self.video_config_vars["effects.bloom.intensity"].get()
                    },
                    "max_effect_intensity": self.video_config_vars["effects.max_effect_intensity"].get(),
                    "effect_threshold": self.video_config_vars["effects.effect_threshold"].get()
                },
                "timing": {
                    "velocity_curve": self.video_config_vars["timing.velocity_curve"].get(),
                    "acceleration_phase": self.video_config_vars["timing.acceleration_phase"].get(),
                    "deceleration_phase": self.video_config_vars["timing.deceleration_phase"].get()
                },
                "advanced": {
                    "floor_spacing_multiplier": self.video_config_vars["advanced.floor_spacing_multiplier"].get(),
                    "transition_smoothness": self.video_config_vars["advanced.transition_smoothness"].get(),
                    "effect_intensity_curve": self.video_config_vars["advanced.effect_intensity_curve"].get()
                }
            }

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            messagebox.showinfo("Config Saved", "Video configuration saved successfully.\nPress 'R' in Processing to reload.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def reset_video_config(self):
        """Reset video config to defaults."""
        import json
        from pathlib import Path

        if not messagebox.askyesno("Reset Config", "Reset all video settings to defaults?"):
            return

        config_path = Path(__file__).parent.parent / "configs" / "video_config.json"

        # Default config
        default_config = {
            "animation": {
                "speed": 0.1,
                "easing_curve": "sine",
                "distance_multiplier": 1.0
            },
            "effects": {
                "chromatic_aberration": {
                    "enabled": True,
                    "intensity": 8.0,
                    "red_alpha": 200,
                    "green_alpha": 200,
                    "blue_alpha": 200
                },
                "motion_blur": {
                    "enabled": True,
                    "samples": 3,
                    "intensity": 15.0,
                    "alpha_divisor": 2
                },
                "bloom": {
                    "enabled": True,
                    "intensity": 80.0
                },
                "max_effect_intensity": 0.8,
                "effect_threshold": 0.05
            },
            "timing": {
                "velocity_curve": "sine_ease",
                "acceleration_phase": 0.3,
                "deceleration_phase": 0.7
            },
            "advanced": {
                "floor_spacing_multiplier": 1.0,
                "transition_smoothness": 1.0,
                "effect_intensity_curve": "sine"
            }
        }

        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)

            # Reload into GUI
            self.reload_video_config()

            messagebox.showinfo("Config Reset", "Video configuration reset to defaults.\nPress 'R' in Processing to reload.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset config: {e}")

    def send_osc_command(self, address: str, args: list):
        """Send OSC command to the system."""
        if not OSC_AVAILABLE:
            self.log_to_widget(self.command_log, "✗ python-osc not installed")
            return

        try:
            # Send to SuperCollider (audio commands)
            if '/carpet/volume' in address or '/carpet/scene' in address or '/carpet/transition' in address:
                client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
                client.send_message(address, args)
                self.log_to_widget(self.command_log, f"→ SC: {address} {args}")

            # Send to Processing (video/scene commands)
            elif '/carpet/goto' in address or '/carpet/elevator' in address:
                client = udp_client.SimpleUDPClient("127.0.0.1", 12000)
                client.send_message(address, args)
                self.log_to_widget(self.command_log, f"→ Processing: {address} {args}")

            # LED commands go to Arduino
            elif '/carpet/led' in address:
                client = udp_client.SimpleUDPClient("127.0.0.1", 12002)
                client.send_message(address, args)
                self.log_to_widget(self.command_log, f"→ Arduino: {address} {args}")

            # Default: send to Processing
            else:
                client = udp_client.SimpleUDPClient("127.0.0.1", 12000)
                client.send_message(address, args)
                self.log_to_widget(self.command_log, f"→ {address} {args}")

        except Exception as e:
            self.log_to_widget(self.command_log, f"✗ Error: {e}")

    def update_scene_dropdown(self):
        """Update scene dropdown based on current display configuration."""
        max_scene = self.core.get_max_scene()
        num_scenes = max_scene + 1
        self.scene_dropdown['values'] = list(range(num_scenes))

        # Log if command_log exists (may be called during initialization)
        if hasattr(self, 'command_log'):
            self.log_to_widget(self.command_log, f"Scenes available: {num_scenes} (0-{max_scene})")

    def scene_up(self):
        """Increment scene and send goto command."""
        max_scene = self.core.get_max_scene()
        current = int(self.scene_var.get())
        new_scene = (current + 1) % (max_scene + 1)
        self.scene_var.set(str(new_scene))
        self.send_osc_command('/carpet/goto', [new_scene])

    def scene_down(self):
        """Decrement scene and send goto command."""
        max_scene = self.core.get_max_scene()
        current = int(self.scene_var.get())
        new_scene = (current - 1) % (max_scene + 1)
        self.scene_var.set(str(new_scene))
        self.send_osc_command('/carpet/goto', [new_scene])

    def set_led(self, color: str, value: int):
        """Set individual LED (from GUI button - bypasses animation temporarily)."""
        if self.hardware_running and self.core.arduino and self.core.arduino.broker:
            try:
                # Use broker for thread-safe write
                self.core.arduino.broker.write_led(color, value)
                self.log_to_widget(self.hardware_log, f"→ LED {color.upper()}: {value}")
            except Exception as e:
                self.log_to_widget(self.hardware_log, f"✗ Error: {e}")
        else:
            self.log_to_widget(self.hardware_log, "✗ Arduino not connected")

    def set_led_animation(self, mode: str):
        """Set LED animation mode."""
        if self.hardware_running and self.core.arduino:
            try:
                self.core.arduino.set_led_animation_mode(mode)
                self.log_to_widget(self.hardware_log, f"→ LED mode: {mode}")
            except Exception as e:
                self.log_to_widget(self.hardware_log, f"✗ Error: {e}")
        else:
            self.log_to_widget(self.hardware_log, "✗ Arduino not connected")

    def send_raw_osc(self):
        """Send raw OSC command from user input."""
        if not OSC_AVAILABLE:
            self.log_to_widget(self.command_log, "✗ python-osc not installed")
            return

        osc_address = self.osc_address_var.get().strip()
        args_str = self.osc_args_var.get().strip()

        if not osc_address:
            self.log_to_widget(self.command_log, "✗ OSC address required")
            return

        # Parse arguments
        args = []
        if args_str:
            for arg in args_str.split():
                try:
                    args.append(int(arg))
                except ValueError:
                    try:
                        args.append(float(arg))
                    except ValueError:
                        args.append(arg)

        # Send using the standard method
        self.send_osc_command(osc_address, args)

    # ========================================================================
    # GLOBAL CONTROLS
    # ========================================================================

    def create_global_controls(self):
        """Create global control buttons at bottom."""
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=5)

        global_frame = ttk.Frame(self.root)
        global_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(global_frame, text="Global Control:",
                 font=('Arial', 14, 'bold')).pack(side='left', padx=10)

        ttk.Button(global_frame, text="▶ START ALL",
                  command=self.start_all, width=20).pack(side='left', padx=5)

        ttk.Button(global_frame, text="■ STOP ALL",
                  command=self.stop_all, width=20).pack(side='left', padx=5)

    def start_all(self):
        """Start all systems."""
        if not self.video_running:
            self.start_video()
            time.sleep(1)

        if not self.audio_running:
            self.start_audio()
            time.sleep(1)

        if not self.hardware_running:
            self.connect_hardware()

    def stop_all(self):
        """Stop all systems."""
        if self.hardware_running:
            self.disconnect_hardware()

        if self.video_running:
            self.stop_video()

        if self.audio_running:
            self.stop_audio()

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def log_to_widget(self, widget, message: str):
        """Log message to a scrolled text widget and to log files."""
        # Write to GUI widget
        widget.config(state='normal')
        widget.insert(tk.END, message + "\n")
        widget.see(tk.END)
        widget.config(state='disabled')

        # Also write to appropriate log file
        from components.logger import get_logger
        if widget == self.video_log:
            logger = get_logger("Processing")
        elif widget == self.audio_log:
            logger = get_logger("SuperCollider")
        elif widget == self.hardware_log:
            logger = get_logger("Arduino")
        elif widget == self.command_log:
            logger = get_logger("Core")
        else:
            logger = get_logger("Core")

        # Parse message to determine log level
        if message.startswith("✓"):
            logger.success(message[2:])  # Remove "✓ " prefix
        elif message.startswith("✗"):
            logger.error(message[2:])  # Remove "✗ " prefix
        elif message.startswith("→"):
            logger.info(message[2:])  # Remove "→ " prefix
        else:
            logger.info(message)

    def _poll_status(self):
        """Poll core status and update GUI if state changes."""
        # Check video/Processing status
        if self.video_running != self.core.pde_running:
            if self.video_running and not self.core.pde_running:
                # Processing stopped unexpectedly
                self.log_to_widget(self.video_log, "✗ Processing exited")
            self.video_running = self.core.pde_running
            self.update_video_ui(self.video_running)

        # Check audio/SuperCollider status
        if self.audio_running != self.core.sc_running:
            if self.audio_running and not self.core.sc_running:
                # SC stopped unexpectedly
                self.log_to_widget(self.audio_log, "✗ SuperCollider exited")
            self.audio_running = self.core.sc_running
            self.update_audio_ui(self.audio_running)

        # Check Arduino status
        if self.hardware_running != self.core.arduino_running:
            if self.hardware_running and not self.core.arduino_running:
                # Arduino disconnected unexpectedly
                self.log_to_widget(self.hardware_log, "✗ Arduino disconnected")
            self.hardware_running = self.core.arduino_running
            self.update_hardware_ui(self.hardware_running)

        # Schedule next poll in 500ms
        self.root.after(500, self._poll_status)

    # ========================================================================
    # SETTINGS PERSISTENCE
    # ========================================================================

    def load_settings(self):
        """Load saved settings and apply to GUI."""
        # Apply saved volume
        volume = self.settings.get("master_volume", DEFAULT_SETTINGS["master_volume"])
        self.volume_var.set(volume)
        self.volume_label.config(text=f"{int(volume * 100)}%")
        self.core.master_volume = volume

        # Apply saved audio device
        audio_device = self.settings.get("audio_device", DEFAULT_SETTINGS["audio_device"])
        if audio_device:
            self.audio_device_var.set(audio_device)

        # Apply saved serial port
        serial_port = self.settings.get("serial_port", DEFAULT_SETTINGS["serial_port"])
        if serial_port:
            self.serial_port_var.set(serial_port)

        # Apply saved keyboard setting
        enable_keyboard = self.settings.get("enable_keyboard", DEFAULT_SETTINGS["enable_keyboard"])
        self.video_keyboard_var.set(enable_keyboard)

        # Apply saved display lists
        saved_active = self.settings.get("active_displays", DEFAULT_SETTINGS["active_displays"])
        saved_inactive = self.settings.get("inactive_displays", DEFAULT_SETTINGS["inactive_displays"])

        # Only restore if we have saved displays
        if saved_active or saved_inactive:
            self.active_displays = saved_active
            self.inactive_displays = saved_inactive
            self.update_display_lists()

            if saved_active:
                self.core.num_displays = len(saved_active)
                # Update scene dropdown based on displays
                self.root.after(100, self.update_scene_dropdown)

        # Apply saved window geometry
        window_x = self.settings.get("window_x")
        window_y = self.settings.get("window_y")
        window_width = self.settings.get("window_width", DEFAULT_SETTINGS["window_width"])
        window_height = self.settings.get("window_height", DEFAULT_SETTINGS["window_height"])

        if window_x is not None and window_y is not None:
            self.root.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
        else:
            self.root.geometry(f"{window_width}x{window_height}")

        print(f"✓ Settings loaded: volume={int(volume*100)}%, active_displays={len(saved_active)}, keyboard={enable_keyboard}")

    def save_settings(self):
        """Save current GUI settings."""
        # Get window geometry
        geometry = self.root.geometry()  # Returns "widthxheight+x+y"
        try:
            size, position = geometry.split('+', 1)
            width, height = map(int, size.split('x'))
            x, y = map(int, position.split('+'))
        except:
            width, height = DEFAULT_SETTINGS["window_width"], DEFAULT_SETTINGS["window_height"]
            x, y = None, None

        self.settings.update({
            # Audio settings
            "audio_device": self.audio_device_var.get(),
            "master_volume": self.volume_var.get(),

            # Video settings
            "active_displays": self.active_displays,
            "inactive_displays": self.inactive_displays,
            "enable_keyboard": self.video_keyboard_var.get(),

            # Hardware settings
            "serial_port": self.serial_port_var.get(),

            # Window settings
            "window_width": width,
            "window_height": height,
            "window_x": x,
            "window_y": y,
        })
        self.settings.save()
        print(f"✓ Settings saved: {len(self.active_displays)} active displays, keyboard={self.video_keyboard_var.get()}")

    def run(self):
        """Run the GUI main loop."""
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing."""
        # Save settings
        self.save_settings()

        if self.core.is_running():
            if messagebox.askokcancel("Quit", "Systems are running. Stop all and quit?"):
                print("\nStopping all systems before exit...")
                self.stop_all()
                # Give systems time to stop
                self.root.after(1000, self.root.destroy)
            # Don't destroy if user cancels
        else:
            self.root.destroy()


def main():
    """Main entry point."""
    app = CarpetHotelGUI()
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.run()


if __name__ == "__main__":
    main()
