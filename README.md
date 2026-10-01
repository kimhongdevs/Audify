# Audify 🎵
> High-fidelity Windows desktop audio recorder for system audio and microphone with real-time streaming MP3 encoding.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6.svg)
![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg)
![Encoding](https://img.shields.io/badge/MP3-LAME%20CBR%20320kbps-brightgreen.svg)

---

## Overview

**Audify** is a Windows desktop application that captures whatever is playing on your computer (via WASAPI loopback) and optionally records and mixes your microphone into a single studio-grade MP3 file.

Built with a custom dark theme with electric purple accents, Audify features a frameless window with a custom draggable title bar, real-time dual-channel stereo VU meters, a circular pulsing record button, system tray integration with global hotkey support, and streaming MP3 encoding that keeps memory usage low regardless of recording length.

**Author & Credits:** Created by **Kimhong, Devs**  
**Version:** 1.0.0

---

## Key Features

1. **System Audio Capture**: Full-quality WASAPI loopback recording without requiring stereo mix or virtual cables.
2. **Microphone Mixing**: Optional microphone capture with real-time sample rate resampling and channel adaptation via `numpy`.
3. **Continuous Clock Keeper**: Built-in silent keeper stream ensures Windows WASAPI loopback never pauses or desyncs during quiet moments or gaps between songs.
4. **Streaming MP3 Encoding**: Streams directly to disk via `lameenc` (LAME CBR 128/192/256/320 kbps, 44.1/48.0 kHz).
5. **Dual-Channel VU Meter**: Real-time Left and Right peak/RMS level visualizer with peak-hold ballistics.
6. **Circular Pulsing Record Button**: Animated glowing wave pulses while recording with instant hover and click feedback.
7. **Global Hotkey**: Press `Ctrl+Shift+R` anytime to start or stop recording, even when minimized or running in the tray.
8. **System Tray Integration**: Minimize-to-tray with tray context menu (Open, Start/Stop, Quit) and desktop notifications.
9. **Recordings History**: Built-in history viewer with instant playback, "Show in folder", and deletion.
10. **State Persistence**: Remembers your device selections, bitrate, sample rate, and output directory in `%APPDATA%/Audify/settings.json`.

---

## Project Structure

```
Audify/
├── main.py                  # Application entry point & Qt event loop
├── generate_assets.py       # Programmatic generator for icon.ico and icon.png
├── build_exe.py             # Packaging script invoking PyInstaller
├── Audify.spec              # PyInstaller specification file
├── version_info.txt         # Windows PE executable metadata (Company: Kimhong, Devs)
├── requirements.txt         # Exact dependencies specification
├── README.md                # Documentation & usage guide
├── assets/
│   ├── icon.ico             # Multi-size Windows application icon (16x16 to 256x256)
│   └── icon.png             # 512x512 high-resolution icon
├── core/
│   ├── __init__.py
│   ├── encoder.py           # Worker thread: consumes PCM queue, streaming LAME MP3 encoding
│   ├── hotkeys.py           # pynput system-wide hotkey listener (Ctrl+Shift+R)
│   ├── recorder.py          # WASAPI loopback & mic capture, numpy resampler & mixer, VU levels
│   └── settings.py          # Config & history manager (%APPDATA%/Audify/settings.json)
├── ui/
│   ├── __init__.py
│   ├── about_dialog.py      # About modal dialog crediting Kimhong, Devs (v1.0.0)
│   ├── history_widget.py    # Recording history dialog with play, reveal, delete
│   ├── main_window.py       # Main frameless UI with devices, timer, and controls
│   ├── record_button.py     # Circular record button with glowing pulse animation
│   ├── styles.py            # Modern dark theme QSS stylesheet
│   ├── title_bar.py         # Custom frameless title bar with dragging and control buttons
│   └── vu_meter.py          # Studio-grade stereo VU level meter widget
└── tests/
    └── test_recorder.py     # Automated integration test for audio pipeline
```

---

## Installation & Setup

### Requirements
- **Windows 10 or 11** (64-bit)
- **Python 3.11+** installed and added to `PATH`

### 1. Create a Virtual Environment (Recommended)
Open PowerShell or Command Prompt in the project folder:
```powershell
# Clone the repository
git clone https://github.com/yourusername/Audify.git
cd Audify

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\Activate.ps1
# Or in Command Prompt: .\venv\Scripts\activate.bat
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Generate App Icons (Optional / Automatic)
The application will automatically generate `assets/icon.ico` and `assets/icon.png` if they are not found. You can also run the generator manually:
```powershell
python generate_assets.py
```

### 4. Run Audify
```powershell
python main.py
```

---

## Using Your Own Custom Icon

If you prefer to supply your own custom `.ico` file:
1. Place your icon file at `assets/icon.ico` (ensure it contains standard sizes: 16x16, 32x32, 48x48, 256x256).
2. Also place a PNG version at `assets/icon.png` (512x512 recommended for the About dialog and title bar).
3. Restart or rebuild the application.

---

## Packaging into a Standalone `.exe`

You can build a single windowed `.exe` with embedded icon, version info, and metadata crediting **Kimhong, Devs**.

### Method 1: Using the Build Script
```powershell
python build_exe.py
```

### Method 2: Direct PyInstaller Command
```powershell
pyinstaller --clean Audify.spec
```

The resulting standalone executable will be located at:
```
dist/Audify.exe
```

When you inspect `dist/Audify.exe` > **Properties** > **Details**, you will see:
- **File description**: Audify - High-Fidelity Audio Recorder
- **Company**: Kimhong, Devs
- **Product version**: 1.0.0.0
- **Copyright**: Copyright © 2026 Kimhong, Devs. All rights reserved.

---

## Testing & Quality Assurance

Run the automated integration test to verify loopback capture, MP3 encoding, and device enumeration:
```powershell
python tests/test_recorder.py
```

---

## Future Improvements & Roadmap

1. **Audio Trimming & Splitter**: Add an in-app waveform trimmer to cut the beginning or ending of recordings before saving.
2. **Noise Suppression**: Integrate lightweight RNNoise or WebRTC VAD on the microphone channel to eliminate background noise.
3. **Lossless FLAC / WAV Export**: Option to save directly to 24-bit 96kHz lossless FLAC or uncompressed WAV.
4. **Audio Ducking**: Automatically lower system audio volume when the user speaks into the microphone (ideal for commentary and podcasts).
5. **Scheduled / Timed Recording**: Set a timer or calendar trigger to record webcasts, radio shows, or streams automatically.
