#!/usr/bin/env python3
"""
Serial Broker for Arduino Communication
========================================

Single source of truth for all serial communication with Arduino.
Thread-safe read/write handling.
"""

import serial
import time
import threading
import queue
import random
from typing import Optional, Callable
from pathlib import Path


class SerialBroker:
    """
    Centralized serial communication handler.
    All Arduino serial traffic goes through this broker.
    """

    def __init__(self, port: str, baudrate: int = 115200):
        """
        Initialize serial broker.

        Args:
            port: Serial port path
            baudrate: Baud rate (default 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.running = False

        # Read thread
        self.read_thread: Optional[threading.Thread] = None

        # Write queue (thread-safe)
        self.write_queue = queue.Queue()
        self.write_thread: Optional[threading.Thread] = None

        # Message callbacks
        self.message_callbacks = []  # List of callback functions

        # Lock for serial operations
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """
        Connect to Arduino.

        Returns:
            True if connection successful
        """
        try:
            print(f"[SerialBroker] Connecting to {self.port}...")
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(2)  # Wait for Arduino to reset

            # Wait for READY message
            print("[SerialBroker] Waiting for Arduino READY...")
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    print(f"[SerialBroker] Arduino: {line}")
                    if line == "READY":
                        print("[SerialBroker] ✓ Arduino ready")
                        break

            # Start worker threads
            self.running = True
            self._start_read_thread()
            self._start_write_thread()

            print("[SerialBroker] ✓ Connected and running")
            return True

        except Exception as e:
            print(f"[SerialBroker] ✗ Connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect and cleanup."""
        print("[SerialBroker] Disconnecting...")
        self.running = False

        # Stop threads
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1)
        if self.write_thread and self.write_thread.is_alive():
            self.write_thread.join(timeout=1)

        # Close serial
        if self.serial_conn:
            if self.serial_conn.is_open:
                # Turn off all LEDs
                try:
                    self.serial_conn.write(b"RED:0\n")
                    self.serial_conn.write(b"YELLOW:0\n")
                    self.serial_conn.write(b"GREEN:0\n")
                    time.sleep(0.1)  # Give time for commands to send
                except:
                    pass

                try:
                    self.serial_conn.close()
                    print("[SerialBroker] Serial port closed")
                except Exception as e:
                    print(f"[SerialBroker] Error closing serial: {e}")

            # Explicitly release the connection
            self.serial_conn = None

        print("[SerialBroker] ✓ Disconnected")

    def _start_read_thread(self):
        """Start thread that reads from serial."""
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

    def _start_write_thread(self):
        """Start thread that writes to serial."""
        self.write_thread = threading.Thread(target=self._write_loop, daemon=True)
        self.write_thread.start()

    def _read_loop(self):
        """
        Continuously read from serial and dispatch messages.
        Runs in background thread.
        """
        print("[SerialBroker] Read thread started")

        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()

                    if line and line != "READY":
                        # Debug: Log all incoming messages
                        if random.randint(0, 10) == 0 or "DOWN" in line.upper():
                            print(f"[SerialBroker] RX: '{line}'")

                        # Dispatch to all registered callbacks
                        for callback in self.message_callbacks:
                            try:
                                callback(line)
                            except Exception as e:
                                print(f"[SerialBroker] Callback error: {e}")

                time.sleep(0.01)  # 100Hz polling

            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    print(f"[SerialBroker] Read error: {e}")
                break

        print("[SerialBroker] Read thread stopped")

    def _write_loop(self):
        """
        Process write queue and send to serial.
        Runs in background thread.
        """
        print("[SerialBroker] Write thread started")
        write_count = 0

        while self.running:
            try:
                # Get message from queue (block with timeout)
                try:
                    message = self.write_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Write to serial
                if self.serial_conn and self.serial_conn.is_open:
                    with self.lock:
                        self.serial_conn.write(message.encode())
                        write_count += 1

                        # Debug: Log every 20th write to show activity
                        if write_count % 20 == 0:
                            print(f"[SerialBroker] Wrote {write_count} messages (latest: {message.strip()})")
                else:
                    print(f"[SerialBroker] WARNING: Cannot write '{message.strip()}' - serial not open")

                self.write_queue.task_done()

            except Exception as e:
                if self.running:
                    print(f"[SerialBroker] Write error: {e}")
                break

        print(f"[SerialBroker] Write thread stopped (wrote {write_count} total messages)")

    def write(self, message: str):
        """
        Queue a message to be written to serial.
        Thread-safe, non-blocking.

        Args:
            message: Message to send (will add newline if missing)
        """
        if not message.endswith('\n'):
            message += '\n'

        self.write_queue.put(message)

    def write_led(self, color: str, value: int):
        """
        Write LED command.
        Thread-safe convenience method.

        Args:
            color: 'red', 'yellow', or 'green'
            value: 0-255 brightness
        """
        # Clamp value
        value = max(0, min(255, value))
        cmd = f"{color.upper()}:{value}"

        # Debug: Print every 50th LED command to avoid spam
        if random.randint(0, 50) == 0:
            print(f"[SerialBroker] Queuing LED command: {cmd}")
            print(f"[SerialBroker] Queue size: {self.write_queue.qsize()}")

        self.write(cmd)  # Use write() method to ensure newline is added

    def register_message_callback(self, callback: Callable[[str], None]):
        """
        Register a callback for incoming messages.

        Args:
            callback: Function that takes (message: str) parameter
        """
        if callback not in self.message_callbacks:
            self.message_callbacks.append(callback)

    def unregister_message_callback(self, callback: Callable[[str], None]):
        """
        Unregister a message callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self.message_callbacks:
            self.message_callbacks.remove(callback)

    def is_connected(self) -> bool:
        """
        Check if broker is connected and running.

        Returns:
            True if connected
        """
        return self.running and self.serial_conn and self.serial_conn.is_open
