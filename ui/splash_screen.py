
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QGuiApplication
from utils.constants import COLORS

class SplashScreen(QWidget):
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 350)
        
        # Center on screen
        self.center_on_screen()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Container frame
        self.container = QFrame()
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background']};
                border-radius: 20px;
                /* No border or shadow for minimal look */
            }}
        """)
        
        # Shadow removed for minimal look
        # shadow = QGraphicsDropShadowEffect(self)
        # self.container.setGraphicsEffect(shadow)
        
        layout.addWidget(self.container)
        
        # Content Layout
        content_layout = QVBoxLayout(self.container)
        content_layout.setContentsMargins(40, 40, 40, 20)
        content_layout.setSpacing(15)
        
        content_layout.addStretch()
        
        # Title
        title = QLabel("✂️ ClipGenius")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            color: {COLORS['primary']};
            font-size: 56px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)
        content_layout.addWidget(title)
        
        # Slogan
        slogan = QLabel("Transform long videos into viral short clips")
        slogan.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 18px;
            font-style: italic;
        """)
        content_layout.addWidget(slogan)
        
        content_layout.addStretch()
        
        # Footer
        footer = QLabel("Built with ❤️ by devxyasir")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Using text_secondary as text_muted is not in constants
        footer.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 10px;
            opacity: 0.7;
        """)
        content_layout.addWidget(footer)
        
        # Fade In Animation
        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(1000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.start()
        
        # Timer to close after 5 seconds
        QTimer.singleShot(5000, self.close_splash)

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def close_splash(self):
        # Fade out
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.finished.connect(self.on_fade_out_finished)
        self.anim.start()
        
    def on_fade_out_finished(self):
        self.finished.emit()
        self.close()
