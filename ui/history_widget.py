"""
Recording History Widget & Dialog for Audify.
Displays list of recorded MP3s with duration, file size, play, folder reveal, and delete options.
"""

import os
import subprocess
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget
)

from core.settings import SettingsManager


def format_duration(seconds: float) -> str:
    """Formats seconds into MM:SS or HH:MM:SS."""
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    s = secs % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{s:02d}"
    return f"{minutes:02d}:{s:02d}"


def format_filesize(size_bytes: int) -> str:
    """Formats bytes into human readable KB or MB."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


class HistoryItemWidget(QWidget):
    """Row item in the recording history list."""

    deleted = Signal(str)

    def __init__(self, entry: Dict[str, Any], settings: SettingsManager, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.entry = entry
        self.settings = settings
        self.file_path = entry.get("path", "")

        self.setStyleSheet("""
            QWidget#historyItem {
                background-color: #19192E;
                border: 1px solid #2B2B48;
                border-radius: 8px;
                padding: 6px;
            }
            QWidget#historyItem:hover {
                border-color: #4C4C7E;
                background-color: #1E1E36;
            }
        """)
        self.setObjectName("historyItem")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Audio icon
        icon_label = QLabel("🎵", self)
        icon_label.setStyleSheet("font-size: 16px; color: #8B5CF6;")
        layout.addWidget(icon_label)

        # Info container
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        file_name = entry.get("filename", os.path.basename(self.file_path))
        name_label = QLabel(file_name, self)
        name_label.setStyleSheet("font-weight: 600; color: #F1F5F9; font-size: 12px;")
        info_layout.addWidget(name_label)

        dur_str = format_duration(entry.get("duration", 0))
        size_str = format_filesize(entry.get("size", 0))
        timestamp = entry.get("timestamp", "")
        meta_text = f"{dur_str}  •  {size_str}"
        if timestamp:
            meta_text += f"  •  {timestamp}"

        meta_label = QLabel(meta_text, self)
        meta_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        info_layout.addWidget(meta_label)

        layout.addLayout(info_layout, stretch=1)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        # Play button
        self.play_btn = QPushButton("▶", self)
        self.play_btn.setFixedSize(30, 30)
        self.play_btn.setToolTip("Play recording")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D4D;
                border: 1px solid #3F3F6D;
                border-radius: 6px;
                color: #A78BFA;
                font-size: 11px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #7C3AED;
                color: #FFFFFF;
                border-color: #8B5CF6;
            }
        """)
        self.play_btn.clicked.connect(self._play_file)
        btn_layout.addWidget(self.play_btn)

        # Open in Folder button
        self.folder_btn = QPushButton("📁", self)
        self.folder_btn.setFixedSize(30, 30)
        self.folder_btn.setToolTip("Show in folder")
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D4D;
                border: 1px solid #3F3F6D;
                border-radius: 6px;
                color: #94A3B8;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #383861;
                color: #F8FAFC;
                border-color: #555588;
            }
        """)
        self.folder_btn.clicked.connect(self._open_folder)
        btn_layout.addWidget(self.folder_btn)

        # Delete button
        self.del_btn = QPushButton("✕", self)
        self.del_btn.setFixedSize(30, 30)
        self.del_btn.setToolTip("Delete recording")
        self.del_btn.setStyleSheet("""
            QPushButton {
                background-color: #2D2D4D;
                border: 1px solid #3F3F6D;
                border-radius: 6px;
                color: #94A3B8;
                font-size: 11px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #EF4444;
                color: #FFFFFF;
                border-color: #F87171;
            }
        """)
        self.del_btn.clicked.connect(self._delete_file)
        btn_layout.addWidget(self.del_btn)

        layout.addLayout(btn_layout)

    def _play_file(self) -> None:
        if os.path.exists(self.file_path):
            try:
                os.startfile(self.file_path)
            except Exception as e:
                QMessageBox.warning(self, "Playback Error", f"Could not play audio: {e}")
        else:
            QMessageBox.warning(self, "File Not Found", "The audio file no longer exists on disk.")

    def _open_folder(self) -> None:
        if os.path.exists(self.file_path):
            subprocess.run(f'explorer.exe /select,"{os.path.normpath(self.file_path)}"', shell=True)
        else:
            folder = os.path.dirname(self.file_path)
            if os.path.exists(folder):
                subprocess.run(f'explorer.exe "{os.path.normpath(folder)}"', shell=True)
            else:
                QMessageBox.warning(self, "Folder Not Found", "The destination folder does not exist.")

    def _delete_file(self) -> None:
        reply = QMessageBox.question(
            self,
            "Delete Recording",
            f"Are you sure you want to delete this recording?\n\n{os.path.basename(self.file_path)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if os.path.exists(self.file_path):
                try:
                    os.remove(self.file_path)
                except Exception as e:
                    QMessageBox.warning(self, "Delete Error", f"Could not remove file: {e}")
            self.settings.remove_history_entry(self.file_path)
            self.deleted.emit(self.file_path)


class HistoryDialog(QDialog):
    """Dialog displaying recording history with management actions."""

    def __init__(self, settings: SettingsManager, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Recording History - Audify")
        self.resize(500, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F1A;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Recording History", self)
        title_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #F8FAFC;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        open_folder_btn = QPushButton("Open Folder", self)
        open_folder_btn.clicked.connect(self._open_output_dir)
        header_layout.addWidget(open_folder_btn)

        layout.addLayout(header_layout)

        # Scroll Area for history items
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)

        self.scroll_area.setWidget(self.list_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Close button at bottom
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        close_btn = QPushButton("Done", self)
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(close_btn)
        layout.addLayout(bottom_layout)

        self.refresh_list()

    def refresh_list(self) -> None:
        # Clear existing
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        history = self.settings.get_history()
        if not history:
            empty_label = QLabel("No recordings yet.\nRecord system or microphone audio to view them here.", self)
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #64748B; font-size: 13px; margin: 40px 0px;")
            self.list_layout.addWidget(empty_label)
            return

        for entry in history:
            item_widget = HistoryItemWidget(entry, self.settings, self.list_container)
            item_widget.deleted.connect(lambda: self.refresh_list())
            self.list_layout.addWidget(item_widget)

        self.list_layout.addStretch()

    def _open_output_dir(self) -> None:
        out_dir = self.settings.ensure_output_dir()
        if os.path.exists(out_dir):
            subprocess.run(f'explorer.exe "{os.path.normpath(out_dir)}"', shell=True)
