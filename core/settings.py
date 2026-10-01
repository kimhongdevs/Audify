"""
Settings and state persistence for Audify.
Saves and loads settings from %APPDATA%/Audify/settings.json.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional


class SettingsManager:
    """Manages application settings, persistence, and recording history."""

    DEFAULT_SETTINGS: Dict[str, Any] = {
        "bitrate": 320,  # 128, 192, 256, 320 kbps
        "sample_rate": 48000,  # 44100 or 48000 Hz
        "channels": 2,  # Stereo
        "mic_enabled": False,
        "mic_volume": 1.0,  # 0.0 - 2.0
        "system_volume": 1.0,  # 0.0 - 2.0
        "selected_output_device_name": None,
        "selected_input_device_name": None,
        "output_dir": "",
        "minimize_to_tray": True,
        "hotkey": "Ctrl+Shift+R",
        "history": []
    }

    def __init__(self) -> None:
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.data: Dict[str, Any] = {}
        self.load()

    def _get_config_dir(self) -> str:
        """Determines the appropriate config directory on Windows."""
        appdata = os.environ.get("APPDATA")
        if appdata:
            base_dir = os.path.join(appdata, "Audify")
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".audify")
        os.makedirs(base_dir, exist_ok=True)
        return base_dir

    def _get_default_output_dir(self) -> str:
        """Returns the default recording save folder: ~/Music/Audify."""
        music_dir = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.exists(music_dir):
            music_dir = os.path.expanduser("~")
        audify_music = os.path.join(music_dir, "Audify")
        return audify_music

    def load(self) -> None:
        """Loads settings from JSON file, falling back to defaults for missing keys."""
        self.data = dict(self.DEFAULT_SETTINGS)
        if not self.data["output_dir"]:
            self.data["output_dir"] = self._get_default_output_dir()

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        self.data.update(saved)
            except Exception as e:
                print(f"[SettingsManager] Failed to load settings: {e}. Using defaults.")

        # Ensure output directory is valid
        if not self.data.get("output_dir"):
            self.data["output_dir"] = self._get_default_output_dir()

        self.ensure_output_dir()

    def save(self) -> None:
        """Atomically saves settings to JSON file."""
        temp_file = self.config_file + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            if os.path.exists(self.config_file):
                os.replace(temp_file, self.config_file)
            else:
                os.rename(temp_file, self.config_file)
        except Exception as e:
            print(f"[SettingsManager] Failed to save settings: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def ensure_output_dir(self) -> str:
        """Ensures that the output directory exists on disk."""
        out_dir = self.data.get("output_dir", self._get_default_output_dir())
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as e:
            print(f"[SettingsManager] Could not create output dir '{out_dir}': {e}")
            out_dir = self._get_default_output_dir()
            os.makedirs(out_dir, exist_ok=True)
            self.data["output_dir"] = out_dir
        return out_dir

    def add_history_entry(self, entry: Dict[str, Any]) -> None:
        """Adds a recording to history (max 100 entries) and saves."""
        history: List[Dict[str, Any]] = self.data.get("history", [])
        # Avoid duplicate path
        history = [h for h in history if h.get("path") != entry.get("path")]
        history.insert(0, entry)
        self.data["history"] = history[:100]
        self.save()

    def remove_history_entry(self, file_path: str) -> None:
        """Removes a recording from the history list."""
        history = self.data.get("history", [])
        self.data["history"] = [h for h in history if h.get("path") != file_path]
        self.save()

    def get_history(self) -> List[Dict[str, Any]]:
        """Returns the recording history list."""
        return self.data.get("history", [])
