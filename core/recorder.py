"""
Audio Capture and Mixing Engine for Audify.
Supports WASAPI Loopback (system audio), Microphone input, real-time resampling,
dynamic mixing, VU meter level calculations, and streaming MP3 encoding.
"""

import math
import os
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pyaudiowpatch as pyaudio

from core.encoder import Mp3EncoderThread


class AudioDeviceInfo:
    """Represents an audio input or loopback device."""

    def __init__(self, index: int, name: str, host_api: int, channels: int, default_sample_rate: float, is_loopback: bool):
        self.index = index
        self.name = name
        self.host_api = host_api
        self.channels = channels
        self.default_sample_rate = int(default_sample_rate)
        self.is_loopback = is_loopback

    def __repr__(self) -> str:
        return f"<AudioDevice [{self.index}] '{self.name}' Loopback={self.is_loopback} Rate={self.default_sample_rate}>"


class AudioRecorder:
    """
    High-performance audio recorder engine utilizing WASAPI loopback and microphone inputs.
    Synchronizes, resamples, mixes, and streams audio to MP3.
    """

    def __init__(
        self,
        on_level_update: Optional[Callable[[float, float, float, float], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[str, float, int], None]] = None
    ) -> None:
        self.on_level_update = on_level_update  # (peak_l, peak_r, rms_l, rms_r) in range [0.0, 1.0]
        self.on_error = on_error
        self.on_finished = on_finished

        self.p: Optional[pyaudio.PyAudio] = None
        self.loopback_stream: Optional[pyaudio.Stream] = None
        self.keeper_stream: Optional[pyaudio.Stream] = None
        self.mic_stream: Optional[pyaudio.Stream] = None

        self.encoder_thread: Optional[Mp3EncoderThread] = None
        self.audio_queue: queue.Queue = queue.Queue(maxsize=500)

        # Recording state
        self.is_recording: bool = False
        self.is_paused: bool = False
        self._pause_lock = threading.Lock()

        # Audio parameters
        self.target_sample_rate: int = 48000
        self.target_channels: int = 2
        self.bitrate: int = 320

        # Mixing buffers
        self.mic_enabled: bool = False
        self.system_volume: float = 1.0
        self.mic_volume: float = 1.0

        # Ring buffer for mic frames to synchronize with loopback clock
        self._mic_buffer_lock = threading.Lock()
        self._mic_buffer = np.zeros((0, 2), dtype=np.float32)

        # Level meter throttling
        self._last_level_emit_time = 0.0

    @staticmethod
    def get_devices() -> Tuple[List[AudioDeviceInfo], List[AudioDeviceInfo], Optional[int], Optional[int]]:
        """
        Enumerates all WASAPI Loopback devices (system audio) and WASAPI Input devices (mics).
        Returns: (loopback_devices, mic_devices, default_loopback_index, default_mic_index)
        """
        p = pyaudio.PyAudio()
        loopback_devices: List[AudioDeviceInfo] = []
        mic_devices: List[AudioDeviceInfo] = []
        default_loopback_idx: Optional[int] = None
        default_mic_idx: Optional[int] = None

        try:
            # Find WASAPI Host API
            wasapi_api_idx = None
            for i in range(p.get_host_api_count()):
                api_info = p.get_host_api_info_by_index(i)
                if api_info["type"] == pyaudio.paWASAPI:
                    wasapi_api_idx = i
                    break

            # Find default devices
            try:
                def_loop = p.get_default_wasapi_loopback()
                if def_loop:
                    default_loopback_idx = def_loop["index"]
            except Exception:
                pass

            try:
                def_in = p.get_default_wasapi_device()
                if def_in:
                    default_mic_idx = def_in["index"]
            except Exception:
                pass

            # Enumerate devices
            device_count = p.get_device_count()
            for idx in range(device_count):
                try:
                    info = p.get_device_info_by_index(idx)
                    # Filter for WASAPI devices if available
                    if wasapi_api_idx is not None and info["hostApi"] != wasapi_api_idx:
                        continue

                    is_loopback = bool(info.get("isLoopbackDevice", False))
                    channels = info.get("maxInputChannels", 0)
                    name = info.get("name", f"Device {idx}")
                    rate = info.get("defaultSampleRate", 48000.0)

                    if is_loopback:
                        loopback_devices.append(
                            AudioDeviceInfo(idx, name, info["hostApi"], channels, rate, True)
                        )
                    elif channels > 0:
                        mic_devices.append(
                            AudioDeviceInfo(idx, name, info["hostApi"], channels, rate, False)
                        )
                except Exception:
                    continue

        finally:
            p.terminate()

        # Fallbacks for defaults if not found
        if default_loopback_idx is None and loopback_devices:
            default_loopback_idx = loopback_devices[0].index
        if default_mic_idx is None and mic_devices:
            default_mic_idx = mic_devices[0].index

        return loopback_devices, mic_devices, default_loopback_idx, default_mic_idx

    def _find_matching_output_device(self, loopback_name: str) -> Optional[int]:
        """Finds the corresponding physical playback device for the loopback device."""
        if not self.p:
            return None
        # Loopback names usually end in ' [Loopback]'
        clean_name = loopback_name.replace(" [Loopback]", "").strip()
        count = self.p.get_device_count()
        # First try exact match with output channels > 0
        for i in range(count):
            try:
                info = self.p.get_device_info_by_index(i)
                if info.get("maxOutputChannels", 0) > 0 and info.get("name", "").strip() == clean_name:
                    return i
            except Exception:
                pass
        # Fallback to default output device
        try:
            def_out = self.p.get_default_output_device_info()
            return def_out["index"]
        except Exception:
            return None

    def start_recording(
        self,
        output_filepath: str,
        loopback_device_index: Optional[int],
        mic_device_index: Optional[int],
        mic_enabled: bool = False,
        bitrate: int = 320,
        sample_rate: int = 48000,
        system_volume: float = 1.0,
        mic_volume: float = 1.0
    ) -> bool:
        """Starts the audio capture and encoding pipeline."""
        if self.is_recording:
            return True

        self.target_sample_rate = sample_rate
        self.target_channels = 2
        self.bitrate = bitrate
        self.mic_enabled = mic_enabled
        self.system_volume = system_volume
        self.mic_volume = mic_volume

        self.audio_queue = queue.Queue(maxsize=1000)
        with self._mic_buffer_lock:
            self._mic_buffer = np.zeros((0, 2), dtype=np.float32)

        self.p = pyaudio.PyAudio()

        # 1. Resolve loopback device info
        try:
            if loopback_device_index is None:
                loopback_info = self.p.get_default_wasapi_loopback()
            else:
                loopback_info = self.p.get_device_info_by_index(loopback_device_index)
        except Exception as e:
            if self.on_error:
                self.on_error(f"Cannot initialize WASAPI Loopback device: {e}")
            self._cleanup()
            return False

        loop_rate = int(loopback_info.get("defaultSampleRate", 48000))
        loop_channels = loopback_info.get("maxInputChannels", 2)
        loop_idx = loopback_info["index"]

        # 2. Start silent keeper stream on the associated playback device
        # This keeps Windows WASAPI clock running even if nothing is playing
        try:
            playback_dev_idx = self._find_matching_output_device(loopback_info.get("name", ""))
            if playback_dev_idx is not None:
                out_info = self.p.get_device_info_by_index(playback_dev_idx)
                out_rate = int(out_info.get("defaultSampleRate", 48000))
                out_channels = min(2, out_info.get("maxOutputChannels", 2))

                def keeper_callback(in_data, frame_count, time_info, status):
                    # Inaudible zeroed PCM
                    silence = b"\x00" * (frame_count * out_channels * 2)
                    return (silence, pyaudio.paContinue)

                self.keeper_stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=out_channels,
                    rate=out_rate,
                    output=True,
                    output_device_index=playback_dev_idx,
                    stream_callback=keeper_callback,
                    frames_per_buffer=1024
                )
        except Exception as e:
            print(f"[AudioRecorder] Keeper stream warning: {e}. Loopback will continue.")

        # 3. Start microphone stream if enabled
        if self.mic_enabled and mic_device_index is not None:
            try:
                mic_info = self.p.get_device_info_by_index(mic_device_index)
                mic_rate = int(mic_info.get("defaultSampleRate", 44100))
                mic_channels = max(1, mic_info.get("maxInputChannels", 1))
                mic_idx = mic_info["index"]

                def mic_callback(in_data, frame_count, time_info, status):
                    self._on_mic_audio(in_data, frame_count, mic_channels, mic_rate)
                    return (None, pyaudio.paContinue)

                self.mic_stream = self.p.open(
                    format=pyaudio.paInt16,
                    channels=mic_channels,
                    rate=mic_rate,
                    input=True,
                    input_device_index=mic_idx,
                    stream_callback=mic_callback,
                    frames_per_buffer=1024
                )
            except Exception as e:
                print(f"[AudioRecorder] Failed to open microphone: {e}")
                self.mic_stream = None
                self.mic_enabled = False

        # 4. Start MP3 Encoder Worker Thread
        self.encoder_thread = Mp3EncoderThread(
            audio_queue=self.audio_queue,
            output_filepath=output_filepath,
            bitrate=self.bitrate,
            sample_rate=self.target_sample_rate,
            channels=self.target_channels,
            on_error=self._handle_encoder_error,
            on_finished=self._handle_encoder_finished
        )
        self.encoder_thread.start()

        # 5. Start WASAPI Loopback stream
        try:
            def loopback_callback(in_data, frame_count, time_info, status):
                self._on_loopback_audio(in_data, frame_count, loop_channels, loop_rate)
                return (None, pyaudio.paContinue)

            self.loopback_stream = self.p.open(
                format=pyaudio.paInt16,
                channels=loop_channels,
                rate=loop_rate,
                input=True,
                input_device_index=loop_idx,
                stream_callback=loopback_callback,
                frames_per_buffer=1024
            )
        except Exception as e:
            if self.on_error:
                self.on_error(f"Failed to start loopback capture: {e}")
            self.stop_recording()
            return False

        self.is_recording = True
        self.is_paused = False
        return True

    def pause_recording(self) -> None:
        """Pauses audio streaming to encoder."""
        with self._pause_lock:
            self.is_paused = True

    def resume_recording(self) -> None:
        """Resumes audio streaming to encoder."""
        with self._pause_lock:
            self.is_paused = False

    def stop_recording(self) -> None:
        """Stops recording, flushes encoder, and cleans up audio streams."""
        if not self.is_recording and not self.encoder_thread:
            return

        self.is_recording = False
        self.is_paused = False

        # Stop audio input streams first to stop new frames
        for s in [self.loopback_stream, self.mic_stream, self.keeper_stream]:
            if s:
                try:
                    s.stop_stream()
                    s.close()
                except Exception:
                    pass

        self.loopback_stream = None
        self.mic_stream = None
        self.keeper_stream = None

        # Signal encoder thread to finish and flush
        if self.encoder_thread:
            try:
                self.audio_queue.put(None)  # Sentinel
                self.encoder_thread.stop()
                self.encoder_thread.join(timeout=5.0)
            except Exception as e:
                print(f"[AudioRecorder] Error stopping encoder thread: {e}")
            self.encoder_thread = None

        self._cleanup()

    def _cleanup(self) -> None:
        if self.p:
            try:
                self.p.terminate()
            except Exception:
                pass
            self.p = None

    def _on_mic_audio(self, in_data: bytes, frame_count: int, channels: int, sample_rate: int) -> None:
        """Callback processing microphone raw audio."""
        if not self.is_recording or self.is_paused:
            return

        try:
            # Parse raw PCM int16 into float32 array [-1.0, 1.0]
            arr = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Convert channel format to stereo (N, 2)
            if channels == 1:
                stereo = np.column_stack((arr, arr))
            elif channels == 2:
                stereo = arr.reshape(-1, 2)
            else:
                # Downmix multi-channel to stereo
                reshaped = arr.reshape(-1, channels)
                stereo = reshaped[:, :2]

            # Resample to target sample rate if needed
            if sample_rate != self.target_sample_rate and len(stereo) > 1:
                stereo = self._resample_audio(stereo, sample_rate, self.target_sample_rate)

            # Append to thread-safe mic ring buffer
            with self._mic_buffer_lock:
                self._mic_buffer = np.vstack((self._mic_buffer, stereo))
                # Keep buffer capped to max 0.3 seconds to prevent drift/lag
                max_samples = int(self.target_sample_rate * 0.3)
                if len(self._mic_buffer) > max_samples:
                    self._mic_buffer = self._mic_buffer[-max_samples:]

        except Exception as e:
            print(f"[AudioRecorder] Mic processing exception: {e}")

    def _on_loopback_audio(self, in_data: bytes, frame_count: int, channels: int, sample_rate: int) -> None:
        """Callback processing loopback raw audio and synchronizing with mic."""
        if not self.is_recording or self.is_paused:
            # Emit zero levels when paused
            self._emit_levels(0.0, 0.0, 0.0, 0.0)
            return

        try:
            # 1. Parse loopback PCM into float32 [-1.0, 1.0]
            arr = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0

            if channels == 1:
                sys_stereo = np.column_stack((arr, arr))
            elif channels == 2:
                sys_stereo = arr.reshape(-1, 2)
            else:
                reshaped = arr.reshape(-1, channels)
                sys_stereo = reshaped[:, :2]

            # Resample loopback to target sample rate if needed
            if sample_rate != self.target_sample_rate and len(sys_stereo) > 1:
                sys_stereo = self._resample_audio(sys_stereo, sample_rate, self.target_sample_rate)

            n_samples = len(sys_stereo)

            # 2. Mixing with microphone if enabled
            if self.mic_enabled:
                with self._mic_buffer_lock:
                    available = len(self._mic_buffer)
                    if available >= n_samples:
                        mic_part = self._mic_buffer[:n_samples]
                        self._mic_buffer = self._mic_buffer[n_samples:]
                    elif available > 0:
                        # Pad shortage with zero silence
                        pad = np.zeros((n_samples - available, 2), dtype=np.float32)
                        mic_part = np.vstack((self._mic_buffer, pad))
                        self._mic_buffer = np.zeros((0, 2), dtype=np.float32)
                    else:
                        mic_part = np.zeros((n_samples, 2), dtype=np.float32)

                # Sum with volume gains
                mixed = (sys_stereo * self.system_volume) + (mic_part * self.mic_volume)
                # Soft limiting / clipping
                mixed = np.clip(mixed, -1.0, 1.0)
            else:
                mixed = np.clip(sys_stereo * self.system_volume, -1.0, 1.0)

            # 3. Calculate and emit VU Meter Levels
            self._calculate_and_emit_levels(mixed)

            # 4. Convert float32 [-1.0, 1.0] back to int16 PCM bytes
            pcm_int16 = (mixed * 32767.0).astype(np.int16).tobytes()

            # 5. Push to streaming MP3 encoder queue
            try:
                self.audio_queue.put_nowait(pcm_int16)
            except queue.Full:
                # Queue full protection: drop frame to prevent memory accumulation
                print("[AudioRecorder] Audio queue full, frame dropped.")

        except Exception as e:
            print(f"[AudioRecorder] Loopback processing exception: {e}")

    @staticmethod
    def _resample_audio(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
        """Fast high-fidelity linear resampling using numpy."""
        src_len = len(audio)
        dst_len = int(src_len * dst_rate / src_rate)
        if dst_len <= 0 or src_len <= 1:
            return audio

        x_old = np.linspace(0.0, 1.0, src_len, endpoint=True)
        x_new = np.linspace(0.0, 1.0, dst_len, endpoint=True)

        left = np.interp(x_new, x_old, audio[:, 0])
        right = np.interp(x_new, x_old, audio[:, 1])
        return np.column_stack((left, right)).astype(np.float32)

    def _calculate_and_emit_levels(self, stereo_audio: np.ndarray) -> None:
        """Calculates peak and RMS levels for L and R channels and emits updates at ~30 FPS."""
        now = time.time()
        if now - self._last_level_emit_time < 0.033:  # ~30 Hz throttle
            return
        self._last_level_emit_time = now

        if len(stereo_audio) == 0:
            self._emit_levels(0.0, 0.0, 0.0, 0.0)
            return

        left = stereo_audio[:, 0]
        right = stereo_audio[:, 1]

        peak_l = float(np.max(np.abs(left)))
        peak_r = float(np.max(np.abs(right)))

        rms_l = float(np.sqrt(np.mean(left ** 2)))
        rms_r = float(np.sqrt(np.mean(right ** 2)))

        self._emit_levels(peak_l, peak_r, rms_l, rms_r)

    def _emit_levels(self, peak_l: float, peak_r: float, rms_l: float, rms_r: float) -> None:
        if self.on_level_update:
            self.on_level_update(
                min(1.0, max(0.0, peak_l)),
                min(1.0, max(0.0, peak_r)),
                min(1.0, max(0.0, rms_l)),
                min(1.0, max(0.0, rms_r))
            )

    def _handle_encoder_error(self, err: str) -> None:
        if self.on_error:
            self.on_error(err)

    def _handle_encoder_finished(self, filepath: str, duration: float, filesize: int) -> None:
        if self.on_finished:
            self.on_finished(filepath, duration, filesize)
