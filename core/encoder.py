"""
Streaming MP3 Encoder for Audify.
Consumes PCM audio chunks from an in-memory queue and streams encoded
MP3 frames to disk using lameenc without accumulating memory.
"""

import os
import queue
import threading
import time
from typing import Callable, Optional


class Mp3EncoderThread(threading.Thread):
    """
    Dedicated worker thread for streaming MP3 encoding.
    Ensures that audio encoding and disk I/O do not block the UI or audio capture.
    """

    def __init__(
        self,
        audio_queue: queue.Queue,
        output_filepath: str,
        bitrate: int = 320,
        sample_rate: int = 48000,
        channels: int = 2,
        on_error: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[str, float, int], None]] = None
    ) -> None:
        super().__init__(name="AudifyMp3EncoderThread", daemon=True)
        self.audio_queue = audio_queue
        self.output_filepath = output_filepath
        self.bitrate = bitrate
        self.sample_rate = sample_rate
        self.channels = channels
        self.on_error = on_error
        self.on_finished = on_finished

        self._stop_event = threading.Event()
        self._total_pcm_bytes: int = 0
        self._total_mp3_bytes: int = 0
        self._start_time: float = 0.0

    def stop(self) -> None:
        """Signals the encoder to stop after draining the remaining queue."""
        self._stop_event.set()

    def run(self) -> None:
        # Lazy import of lameenc to ensure module is ready
        import lameenc

        file_handle = None
        self._start_time = time.time()
        try:
            # Ensure target directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.output_filepath)), exist_ok=True)
            file_handle = open(self.output_filepath, "wb")

            # Initialize LAME encoder
            encoder = lameenc.Encoder()
            encoder.set_bit_rate(self.bitrate)
            encoder.set_in_sample_rate(self.sample_rate)
            encoder.set_channels(self.channels)
            # High quality mode (2 = High, recommended for high-fidelity recording)
            encoder.set_quality(2)

            while not self._stop_event.is_set() or not self.audio_queue.empty():
                try:
                    # Timeout allows checking stop_event periodically
                    chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                if chunk is None:  # Sentinel value signaling stop
                    break

                if len(chunk) > 0:
                    self._total_pcm_bytes += len(chunk)
                    mp3_data = encoder.encode(chunk)
                    if mp3_data:
                        file_handle.write(mp3_data)
                        self._total_mp3_bytes += len(mp3_data)
                
                self.audio_queue.task_done()

            # Drain any remaining frames and finalize MP3 stream
            while not self.audio_queue.empty():
                try:
                    chunk = self.audio_queue.get_nowait()
                    if chunk and chunk is not None and len(chunk) > 0:
                        self._total_pcm_bytes += len(chunk)
                        mp3_data = encoder.encode(chunk)
                        if mp3_data:
                            file_handle.write(mp3_data)
                            self._total_mp3_bytes += len(mp3_data)
                    self.audio_queue.task_done()
                except queue.Empty:
                    break

            # Flush final MP3 frames
            final_mp3 = encoder.flush()
            if final_mp3:
                file_handle.write(final_mp3)
                self._total_mp3_bytes += len(final_mp3)

            file_handle.flush()
            os.fsync(file_handle.fileno())
            file_handle.close()
            file_handle = None

            # Calculate duration from PCM bytes (16-bit stereo = 4 bytes per sample)
            bytes_per_sample_frame = self.channels * 2
            total_samples = self._total_pcm_bytes / bytes_per_sample_frame
            duration_seconds = total_samples / self.sample_rate

            file_size = os.path.getsize(self.output_filepath) if os.path.exists(self.output_filepath) else self._total_mp3_bytes

            if self.on_finished:
                self.on_finished(self.output_filepath, duration_seconds, file_size)

        except Exception as e:
            error_msg = f"Encoder error: {e}"
            print(f"[Mp3EncoderThread] {error_msg}")
            if self.on_error:
                self.on_error(error_msg)
        finally:
            if file_handle and not file_handle.closed:
                try:
                    file_handle.close()
                except Exception:
                    pass
