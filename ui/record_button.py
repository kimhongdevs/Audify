"""
Large Circular Pulsing Record Button for Audify.
Features smooth glowing pulse waves during recording and intuitive hover/click animations.
"""

import math
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPen,
    QRadialGradient
)
from PySide6.QtWidgets import QWidget


class CircularRecordButton(QWidget):
    """
    A premium circular action button that pulses with expanding glowing rings
    when recording is active.
    """

    clicked = Signal()

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setFixedSize(88, 88)
        self.setCursor(Qt.PointingHandCursor)

        self._is_recording: bool = False
        self._is_paused: bool = False
        self._is_hovered: bool = False
        self._is_pressed: bool = False

        # Pulse animation state
        self._pulse_phase: float = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(20)  # 50 FPS
        self._pulse_timer.timeout.connect(self._update_pulse)

    def set_recording(self, recording: bool, paused: bool = False) -> None:
        """Updates recording state and controls pulse animation."""
        self._is_recording = recording
        self._is_paused = paused
        if recording:
            if not self._pulse_timer.isActive():
                self._pulse_timer.start()
        else:
            if self._pulse_timer.isActive():
                self._pulse_timer.stop()
            self._pulse_phase = 0.0
        self.update()

    def _update_pulse(self) -> None:
        """Advances pulse phase."""
        speed = 0.04 if not self._is_paused else 0.015
        self._pulse_phase = (self._pulse_phase + speed) % 1.0
        self.update()

    def enterEvent(self, event) -> None:
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._is_hovered = False
        self._is_pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            self.update()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._is_pressed:
            self._is_pressed = False
            self.update()
            self.clicked.emit()
            event.accept()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        center = QPointF(center_x, center_y)

        base_radius = 28.0
        if self._is_pressed:
            base_radius -= 2.0
        elif self._is_hovered and not self._is_recording:
            base_radius += 1.5

        # 1. Pulsing Outer Glow Aura when recording
        if self._is_recording:
            pulse = self._pulse_phase
            wave_radius = base_radius + 4.0 + (pulse * 14.0)
            alpha = int(max(0, 160 * (1.0 - pulse)))
            aura_color = QColor(245, 158, 11, alpha) if self._is_paused else QColor(239, 68, 68, alpha)

            painter.setPen(QPen(aura_color, 2.5))
            painter.setBrush(QColor(aura_color.red(), aura_color.green(), aura_color.blue(), int(alpha * 0.2)))
            painter.drawEllipse(center, wave_radius, wave_radius)

            # Secondary subtle inner glow
            inner_glow_radius = base_radius + 4.0
            painter.setPen(QPen(QColor(aura_color.red(), aura_color.green(), aura_color.blue(), 100), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, inner_glow_radius, inner_glow_radius)

        # 2. Outer Ring Background
        ring_radius = base_radius + 3.0
        painter.setPen(QPen(QColor("#252542"), 2))
        painter.setBrush(QColor("#16162B"))
        painter.drawEllipse(center, ring_radius, ring_radius)

        # 3. Main Center Circle with Gradient
        gradient = QRadialGradient(center, base_radius)
        if self._is_recording:
            if self._is_paused:
                gradient.setColorAt(0.0, QColor("#FBBF24"))
                gradient.setColorAt(0.8, QColor("#D97706"))
                gradient.setColorAt(1.0, QColor("#B45309"))
            else:
                gradient.setColorAt(0.0, QColor("#F87171"))
                gradient.setColorAt(0.8, QColor("#EF4444"))
                gradient.setColorAt(1.0, QColor("#DC2626"))
        else:
            # Idle ready state: Electric violet / crimson gradient
            if self._is_hovered:
                gradient.setColorAt(0.0, QColor("#F87171"))
                gradient.setColorAt(0.85, QColor("#EF4444"))
                gradient.setColorAt(1.0, QColor("#991B1B"))
            else:
                gradient.setColorAt(0.0, QColor("#EF4444"))
                gradient.setColorAt(0.85, QColor("#DC2626"))
                gradient.setColorAt(1.0, QColor("#7F1D1D"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center, base_radius, base_radius)

        # 4. Center Icon: Circle when idle, Square (Stop) when recording, Two Bars when paused
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))

        if self._is_recording:
            if self._is_paused:
                # Two pause bars
                bar_w, bar_h = 4.0, 14.0
                painter.drawRoundedRect(QRectF(center_x - 6.0, center_y - bar_h / 2, bar_w, bar_h), 2, 2)
                painter.drawRoundedRect(QRectF(center_x + 2.0, center_y - bar_h / 2, bar_w, bar_h), 2, 2)
            else:
                # Stop Square
                square_size = 14.0
                painter.drawRoundedRect(
                    QRectF(center_x - square_size / 2, center_y - square_size / 2, square_size, square_size),
                    3, 3
                )
        else:
            # Center bright white recording dot
            dot_radius = 8.0
            painter.drawEllipse(center, dot_radius, dot_radius)
