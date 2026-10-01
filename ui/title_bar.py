"""
Custom Frameless Title Bar for Audify.
Supports window dragging, minimize, close, and about dialog trigger.
"""

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget
)


class FramelessTitleBar(QWidget):
    """Custom title bar for frameless modern window."""

    about_clicked = Signal()
    minimize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent: QWidget, title: str = "Audify", icon_path: str = "") -> None:
        super().__init__(parent)
        self.setObjectName("titleBar")
        self._parent = parent
        self._drag_pos: QPoint = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        # App Icon
        self.icon_label = QLabel(self)
        if icon_path:
            pixmap = QPixmap(icon_path).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
        layout.addWidget(self.icon_label)

        # App Title
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # About button
        self.about_btn = QPushButton("ⓘ", self)
        self.about_btn.setObjectName("titleBarButton")
        self.about_btn.setToolTip("About Audify")
        self.about_btn.clicked.connect(self.about_clicked.emit)
        layout.addWidget(self.about_btn)

        # Minimize button
        self.min_btn = QPushButton("—", self)
        self.min_btn.setObjectName("titleBarButton")
        self.min_btn.setToolTip("Minimize")
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(self.min_btn)

        # Close button
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setObjectName("titleBarButton")
        self.close_btn.setProperty("isClose", True)
        self.close_btn.setStyleSheet("""
            QPushButton:hover {
                background-color: #EF4444;
                color: #FFFFFF;
            }
        """)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(self.close_btn)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_pos = QPoint()
        event.accept()
