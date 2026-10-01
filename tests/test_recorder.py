"""
Automated Integration Test for Audify Audio Engine.
Tests device discovery, WASAPI loopback capture, MP3 streaming encoding, and file finalization.
"""

import os
import sys
import time

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recorder import AudioRecorder
from core.settings import SettingsManager


def test_audio_pipeline():
    print("\n--- [1] Testing SettingsManager ---")
    settings = SettingsManager()
    out_dir = settings.ensure_output_dir()
    print(f"Output directory verified: {out_dir}")
    assert os.path.exists(out_dir), "Output directory must exist"

    print("\n--- [2] Testing Device Discovery ---")
    loopbacks, mics, def_loop, def_mic = AudioRecorder.get_devices()
    print(f"Found {len(loopbacks)} loopback devices, {len(mics)} mic devices.")
    print(f"Default loopback index: {def_loop}, Default mic index: {def_mic}")
    assert len(loopbacks) > 0, "At least one WASAPI loopback device should be found on Windows"

    print("\n--- [3] Testing Recording & Streaming MP3 Encoding ---")
    test_mp3 = os.path.join(out_dir, "test_audify_recording.mp3")
    if os.path.exists(test_mp3):
        os.remove(test_mp3)

    finished_data = {}

    def on_level(pl, pr, rl, rr):
        # Verify level callback doesn't error
        pass

    def on_finished(fp, dur, size):
        print(f"Record finished callback: path={fp}, duration={dur:.2f}s, size={size} bytes")
        finished_data["path"] = fp
        finished_data["duration"] = dur
        finished_data["size"] = size

    def on_err(err):
        print(f"Recorder error: {err}")

    recorder = AudioRecorder(
        on_level_update=on_level,
        on_error=on_err,
        on_finished=on_finished
    )

    print(f"Starting test recording to: {test_mp3}...")
    success = recorder.start_recording(
        output_filepath=test_mp3,
        loopback_device_index=def_loop,
        mic_device_index=None,
        mic_enabled=False,
        bitrate=320,
        sample_rate=48000
    )
    assert success, "Recording should start successfully"
    print("Recording active, waiting 2.5 seconds...")
    time.sleep(2.5)

    print("Stopping recording...")
    recorder.stop_recording()

    # Allow encoder thread final flush
    time.sleep(0.5)

    assert os.path.exists(test_mp3), "MP3 file must be created on disk"
    file_size = os.path.getsize(test_mp3)
    print(f"Created MP3 file size: {file_size} bytes")
    assert file_size > 1000, f"MP3 file size should be > 1KB, got {file_size}"

    # Verify ID3/MP3 sync frame header (0xFF 0xFB or 0xFF 0xF3 or similar)
    with open(test_mp3, "rb") as f:
        header = f.read(4)
        print(f"MP3 Header bytes: {header.hex()}")
        # First 11 bits are all 1s (0xFFE0 mask)
        is_mp3_sync = header[0] == 0xFF and (header[1] & 0xE0) == 0xE0
        print(f"Valid MP3 frame sync detected: {is_mp3_sync}")
        assert is_mp3_sync, "File must start with valid MP3 frame sync"

    # Clean up test file
    try:
        os.remove(test_mp3)
        print("Cleaned up test MP3 file.")
    except Exception:
        pass

    print("\n===========================================")
    print("  ALL AUDIO ENGINE TESTS PASSED (100%)!")
    print("===========================================\n")


if __name__ == "__main__":
    test_audio_pipeline()
