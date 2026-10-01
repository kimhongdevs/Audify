"""
Main Application Window for Audify.
Integrates custom frameless title bar, device selectors, real-time VU meter,
large pulsing record button, settings management, system tray, and history.
"""

from datetime import datetime
import os
import time
from typing import Optional

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizeGrip,
    QSlider,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget
)

from core.hotkeys import GlobalHotkeyManager
from core.recorder import AudioDeviceInfo, AudioRecorder
from core.settings import SettingsManager
from ui.about_dialog import AboutDialog
from ui.history_widget import HistoryDialog, format_duration
from ui.record_button import CircularRecordButton
from ui.title_bar import FramelessTitleBar
from ui.vu_meter import VuMeterWidget


class MainWindow(QMainWindow):
    """Audify Main Application Window."""

    # Thread-safe Qt Signals
    levels_updated = Signal(float, float, float, float)
    recording_error = Signal(str)
    recording_finished = Signal(str, float, int)

    def __init__(self, settings: SettingsManager, icon_path: str = "") -> None:
        super().__init__()
        self.settings = settings
        self.icon_path = icon_path

        # Core recording engine
        self.recorder = AudioRecorder(
            on_level_update=lambda pl, pr, rl, rr: self.levels_updated.emit(pl, pr, rl, rr),
            on_error=lambda err: self.recording_error.emit(err),
            on_finished=lambda fp, dur, size: self.recording_finished.emit(fp, dur, size)
        )

        # Connect signals to GUI slots
        self.levels_updated.connect(self._on_levels_updated)
        self.recording_error.connect(self._on_recording_error)
        self.recording_finished.connect(self._on_recording_finished)

        # Global Hotkey Manager (Ctrl+Shift+R)
        self.hotkey_mgr = GlobalHotkeyManager("<ctrl>+<shift>+r")
        self.hotkey_mgr.signals.triggered.connect(self.toggle_recording)
        self.hotkey_mgr.start()

        # Recording timer state
        self.timer_seconds: float = 0.0
        self._record_start_time: float = 0.0
        self._record_elapsed_before_pause: float = 0.0
        self.gui_timer = QTimer(self)
        self.gui_timer.setInterval(200)
        self.gui_timer.timeout.connect(self._update_timer_display)

        # Window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(480, 680)
        self.setMinimumSize(440, 620)
        self.setWindowTitle("Audify")
        if self.icon_path and os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        # Setup UI layout and components
        self._init_ui()

        # Setup System Tray
        self._init_tray()

        # Enumerate and populate audio devices
        self.refresh_devices()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Custom Title Bar
        self.title_bar = FramelessTitleBar(self, title="Audify", icon_path=self.icon_path)
        self.title_bar.about_clicked.connect(self._open_about_dialog)
        self.title_bar.minimize_clicked.connect(self._on_minimize_clicked)
        self.title_bar.close_clicked.connect(self.close)
        main_layout.addWidget(self.title_bar)

        # Content container
        content_widget = QWidget(self)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(18, 14, 18, 10)
        content_layout.setSpacing(12)

        # Top Bar: Status Chip & Global Hotkey Badge
        top_bar = QHBoxLayout()
        self.status_chip = QLabel("● Ready", self)
        self.status_chip.setObjectName("statusChip")
        self.status_chip.setProperty("state", "ready")
        self.status_chip.setStyleSheet("QLabel { background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 3px 10px; font-weight: 600; font-size: 11px; }")
        top_bar.addWidget(self.status_chip)

        top_bar.addStretch()

        hotkey_label = QLabel("Global Hotkey: Ctrl+Shift+R", self)
        hotkey_label.setObjectName("hotkeyBadge")
        top_bar.addWidget(hotkey_label)
        content_layout.addLayout(top_bar)

        # 2. Visualizer Card (Timer, VU Meter, Large Pulsing Record Button)
        vis_card = QFrame(self)
        vis_card.setObjectName("highlightCard")
        vis_layout = QVBoxLayout(vis_card)
        vis_layout.setContentsMargins(14, 12, 14, 14)
        vis_layout.setSpacing(8)

        # Digital Timer
        self.timer_label = QLabel("00:00:00", self)
        self.timer_label.setObjectName("timerDisplay")
        self.timer_label.setAlignment(Qt.AlignCenter)
        vis_layout.addWidget(self.timer_label)

        # Dual Channel VU Level Meter
        self.vu_meter = VuMeterWidget(self)
        vis_layout.addWidget(self.vu_meter)

        # Circular Record Button & Secondary Actions
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)
        controls_layout.setSpacing(20)

        # Pause / Resume Button
        self.pause_btn = QPushButton("⏸ Pause", self)
        self.pause_btn.setObjectName("pauseButton")
        self.pause_btn.setFixedSize(86, 36)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        controls_layout.addWidget(self.pause_btn)

        # Center Large Pulsing Record Button
        self.record_btn = CircularRecordButton(self)
        self.record_btn.setToolTip("Start / Stop Recording (Ctrl+Shift+R)")
        self.record_btn.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_btn)

        # Stop Button
        self.stop_btn = QPushButton("⏹ Stop", self)
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setFixedSize(86, 36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)
        controls_layout.addWidget(self.stop_btn)

        vis_layout.addLayout(controls_layout)
        content_layout.addWidget(vis_card)

        # 3. Audio Devices Card
        device_card = QFrame(self)
        device_card.setObjectName("cardWidget")
        dev_layout = QVBoxLayout(device_card)
        dev_layout.setContentsMargins(12, 10, 12, 10)
        dev_layout.setSpacing(8)

        # Header with Refresh
        dev_header = QHBoxLayout()
        dev_title = QLabel("Audio Sources", self)
        dev_title.setObjectName("sectionHeader")
        dev_header.addWidget(dev_title)
        dev_header.addStretch()

        self.refresh_btn = QPushButton("↻ Refresh Devices", self)
        self.refresh_btn.setFixedSize(115, 24)
        self.refresh_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        dev_header.addWidget(self.refresh_btn)
        dev_layout.addLayout(dev_header)

        # System Loopback Selector
        loop_row = QHBoxLayout()
        loop_lbl = QLabel("System Output:", self)
        loop_lbl.setStyleSheet("color: #CBD5E1; font-weight: 500; min-width: 95px;")
        self.loopback_combo = QComboBox(self)
        self.loopback_combo.currentIndexChanged.connect(self._on_loopback_changed)
        loop_row.addWidget(loop_lbl)
        loop_row.addWidget(self.loopback_combo, stretch=1)
        dev_layout.addLayout(loop_row)

        # Microphone Toggle and Selector
        mic_row = QHBoxLayout()
        self.mic_checkbox = QCheckBox("Record Mic", self)
        self.mic_checkbox.setStyleSheet("min-width: 95px;")
        self.mic_checkbox.setChecked(self.settings.get("mic_enabled", False))
        self.mic_checkbox.toggled.connect(self._on_mic_toggled)
        self.mic_combo = QComboBox(self)
        self.mic_combo.setEnabled(self.mic_checkbox.isChecked())
        self.mic_combo.currentIndexChanged.connect(self._on_mic_changed)
        mic_row.addWidget(self.mic_checkbox)
        mic_row.addWidget(self.mic_combo, stretch=1)
        dev_layout.addLayout(mic_row)

        content_layout.addWidget(device_card)

        # 4. Format & Save Settings Card
        format_card = QFrame(self)
        format_card.setObjectName("cardWidget")
        format_layout = QVBoxLayout(format_card)
        format_layout.setContentsMargins(12, 10, 12, 10)
        format_layout.setSpacing(8)

        format_title = QLabel("Output & Encoding", self)
        format_title.setObjectName("sectionHeader")
        format_layout.addWidget(format_title)

        grid = QGridLayout()
        grid.setSpacing(8)

        # Bitrate
        grid.addWidget(QLabel("Bitrate:", self), 0, 0)
        self.bitrate_combo = QComboBox(self)
        for b in [128, 192, 256, 320]:
            self.bitrate_combo.addItem(f"{b} kbps (CBR)", b)
        curr_bitrate = self.settings.get("bitrate", 320)
        idx = self.bitrate_combo.findData(curr_bitrate)
        if idx >= 0:
            self.bitrate_combo.setCurrentIndex(idx)
        self.bitrate_combo.currentIndexChanged.connect(self._on_bitrate_changed)
        grid.addWidget(self.bitrate_combo, 0, 1)

        # Sample Rate
        grid.addWidget(QLabel("Sample Rate:", self), 0, 2)
        self.rate_combo = QComboBox(self)
        self.rate_combo.addItem("48.0 kHz", 48000)
        self.rate_combo.addItem("44.1 kHz", 44100)
        curr_rate = self.settings.get("sample_rate", 48000)
        r_idx = self.rate_combo.findData(curr_rate)
        if r_idx >= 0:
            self.rate_combo.setCurrentIndex(r_idx)
        self.rate_combo.currentIndexChanged.connect(self._on_rate_changed)
        grid.addWidget(self.rate_combo, 0, 3)

        format_layout.addLayout(grid)

        # Output Folder Row
        folder_row = QHBoxLayout()
        folder_lbl = QLabel("Save To:", self)
        folder_lbl.setStyleSheet("color: #CBD5E1; font-weight: 500; min-width: 55px;")
        folder_row.addWidget(folder_lbl)

        self.folder_label = QLabel(self.settings.ensure_output_dir(), self)
        self.folder_label.setStyleSheet("color: #94A3B8; font-size: 11px; background: #131325; padding: 5px 8px; border-radius: 6px; border: 1px solid #23233C;")
        folder_row.addWidget(self.folder_label, stretch=1)

        browse_btn = QPushButton("Browse...", self)
        browse_btn.setFixedSize(76, 26)
        browse_btn.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        browse_btn.clicked.connect(self._browse_output_dir)
        folder_row.addWidget(browse_btn)

        format_layout.addLayout(folder_row)
        content_layout.addWidget(format_card)

        # 5. Bottom Bar: History Button & Footer
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 4, 0, 0)

        self.history_btn = QPushButton("📜 Recordings History", self)
        self.history_btn.setStyleSheet("font-size: 11px; padding: 4px 10px;")
        self.history_btn.clicked.connect(self._open_history_dialog)
        bottom_bar.addWidget(self.history_btn)

        bottom_bar.addStretch()

        # Branding Footer
        footer_label = QLabel("© Kimhong, Devs", self)
        footer_label.setObjectName("footerText")
        bottom_bar.addWidget(footer_label)

        # Resizing grip in bottom-right corner
        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(14, 14)
        bottom_bar.addWidget(size_grip, alignment=Qt.AlignBottom | Qt.AlignRight)

        content_layout.addLayout(bottom_bar)
        main_layout.addWidget(content_widget, stretch=1)

    def _init_tray(self) -> None:
        """Initializes the Windows system tray icon and menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return

        self.tray_icon = QSystemTrayIcon(self)
        if self.icon_path and os.path.exists(self.icon_path):
            self.tray_icon.setIcon(QIcon(self.icon_path))
        else:
            self.tray_icon.setIcon(self.windowIcon())

        tray_menu = QMenu(self)
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #16162B;
                border: 1px solid #2B2B4D;
                color: #F1F5F9;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #7C3AED;
            }
        """)

        show_action = QAction("Open Audify", self)
        show_action.triggered.connect(self._restore_from_tray)
        tray_menu.addAction(show_action)

        self.tray_record_action = QAction("Start Recording", self)
        self.tray_record_action.triggered.connect(self.toggle_recording)
        tray_menu.addAction(self.tray_record_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit Audify", self)
        quit_action.triggered.connect(self._quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger or reason == QSystemTrayIcon.DoubleClick:
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_minimize_clicked(self) -> None:
        if self.settings.get("minimize_to_tray", True) and self.tray_icon:
            self.hide()
            self.tray_icon.showMessage(
                "Audify Minimized",
                "Recording continues in background. Press Ctrl+Shift+R to toggle.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.showMinimized()

    def refresh_devices(self) -> None:
        """Refreshes and populates available WASAPI audio loopback and mic devices."""
        loopbacks, mics, def_loop_idx, def_mic_idx = AudioRecorder.get_devices()

        # Update loopback dropdown
        self.loopback_combo.blockSignals(True)
        self.loopback_combo.clear()
        saved_loop_name = self.settings.get("selected_output_device_name")
        target_loop_idx = 0

        for i, dev in enumerate(loopbacks):
            clean_name = dev.name.replace(" [Loopback]", "").strip()
            self.loopback_combo.addItem(f"{clean_name} ({dev.default_sample_rate} Hz)", dev.index)
            if saved_loop_name and saved_loop_name in dev.name:
                target_loop_idx = i
            elif not saved_loop_name and dev.index == def_loop_idx:
                target_loop_idx = i

        if self.loopback_combo.count() > 0:
            self.loopback_combo.setCurrentIndex(target_loop_idx)
        else:
            self.loopback_combo.addItem("No WASAPI Loopback Device Found", None)
        self.loopback_combo.blockSignals(False)

        # Update mic dropdown
        self.mic_combo.blockSignals(True)
        self.mic_combo.clear()
        saved_mic_name = self.settings.get("selected_input_device_name")
        target_mic_idx = 0

        for i, dev in enumerate(mics):
            self.mic_combo.addItem(f"{dev.name} ({dev.default_sample_rate} Hz)", dev.index)
            if saved_mic_name and saved_mic_name in dev.name:
                target_mic_idx = i
            elif not saved_mic_name and dev.index == def_mic_idx:
                target_mic_idx = i

        if self.mic_combo.count() > 0:
            self.mic_combo.setCurrentIndex(target_mic_idx)
        else:
            self.mic_combo.addItem("No Microphone Device Found", None)
        self.mic_combo.blockSignals(False)

    def _on_loopback_changed(self, index: int) -> None:
        text = self.loopback_combo.currentText()
        self.settings.set("selected_output_device_name", text)

    def _on_mic_changed(self, index: int) -> None:
        text = self.mic_combo.currentText()
        self.settings.set("selected_input_device_name", text)

    def _on_mic_toggled(self, checked: bool) -> None:
        self.mic_combo.setEnabled(checked)
        self.settings.set("mic_enabled", checked)

    def _on_bitrate_changed(self, index: int) -> None:
        bitrate = self.bitrate_combo.currentData()
        self.settings.set("bitrate", bitrate)

    def _on_rate_changed(self, index: int) -> None:
        rate = self.rate_combo.currentData()
        self.settings.set("sample_rate", rate)

    def _browse_output_dir(self) -> None:
        current_dir = self.settings.ensure_output_dir()
        selected_dir = QFileDialog.getExistingDirectory(
            self, "Select Recording Save Folder", current_dir
        )
        if selected_dir:
            self.settings.set("output_dir", selected_dir)
            self.folder_label.setText(selected_dir)

    def toggle_recording(self) -> None:
        """Toggles between starting and stopping recording."""
        if not self.recorder.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self) -> None:
        """Starts audio recording and encoding."""
        if self.recorder.is_recording:
            return

        # Generate unique auto-named file: Audify_YYYY-MM-DD_HH-MM-SS.mp3
        out_dir = self.settings.ensure_output_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Audify_{timestamp}.mp3"
        filepath = os.path.join(out_dir, filename)

        loop_idx = self.loopback_combo.currentData()
        mic_idx = self.mic_combo.currentData() if self.mic_checkbox.isChecked() else None
        bitrate = self.bitrate_combo.currentData() or 320
        rate = self.rate_combo.currentData() or 48000

        success = self.recorder.start_recording(
            output_filepath=filepath,
            loopback_device_index=loop_idx,
            mic_device_index=mic_idx,
            mic_enabled=self.mic_checkbox.isChecked(),
            bitrate=bitrate,
            sample_rate=rate
        )

        if success:
            # Update UI state
            self.record_btn.set_recording(True, False)
            self.pause_btn.setEnabled(True)
            self.pause_btn.setText("⏸ Pause")
            self.stop_btn.setEnabled(True)

            self.loopback_combo.setEnabled(False)
            self.mic_combo.setEnabled(False)
            self.mic_checkbox.setEnabled(False)
            self.bitrate_combo.setEnabled(False)
            self.rate_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)

            self._set_status("recording", "● Recording...")
            if self.tray_record_action:
                self.tray_record_action.setText("Stop Recording")

            # Start timer
            self.timer_seconds = 0.0
            self._record_elapsed_before_pause = 0.0
            self._record_start_time = time.time()
            self.gui_timer.start()

    def toggle_pause(self) -> None:
        """Pauses or resumes ongoing recording."""
        if not self.recorder.is_recording:
            return

        if not self.recorder.is_paused:
            self.recorder.pause_recording()
            self.record_btn.set_recording(True, True)
            self.pause_btn.setText("▶ Resume")
            self._set_status("paused", "● Paused")
            self._record_elapsed_before_pause += time.time() - self._record_start_time
            self.gui_timer.stop()
        else:
            self.recorder.resume_recording()
            self.record_btn.set_recording(True, False)
            self.pause_btn.setText("⏸ Pause")
            self._set_status("recording", "● Recording...")
            self._record_start_time = time.time()
            self.gui_timer.start()

    def stop_recording(self) -> None:
        """Stops ongoing recording."""
        if not self.recorder.is_recording:
            return

        self._set_status("ready", "● Finalizing MP3...")
        self.gui_timer.stop()
        self.vu_meter.reset_levels()

        self.recorder.stop_recording()

        # Reset UI
        self.record_btn.set_recording(False, False)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Pause")
        self.stop_btn.setEnabled(False)

        self.loopback_combo.setEnabled(True)
        self.mic_checkbox.setEnabled(True)
        self.mic_combo.setEnabled(self.mic_checkbox.isChecked())
        self.bitrate_combo.setEnabled(True)
        self.rate_combo.setEnabled(True)
        self.refresh_btn.setEnabled(True)

        if self.tray_record_action:
            self.tray_record_action.setText("Start Recording")

    def _set_status(self, state: str, text: str) -> None:
        """Sets status chip text and color."""
        self.status_chip.setText(text)
        if state == "recording":
            self.status_chip.setStyleSheet("QLabel { background-color: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); border-radius: 10px; padding: 3px 10px; font-weight: 600; font-size: 11px; }")
        elif state == "paused":
            self.status_chip.setStyleSheet("QLabel { background-color: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 10px; padding: 3px 10px; font-weight: 600; font-size: 11px; }")
        else:
            self.status_chip.setStyleSheet("QLabel { background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 3px 10px; font-weight: 600; font-size: 11px; }")

    def _update_timer_display(self) -> None:
        if self.recorder.is_recording and not self.recorder.is_paused:
            total_sec = self._record_elapsed_before_pause + (time.time() - self._record_start_time)
            self.timer_seconds = total_sec
            secs = int(total_sec)
            hrs = secs // 3600
            mins = (secs % 3600) // 60
            s = secs % 60
            self.timer_label.setText(f"{hrs:02d}:{mins:02d}:{s:02d}")

    def _on_levels_updated(self, peak_l: float, peak_r: float, rms_l: float, rms_r: float) -> None:
        if self.recorder.is_recording and not self.recorder.is_paused:
            self.vu_meter.update_levels(peak_l, peak_r, rms_l, rms_r)
        else:
            self.vu_meter.reset_levels()

    def _on_recording_error(self, err_msg: str) -> None:
        self.stop_recording()
        QMessageBox.critical(self, "Recording Error", f"An audio error occurred:\n{err_msg}")
        self._set_status("ready", "● Error encountered")

    def _on_recording_finished(self, filepath: str, duration: float, size: int) -> None:
        # Add to history
        filename = os.path.basename(filepath)
        entry = {
            "filename": filename,
            "path": filepath,
            "duration": duration,
            "size": size,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.settings.add_history_entry(entry)

        self._set_status("ready", f"● Saved: {filename}")
        if self.tray_icon:
            self.tray_icon.showMessage(
                "Recording Saved",
                f"{filename}\nDuration: {format_duration(duration)}",
                QSystemTrayIcon.Information,
                3000
            )

    def _open_history_dialog(self) -> None:
        dlg = HistoryDialog(self.settings, self)
        dlg.exec()

    def _open_about_dialog(self) -> None:
        dlg = AboutDialog(icon_path=self.icon_path, parent=self)
        dlg.exec()

    def _quit_application(self) -> None:
        self.stop_recording()
        self.hotkey_mgr.stop()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        """Handle window closing: check if minimize to tray is enabled."""
        if self.settings.get("minimize_to_tray", True) and self.tray_icon and not QApplication.isSavingSession():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Audify Minimized to Tray",
                "Audify is still running. Right-click the tray icon to quit.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self._quit_application()
            event.accept()
