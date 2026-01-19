from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QLabel, QStyle, QFrame
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTime

try:
    from utils.constants import COLORS
except ImportError:
    # Fallback/Debug
    COLORS = {
        'surface': '#16213E',
        'text': '#FFFFFF',
        'primary': '#6C5CE7',
        'primary_hover': '#5B4CD6',
        'secondary': '#00CEC9'
    }

class VideoPlayer(QWidget):
    """Reusable video player widget with controls."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_widget = QVideoWidget()  # Create video output first
        self.setup_player()
        self.setup_ui()
        
    def setup_player(self):
        """Initialize media player backend."""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Connect signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.mediaStatusChanged.connect(self.media_status_changed)
        self.media_player.errorOccurred.connect(self.handle_errors)
        
    def setup_ui(self):
        """Setup player UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video Surface
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: black; border-radius: 8px;")
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        video_layout.addWidget(self.video_widget)
        layout.addWidget(self.video_container, 1)
        
        # Controls Bar
        controls = QWidget()
        controls.setStyleSheet(f"background-color: {COLORS['surface']}; border-radius: 8px;")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # Play/Pause Button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.clicked.connect(self.toggle_play)
        self.play_btn.setFixedSize(32, 32)
        controls_layout.addWidget(self.play_btn)
        
        # Stop Button
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop_video)
        self.stop_btn.setFixedSize(32, 32)
        controls_layout.addWidget(self.stop_btn)
        
        # Current Time
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text']};")
        controls_layout.addWidget(self.time_label)
        
        # Seek Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        self.slider.sliderPressed.connect(self.media_player.pause)
        self.slider.sliderReleased.connect(self.media_player.play)
        controls_layout.addWidget(self.slider)
        
        # Total Duration
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet(f"color: {COLORS['text']};")
        controls_layout.addWidget(self.duration_label)
        
        layout.addWidget(controls)
        
    def load_video(self, path: str):
        """Load a video file."""
        self.media_player.setSource(QUrl.fromLocalFile(path))
        self.play_btn.setEnabled(True)
        # Auto play briefly to load metadata then pause? Or just pause.
        # self.media_player.play()
        # self.media_player.pause()
        
    def stop_video(self):
        """Stop video playback."""
        self.media_player.stop()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def toggle_play(self):
        """Toggle play/pause state."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            
    def position_changed(self, position):
        """Update slider and label as video plays."""
        self.slider.setValue(position)
        self.time_label.setText(self.format_time(position))
        
    def duration_changed(self, duration):
        """Update slider range and duration label."""
        self.slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))
        
    def set_position(self, position):
        """Seek to position."""
        self.media_player.setPosition(position)
        
    def media_status_changed(self, status):
        """Handle status changes (e.g. EndOfMedia)."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))

    def handle_errors(self):
        self.play_btn.setEnabled(False)
        self.time_label.setText("Error: " + self.media_player.errorString())

    def format_time(self, ms):
        """Format milliseconds to mm:ss."""
        seconds = (ms // 1000) % 60
        minutes = (ms // 60000)
        return f"{minutes:02}:{seconds:02}"
