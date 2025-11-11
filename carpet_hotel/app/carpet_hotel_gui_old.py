#!/usr/bin/env python3
"""
Carpet Hotel GUI - Control Panel
=================================

Graphical interface for controlling Video, Audio, Hardware, and Commands.
Each component can be started/stopped independently.

Usage:
    python carpet_hotel_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from pathlib import Path
import json

# Import the launcher class
from carpet_hotel import CarpetHotelLauncher

# Check for optional dependencies
try:
    from pythonosc import udp_client
    OSC_AVAILABLE = True
except ImportError:
    OSC_AVAILABLE = False

class CarpetHotelGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Carpet Hotel - Control Panel")
        self.root.geometry("900x800")

        # Component instances (one for each subsystem)
        self.video_launcher = None
        self.audio_launcher = None
        self.hardware_launcher = None

        # State tracking
        self.video_running = False
        self.audio_running = False
        self.hardware_running = False
        self.all_running = False

        # Load configuration
        self.config = self.load_config()

        # Create GUI
        self.create_widgets()

    def load_config(self):
        """Load saved configuration."""
        config_file = Path(__file__).parent / "configs" / ".carpet_hotel_config.json"
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Could not load config: {e}")

        # Default configuration
        return {
            'audio_device': None,
            'sample_rate': None,
            'displays': [1, 2],
            'arduino_port': 'auto',
            'enable_keyboard': True,
            'enable_osc': True
        }

    def save_config(self):
        """Save configuration."""
        config_file = Path(__file__).parent / "configs" / ".carpet_hotel_config.json"
        config_file.parent.mkdir(exist_ok=True)
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")

    def create_widgets(self):
        """Create all GUI widgets."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=(10, 5))

        # Tab 1: Video (Processing)
        self.create_video_tab(notebook)

        # Tab 2: Audio (SuperCollider)
        self.create_audio_tab(notebook)

        # Tab 3: Hardware (Arduino)
        self.create_hardware_tab(notebook)

        # Tab 4: Command (Control)
        self.create_command_tab(notebook)

        # Global controls at bottom
        self.create_global_controls()

    def create_video_tab(self, notebook):
        """Create Video/Processing tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Video")

        # Header
        ttk.Label(tab, text="Video System (Processing)", font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(tab, text="Controls the visual display across multiple screens").pack()

        # Status
        status_frame = ttk.LabelFrame(tab, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)

        self.video_status_label = ttk.Label(status_frame, text="● Stopped", foreground='red', font=('Arial', 14, 'bold'))
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

        # Testing section (collapsible)
        testing_frame = ttk.LabelFrame(tab, text="▼ Testing & Configuration", padding=10)
        testing_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Display configuration
        ttk.Label(testing_frame, text="Displays:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(5,2))
        self.video_displays_var = tk.StringVar(value=','.join(map(str, self.config.get('displays', [1, 2]))))
        ttk.Entry(testing_frame, textvariable=self.video_displays_var, width=30).pack(anchor='w', padx=20)
        ttk.Label(testing_frame, text="  (comma-separated display numbers)", foreground='gray').pack(anchor='w', padx=20)

        # Keyboard control
        self.video_keyboard_var = tk.BooleanVar(value=self.config.get('enable_keyboard', True))
        ttk.Checkbutton(testing_frame, text="Enable keyboard control in Processing",
                       variable=self.video_keyboard_var).pack(anchor='w', pady=5, padx=20)

        # Log output
        ttk.Label(testing_frame, text="Log Output:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10,2))
        self.video_log = scrolledtext.ScrolledText(testing_frame, height=8, width=70, state='disabled')
        self.video_log.pack(fill='both', expand=True, padx=20, pady=5)

    def create_audio_tab(self, notebook):
        """Create Audio/SuperCollider tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Audio")

        # Header
        ttk.Label(tab, text="Audio System (SuperCollider)", font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(tab, text="Controls multi-channel audio mixing and playback").pack()

        # Status
        status_frame = ttk.LabelFrame(tab, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)

        self.audio_status_label = ttk.Label(status_frame, text="● Stopped", foreground='red', font=('Arial', 14, 'bold'))
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

        # Testing section
        testing_frame = ttk.LabelFrame(tab, text="▼ Testing & Configuration", padding=10)
        testing_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Audio device
        ttk.Label(testing_frame, text="Audio Device:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(5,2))
        self.audio_device_var = tk.StringVar(value=self.config.get('audio_device', 'default') or 'default')
        ttk.Entry(testing_frame, textvariable=self.audio_device_var, width=40).pack(anchor='w', padx=20)
        ttk.Label(testing_frame, text='  (e.g. "MacBook Pro Speakers" or "default")', foreground='gray').pack(anchor='w', padx=20)

        # Sample rate
        ttk.Label(testing_frame, text="Sample Rate (Hz):", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10,2))
        self.audio_rate_var = tk.StringVar(value=str(self.config.get('sample_rate', 'auto') or 'auto'))
        ttk.Entry(testing_frame, textvariable=self.audio_rate_var, width=20).pack(anchor='w', padx=20)
        ttk.Label(testing_frame, text='  (48000, 44100, or "auto")', foreground='gray').pack(anchor='w', padx=20)

        # Log output
        ttk.Label(testing_frame, text="Log Output:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10,2))
        self.audio_log = scrolledtext.ScrolledText(testing_frame, height=6, width=70, state='disabled')
        self.audio_log.pack(fill='both', expand=True, padx=20, pady=5)

    def create_hardware_tab(self, notebook):
        """Create Hardware/Arduino tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Hardware")

        # Header
        ttk.Label(tab, text="Hardware System (Arduino)", font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(tab, text="Controls elevator buttons, LEDs, and OSC communication").pack()

        # Status
        status_frame = ttk.LabelFrame(tab, text="Status", padding=10)
        status_frame.pack(fill='x', padx=20, pady=10)

        self.hardware_status_label = ttk.Label(status_frame, text="● Stopped", foreground='red', font=('Arial', 14, 'bold'))
        self.hardware_status_label.pack()

        # Control buttons
        control_frame = ttk.Frame(tab)
        control_frame.pack(pady=10)

        self.hardware_start_btn = ttk.Button(control_frame, text="▶ Start Hardware",
                                            command=self.start_hardware, width=20)
        self.hardware_start_btn.pack(side='left', padx=5)

        self.hardware_stop_btn = ttk.Button(control_frame, text="■ Stop Hardware",
                                           command=self.stop_hardware, width=20, state='disabled')
        self.hardware_stop_btn.pack(side='left', padx=5)

        # Testing section
        testing_frame = ttk.LabelFrame(tab, text="▼ Testing & Configuration", padding=10)
        testing_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Arduino port
        ttk.Label(testing_frame, text="Arduino Port:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(5,2))
        self.arduino_port_var = tk.StringVar(value=self.config.get('arduino_port', 'auto'))
        ttk.Entry(testing_frame, textvariable=self.arduino_port_var, width=40).pack(anchor='w', padx=20)
        ttk.Label(testing_frame, text='  (e.g. "/dev/cu.usbmodem..." or "auto")', foreground='gray').pack(anchor='w', padx=20)

        ttk.Button(testing_frame, text="🔄 Scan for Arduino", command=self.scan_arduino).pack(anchor='w', padx=20, pady=5)

        # OSC enable
        self.hardware_osc_var = tk.BooleanVar(value=self.config.get('enable_osc', True))
        ttk.Checkbutton(testing_frame, text="Enable OSC communication",
                       variable=self.hardware_osc_var).pack(anchor='w', pady=5, padx=20)

        # Log output
        ttk.Label(testing_frame, text="Log Output:", font=('Arial', 12, 'bold')).pack(anchor='w', pady=(10,2))
        self.hardware_log = scrolledtext.ScrolledText(testing_frame, height=6, width=70, state='disabled')
        self.hardware_log.pack(fill='both', expand=True, padx=20, pady=5)

    def create_command_tab(self, notebook):
        """Create Command/Control tab."""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Command")

        # Header
        ttk.Label(tab, text="System Commands", font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(tab, text="Direct control of elevator, LEDs, and floor selection").pack()

        # Note about requirements
        req_frame = ttk.Frame(tab)
        req_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(req_frame, text="⚠ Requires:", font=('Arial', 12, 'bold')).pack(anchor='w')
        ttk.Label(req_frame, text="  • Video system running (for floor changes)", foreground='gray').pack(anchor='w', padx=20)
        ttk.Label(req_frame, text="  • Hardware system running (for LED controls)", foreground='gray').pack(anchor='w', padx=20)

        # Elevator controls
        elevator_frame = ttk.LabelFrame(tab, text="Elevator Control", padding=10)
        elevator_frame.pack(fill='x', padx=20, pady=10)

        btn_frame = ttk.Frame(elevator_frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="▲ UP", command=lambda: self.send_command('/carpet/elevator/up'),
                  width=15).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="▼ DOWN", command=lambda: self.send_command('/carpet/elevator/down'),
                  width=15).pack(side='left', padx=5)

        # Floor selection
        floor_frame = ttk.LabelFrame(tab, text="Direct Floor Selection", padding=10)
        floor_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(floor_frame, text="Select floor:").pack(side='left', padx=5)

        # Create floor buttons in a grid
        floor_btn_frame = ttk.Frame(floor_frame)
        floor_btn_frame.pack(side='left', padx=10)

        for i in range(9):  # Floors 0-8
            btn = ttk.Button(floor_btn_frame, text=str(i),
                           command=lambda floor=i: self.goto_floor(floor),
                           width=5)
            btn.grid(row=i//5, column=i%5, padx=2, pady=2)

        # LED controls
        led_frame = ttk.LabelFrame(tab, text="LED Control", padding=10)
        led_frame.pack(fill='x', padx=20, pady=10)

        # Individual LEDs
        ttk.Label(led_frame, text="Individual LEDs:").pack(anchor='w')
        led_btn_frame = ttk.Frame(led_frame)
        led_btn_frame.pack(fill='x', pady=5)

        for color in ['Red', 'Yellow', 'Green']:
            frame = ttk.Frame(led_btn_frame)
            frame.pack(side='left', padx=10)
            ttk.Label(frame, text=f"{color}:").pack(side='left')
            ttk.Button(frame, text="ON", command=lambda c=color: self.set_led(c.lower(), 1),
                      width=6).pack(side='left', padx=2)
            ttk.Button(frame, text="OFF", command=lambda c=color: self.set_led(c.lower(), 0),
                      width=6).pack(side='left', padx=2)

        # LED animations
        ttk.Label(led_frame, text="Animations:").pack(anchor='w', pady=(10,0))
        anim_frame = ttk.Frame(led_frame)
        anim_frame.pack(fill='x', pady=5)

        ttk.Button(anim_frame, text="Stable Mode", command=lambda: self.set_led_mode('STABLE'),
                  width=15).pack(side='left', padx=5)
        ttk.Button(anim_frame, text="Transition Mode", command=lambda: self.set_led_mode('TRANSITION'),
                  width=15).pack(side='left', padx=5)
        ttk.Button(anim_frame, text="Off", command=lambda: self.set_led_mode('OFF'),
                  width=15).pack(side='left', padx=5)

        # Raw OSC Command section
        raw_frame = ttk.LabelFrame(tab, text="Custom OSC Command", padding=10)
        raw_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(raw_frame, text="Send raw OSC commands directly", foreground='gray').pack(anchor='w')

        input_frame = ttk.Frame(raw_frame)
        input_frame.pack(fill='x', pady=5)

        ttk.Label(input_frame, text="OSC Address:").pack(side='left', padx=5)
        self.osc_address_var = tk.StringVar(value="/carpet/")
        ttk.Entry(input_frame, textvariable=self.osc_address_var, width=25).pack(side='left', padx=5)

        ttk.Label(input_frame, text="Args:").pack(side='left', padx=5)
        self.osc_args_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.osc_args_var, width=20).pack(side='left', padx=5)

        ttk.Button(input_frame, text="Send", command=self.send_raw_osc, width=10).pack(side='left', padx=5)

        ttk.Label(raw_frame, text='Example: /carpet/scene 0 2 0  or  /carpet/volume 0.5',
                 foreground='gray', font=('Arial', 9)).pack(anchor='w', padx=5)

        # Command log
        ttk.Label(tab, text="Command Log:", font=('Arial', 12, 'bold')).pack(anchor='w', padx=20, pady=(10,2))
        self.command_log = scrolledtext.ScrolledText(tab, height=6, width=70, state='disabled')
        self.command_log.pack(fill='both', expand=True, padx=20, pady=5)

    def create_global_controls(self):
        """Create global control buttons at bottom."""
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=5)

        global_frame = ttk.Frame(self.root)
        global_frame.pack(fill='x', padx=20, pady=10)

        ttk.Label(global_frame, text="Global Control:", font=('Arial', 14, 'bold')).pack(side='left', padx=10)

        self.global_start_btn = ttk.Button(global_frame, text="▶ START ALL SYSTEMS",
                                          command=self.start_all, width=25)
        self.global_start_btn.pack(side='left', padx=5)

        self.global_stop_btn = ttk.Button(global_frame, text="■ STOP ALL SYSTEMS",
                                         command=self.stop_all, width=25, state='disabled')
        self.global_stop_btn.pack(side='left', padx=5)

        # Status indicator
        self.global_status_label = ttk.Label(global_frame, text="All systems stopped",
                                            foreground='gray', font=('Arial', 12))
        self.global_status_label.pack(side='left', padx=20)

    # Video control methods
    def start_video(self):
        """Start Processing video system."""
        if self.video_running:
            return

        self.log_to_widget(self.video_log, "Starting video system...")
        self.video_status_label.config(text="● Starting...", foreground='orange')

        def start_thread():
            try:
                # Parse displays
                displays = [int(d.strip()) for d in self.video_displays_var.get().split(',')]

                # Create launcher for video only
                self.video_launcher = CarpetHotelLauncher(
                    enable_keyboard=self.video_keyboard_var.get(),
                    enable_python_terminal=False,
                    enable_osc_external=False,
                    displays=displays
                )

                # Launch Processing
                if self.video_launcher.launch_processing():
                    self.video_running = True
                    self.root.after(0, self.update_video_ui, True)
                    self.log_to_widget(self.video_log, "✓ Video system started")
                else:
                    self.root.after(0, self.update_video_ui, False)
                    self.log_to_widget(self.video_log, "✗ Failed to start video system")
            except Exception as e:
                self.log_to_widget(self.video_log, f"✗ Error: {e}")
                self.root.after(0, self.update_video_ui, False)

        threading.Thread(target=start_thread, daemon=True).start()

    def stop_video(self):
        """Stop Processing video system."""
        if not self.video_running:
            return

        self.log_to_widget(self.video_log, "Stopping video system...")

        if self.video_launcher:
            if self.video_launcher.processing_process:
                self.video_launcher.processing_process.terminate()
                self.video_launcher.processing_process = None

        self.video_running = False
        self.update_video_ui(False)
        self.log_to_widget(self.video_log, "✓ Video system stopped")

    def update_video_ui(self, running):
        """Update video tab UI based on state."""
        if running:
            self.video_status_label.config(text="● Running", foreground='green')
            self.video_start_btn.config(state='disabled')
            self.video_stop_btn.config(state='normal')
        else:
            self.video_status_label.config(text="● Stopped", foreground='red')
            self.video_start_btn.config(state='normal')
            self.video_stop_btn.config(state='disabled')

        self.update_global_status()

    # Audio control methods
    def start_audio(self):
        """Start SuperCollider audio system."""
        if self.audio_running:
            return

        self.log_to_widget(self.audio_log, "Starting audio system...")
        self.audio_status_label.config(text="● Starting...", foreground='orange')

        def start_thread():
            try:
                # Parse audio settings
                audio_device = self.audio_device_var.get()
                if audio_device == 'default':
                    audio_device = None

                sample_rate = self.audio_rate_var.get()
                if sample_rate == 'auto':
                    sample_rate = None
                else:
                    try:
                        sample_rate = int(sample_rate)
                    except:
                        sample_rate = None

                # Create launcher for audio only
                self.audio_launcher = CarpetHotelLauncher(
                    audio_device=audio_device,
                    sample_rate=sample_rate,
                    enable_keyboard=False,
                    enable_python_terminal=False,
                    enable_osc_external=False
                )

                # Launch SuperCollider
                if self.audio_launcher.launch_supercollider():
                    self.audio_running = True
                    self.root.after(0, self.update_audio_ui, True)
                    self.log_to_widget(self.audio_log, "✓ Audio system started")
                else:
                    self.root.after(0, self.update_audio_ui, False)
                    self.log_to_widget(self.audio_log, "✗ Failed to start audio system")
            except Exception as e:
                self.log_to_widget(self.audio_log, f"✗ Error: {e}")
                self.root.after(0, self.update_audio_ui, False)

        threading.Thread(target=start_thread, daemon=True).start()

    def stop_audio(self):
        """Stop SuperCollider audio system."""
        if not self.audio_running:
            return

        self.log_to_widget(self.audio_log, "Stopping audio system...")

        if self.audio_launcher:
            if self.audio_launcher.sc_process:
                self.audio_launcher.sc_process.terminate()
                self.audio_launcher.sc_process = None

        self.audio_running = False
        self.update_audio_ui(False)
        self.log_to_widget(self.audio_log, "✓ Audio system stopped")

    def update_audio_ui(self, running):
        """Update audio tab UI based on state."""
        if running:
            self.audio_status_label.config(text="● Running", foreground='green')
            self.audio_start_btn.config(state='disabled')
            self.audio_stop_btn.config(state='normal')
        else:
            self.audio_status_label.config(text="● Stopped", foreground='red')
            self.audio_start_btn.config(state='normal')
            self.audio_stop_btn.config(state='disabled')

        self.update_global_status()

    # Hardware control methods
    def start_hardware(self):
        """Start Arduino hardware system."""
        if self.hardware_running:
            return

        self.log_to_widget(self.hardware_log, "Starting hardware system...")
        self.hardware_status_label.config(text="● Starting...", foreground='orange')

        def start_thread():
            try:
                arduino_port = self.arduino_port_var.get()
                if arduino_port == '':
                    arduino_port = 'auto'

                # Create launcher for hardware only
                self.hardware_launcher = CarpetHotelLauncher(
                    enable_keyboard=False,
                    enable_python_terminal=False,
                    enable_osc_external=self.hardware_osc_var.get(),
                    arduino_port=arduino_port
                )

                # Setup OSC and Arduino
                if self.hardware_osc_var.get():
                    self.hardware_launcher.setup_osc()
                    time.sleep(1)
                    self.hardware_launcher.setup_arduino()

                    self.hardware_running = True
                    self.root.after(0, self.update_hardware_ui, True)
                    self.log_to_widget(self.hardware_log, "✓ Hardware system started")
                else:
                    self.root.after(0, self.update_hardware_ui, False)
                    self.log_to_widget(self.hardware_log, "✗ OSC must be enabled")
            except Exception as e:
                self.log_to_widget(self.hardware_log, f"✗ Error: {e}")
                self.root.after(0, self.update_hardware_ui, False)

        threading.Thread(target=start_thread, daemon=True).start()

    def stop_hardware(self):
        """Stop Arduino hardware system."""
        if not self.hardware_running:
            return

        self.log_to_widget(self.hardware_log, "Stopping hardware system...")

        if self.hardware_launcher:
            self.hardware_launcher.cleanup_arduino()
            if self.hardware_launcher.osc_server:
                self.hardware_launcher.osc_server.shutdown()

        self.hardware_running = False
        self.update_hardware_ui(False)
        self.log_to_widget(self.hardware_log, "✓ Hardware system stopped")

    def update_hardware_ui(self, running):
        """Update hardware tab UI based on state."""
        if running:
            self.hardware_status_label.config(text="● Running", foreground='green')
            self.hardware_start_btn.config(state='disabled')
            self.hardware_stop_btn.config(state='normal')
        else:
            self.hardware_status_label.config(text="● Stopped", foreground='red')
            self.hardware_start_btn.config(state='normal')
            self.hardware_stop_btn.config(state='disabled')

        self.update_global_status()

    def scan_arduino(self):
        """Scan for Arduino devices."""
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())

            if not ports:
                self.log_to_widget(self.hardware_log, "No serial ports found")
                return

            self.log_to_widget(self.hardware_log, "Available ports:")
            for port in ports:
                desc_lower = port.description.lower()
                is_arduino = any(keyword in desc_lower for keyword in
                               ['arduino', 'adafruit', 'ch340', 'ch341', 'ftdi', 'nano'])
                marker = " ⭐" if is_arduino else ""
                self.log_to_widget(self.hardware_log, f"  {port.device}{marker}: {port.description}")

                if is_arduino:
                    self.arduino_port_var.set(port.device)
        except Exception as e:
            self.log_to_widget(self.hardware_log, f"Error scanning: {e}")

    # Command methods
    def send_command(self, osc_address, *args):
        """Send OSC command."""
        if not OSC_AVAILABLE:
            self.log_to_widget(self.command_log, "✗ python-osc not installed")
            return

        try:
            # Try to use video launcher's OSC client first
            if self.video_launcher and hasattr(self.video_launcher, 'osc_client') and self.video_launcher.osc_client:
                self.video_launcher.osc_client.send_message(osc_address, list(args) if args else [])
                self.log_to_widget(self.command_log, f"→ Sent: {osc_address} {args}")
            else:
                self.log_to_widget(self.command_log, "✗ Video system not running")
        except Exception as e:
            self.log_to_widget(self.command_log, f"✗ Error: {e}")

    def goto_floor(self, floor):
        """Go to specific floor."""
        self.send_command('/carpet/goto', floor)

    def set_led(self, color, state):
        """Set LED state."""
        self.send_command(f'/carpet/led/{color}', state)

    def set_led_mode(self, mode):
        """Set LED animation mode."""
        if self.hardware_launcher:
            try:
                self.hardware_launcher.set_led_animation_mode(mode)
                self.log_to_widget(self.command_log, f"→ LED mode: {mode}")
            except Exception as e:
                self.log_to_widget(self.command_log, f"✗ Error: {e}")
        else:
            self.log_to_widget(self.command_log, "✗ Hardware system not running")

    def send_raw_osc(self):
        """Send raw OSC command from user input."""
        osc_address = self.osc_address_var.get().strip()
        args_str = self.osc_args_var.get().strip()

        if not osc_address:
            self.log_to_widget(self.command_log, "✗ OSC address required")
            return

        # Parse arguments (space-separated)
        args = []
        if args_str:
            for arg in args_str.split():
                # Try to convert to appropriate type
                try:
                    # Try int first
                    args.append(int(arg))
                except ValueError:
                    try:
                        # Try float
                        args.append(float(arg))
                    except ValueError:
                        # Keep as string
                        args.append(arg)

        # Send the command
        self.send_command(osc_address, *args)

    # Global control methods
    def start_all(self):
        """Start all systems."""
        self.log_to_widget(self.command_log, "Starting all systems...")

        # Start audio first (needs time to boot)
        if not self.audio_running:
            self.start_audio()
            time.sleep(2)

        # Start hardware
        if not self.hardware_running:
            self.start_hardware()
            time.sleep(1)

        # Start video last
        if not self.video_running:
            self.start_video()

        self.all_running = True
        self.update_global_ui()

    def stop_all(self):
        """Stop all systems."""
        self.log_to_widget(self.command_log, "Stopping all systems...")

        if self.video_running:
            self.stop_video()

        if self.hardware_running:
            self.stop_hardware()

        if self.audio_running:
            self.stop_audio()

        self.all_running = False
        self.update_global_ui()

    def update_global_status(self):
        """Update global status based on individual systems."""
        running_count = sum([self.video_running, self.audio_running, self.hardware_running])

        if running_count == 3:
            self.global_status_label.config(text="All systems running", foreground='green')
            self.all_running = True
        elif running_count > 0:
            self.global_status_label.config(text=f"{running_count}/3 systems running", foreground='orange')
            self.all_running = False
        else:
            self.global_status_label.config(text="All systems stopped", foreground='gray')
            self.all_running = False

        self.update_global_ui()

    def update_global_ui(self):
        """Update global control buttons."""
        if self.all_running:
            self.global_start_btn.config(state='disabled')
            self.global_stop_btn.config(state='normal')
        else:
            self.global_start_btn.config(state='normal')
            self.global_stop_btn.config(state='normal' if any([self.video_running, self.audio_running, self.hardware_running]) else 'disabled')

    # Utility methods
    def log_to_widget(self, widget, message):
        """Add message to scrolled text widget."""
        def update():
            widget.config(state='normal')
            widget.insert(tk.END, f"{message}\n")
            widget.see(tk.END)
            widget.config(state='disabled')

        self.root.after(0, update)

    def run(self):
        """Run the GUI."""
        # Set up cleanup on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handle window close."""
        # Stop all systems
        if any([self.video_running, self.audio_running, self.hardware_running]):
            self.stop_all()
            time.sleep(1)

        # Save configuration
        self.config['displays'] = [int(d.strip()) for d in self.video_displays_var.get().split(',')]
        self.config['audio_device'] = self.audio_device_var.get() if self.audio_device_var.get() != 'default' else None
        try:
            rate = self.audio_rate_var.get()
            self.config['sample_rate'] = int(rate) if rate != 'auto' else None
        except:
            self.config['sample_rate'] = None
        self.config['arduino_port'] = self.arduino_port_var.get()
        self.config['enable_keyboard'] = self.video_keyboard_var.get()
        self.config['enable_osc'] = self.hardware_osc_var.get()
        self.save_config()

        self.root.destroy()

def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("  CARPET HOTEL - Control Panel")
    print("="*60 + "\n")

    gui = CarpetHotelGUI()
    gui.run()

if __name__ == '__main__':
    main()
