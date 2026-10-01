"""
About Dialog for Audify.
Displays branding, credits to "Kimhong, Devs", version 1.0.0, and technical stack details.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget
)


class AboutDialog(QDialog):
    """Modern modal dialog showing application details and creator credits."""

    def __init__(self, icon_path: str = "", parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Audify")
        self.setFixedSize(420, 440)
        self.setStyleSheet("""
            QDialog {
                background-color: #0F0F1A;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 28, 24, 20)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        # App Logo Icon
        if icon_path:
            logo_label = QLabel(self)
            pixmap = QPixmap(icon_path).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)

        # App Title & Version
        title_label = QLabel("Audify", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 26px; font-weight: 800; color: #FFFFFF; letter-spacing: 1px;")
        layout.addWidget(title_label)

        version_badge = QLabel("Version 1.0.0  •  Windows Release", self)
        version_badge.setAlignment(Qt.AlignCenter)
        version_badge.setStyleSheet("""
            background-color: #1F1F38;
            color: #818CF8;
            font-size: 11px;
            font-weight: 600;
            border-radius: 12px;
            padding: 4px 12px;
            border: 1px solid #313158;
        """)
        layout.addWidget(version_badge)

        # Divider line
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #23233D; border: none; max-height: 1px;")
        layout.addWidget(line)

        # Creator Credits Card
        credit_card = QFrame(self)
        credit_card.setStyleSheet("""
            QFrame {
                background-color: #17172C;
                border: 1px solid #2B2B4A;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        credit_layout = QVBoxLayout(credit_card)
        credit_layout.setSpacing(4)
        credit_layout.setAlignment(Qt.AlignCenter)

        created_by_label = QLabel("Created by Kimhong, Devs", credit_card)
        created_by_label.setAlignment(Qt.AlignCenter)
        created_by_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #38BDF8;")
        credit_layout.addWidget(created_by_label)

        desc_label = QLabel(
            "High-fidelity system audio and microphone recorder\nwith real-time WASAPI loopback & streaming LAME MP3 encoding.",
            credit_card
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.4;")
        credit_layout.addWidget(desc_label)

        layout.addWidget(credit_card)

        # Tech stack chips
        stack_label = QLabel("PySide6  •  PyAudioWPatch  •  lameenc  •  numpy", self)
        stack_label.setAlignment(Qt.AlignCenter)
        stack_label.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 500;")
        layout.addWidget(stack_label)

        layout.addStretch()

        # Close button
        ok_btn = QPushButton("Close", self)
        ok_btn.setFixedWidth(100)
        ok_btn.setObjectName("primaryButton")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignCenter)
