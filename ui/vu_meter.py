"""
Dual-Channel Stereo VU Level Meter Widget for Audify.
Renders Left and Right channel peak and RMS levels with studio-grade
smooth decay ballistics and peak-hold indicators.
"""

import math
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPaintEvent,
    QPainter,
    QPen
)
from PySide6.QtWidgets import QWidget


class VuMeterWidget(QWidget):
    """Studio-grade stereo audio level meter with peak hold and smooth ballistics."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setMaximumHeight(54)

        # Current display levels [0.0, 1.0]
        self._current_l: float = 0.0
        self._current_r: float = 0.0

        # Peak hold levels and timers
        self._peak_l: float = 0.0
        self._peak_r: float = 0.0
        self._peak_decay_l: float = 0.0
        self._peak_decay_r: float = 0.0

        # Decay animation timer (running at ~60 FPS)
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60 FPS
        self._anim_timer.timeout.connect(self._process_decay)
        self._anim_timer.start()

    def update_levels(self, peak_l: float, peak_r: float, rms_l: float, rms_r: float) -> None:
        """
        Receives new audio levels from the recorder thread.
        Uses a combination of RMS and Peak with non-linear perception scaling.
        """
        # Convert to perceptual curve (dB-like curve: power of 0.5)
        target_l = math.sqrt(max(0.0, min(1.0, peak_l)))
        target_r = math.sqrt(max(0.0, min(1.0, peak_r)))

        # Instant attack
        if target_l > self._current_l:
            self._current_l = target_l
        if target_r > self._current_r:
            self._current_r = target_r

        # Peak hold update
        if target_l >= self._peak_l:
            self._peak_l = target_l
            self._peak_decay_l = 0.0
        if target_r >= self._peak_r:
            self._peak_r = target_r
            self._peak_decay_r = 0.0

        self.update()

    def reset_levels(self) -> None:
        """Resets all meters to zero."""
        self._current_l = 0.0
        self._current_r = 0.0
        self._peak_l = 0.0
        self._peak_r = 0.0
        self.update()

    def _process_decay(self) -> None:
        """Smoothly decays audio meters when silent."""
        decay_factor = 0.92
        changed = False

        if self._current_l > 0.001:
            self._current_l *= decay_factor
            changed = True
        else:
            self._current_l = 0.0

        if self._current_r > 0.001:
            self._current_r *= decay_factor
            changed = True
        else:
            self._current_r = 0.0

        # Peak hold decay (starts decaying after delay)
        self._peak_decay_l += 0.016
        if self._peak_decay_l > 0.5:
            self._peak_l = max(0.0, self._peak_l - 0.015)
            changed = True

        self._peak_decay_r += 0.016
        if self._peak_decay_r > 0.5:
            self._peak_r = max(0.0, self._peak_r - 0.015)
            changed = True

        if changed:
            self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        bar_height = 10
        label_width = 16
        bar_x = label_width + 8
        bar_width = width - bar_x - 12

        # Channel L
        y_l = 6
        self._draw_channel(painter, "L", y_l, bar_x, bar_width, bar_height, self._current_l, self._peak_l)

        # Channel R
        y_r = y_l + bar_height + 8
        self._draw_channel(painter, "R", y_r, bar_x, bar_width, bar_height, self._current_r, self._peak_r)

        # DB Scale ticks at the bottom
        y_ticks = y_r + bar_height + 4
        self._draw_db_scale(painter, bar_x, bar_width, y_ticks)

    def _draw_channel(
        self,
        painter: QPainter,
        label: str,
        y: int,
        bar_x: int,
        bar_width: int,
        bar_height: int,
        level: float,
        peak: float
    ) -> None:
        # Channel label
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QColor("#94A3B8"))
        painter.drawText(QRectF(0, y - 2, 16, bar_height + 4), Qt.AlignCenter, label)

        # Background track
        bg_rect = QRectF(bar_x, y, bar_width, bar_height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#141426"))
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Subtle border around track
        painter.setPen(QPen(QColor("#252542"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Active meter bar
        fill_width = max(0.0, min(float(bar_width), float(bar_width) * level))
        if fill_width > 1:
            meter_rect = QRectF(bar_x, y, fill_width, bar_height)
            gradient = QLinearGradient(bar_x, 0, bar_x + bar_width, 0)
            gradient.setColorAt(0.0, QColor("#06B6D4"))   # Neon Cyan
            gradient.setColorAt(0.65, QColor("#8B5CF6"))  # Electric Purple
            gradient.setColorAt(0.85, QColor("#F59E0B"))  # Warning Amber
            gradient.setColorAt(1.0, QColor("#EF4444"))   # Peak Crimson

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(meter_rect, 4, 4)

        # Peak hold tick
        if peak > 0.02:
            peak_x = bar_x + (bar_width * min(1.0, peak)) - 2
            painter.setPen(Qt.NoPen)
            if peak >= 0.95:
                painter.setBrush(QColor("#EF4444"))
            elif peak >= 0.8:
                painter.setBrush(QColor("#FBBF24"))
            else:
                painter.setBrush(QColor("#A78BFA"))
            painter.drawRoundedRect(QRectF(peak_x, y, 2.5, bar_height), 1, 1)

    def _draw_db_scale(self, painter: QPainter, bar_x: int, bar_width: int, y: int) -> None:
        painter.setFont(QFont("Segoe UI", 7))
        painter.setPen(QColor("#64748B"))

        # Decibel points: -40dB, -20dB, -12dB, -6dB, 0dB
        db_points = [
            (-40, 0.05),
            (-20, 0.25),
            (-12, 0.50),
            (-6, 0.75),
            (0, 1.00)
        ]
        for db, ratio in db_points:
            x_pos = bar_x + int(bar_width * ratio)
            text = f"{db}dB" if db != 0 else "0"
            painter.drawText(QRectF(x_pos - 15, y, 30, 12), Qt.AlignCenter, text)
