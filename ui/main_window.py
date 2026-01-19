"""
ClipGenius - Main Window
PyQt6 main application window with modern dark theme
"""
import os
import sys
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QLineEdit, QTextEdit, QSpinBox,
    QSlider, QCheckBox, QProgressBar, QFileDialog, QMessageBox,
    QGroupBox, QScrollArea, QSplitter, QListWidget, QListWidgetItem,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QSizePolicy, QComboBox, QTabWidget, QTabBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPalette

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.styles import Styles, COLORS
from utils.config import config, ConfigManager
from utils.constants import APP_NAME, APP_VERSION, DEFAULT_MIN_CLIP_DURATION, DEFAULT_MAX_CLIP_DURATION


class WorkerThread(QThread):
    """Generic worker thread for background tasks with cancellation support."""
    progress = pyqtSignal(int, str)  # percent, status
    finished = pyqtSignal(object)  # result
    error = pyqtSignal(str)  # error message
    cancelled = pyqtSignal()  # cancelled signal
    log = pyqtSignal(str)  # log message signal
    
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self._cancel_requested = False
    
    def cancel(self):
        """Request cancellation of the task."""
        self._cancel_requested = True
    
    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancel_requested
    
    def run(self):
        try:
            # Pass progress callback and cancel check function
            self.kwargs['progress_callback'] = lambda p, s: self.progress.emit(int(p), s)
            self.kwargs['cancel_check'] = lambda: self._cancel_requested
            # Pass log callback if supported by target
            self.kwargs['log_callback'] = lambda msg: self.log.emit(str(msg))
            result = self.target(*self.args, **self.kwargs)
            
            if self._cancel_requested:
                self.cancelled.emit()
            else:
                self.finished.emit(result)
        except Exception as e:
            if self._cancel_requested:
                self.cancelled.emit()
            else:
                self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window for ClipGenius."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - AI Video Clip Generator")
        self.setMinimumSize(1200, 800)
        
        # Initialize state
        self.current_video_path = None
        self.current_project = None
        self.clips = []
        self.worker = None
        
        # Apply styles
        self.setStyleSheet(Styles.get_main_stylesheet())
        
        # Setup UI
        self._setup_ui()
        
        # Load last project if exists
        last_project = config.get("last_project")
        if last_project and os.path.exists(last_project):
            self._load_project(last_project)
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout with sidebar and content
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        content = self._create_content_area()
        main_layout.addWidget(content, 1)
    
    def _create_sidebar(self) -> QFrame:
        """Create the left sidebar navigation."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)
        
        # Logo/Title
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 20)
        
        title = QLabel(f"✂️ {APP_NAME}")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['primary_light']};")
        title_layout.addWidget(title)
        layout.addWidget(title_container)
        
        # New Project button
        btn_new = QPushButton("➕  New Project")
        btn_new.setProperty("class", "primary")
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self._on_new_project)
        layout.addWidget(btn_new)
        
        layout.addSpacing(20)
        
        # Recent projects
        recent_label = QLabel("📁 Recent Projects")
        recent_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(recent_label)
        
        self.projects_list = QListWidget()
        self.projects_list.setMaximumHeight(200)
        self.projects_list.itemClicked.connect(self._on_project_selected)
        layout.addWidget(self.projects_list)
        
        self._refresh_projects_list()
        
        layout.addStretch()
        
        # Settings section
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(divider)
        
        btn_about = QPushButton("ℹ️  About")
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.clicked.connect(self._show_about)
        layout.addWidget(btn_about)
        
        # Version
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"color: {COLORS['text_muted']};")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        return sidebar
    
    def _create_content_area(self) -> QWidget:
        """Create the main content area."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Main Tab Widget for organized UI
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {COLORS['background']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_secondary']};
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['surface_light']};
            }}
        """)
        
        # Tab 1: Video Input
        input_tab = QWidget()
        input_layout = QVBoxLayout(input_tab)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(20)
        video_section = self._create_video_input_section()
        input_layout.addWidget(video_section)
        input_layout.addStretch()
        self.tab_widget.addTab(input_tab, "📥 Video Input")
        
        # Tab 2: AI Analysis Settings
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(20)
        settings_section = self._create_settings_section()
        settings_layout.addWidget(settings_section)
        settings_layout.addStretch()
        self.tab_widget.addTab(settings_tab, "⚙️ Settings")
        
        # Tab 3: Clips Editor
        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        editor_layout.setContentsMargins(20, 20, 20, 20)
        editor_layout.setSpacing(20)
        clips_section = self._create_clips_section()
        editor_layout.addWidget(clips_section, 1)
        self.tab_widget.addTab(editor_tab, "✂️ Clips Editor")
        
        # Tab 4: Export & Logs
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        export_layout.setContentsMargins(20, 20, 20, 20)
        export_layout.setSpacing(20)
        log_section = self._create_log_section()
        export_layout.addWidget(log_section, 1)
        self.tab_widget.addTab(export_tab, "📤 Export & Logs")
        
        layout.addWidget(self.tab_widget, 1)
        
        # Bottom action bar
        action_bar = self._create_action_bar()
        layout.addWidget(action_bar)
        
        return content
    
    def _create_header(self) -> QWidget:
        """Create the header with project name."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.project_label = QLabel("No project selected")
        self.project_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        layout.addWidget(self.project_label)
        
        layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            background-color: {COLORS['success']};
            color: white;
            padding: 5px 15px;
            border-radius: 12px;
            font-weight: 600;
        """)
        layout.addWidget(self.status_label)
        
        return header
    
    def _create_video_input_section(self) -> QGroupBox:
        """Create video input section."""
        group = QGroupBox("📹 Video Source")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        url_label.setFixedWidth(100)
        url_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        url_layout.addWidget(self.url_input)
        
        self.btn_download = QPushButton("⬇️ Download")
        self.btn_download.clicked.connect(self._on_download_video)
        url_layout.addWidget(self.btn_download)
        
        layout.addLayout(url_layout)
        
        # OR divider
        divider_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFixedHeight(1)
        line1.setStyleSheet(f"background-color: {COLORS['border']};")
        divider_layout.addWidget(line1)
        
        or_label = QLabel("OR")
        or_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 0 15px;")
        divider_layout.addWidget(or_label)
        
        line2 = QFrame()
        line2.setFixedHeight(1)
        line2.setStyleSheet(f"background-color: {COLORS['border']};")
        divider_layout.addWidget(line2)
        
        layout.addLayout(divider_layout)
        
        # File input
        file_layout = QHBoxLayout()
        file_label = QLabel("Local File:")
        file_label.setFixedWidth(100)
        file_layout.addWidget(file_label)
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Select a local video file...")
        self.file_input.setReadOnly(True)
        file_layout.addWidget(self.file_input)
        
        self.btn_browse = QPushButton("📂 Browse")
        self.btn_browse.clicked.connect(self._on_browse_file)
        file_layout.addWidget(self.btn_browse)
        
        layout.addLayout(file_layout)
        
        # Calibration button (small link-style)
        cal_layout = QHBoxLayout()
        cal_layout.addStretch()
        self.btn_calibrate = QPushButton("🎯 Calibrate Uploader")
        self.btn_calibrate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_calibrate.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['primary']};
                border: none;
                text-align: right;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        self.btn_calibrate.clicked.connect(self._on_calibrate)
        cal_layout.addWidget(self.btn_calibrate)
        layout.addLayout(cal_layout)
        
        # Video info display
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.video_info_label)
        
        return group
    
    def _create_settings_section(self) -> QGroupBox:
        """Create settings section."""
        group = QGroupBox("⚙️ Clip Settings")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Duration settings
        duration_layout = QHBoxLayout()
        
        # Min duration
        min_layout = QVBoxLayout()
        min_label = QLabel("Min Duration (seconds)")
        min_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        min_layout.addWidget(min_label)
        
        self.min_duration_spin = QSpinBox()
        self.min_duration_spin.setRange(15, 300)
        self.min_duration_spin.setValue(config.get("min_clip_duration", DEFAULT_MIN_CLIP_DURATION))
        self.min_duration_spin.setSuffix(" sec")
        min_layout.addWidget(self.min_duration_spin)
        duration_layout.addLayout(min_layout)
        
        # Max duration
        max_layout = QVBoxLayout()
        max_label = QLabel("Max Duration (seconds)")
        max_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        max_layout.addWidget(max_label)
        
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setRange(30, 600)
        self.max_duration_spin.setValue(config.get("max_clip_duration", DEFAULT_MAX_CLIP_DURATION))
        self.max_duration_spin.setSuffix(" sec")
        max_layout.addWidget(self.max_duration_spin)
        duration_layout.addLayout(max_layout)
        
        duration_layout.addStretch()
        layout.addLayout(duration_layout)
        
        # Captions toggle
        self.captions_check = QCheckBox("📝 Add Captions (Auto-generated subtitles)")
        self.captions_check.setChecked(config.get("enable_captions", False))
        layout.addWidget(self.captions_check)
        
        # Background music section
        music_layout = QHBoxLayout()
        
        self.music_check = QCheckBox("🎵 Add Background Music")
        self.music_check.setChecked(config.get("enable_background_music", False))
        self.music_check.toggled.connect(self._on_music_toggle)
        music_layout.addWidget(self.music_check)
        
        music_layout.addStretch()
        
        music_label = QLabel("Volume:")
        music_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        music_layout.addWidget(music_label)
        
        self.music_volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.music_volume_slider.setRange(0, 100)
        self.music_volume_slider.setValue(config.get("background_music_volume", 30))
        self.music_volume_slider.setFixedWidth(150)
        self.music_volume_slider.setEnabled(self.music_check.isChecked())
        music_layout.addWidget(self.music_volume_slider)
        
        self.volume_label = QLabel(f"{self.music_volume_slider.value()}%")
        self.volume_label.setFixedWidth(40)
        self.music_volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        music_layout.addWidget(self.volume_label)
        
        layout.addLayout(music_layout)
        
        # Music file selection
        music_file_layout = QHBoxLayout()
        music_file_layout.addSpacing(30)
        
        self.music_file_input = QLineEdit()
        self.music_file_input.setPlaceholderText("Select background music file...")
        self.music_file_input.setEnabled(self.music_check.isChecked())
        music_file_layout.addWidget(self.music_file_input)
        
        self.btn_music_browse = QPushButton("🎵 Select")
        self.btn_music_browse.setEnabled(self.music_check.isChecked())
        self.btn_music_browse.clicked.connect(self._on_browse_music)
        music_file_layout.addWidget(self.btn_music_browse)
        
        layout.addLayout(music_file_layout)
        
        # Enhancement toggles
        enhance_layout = QHBoxLayout()
        
        self.video_enhance_check = QCheckBox("🎬 Enhance Video (color correction, sharpening)")
        self.video_enhance_check.setChecked(config.get("enable_video_enhancement", True))
        enhance_layout.addWidget(self.video_enhance_check)
        
        self.audio_enhance_check = QCheckBox("🔊 Enhance Audio (noise reduction, normalization)")
        self.audio_enhance_check.setChecked(config.get("enable_audio_enhancement", True))
        enhance_layout.addWidget(self.audio_enhance_check)
        
        layout.addLayout(enhance_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(separator)
        
        # Cookies file section (for user's own Gemini account)
        cookies_layout = QHBoxLayout()
        
        cookies_label = QLabel("🔐 Cookies File (your Gemini account):")
        cookies_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        cookies_layout.addWidget(cookies_label)
        
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("Select your cookies.txt file...")
        cookies_file = config.get("cookies_file", "")
        if cookies_file:
            self.cookies_input.setText(cookies_file)
        cookies_layout.addWidget(self.cookies_input)
        
        self.btn_cookies_browse = QPushButton("📂 Browse")
        self.btn_cookies_browse.clicked.connect(self._on_browse_cookies)
        cookies_layout.addWidget(self.btn_cookies_browse)
        
        layout.addLayout(cookies_layout)
        
        # Cookies help text
        cookies_help = QLabel("Export cookies from Chrome using 'Get cookies.txt LOCALLY' extension")
        cookies_help.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        layout.addWidget(cookies_help)
        
        return group
    
    def _create_clips_section(self) -> QGroupBox:
        """Create clips preview section."""
        group = QGroupBox("🎬 Generated Clips")
        layout = QVBoxLayout(group)
        
        # Video Preview Player removed as per request
        # from ui.video_player import VideoPlayer
        # self.video_player = VideoPlayer()
        # self.video_player.setMinimumHeight(300)
        # layout.addWidget(self.video_player)        
        # Clips table
        self.clips_table = QTableWidget()
        self.clips_table.setColumnCount(5)
        self.clips_table.setHorizontalHeaderLabels([
            "Title", "Start", "End", "Duration", "Viral Score"
        ])
        self.clips_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.clips_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.clips_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.clips_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.clips_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.clips_table.setMinimumHeight(200)
        self.clips_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # self.clips_table.itemSelectionChanged.connect(self._on_clip_selected)
        layout.addWidget(self.clips_table)
        
        # No clips message
        self.no_clips_label = QLabel("No clips yet. Click 'Analyze Video' to generate clips with AI.")
        self.no_clips_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_clips_label.setStyleSheet(f"color: {COLORS['text_muted']}; padding: 30px;")
        layout.addWidget(self.no_clips_label)
        
        return group
    
    def _create_log_section(self) -> QGroupBox:
        """Create log/console output section."""
        group = QGroupBox("📋 Activity Log")
        layout = QVBoxLayout(group)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        self.log_text.setPlaceholderText("Activity log will appear here...")
        layout.addWidget(self.log_text)
        
        # Clear button
        btn_clear_log = QPushButton("🗑️ Clear Log")
        btn_clear_log.setFixedWidth(120)
        btn_clear_log.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(btn_clear_log, alignment=Qt.AlignmentFlag.AlignRight)
        
        return group
    
    def _log(self, message: str):
        """Add a message to the log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _create_action_bar(self) -> QWidget:
        """Create bottom action bar."""
        bar = QWidget()
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border-radius: 12px;
                padding: 10px;
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(20)
        layout.addWidget(self.progress_bar, 1)
        
        # Progress label
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        # Analyze button
        self.btn_analyze = QPushButton("🤖 Analyze Video")
        self.btn_analyze.setProperty("class", "primary")
        self.btn_analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_analyze.setFixedWidth(180)
        self.btn_analyze.clicked.connect(self._on_analyze_video)
        layout.addWidget(self.btn_analyze)
        
        # Generate button
        self.btn_generate = QPushButton("✨ Generate Clips")
        self.btn_generate.setProperty("class", "success")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.setFixedWidth(180)
        self.btn_generate.clicked.connect(self._on_generate_clips)
        self.btn_generate.setEnabled(False)
        layout.addWidget(self.btn_generate)
        
        # Cancel button (hidden initially, shown during operations)
        self.btn_cancel = QPushButton("🛑 Cancel")
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error']};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C0392B;
            }}
        """)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setFixedWidth(120)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_cancel.setVisible(False)
        layout.addWidget(self.btn_cancel)
        
        # Retry button (hidden initially, shown on error)
        self.btn_retry = QPushButton("🔄 Retry")
        self.btn_retry.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: {COLORS['background']};
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #F39C12;
            }}
        """)
        self.btn_retry.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_retry.setFixedWidth(120)
        self.btn_retry.clicked.connect(self._on_retry)
        self.btn_retry.setVisible(False)
        layout.addWidget(self.btn_retry)
        
        # Store reference to current worker and last action
        self.current_worker = None
        self.last_action = None
        
        return bar
    
    # ==================== Event Handlers ====================
    
    def _refresh_projects_list(self):
        """Refresh the recent projects list."""
        self.projects_list.clear()
        
        try:
            from core.project_manager import ProjectManager
            pm = ProjectManager()
            projects = pm.list_projects()
            
            for project in projects[:10]:
                item = QListWidgetItem(f"📁 {project.get('name', 'Untitled')}")
                item.setData(Qt.ItemDataRole.UserRole, project.get('path'))
                self.projects_list.addItem(item)
        except Exception as e:
            print(f"Failed to load projects: {e}")
    
    def _on_new_project(self):
        """Create a new project."""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self, "New Project", "Enter project name:",
            QLineEdit.EchoMode.Normal, ""
        )
        
        if ok and name:
            try:
                from core.project_manager import ProjectManager
                pm = ProjectManager()
                project = pm.create_project(name)
                self.current_project = project
                self.project_label.setText(name)
                
                # Convert Path to string for JSON serialization
                project_path = str(pm.base_dir / project['folder_name'])
                config.set("last_project", project_path)
                config.add_recent_project(project_path)
                
                self._refresh_projects_list()
                self._update_status("Project created", "success")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project: {e}")
    
    def _on_project_selected(self, item):
        """Handle project selection from list."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self._load_project(path)
    
    def _load_project(self, path):
        """Load a project from path."""
        try:
            from core.project_manager import ProjectManager
            pm = ProjectManager()
            project = pm.load_project(path)
            self.current_project = project
            self.project_label.setText(project.get('name', 'Untitled'))
            
            # Load settings
            settings = project.get('settings', {})
            self.min_duration_spin.setValue(settings.get('min_duration', 60))
            self.max_duration_spin.setValue(settings.get('max_duration', 120))
            self.captions_check.setChecked(settings.get('enable_captions', False))
            self.music_check.setChecked(settings.get('enable_music', False))
            self.video_enhance_check.setChecked(settings.get('enhance_video', True))
            self.audio_enhance_check.setChecked(settings.get('enhance_audio', True))
            
            # Load video path if exists
            if project.get('source_video'):
                self.file_input.setText(project['source_video'])
                self.current_video_path = project['source_video']
            
            # Load clips
            self.clips = project.get('clips', [])
            self._update_clips_table()
            
            config.set("last_project", path)
            self._update_status("Project loaded", "success")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project: {e}")
    
    def _on_download_video(self):
        """Download video from URL."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
        
        if not self.current_project:
            QMessageBox.warning(self, "Error", "Please create or select a project first")
            return
        
        self._log(f"Starting download: {url[:50]}...")
        self._update_status("Downloading...", "warning")
        self.btn_download.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        def download(progress_callback=None):
            from core.downloader import VideoDownloader
            from core.project_manager import ProjectManager
            
            pm = ProjectManager()
            pm.current_project = self.current_project
            source_folder = pm.get_source_folder()
            
            downloader = VideoDownloader(source_folder)
            return downloader.download(url, progress_callback=progress_callback)
        
        self.worker = WorkerThread(download)
        self.worker.progress.connect(lambda p, s: (
            self.progress_bar.setValue(int(p)),
            self.progress_label.setText(s),
            self._log(s) if "complete" in s.lower() else None
        ))
        self.worker.finished.connect(self._on_download_complete)
        self.worker.error.connect(self._on_download_error)
        self.worker.start()
    
    def _on_download_complete(self, path):
        """Handle download completion."""
        self.current_video_path = path
        self.file_input.setText(path)
        self.btn_download.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._update_status("Download complete", "success")
        self._log(f"✅ Download complete: {os.path.basename(path)}")
        
        # Update project
        if self.current_project:
            self.current_project['source_video'] = path
    
    def _on_download_error(self, error):
        """Handle download error."""
        self.btn_download.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._update_status("Download failed", "error")
        self._log(f"❌ Download failed: {error}")
        QMessageBox.critical(self, "Error", f"Download failed: {error}")
    
    def _on_browse_file(self):
        """Browse for local video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video",
            "", "Video Files (*.mp4 *.mkv *.avi *.mov *.webm);;All Files (*)"
        )
        
        if file_path:
            self.file_input.setText(file_path)
            self.current_video_path = file_path
            
            # Update video info
            try:
                from core.video_processor import VideoProcessor
                vp = VideoProcessor()
                info = vp.get_video_info(file_path)
                duration_min = info['duration'] / 60
                self.video_info_label.setText(
                    f"Duration: {duration_min:.1f} min | "
                    f"Resolution: {info['width']}x{info['height']} | "
                    f"FPS: {info['fps']:.0f}"
                )
            except:
                pass
        
    def _on_calibrate(self):
        """Launch the calibration wizard dialog."""
        from ui.calibration_dialog import CalibrationDialog
        dialog = CalibrationDialog(self)
        dialog.exec()

    def _on_browse_music(self):
        """Browse for background music file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Background Music",
            "", "Audio Files (*.mp3 *.wav *.aac *.ogg *.m4a);;All Files (*)"
        )
        
        if file_path:
            self.music_file_input.setText(file_path)
    
    def _on_browse_cookies(self):
        """Browse for cookies.txt file for Gemini authentication."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Cookies File",
            "", "Cookies File (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.cookies_input.setText(file_path)
            # Save to config
            config.set("cookies_file", file_path)
            self._log(f"✅ Cookies file set: {Path(file_path).name}")
            self._update_status("Cookies file loaded - ready to use your Gemini account!", "success")
    
    def _on_music_toggle(self, checked):
        """Handle music checkbox toggle."""
        self.music_volume_slider.setEnabled(checked)
        self.music_file_input.setEnabled(checked)
        self.btn_music_browse.setEnabled(checked)
    
    def _on_cancel(self):
        """Cancel the current long-running operation."""
        if self.current_worker and self.current_worker.isRunning():
            self._log("🛑 Cancelling operation...")
            self.current_worker.cancel()
            self._update_status("Cancelling...", "warning")
            
            # Reset UI after a short delay
            from PyQt6.QtCore import QTimer
            def reset_ui():
                self.btn_cancel.setVisible(False)
                self.progress_bar.setVisible(False)
                self.btn_analyze.setEnabled(True)
                self.btn_generate.setEnabled(len(self.clips) > 0)
                self._update_status("Operation cancelled", "warning")
                self._log("✅ Operation cancelled by user")
            
            QTimer.singleShot(500, reset_ui)
        else:
            self.btn_cancel.setVisible(False)
            
    def _on_retry(self):
        """Retry the last failed operation."""
        self.btn_retry.setVisible(False)
        if self.last_action == 'analyze':
            self._log("🔄 Retrying analysis...")
            self._on_analyze_video()
        elif self.last_action == 'generate':
            self._log("🔄 Retrying clip generation...")
            self._on_generate_clips()
    
    def _on_analyze_video(self):
        """Analyze video using Gemini AI."""
        # Check if we have either a video path OR a YouTube URL
        youtube_url = self.url_input.text().strip() if hasattr(self, 'url_input') else None
        has_youtube_url = youtube_url and ('youtube.com' in youtube_url or 'youtu.be' in youtube_url)
        
        if not self.current_video_path and not has_youtube_url:
            QMessageBox.warning(self, "Error", "Please select a video file or enter a YouTube URL")
            return
        
        # Check if cookies.txt exists - first check config, then default location
        cookies_file_from_config = config.get("cookies_file", "")
        if cookies_file_from_config and Path(cookies_file_from_config).exists():
            cookies_path = Path(cookies_file_from_config)
        else:
            cookies_path = Path(__file__).parent.parent / "cookies.txt"
        
        if not cookies_path.exists():
            QMessageBox.warning(
                self, "Cookies Required",
                "Please set your cookies.txt file in the Settings section above.\n\n"
                "1. Install 'Get cookies.txt LOCALLY' Chrome extension\n"
                "2. Go to gemini.google.com and sign in\n"
                "3. Export cookies using the extension\n"
                "4. Use the 'Browse' button in Settings to select the file"
            )
            return
        
        self._log("Starting Gemini analysis...")
        self._update_status("Analyzing...", "warning")
        self.btn_analyze.setEnabled(False)
        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_cancel.setVisible(True)  # Show cancel button
        self.btn_retry.setVisible(False)  # Hide retry button
        self.last_action = 'analyze'      # Track action
        self.progress_label.setText("Preparing...")
        
        def analyze(progress_callback=None, cancel_check=None):
            from core.gemini_automation import GeminiAutomation
            from core.project_manager import ProjectManager
            
            # Use cookies-based authentication
            gemini = GeminiAutomation(
                cookies_file=str(cookies_path)
            )
            
            # Get project folder for saving clips.json
            output_folder = None
            if self.current_project:
                pm = ProjectManager()
                pm.current_project = self.current_project
                output_folder = pm.get_source_folder()
            
            # Check if we have a YouTube URL (and no local video or prefer URL)
            youtube_url = self.url_input.text().strip() if hasattr(self, 'url_input') else None
            
            # If URL is provided and looks like a YouTube link, use it directly
            if youtube_url and ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
                return gemini.analyze_video(
                    video_path=self.current_video_path,
                    youtube_url=youtube_url,
                    output_folder=output_folder,
                    progress_callback=progress_callback,
                    cancel_check=cancel_check
                )
            else:
                return gemini.analyze_video(
                    video_path=self.current_video_path,
                    output_folder=output_folder,
                    progress_callback=progress_callback,
                    cancel_check=cancel_check
                )
        
        self.worker = WorkerThread(analyze)
        self.current_worker = self.worker  # Store for cancellation
        self.worker.progress.connect(lambda p, s: (
            self.progress_bar.setValue(int(p)),
            self.progress_label.setText(s),
            self._log(s)
        ))
        self.worker.finished.connect(self._on_analysis_complete)
        self.worker.error.connect(self._on_analysis_error)
        self.worker.cancelled.connect(lambda: self._log("Operation cancelled"))
        self.worker.start()
    
    def _on_analysis_complete(self, clips):
        """Handle analysis completion."""
        self.clips = clips
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.progress_label.setText("")
        
        if clips:
            self._update_clips_table()
            self.btn_generate.setEnabled(True)
            self._update_status(f"Found {len(clips)} clips!", "success")
            self._log(f"✅ Analysis complete! Found {len(clips)} clips")
        else:
            self._update_status("No clips found", "warning")
            self._log("⚠️ No clips found in response")
            QMessageBox.information(
                self, "Analysis Complete",
                "No suitable clips were found. Try adjusting the duration settings."
            )
    
    def _on_analysis_error(self, error):
        """Handle analysis error."""
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.progress_label.setText("")
        self.btn_retry.setVisible(True)  # Show retry button
        self._update_status("Analysis failed", "error")
        self._log(f"❌ Error: {error}")
        QMessageBox.critical(self, "Error", f"Analysis failed: {error}")
    
    def _update_clips_table(self):
        """Update the clips table with current clips."""
        self.clips_table.setRowCount(len(self.clips))
        self.no_clips_label.setVisible(len(self.clips) == 0)
        
        for i, clip in enumerate(self.clips):
            self.clips_table.setItem(i, 0, QTableWidgetItem(clip.get('title', 'Untitled')))
            self.clips_table.setItem(i, 1, QTableWidgetItem(clip.get('start_time', '0:00')))
            self.clips_table.setItem(i, 2, QTableWidgetItem(clip.get('end_time', '0:00')))
            
            # Calculate duration
            try:
                from core.video_processor import VideoProcessor
                vp = VideoProcessor()
                start = vp.time_to_seconds(clip.get('start_time', '0:00'))
                end = vp.time_to_seconds(clip.get('end_time', '0:00'))
                duration = f"{int(end - start)}s"
            except:
                duration = "N/A"
            
            self.clips_table.setItem(i, 3, QTableWidgetItem(duration))
            
            score = clip.get('viral_score', 5)
            score_item = QTableWidgetItem(f"{'⭐' * min(score, 5)}")
            self.clips_table.setItem(i, 4, score_item)
    
    # Video preview logic removed


    def _on_generate_clips(self):
        """Generate video clips."""
        if not self.clips:
            QMessageBox.warning(self, "Error", "No clips to generate. Analyze video first.")
            return
        
        self._update_status("Generating clips...", "warning")
        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_cancel.setVisible(True)
        self.btn_retry.setVisible(False)
        self.last_action = 'generate'
        self.progress_label.setText("Processing...")
        
        def generate(progress_callback=None, cancel_check=None, log_callback=None):
            from core.video_processor import VideoProcessor
            from core.audio_processor import AudioProcessor
            from core.caption_generator import CaptionGenerator
            from core.project_manager import ProjectManager
            
            pm = ProjectManager()
            pm.current_project = self.current_project
            exports_folder = pm.get_exports_folder()
            
            # User request: Output to folder named after original video
            video_name = Path(self.current_video_path).stem
            sanitized_folder_name = "".join([c for c in video_name if c.isalnum() or c in "._- "]).strip()
            # If name is empty (e.g. all special chars), fallback
            if not sanitized_folder_name:
                sanitized_folder_name = f"video_{int(time.time())}"
                
            project_exports = os.path.join(exports_folder, sanitized_folder_name)
            os.makedirs(project_exports, exist_ok=True)
            
            vp = VideoProcessor()
            if log_callback:
                vp.log_callback = log_callback
            ap = AudioProcessor()
            
            # Process clips
            output_paths = vp.process_clips_batch(
                self.current_video_path,
                self.clips,
                project_exports,  # Use subfolder
                vertical=True,
                enhance=self.video_enhance_check.isChecked(),
                max_workers=4,
                cancel_check=cancel_check
            )
            
            if cancel_check and cancel_check():
                return []
            
            # Post-processing
            final_paths = []
            for i, output_path in enumerate(output_paths):
                if cancel_check and cancel_check():
                    return []

                current_path = output_path
                
                # Audio enhancement
                if self.audio_enhance_check.isChecked():
                    enhanced_path = output_path.replace('.mp4', '_audio_enhanced.mp4')
                    current_path = ap.enhance_audio(current_path, enhanced_path)
                
                # Add background music
                if self.music_check.isChecked() and self.music_file_input.text():
                    music_path = output_path.replace('.mp4', '_with_music.mp4')
                    current_path = ap.add_background_music(
                        current_path,
                        self.music_file_input.text(),
                        music_path,
                        music_volume=self.music_volume_slider.value()
                    )
                
                # Add captions
                if self.captions_check.isChecked():
                    try:
                        cg = CaptionGenerator()
                        caption_path = output_path.replace('.mp4', '_captioned.mp4')
                        current_path = cg.auto_caption_video(current_path, caption_path)
                    except Exception as e:
                        print(f"Caption generation failed: {e}")
                
                final_paths.append(current_path)
            
            return final_paths
        
        self.worker = WorkerThread(generate)
        self.current_worker = self.worker
        self.worker.progress.connect(lambda p, s: (
            self.progress_bar.setValue(int(p)),
            self.progress_label.setText(s)
        ))
        self.worker.finished.connect(self._on_generation_complete)
        self.worker.error.connect(self._on_generation_error)
        self.worker.cancelled.connect(lambda: self._log("Generation cancelled"))
        self.worker.log.connect(lambda msg: self._log(msg))
        self.worker.start()
    
    def _on_generation_complete(self, paths):
        """Handle clip generation completion."""
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.progress_label.setText("")
        self._update_status(f"Generated {len(paths)} clips!", "success")
        
        # Get exports folder
        try:
            from core.project_manager import ProjectManager
            pm = ProjectManager()
            pm.current_project = self.current_project
            exports_folder = pm.get_exports_folder()
            
            result = QMessageBox.information(
                self, "Generation Complete",
                f"Successfully generated {len(paths)} clips!\n\n"
                f"Saved to: {exports_folder}",
                QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok
            )
            
            if result == QMessageBox.StandardButton.Open:
                os.startfile(exports_folder)
        except:
            pass
    
    def _on_generation_error(self, error):
        """Handle generation error."""
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_retry.setVisible(True)
        self.progress_label.setText("")
        self._update_status("Generation failed", "error")
        self._log(f"❌ Error: {error}")
        QMessageBox.critical(self, "Error", f"Generation failed: {error}")
    
    def _show_about(self):
        """Show About dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame
        
        dialog = QDialog(self)
        dialog.setWindowTitle("About ClipGenius")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QFrame.h_line {{
                background-color: {COLORS['border']};
                max-height: 1px;
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("👤 Creator")
        header.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        name = QLabel("Muhammad Yasir\nAI & Automation Engineer")
        name.setStyleSheet("font-size: 16px; font-weight: 600;")
        layout.addWidget(name)
        
        # Divider
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setProperty("class", "h_line")
        layout.addWidget(line1)
        
        # About
        about_header = QLabel("🧠 About")
        about_header.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 14px;")
        layout.addWidget(about_header)
        
        about_text = QLabel("Building reliable automation, AI, and video-processing tools with a focus on performance, scalability, and real-world usability.")
        about_text.setWordWrap(True)
        about_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(about_text)
        
        # Divider
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setProperty("class", "h_line")
        layout.addWidget(line2)
        
        # Expertise
        exp_header = QLabel("🛠 Expertise")
        exp_header.setStyleSheet(f"color: {COLORS['primary']}; font-weight: bold; font-size: 14px;")
        layout.addWidget(exp_header)
        
        expertise = QLabel("• AI Automation\n• Python Development\n• Web Scraping & Data Extraction\n• Machine Learning\n• Data Science & Analytics\n• AI Agents & Workflow Systems")
        expertise.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(expertise)

        # Links (Buttons)
        links_layout = QHBoxLayout()
        links_layout.setSpacing(10)
        
        def open_url(url):
            import webbrowser
            webbrowser.open(url)
            
        # GitHub
        btn_github = QPushButton("GitHub")
        btn_github.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_github.clicked.connect(lambda: open_url("https://github.com/devxyasir"))
        links_layout.addWidget(btn_github)
        
        # LinkedIn
        btn_linkedin = QPushButton("LinkedIn")
        btn_linkedin.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_linkedin.clicked.connect(lambda: open_url("https://linkedin.com/in/devxyasir"))
        links_layout.addWidget(btn_linkedin)
            
        # Facebook
        btn_fb = QPushButton("Facebook")
        btn_fb.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_fb.clicked.connect(lambda: open_url("https://facebook.com/devxyasir"))
        links_layout.addWidget(btn_fb)
        
        # WhatsApp
        btn_wa = QPushButton("WhatsApp")
        btn_wa.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_wa.clicked.connect(lambda: open_url("https://wa.me/+923156808967"))
        links_layout.addWidget(btn_wa)
        
        # Email
        btn_email = QPushButton("Email")
        btn_email.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_email.clicked.connect(lambda: open_url("mailto:neverseenbefore942@gmail.com"))
        links_layout.addWidget(btn_email)
        
        links_layout.addStretch()
        layout.addLayout(links_layout)
        
        # Footer
        footer = QLabel(f"Built and maintained by Muhammad Yasir\nVersion: v{APP_VERSION}")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; margin-top: 20px;")
        layout.addWidget(footer)
        
        dialog.exec()
        

    
    def _detect_chrome_profiles(self, line_edit):
        """Detect Chrome profiles and let user select."""
        profiles = config.detect_chrome_profiles()
        
        if not profiles:
            QMessageBox.warning(self, "No Profiles", "No Chrome profiles found.")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        profile_names = [os.path.basename(p) + f" ({p})" for p in profiles]
        selected, ok = QInputDialog.getItem(
            self, "Select Profile",
            "Available Chrome profiles:",
            profile_names, 0, False
        )
        
        if ok and selected:
            # Extract path from selection
            idx = profile_names.index(selected)
            line_edit.setText(profiles[idx])
    
    def _save_settings(self, dialog, chrome_path):
        """Save settings and close dialog."""
        config.set("chrome_profile_path", chrome_path)
        config.set("min_clip_duration", self.min_duration_spin.value())
        config.set("max_clip_duration", self.max_duration_spin.value())
        config.set("enable_captions", self.captions_check.isChecked())
        config.set("enable_background_music", self.music_check.isChecked())
        config.set("background_music_volume", self.music_volume_slider.value())
        config.set("enable_video_enhancement", self.video_enhance_check.isChecked())
        config.set("enable_audio_enhancement", self.audio_enhance_check.isChecked())
        
        dialog.accept()
        self._update_status("Settings saved", "success")
    
    def _update_status(self, text, status_type="info"):
        """Update the status label."""
        colors = {
            "success": COLORS['success'],
            "warning": COLORS['warning'],
            "error": COLORS['error'],
            "info": COLORS['primary']
        }
        
        color = colors.get(status_type, COLORS['primary'])
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 5px 15px;
            border-radius: 12px;
            font-weight: 600;
        """)


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
