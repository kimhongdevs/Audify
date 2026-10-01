"""
Audify - Professional Windows Audio Recorder
Records system loopback audio and microphone input directly to high-quality MP3.

Created by Kimhong, Devs
Version: 1.0.0
"""

import os
import signal
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from core.settings import SettingsManager
from ui.main_window import MainWindow
from ui.styles import DARK_THEME_QSS


def main() -> None:
    # Ensure working directory is application root
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Audify")
    app.setOrganizationName("Kimhong, Devs")
    app.setApplicationVersion("1.0.0")

    # Apply global modern dark stylesheet
    app.setStyleSheet(DARK_THEME_QSS)

    # Ensure assets and icon exist
    assets_dir = os.path.join(base_dir, "assets")
    icon_png = os.path.join(assets_dir, "icon.png")
    icon_ico = os.path.join(assets_dir, "icon.ico")

    if not os.path.exists(icon_png) or not os.path.exists(icon_ico):
        try:
            from generate_assets import generate_icon
            generate_icon(assets_dir)
        except Exception as e:
            print(f"[Audify] Could not auto-generate icon: {e}")

    icon_path = icon_ico if os.path.exists(icon_ico) else icon_png
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Initialize settings and start main window
    settings = SettingsManager()
    window = MainWindow(settings=settings, icon_path=icon_png if os.path.exists(icon_png) else icon_ico)
    window.show()

    # Graceful handling of Ctrl+C in terminal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if "--test" in sys.argv:
        try:
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                sys.stdout = open("CONOUT$", "w", buffering=1, encoding="utf-8", errors="replace")
                sys.stderr = open("CONOUT$", "w", buffering=1, encoding="utf-8", errors="replace")
        except Exception:
            pass

        log_file = os.path.join(base_dir, "test_verification.log")

        def log_msg(msg: str) -> None:
            print(msg)
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass

        log_msg("\n=== [Audify Test Mode] ===")
        log_msg(f"Executable: {sys.executable}")
        log_msg(f"Frozen: {getattr(sys, 'frozen', False)}")
        log_msg(f"Output devices found: {window.loopback_combo.count()}")
        log_msg(f"Mic devices found: {window.mic_combo.count()}")

        if window.loopback_combo.count() == 0:
            log_msg("[ERROR] No loopback devices detected!")
            window.hotkey_mgr.stop()
            os._exit(1)

        log_msg("[Audify Test Mode] Starting test recording for 2 seconds...")
        window.start_recording()

        def stop_and_validate():
            log_msg("[Audify Test Mode] Stopping recording...")
            window.stop_recording()

            def validate_result():
                history = settings.get_history()
                if not history:
                    log_msg("[ERROR] History is empty, recording failed!")
                    window.hotkey_mgr.stop()
                    os._exit(1)

                rec = history[0]
                rec_path = rec.get("path")
                log_msg(f"[Audify Test Mode] Recorded MP3 Path: {rec_path}")
                if not rec_path or not os.path.exists(rec_path):
                    log_msg("[ERROR] Recorded MP3 does not exist on disk!")
                    window.hotkey_mgr.stop()
                    os._exit(1)

                file_size = os.path.getsize(rec_path)
                log_msg(f"[Audify Test Mode] Recorded MP3 Size: {file_size} bytes")
                if file_size < 1000:
                    log_msg(f"[ERROR] Recorded MP3 too small: {file_size} bytes")
                    window.hotkey_mgr.stop()
                    os._exit(1)

                # Verify MP3 sync header
                with open(rec_path, "rb") as f:
                    header = f.read(4)
                    is_mp3_sync = header[0] == 0xFF and (header[1] & 0xE0) == 0xE0
                    log_msg(f"[Audify Test Mode] Valid MP3 frame sync detected: {is_mp3_sync}")
                    if not is_mp3_sync:
                        log_msg("[ERROR] File does not have valid MP3 frame header!")
                        window.hotkey_mgr.stop()
                        os._exit(1)

                # Clean up test recording
                try:
                    os.remove(rec_path)
                    settings.remove_history_entry(rec_path)
                    log_msg("[Audify Test Mode] Test file cleaned up.")
                except Exception:
                    pass

                log_msg("=== [Audify Test Mode: All Verification Checks Passed!] ===\n")
                window.hotkey_mgr.stop()
                if window.tray_icon:
                    window.tray_icon.hide()
                os._exit(0)

            QTimer.singleShot(800, validate_result)

        QTimer.singleShot(2500, stop_and_validate)

    exit_code = app.exec()
    try:
        window.hotkey_mgr.stop()
        if window.tray_icon:
            window.tray_icon.hide()
    except Exception:
        pass
    os._exit(exit_code)


if __name__ == "__main__":
    main()
