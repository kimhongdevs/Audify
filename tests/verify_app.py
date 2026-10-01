"""
Verification script for Audify GUI launch and device enumeration.
"""
import sys
import os

# Set working directory to project root
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root_dir)
sys.path.insert(0, root_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from core.settings import SettingsManager
from ui.main_window import MainWindow

try:
    app = QApplication(sys.argv)
    settings = SettingsManager()
    window = MainWindow(settings=settings)
    window.show()

    loopbacks = window.loopback_combo.count()
    mics = window.mic_combo.count()
    print(f"Loopback devices found: {loopbacks}")
    print(f"Mic devices found: {mics}")

    assert loopbacks > 0, "No loopback devices detected"
    assert mics > 0, "No mic devices detected"
    print("MainWindow initialized and displayed successfully without errors!")

    # Close cleanly after 1 second
    def clean_exit():
        print("Closing window via _quit_application()...")
        window._quit_application()

    QTimer.singleShot(1000, clean_exit)
    exit_code = app.exec()
    print(f"App event loop finished with code: {exit_code}")
    sys.exit(exit_code)

except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
