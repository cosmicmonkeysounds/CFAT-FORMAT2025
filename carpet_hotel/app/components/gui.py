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

# Get absolute path to app directory
APP_DIR = Path(__file__).parent.parent.absolute()
CONFIGS_DIR = APP_DIR / "configs"

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
        self.root.geometry("1200x1000")

        # Configure default font sizes (larger)
        default_font = ('Arial', 12)
        header_font = ('Arial', 18, 'bold')
        button_font = ('Arial', 14)

        self.root.option_add('*TButton*Font', button_font)
        self.root.option_add('*TLabel*Font', default_font)
        self.root.option_add('*TEntry*Font', default_font)
        self.root.option_add('*TCombobox*Font', default_font)

        # Core instance
        self.core = CarpetHotelCore()

        # Settings manager
        self.settings = SettingsManager()

        # Component running states
        self.video_running = False
        self.audio_running = False
        self.hardware_running = False

        # Auto-restart timer (30 minutes = 1800 seconds)
        self.auto_restart_interval = 10 * 60  # 10 minutes in seconds
        self.video_start_time = None
        self.audio_start_time = None
        self._restart_check_id = None

        # Display configuration now managed in Hardware tab via video_config.json

        # Create GUI
        self.create_gui()

        # Initial setup
        # Display detection now handled in Hardware tab on-demand
        self.refresh_audio_devices()
        self.refresh_serial_ports()

        # Start status polling
        self._poll_status()

        # Start auto-restart check (every 10 seconds)
        self._start_auto_restart_check()

        # Load saved settings and apply them
        self.load_settings()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_gui(self):
        """Create all GUI elements."""
        # Create sticky header with START/STOP ALL at top
        self.create_sticky_header()

        # Create main container frame with scrollbar
        main_container = ttk.Frame(self.root)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Create notebook for tabs inside scrollable area
        notebook = ttk.Notebook(scrollable_frame)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.create_video_tab(notebook)
        self.create_audio_tab(notebook)
        self.create_hardware_tab(notebook)
        self.create_command_tab(notebook)
        self.create_video_config_tab(notebook)

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

        # Display configuration info
        display_frame = ttk.LabelFrame(tab, text="Display Configuration", padding=10)
        display_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Help text
        help_text = "Configure displays in the Hardware tab. Current configuration shown below."
        ttk.Label(display_frame, text=help_text, foreground='gray',
                 font=('Arial', 9)).pack(anchor='w', pady=(0,10))

        # Configure displays button
        btn_frame = ttk.Frame(display_frame)
        btn_frame.pack(fill='x', pady=5)

        ttk.Button(btn_frame, text="⚙ Configure Displays (Hardware Tab)",
                  command=lambda: self.notebook.select(2),  # Switch to Hardware tab (index 2)
                  width=30).pack(side='left', padx=5)

        ttk.Button(btn_frame, text="↻ Refresh Config",
                  command=self.refresh_video_display_config,
                  width=15).pack(side='left', padx=5)

        # Display configuration list
        config_frame = ttk.Frame(display_frame)
        config_frame.pack(fill='both', expand=True, pady=10)

        ttk.Label(config_frame, text="Scene Displays:",
                 font=('Arial', 11, 'bold')).pack(anchor='w')

        self.video_scene_displays_text = scrolledtext.ScrolledText(config_frame, height=4, width=80, state='disabled')
        self.video_scene_displays_text.pack(fill='x', pady=5)

        ttk.Label(config_frame, text="Composite Display:",
                 font=('Arial', 11, 'bold')).pack(anchor='w', pady=(10,0))

        self.video_composite_text = scrolledtext.ScrolledText(config_frame, height=2, width=80, state='disabled')
        self.video_composite_text.pack(fill='x', pady=5)

        # Auto-refresh config on startup
        self.root.after(300, self.refresh_video_display_config)

        # Keyboard control option (always enabled by default)
        self.video_keyboard_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(display_frame, text="Enable keyboard control in Processing",
                       variable=self.video_keyboard_var).pack(anchor='w', pady=10)

        # Log output
        ttk.Label(tab, text="Log Output:", font=('Arial', 10, 'bold')).pack(anchor='w', padx=20)
        self.video_log = scrolledtext.ScrolledText(tab, height=6, width=80, state='disabled')
        self.video_log.pack(fill='x', padx=20, pady=5)

    # Old display list methods removed - display configuration now in Hardware tab

    def refresh_video_display_config(self):
        """Refresh display configuration shown in Video tab."""
        import json

        config_path = CONFIGS_DIR / "video_config.json"

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            if 'displays' not in config:
                self.log_to_widget_direct(self.video_scene_displays_text,
                                         "No display configuration found. Please configure in Hardware tab.")
                self.log_to_widget_direct(self.video_composite_text, "Not configured")
                return

            displays_config = config['displays']

            # Show scene displays
            scene_text = ""
            if 'scene_displays' in displays_config:
                for disp in displays_config['scene_displays']:
                    if disp.get('enabled'):
                        scene_text += f"  {disp['letter']}: Display {disp['physical_display']} - {disp['device_name']}\n"

            if not scene_text:
                scene_text = "  No scene displays configured"

            self.log_to_widget_direct(self.video_scene_displays_text, scene_text)

            # Show composite display
            composite_text = ""
            if 'composite_display' in displays_config:
                comp = displays_config['composite_display']
                if comp.get('enabled'):
                    composite_text = f"  Z: Display {comp['physical_display']} - {comp['device_name']}\n"
                    composite_text += f"  Blend Mode: {comp['blend_mode']}\n"
                    composite_text += f"  Sources: {', '.join(comp.get('blend_sources', []))}"
                else:
                    composite_text = "  Disabled"
            else:
                composite_text = "  Not configured"

            self.log_to_widget_direct(self.video_composite_text, composite_text)

        except Exception as e:
            self.log_to_widget_direct(self.video_scene_displays_text,
                                     f"Error loading config: {e}")
            self.log_to_widget_direct(self.video_composite_text, "Error")

    def log_to_widget_direct(self, widget, message: str):
        """Write directly to a text widget (for display config)."""
        widget.config(state='normal')
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, message)
        widget.config(state='disabled')

    def start_video(self):
        """Start Processing video system."""
        if self.video_running:
            return

        self.log_to_widget(self.video_log, "Starting Processing video system...")
        self.log_to_widget(self.video_log, "  (Reading display config from video_config.json)")
        self.log_to_widget(self.video_log, f"  Keyboard enabled: {self.video_keyboard_var.get()}")

        def start_thread():
            # Processing now reads display config from video_config.json
            success = self.core.start_processing(
                displays=None,  # Not used anymore - Processing reads from config
                enable_keyboard=self.video_keyboard_var.get()
            )

            if success:
                self.video_running = True
                self.video_start_time = time.time()
                self.root.after(0, self.update_video_ui, True)
                self.log_to_widget(self.video_log, "✓ Processing started (auto-restart in 30 min)")
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
                self.video_start_time = None
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

        # Audio routing mode selection
        routing_frame = ttk.Frame(config_frame)
        routing_frame.pack(fill='x', pady=5)

        ttk.Label(routing_frame, text="Audio Routing:", width=15).pack(side='left', padx=5)
        self.audio_routing_var = tk.StringVar(value="quad")
        self.audio_routing_dropdown = ttk.Combobox(routing_frame,
                                                    textvariable=self.audio_routing_var,
                                                    state='readonly', width=40)
        routing_options = [
            "quad - Bus 1→Ch 0+1, Bus 2→Ch 2+3 (4 channels)",
            "stereo - Bus 1→Ch 0, Bus 2→Ch 1 (2 channels)"
        ]
        self.audio_routing_dropdown['values'] = routing_options
        self.audio_routing_dropdown.current(0)
        self.audio_routing_dropdown.pack(side='left', padx=5)
        self.audio_routing_dropdown.bind('<<ComboboxSelected>>', self.on_audio_routing_change)

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

        # Note: SuperCollider now runs at fixed 100% volume
        # Volume control removed from OSC messaging

    def on_audio_routing_change(self, event=None):
        """Handle audio routing mode change."""
        routing_str = self.audio_routing_var.get()
        # Extract mode from string (e.g., "quad - ..." → "quad")
        routing = routing_str.split(" - ")[0]

        # Save setting
        self.settings.set("audio_routing", routing)
        self.settings.save()

        # Log the change
        self.log_to_widget(self.audio_log, f"Audio routing set to: {routing.upper()}")

        # Note: SuperCollider will need to be restarted to apply routing changes
        if self.audio_running:
            self.log_to_widget(self.audio_log, "⚠ Restart audio to apply routing change")

    def start_audio(self):
        """Start SuperCollider audio system."""
        if self.audio_running:
            return

        # Get the selected routing mode
        routing_str = self.audio_routing_var.get()
        routing = routing_str.split(" - ")[0]  # Extract "quad" or "stereo"

        self.log_to_widget(self.audio_log, "Starting SuperCollider audio system...")
        self.log_to_widget(self.audio_log, f"(Audio routing: {routing.upper()})")

        def start_thread():
            success = self.core.start_supercollider(audio_routing=routing)

            if success:
                self.audio_running = True
                self.audio_start_time = time.time()
                self.root.after(0, self.update_audio_ui, True)
                self.log_to_widget(self.audio_log, "✓ SuperCollider started (auto-restart in 30 min)")
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
                self.audio_start_time = None
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

        # Info box
        info_frame = ttk.LabelFrame(tab, text="ℹ System Overview", padding=10)
        info_frame.pack(fill='x', padx=20, pady=5)

        info_text = """Elevator Controls: Simple press UP or DOWN button = move 1 scene in that direction
Displays: Configure scene displays (A-G) and optional composite (Z) below
Arduino: Auto-detected on first connection attempt"""

        ttk.Label(info_frame, text=info_text, foreground='#555',
                 font=('Arial', 9), justify='left').pack(anchor='w')

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

        # Display Configuration
        display_frame = ttk.LabelFrame(tab, text="Display Configuration", padding=10)
        display_frame.pack(fill='x', padx=20, pady=10)

        # Refresh displays button
        refresh_frame = ttk.Frame(display_frame)
        refresh_frame.pack(fill='x', pady=5)
        ttk.Button(refresh_frame, text="🔄 Detect Displays",
                  command=self.refresh_displays_hardware, width=20).pack(side='left', padx=5)

        # Info frame with note about display order
        info_frame = ttk.Frame(display_frame)
        info_frame.pack(fill='x', pady=5)
        note_text = "ℹ Display numbers shown below match Processing's order (test each display to verify)"
        ttk.Label(info_frame, text=note_text,
                 foreground='#0066cc', font=('Arial', 9)).pack(side='left', padx=5)

        # Display list container
        self.display_list_frame = ttk.Frame(display_frame)
        self.display_list_frame.pack(fill='both', expand=True, pady=5)

        # Display rows will be added here dynamically
        self.display_rows = []

        # Auto-detect displays on startup
        self.root.after(100, self.refresh_displays_hardware)
        self.root.after(200, self.load_display_config_to_gui)

        # Composite display section
        composite_frame = ttk.LabelFrame(display_frame, text="Composite Display (Z)", padding=10)
        composite_frame.pack(fill='x', pady=10)

        comp_row1 = ttk.Frame(composite_frame)
        comp_row1.pack(fill='x', pady=5)

        self.composite_enabled_var = tk.BooleanVar(value=False)
        self.composite_enabled_var.trace('w', lambda *args: self.auto_save_display_config())
        ttk.Checkbutton(comp_row1, text="Enable Z Display",
                       variable=self.composite_enabled_var,
                       command=self.update_composite_state).pack(side='left', padx=5)

        ttk.Label(comp_row1, text="Physical Display:", width=15).pack(side='left', padx=10)
        self.composite_display_var = tk.StringVar(value="")
        self.composite_display_var.trace('w', lambda *args: self.auto_save_display_config())
        self.composite_display_dropdown = ttk.Combobox(comp_row1,
                                                      textvariable=self.composite_display_var,
                                                      state='disabled', width=25)
        self.composite_display_dropdown.pack(side='left', padx=5)

        comp_row2 = ttk.Frame(composite_frame)
        comp_row2.pack(fill='x', pady=5)

        ttk.Label(comp_row2, text="Blend Mode:", width=15).pack(side='left', padx=5)
        self.composite_blend_var = tk.StringVar(value="multiply")
        self.composite_blend_var.trace('w', lambda *args: self.auto_save_display_config())
        blend_modes = ['multiply', 'add', 'subtract', 'screen', 'lightest', 'darkest', 'difference', 'exclusion']
        self.composite_blend_dropdown = ttk.Combobox(comp_row2,
                                                     textvariable=self.composite_blend_var,
                                                     values=blend_modes,
                                                     state='disabled', width=25)
        self.composite_blend_dropdown.pack(side='left', padx=5)

        ttk.Button(comp_row2, text="💾 Save Display Config",
                  command=self.save_display_config, width=20).pack(side='right', padx=5)

        # Serial port configuration
        config_frame = ttk.LabelFrame(tab, text="Serial Port Configuration", padding=10)
        config_frame.pack(fill='x', padx=20, pady=10)

        port_frame = ttk.Frame(config_frame)
        port_frame.pack(fill='x', pady=5)

        ttk.Label(port_frame, text="Serial Port:", width=15).pack(side='left', padx=5)
        self.serial_port_var = tk.StringVar(value="Auto-detect")
        self.serial_port_var.trace('w', lambda *args: self.save_arduino_port())
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
        port_labels = ["Auto-detect"]  # Add auto-detect as first option

        for port in ports:
            label = f"{port['device']}"
            if port['is_arduino']:
                label += " [Arduino]"
            label += f" - {port['description']}"
            port_labels.append(label)

        self.serial_port_dropdown['values'] = port_labels

        # Restore saved port from settings
        saved_port = self.settings.get('serial_port', "Auto-detect")
        if saved_port and saved_port in port_labels:
            self.serial_port_var.set(saved_port)
        elif saved_port == "Auto-detect":
            self.serial_port_var.set("Auto-detect")
        else:
            # Saved port not available, default to Auto-detect
            self.serial_port_var.set("Auto-detect")

        self.log_to_widget(self.hardware_log, f"Found {len(ports)} serial ports (+ Auto-detect option)")

    def refresh_displays_hardware(self):
        """Detect and display all connected displays in Hardware tab."""
        from components.utils.utils import detect_displays

        displays = detect_displays()

        # Clear existing display rows
        for row in self.display_rows:
            row.destroy()
        self.display_rows = []

        if not displays:
            no_displays_label = ttk.Label(self.display_list_frame,
                                         text="No displays detected",
                                         foreground='red')
            no_displays_label.pack(pady=10)
            self.display_rows.append(no_displays_label)
            return

        # Create header row
        header = ttk.Frame(self.display_list_frame)
        header.pack(fill='x', pady=5)
        ttk.Label(header, text="Enable", width=8, font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Label(header, text="Letter", width=8, font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Label(header, text="Physical #", width=10, font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Label(header, text="Device Name", width=40, font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        ttk.Label(header, text="Resolution", width=15, font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        self.display_rows.append(header)

        # Create row for each display
        self.display_vars = []
        for display in displays:
            row_frame = ttk.Frame(self.display_list_frame)
            row_frame.pack(fill='x', pady=2)

            # Enabled checkbox
            enabled_var = tk.BooleanVar(value=False)
            enabled_var.trace('w', lambda *args: self.auto_save_display_config())
            ttk.Checkbutton(row_frame, variable=enabled_var).pack(side='left', padx=5)

            # Letter dropdown (A-G)
            letter_var = tk.StringVar(value="")
            letter_var.trace('w', lambda *args: self.auto_save_display_config())
            letter_combo = ttk.Combobox(row_frame, textvariable=letter_var,
                                       values=['A', 'B', 'C', 'D', 'E', 'F', 'G'],
                                       state='readonly', width=5)
            letter_combo.pack(side='left', padx=5)

            # Physical display number
            phys_label = ttk.Label(row_frame, text=str(display['index'] + 1), width=10)
            phys_label.pack(side='left', padx=5)

            # Device name
            device_name = display['name']
            device_label = ttk.Label(row_frame, text=device_name, width=40)
            device_label.pack(side='left', padx=5)

            # Resolution
            res_text = f"{display['resolution'][0]}×{display['resolution'][1]}"
            res_label = ttk.Label(row_frame, text=res_text, width=15)
            res_label.pack(side='left', padx=5)

            # Test button
            test_btn = ttk.Button(row_frame, text="Test",
                                 command=lambda idx=display['index']: self.test_display(idx),
                                 width=8)
            test_btn.pack(side='left', padx=5)

            self.display_rows.append(row_frame)
            self.display_vars.append({
                'index': display['index'],
                'name': device_name,
                'enabled': enabled_var,
                'letter': letter_var,
                'resolution': display['resolution']
            })

        # Update composite display dropdown
        display_options = [f"{i+1}: {d['name']}" for i, d in enumerate(displays)]
        self.composite_display_dropdown['values'] = display_options

        self.log_to_widget(self.hardware_log, f"✓ Detected {len(displays)} displays")

    def update_composite_state(self):
        """Enable/disable composite display controls."""
        state = 'readonly' if self.composite_enabled_var.get() else 'disabled'
        self.composite_display_dropdown.config(state=state)
        self.composite_blend_dropdown.config(state=state)

    def test_display(self, display_index):
        """Show a test pattern on the specified display."""
        try:
            # Get display info
            from screeninfo import get_monitors
            monitors = get_monitors()

            if display_index >= len(monitors):
                import tkinter.messagebox as msgbox
                msgbox.showerror("Error", f"Display {display_index + 1} not found!")
                return

            monitor = monitors[display_index]

            # Create fullscreen test window
            test_window = tk.Toplevel(self.root)
            test_window.attributes('-fullscreen', True)
            test_window.attributes('-topmost', True)
            test_window.configure(bg='#2c3e50')

            # Position on target display
            test_window.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")

            # Add display info
            frame = tk.Frame(test_window, bg='#2c3e50')
            frame.place(relx=0.5, rely=0.5, anchor='center')

            # Display number (large)
            tk.Label(frame,
                    text=f"Display {display_index + 1}",
                    font=('Arial', 72, 'bold'),
                    bg='#2c3e50',
                    fg='#ecf0f1').pack(pady=20)

            # Display name
            tk.Label(frame,
                    text=monitor.name if hasattr(monitor, 'name') else f"Monitor {display_index + 1}",
                    font=('Arial', 32),
                    bg='#2c3e50',
                    fg='#95a5a6').pack(pady=10)

            # Resolution
            tk.Label(frame,
                    text=f"{monitor.width} × {monitor.height}",
                    font=('Arial', 24),
                    bg='#2c3e50',
                    fg='#7f8c8d').pack(pady=10)

            # Instructions
            tk.Label(frame,
                    text="Press ESC or click to close",
                    font=('Arial', 16),
                    bg='#2c3e50',
                    fg='#95a5a6').pack(pady=30)

            # Close on ESC or click
            test_window.bind('<Escape>', lambda e: test_window.destroy())
            test_window.bind('<Button-1>', lambda e: test_window.destroy())

            # Auto-close after 5 seconds
            test_window.after(5000, test_window.destroy)

            self.log_to_widget(self.hardware_log, f"✓ Test window shown on display {display_index + 1}")

        except Exception as e:
            import tkinter.messagebox as msgbox
            msgbox.showerror("Error", f"Failed to test display:\n{e}")

    def load_display_config_to_gui(self):
        """Load saved display configuration into GUI."""
        import json

        config_path = CONFIGS_DIR / "video_config.json"

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            if 'displays' not in config:
                return

            displays_config = config['displays']

            # Load scene displays
            if 'scene_displays' in displays_config:
                for scene_disp in displays_config['scene_displays']:
                    if scene_disp.get('enabled'):
                        letter = scene_disp['letter']
                        phys_idx = scene_disp['physical_display'] - 1  # Convert to 0-indexed

                        # Find matching display var
                        for var_dict in self.display_vars:
                            if var_dict['index'] == phys_idx:
                                var_dict['enabled'].set(True)
                                var_dict['letter'].set(letter)
                                break

            # Load composite display
            if 'composite_display' in displays_config:
                comp = displays_config['composite_display']
                if comp.get('enabled'):
                    self.composite_enabled_var.set(True)
                    if comp.get('physical_display'):
                        # Find matching display in dropdown
                        phys_num = comp['physical_display']
                        for option in self.composite_display_dropdown['values']:
                            if option.startswith(f"{phys_num}:"):
                                self.composite_display_var.set(option)
                                break
                    self.composite_blend_var.set(comp.get('blend_mode', 'multiply'))
                    self.update_composite_state()

        except Exception as e:
            # Config doesn't exist or is invalid - not an error, just means first run
            pass

    def auto_save_display_config(self):
        """Auto-save display configuration (debounced)."""
        # Cancel any pending auto-save
        if hasattr(self, '_auto_save_timer'):
            self.root.after_cancel(self._auto_save_timer)

        # Schedule save after 500ms delay (debounce)
        self._auto_save_timer = self.root.after(500, self._do_auto_save)

    def _do_auto_save(self):
        """Actually perform the auto-save."""
        if not hasattr(self, 'display_vars') or not self.display_vars:
            return  # Not yet initialized

        self.save_display_config(silent=True)
        # Also refresh the video config display
        self.refresh_video_display_config()

    def save_display_config(self, silent=False):
        """Save display configuration to video_config.json."""
        import json

        config_path = CONFIGS_DIR / "video_config.json"

        try:
            # Load existing config
            with open(config_path, 'r') as f:
                config = json.load(f)

            # Build scene displays array
            scene_displays = []
            for var_dict in self.display_vars:
                if var_dict['enabled'].get() and var_dict['letter'].get():
                    scene_displays.append({
                        "letter": var_dict['letter'].get(),
                        "physical_display": var_dict['index'] + 1,  # 1-indexed for Processing
                        "device_name": var_dict['name'],
                        "enabled": True
                    })

            # Sort by letter
            scene_displays.sort(key=lambda x: x['letter'])

            # Build composite display config
            composite_config = {
                "letter": "Z",
                "physical_display": None,
                "device_name": "",
                "enabled": False,
                "blend_mode": self.composite_blend_var.get(),
                "blend_sources": ["A", "B"]
            }

            if self.composite_enabled_var.get():
                comp_display_text = self.composite_display_var.get()
                if comp_display_text:
                    # Extract display index from "1: Display Name" format
                    comp_idx = int(comp_display_text.split(':')[0])
                    composite_config['physical_display'] = comp_idx
                    composite_config['device_name'] = comp_display_text.split(': ', 1)[1]
                    composite_config['enabled'] = True

                    # Update blend sources based on enabled scene displays
                    composite_config['blend_sources'] = [d['letter'] for d in scene_displays]

            # Update config
            config['displays'] = {
                'scene_displays': scene_displays,
                'composite_display': composite_config
            }

            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            if not silent:
                self.log_to_widget(self.hardware_log, "✓ Display configuration saved")
                import tkinter.messagebox as msgbox
                msgbox.showinfo("Success", "Display configuration saved!\n\nRestart Processing to apply changes.")

        except Exception as e:
            if not silent:
                self.log_to_widget(self.hardware_log, f"✗ Failed to save config: {e}")
                import tkinter.messagebox as msgbox
                msgbox.showerror("Error", f"Failed to save configuration:\n{e}")

    def save_arduino_port(self):
        """Save the selected Arduino port to settings."""
        port = self.serial_port_var.get()
        self.settings.set('serial_port', port)
        self.settings.save()

    def connect_hardware(self):
        """Connect to Arduino."""
        if self.hardware_running:
            return

        port = self.serial_port_var.get()
        if not port:
            self.log_to_widget(self.hardware_log, "✗ Please select a serial port")
            return

        # Handle auto-detect
        if port == "Auto-detect":
            self.log_to_widget(self.hardware_log, "Auto-detecting Arduino...")
            port = "auto"  # Signal to use auto-detection
        else:
            # Extract just the device path
            port = port.split()[0]

        self.log_to_widget(self.hardware_log, f"Connecting to Arduino... ({port})")

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

        ttk.Label(osc_frame, text='Example: /carpet/scene 0 2 0  or  /carpet/goto 5',
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

            print("✓ Video configuration reloaded from file")
        except Exception as e:
            print(f"✗ Failed to load config: {e}")

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

            print("✓ Video configuration saved successfully")
            print("  Press 'R' in Processing to reload")
        except Exception as e:
            print(f"✗ Failed to save config: {e}")

    def reset_video_config(self):
        """Reset video config to defaults."""
        import json
        from pathlib import Path

        print("Resetting video configuration to defaults...")

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

            print("✓ Video configuration reset to defaults")
            print("  Press 'R' in Processing to reload")
        except Exception as e:
            print(f"✗ Failed to reset config: {e}")

    def send_osc_command(self, address: str, args: list):
        """Send OSC command to the system."""
        if not OSC_AVAILABLE:
            self.log_to_widget(self.command_log, "✗ python-osc not installed")
            return

        try:
            # Send to SuperCollider (audio commands)
            if '/carpet/scene' in address or '/carpet/transition' in address:
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

    def create_sticky_header(self):
        """Create sticky header with START/STOP ALL at top."""
        # Header frame with darker background for more contrast
        header_frame = tk.Frame(self.root, bg='#1a1a1a', height=90)
        header_frame.pack(fill='x', side='top')
        header_frame.pack_propagate(False)  # Prevent frame from shrinking

        # Title
        title_label = tk.Label(header_frame, text="CARPET HOTEL CONTROL",
                              font=('Arial', 24, 'bold'), bg='#1a1a1a', fg='#00ff00')
        title_label.pack(side='left', padx=30, pady=20)

        # Button frame
        button_frame = tk.Frame(header_frame, bg='#1a1a1a')
        button_frame.pack(side='right', padx=30, pady=15)

        # START ALL button (bright green with black text for maximum contrast)
        self.start_all_btn = tk.Button(button_frame, text="▶ START ALL",
                                       command=self.start_all,
                                       font=('Arial', 18, 'bold'),
                                       bg='#00ff00', fg='black',
                                       activebackground='#00dd00',
                                       activeforeground='black',
                                       width=16, height=2,
                                       relief='raised', bd=5,
                                       highlightbackground='#00aa00',
                                       highlightthickness=2)
        self.start_all_btn.pack(side='left', padx=15)

        # STOP ALL button (bright red with white text for maximum contrast)
        self.stop_all_btn = tk.Button(button_frame, text="■ STOP ALL",
                                      command=self.stop_all,
                                      font=('Arial', 18, 'bold'),
                                      bg='#ff0000', fg='white',
                                      activebackground='#dd0000',
                                      activeforeground='white',
                                      width=16, height=2,
                                      relief='raised', bd=5,
                                      highlightbackground='#aa0000',
                                      highlightthickness=2)
        self.stop_all_btn.pack(side='left', padx=15)

        # Separator line (thicker and more visible)
        separator = tk.Frame(self.root, height=3, bg='#444444')
        separator.pack(fill='x')

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
    # AUTO-RESTART (30 min cycle)
    # ========================================================================

    def _start_auto_restart_check(self):
        """Start the periodic auto-restart check."""
        self._check_auto_restart()

    def _check_auto_restart(self):
        """Check if Processing or SuperCollider need to be restarted."""
        current_time = time.time()

        # Check if video needs restart
        if self.video_running and self.video_start_time:
            elapsed = current_time - self.video_start_time
            if elapsed >= self.auto_restart_interval:
                self.log_to_widget(self.video_log, f"⏱ Auto-restart: 30 minutes elapsed, restarting Processing...")
                self._auto_restart_video()

        # Check if audio needs restart
        if self.audio_running and self.audio_start_time:
            elapsed = current_time - self.audio_start_time
            if elapsed >= self.auto_restart_interval:
                self.log_to_widget(self.audio_log, f"⏱ Auto-restart: 30 minutes elapsed, restarting SuperCollider...")
                self._auto_restart_audio()

        # Schedule next check in 10 seconds
        self._restart_check_id = self.root.after(10000, self._check_auto_restart)

    def _auto_restart_video(self):
        """Automatically restart Processing."""
        def restart_thread():
            # Stop
            self.log_to_widget(self.video_log, "  Stopping Processing...")
            if self.core.stop_processing():
                self.video_running = False
                self.root.after(0, self.update_video_ui, False)

                # Wait a moment
                time.sleep(2)

                # Start again
                self.log_to_widget(self.video_log, "  Starting Processing...")
                success = self.core.start_processing(
                    displays=None,
                    enable_keyboard=self.video_keyboard_var.get()
                )

                if success:
                    self.video_running = True
                    self.video_start_time = time.time()
                    self.root.after(0, self.update_video_ui, True)
                    self.log_to_widget(self.video_log, "✓ Processing auto-restarted successfully")
                else:
                    self.log_to_widget(self.video_log, "✗ Failed to auto-restart Processing")
                    self.root.after(0, self.update_video_ui, False)
            else:
                self.log_to_widget(self.video_log, "✗ Failed to stop Processing for auto-restart")

        threading.Thread(target=restart_thread, daemon=True).start()

    def _auto_restart_audio(self):
        """Automatically restart SuperCollider."""
        def restart_thread():
            # Get the current routing mode
            routing_str = self.audio_routing_var.get()
            routing = routing_str.split(" - ")[0]

            # Stop
            self.log_to_widget(self.audio_log, "  Stopping SuperCollider...")
            if self.core.stop_supercollider():
                self.audio_running = False
                self.root.after(0, self.update_audio_ui, False)

                # Wait a moment
                time.sleep(2)

                # Start again
                self.log_to_widget(self.audio_log, "  Starting SuperCollider...")
                success = self.core.start_supercollider(audio_routing=routing)

                if success:
                    self.audio_running = True
                    self.audio_start_time = time.time()
                    self.root.after(0, self.update_audio_ui, True)
                    self.log_to_widget(self.audio_log, "✓ SuperCollider auto-restarted successfully")
                else:
                    self.log_to_widget(self.audio_log, "✗ Failed to auto-restart SuperCollider")
                    self.root.after(0, self.update_audio_ui, False)
            else:
                self.log_to_widget(self.audio_log, "✗ Failed to stop SuperCollider for auto-restart")

        threading.Thread(target=restart_thread, daemon=True).start()

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

        # Apply saved audio routing
        audio_routing = self.settings.get("audio_routing", DEFAULT_SETTINGS.get("audio_routing", "quad"))
        # Map routing mode to dropdown value
        routing_map = {
            "quad": "quad - Bus 1→Ch 0+1, Bus 2→Ch 2+3 (4 channels)",
            "stereo": "stereo - Bus 1→Ch 0, Bus 2→Ch 1 (2 channels)"
        }
        if audio_routing in routing_map:
            self.audio_routing_var.set(routing_map[audio_routing])

        # Apply saved serial port
        serial_port = self.settings.get("serial_port", DEFAULT_SETTINGS["serial_port"])
        if serial_port:
            self.serial_port_var.set(serial_port)

        # Apply saved keyboard setting
        enable_keyboard = self.settings.get("enable_keyboard", DEFAULT_SETTINGS["enable_keyboard"])
        self.video_keyboard_var.set(enable_keyboard)

        # Apply saved display lists
        # Display configuration now managed via video_config.json in Hardware tab
        # Old active/inactive display settings are no longer used

        # Apply saved window geometry
        window_x = self.settings.get("window_x")
        window_y = self.settings.get("window_y")
        window_width = self.settings.get("window_width", DEFAULT_SETTINGS["window_width"])
        window_height = self.settings.get("window_height", DEFAULT_SETTINGS["window_height"])

        if window_x is not None and window_y is not None:
            self.root.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
        else:
            self.root.geometry(f"{window_width}x{window_height}")

        print(f"✓ Settings loaded: volume={int(volume*100)}%, keyboard={enable_keyboard}")

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
            # Display configuration now managed via video_config.json
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
        print(f"✓ Settings saved (displays configured via video_config.json)")

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
