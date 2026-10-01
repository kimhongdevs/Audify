"""
Global Hotkey Listener for Audify.
Uses pynput to monitor system-wide hotkeys (e.g., Ctrl+Shift+R)
and signals the Qt GUI thread.
"""

from typing import Callable, Optional
from PySide6.QtCore import QObject, Signal


class GlobalHotkeySignals(QObject):
    """Signals bridge for global hotkeys across threads."""
    triggered = Signal()


class GlobalHotkeyManager:
    """Manages system-wide global hotkeys using pynput."""

    def __init__(self, hotkey_str: str = "<ctrl>+<shift>+r") -> None:
        self.hotkey_str = hotkey_str.lower()
        self.signals = GlobalHotkeySignals()
        self._listener = None
        self._is_running = False

    def start(self) -> bool:
        """Starts the background keyboard listener."""
        if self._is_running:
            return True

        try:
            from pynput import keyboard

            # Build hotkey mapping
            hotkey_map = {
                self.hotkey_str: self._on_hotkey_triggered
            }
            self._listener = keyboard.GlobalHotKeys(hotkey_map)
            self._listener.daemon = True
            self._listener.start()
            self._is_running = True
            return True
        except Exception as e:
            print(f"[GlobalHotkeyManager] Failed to register global hotkey '{self.hotkey_str}': {e}")
            return False

    def stop(self) -> None:
        """Stops the global keyboard listener."""
        if self._listener and self._is_running:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._is_running = False
            self._listener = None

    def _on_hotkey_triggered(self) -> None:
        """Invoked from pynput thread when hotkey combination is pressed."""
        self.signals.triggered.emit()
