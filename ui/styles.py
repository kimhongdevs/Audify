"""
Modern Dark Theme QSS Stylesheet and Palette for Audify.
Features electric purple (#7C3AED), deep obsidian background (#0F0F1A),
sleek glassmorphic surfaces, and responsive micro-interactions.
"""

DARK_THEME_QSS = """
/* Base Application Window */
QMainWindow, QDialog, QWidget#centralWidget {
    background-color: #0F0F1A;
    color: #F3F4F6;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Frameless Window Frame & Title Bar */
#titleBar {
    background-color: #141424;
    border-bottom: 1px solid #25253E;
    min-height: 40px;
    max-height: 40px;
}

#titleLabel {
    font-weight: 700;
    font-size: 14px;
    color: #F8FAFC;
    letter-spacing: 0.5px;
}

#titleBarButton {
    background: transparent;
    border: none;
    border-radius: 4px;
    color: #94A3B8;
    font-size: 13px;
    font-weight: 600;
    min-width: 32px;
    min-height: 28px;
}

#titleBarButton:hover {
    background-color: #262642;
    color: #FFFFFF;
}

#titleBarCloseButton:hover {
    background-color: #DC2626;
    color: #FFFFFF;
}

/* Cards & Containers */
.QFrame#cardWidget, QWidget#cardWidget {
    background-color: #18182D;
    border: 1px solid #282845;
    border-radius: 12px;
    padding: 12px;
}

.QFrame#highlightCard, QWidget#highlightCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1C1C36, stop:1 #221E3E);
    border: 1px solid #3E2F6E;
    border-radius: 14px;
}

/* Section Header Labels */
QLabel#sectionHeader {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #818CF8;
    margin-bottom: 2px;
}

QLabel#statusChip {
    font-size: 11px;
    font-weight: 600;
    border-radius: 10px;
    padding: 3px 10px;
    background-color: #202038;
    color: #94A3B8;
    border: 1px solid #2F2F52;
}

QLabel#statusChipRecording {
    background-color: rgba(239, 68, 68, 0.15);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

QLabel#statusChipPaused {
    background-color: rgba(245, 158, 11, 0.15);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.4);
}

QLabel#statusChipReady {
    background-color: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

/* Timer Display */
QLabel#timerDisplay {
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 38px;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: 2px;
    margin: 4px 0px;
}

/* Buttons */
QPushButton {
    background-color: #252542;
    border: 1px solid #36365C;
    border-radius: 8px;
    color: #F1F5F9;
    font-weight: 600;
    font-size: 12px;
    padding: 7px 14px;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #313156;
    border-color: #4C4C7E;
}

QPushButton:pressed {
    background-color: #1D1D34;
}

QPushButton:disabled {
    background-color: #171728;
    border-color: #222238;
    color: #555570;
}

/* Accent Buttons */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #6366F1);
    border: 1px solid #8B5CF6;
    color: #FFFFFF;
    font-weight: 700;
}

QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #4F46E5);
    border-color: #A78BFA;
}

QPushButton#primaryButton:pressed {
    background: #6D28D9;
}

QPushButton#pauseButton {
    background-color: #2D2718;
    border: 1px solid #785A14;
    color: #FBBF24;
}

QPushButton#pauseButton:hover {
    background-color: #3D3522;
    border-color: #B4841E;
}

QPushButton#stopButton {
    background-color: #2E1B22;
    border: 1px solid #7A2837;
    color: #F87171;
}

QPushButton#stopButton:hover {
    background-color: #42232E;
    border-color: #B0344A;
}

/* ComboBoxes */
QComboBox {
    background-color: #151528;
    border: 1px solid #2B2B47;
    border-radius: 8px;
    color: #E2E8F0;
    padding: 6px 12px;
    min-height: 20px;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #4F46E5;
}

QComboBox:focus {
    border: 1px solid #7C3AED;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left-width: 0px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94A3B8;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #17172C;
    border: 1px solid #323254;
    border-radius: 8px;
    selection-background-color: #4338CA;
    selection-color: #FFFFFF;
    color: #E2E8F0;
    padding: 4px;
    outline: none;
}

/* Checkbox */
QCheckBox {
    spacing: 8px;
    color: #E2E8F0;
    font-size: 12px;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #3C3C60;
    background-color: #161628;
}

QCheckBox::indicator:hover {
    border-color: #6366F1;
}

QCheckBox::indicator:checked {
    background-color: #7C3AED;
    border-color: #8B5CF6;
    image: none;
}

/* Horizontal Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 5px;
    background: #252542;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366F1, stop:1 #8B5CF6);
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #7C3AED;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #EDE9FE;
    border-color: #A78BFA;
    transform: scale(1.1);
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #111120;
    width: 8px;
    margin: 0px 0px 0px 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #2A2A47;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #41416B;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

/* ToolTips */
QToolTip {
    background-color: #1F1F35;
    color: #F8FAFC;
    border: 1px solid #38385E;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Footer & Muted Text */
QLabel#footerText {
    color: #64748B;
    font-size: 11px;
    font-weight: 500;
}

QLabel#hotkeyBadge {
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 10px;
    color: #94A3B8;
    background-color: #18182D;
    border: 1px solid #2B2B48;
    border-radius: 4px;
    padding: 2px 6px;
}
"""
