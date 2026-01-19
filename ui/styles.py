"""
ClipGenius - PyQt6 Styles
Beautiful dark theme with modern aesthetics
"""

# Color palette
COLORS = {
    "primary": "#6C5CE7",
    "primary_hover": "#5B4CD6", 
    "primary_light": "#A29BFE",
    "secondary": "#00CEC9",
    "secondary_hover": "#00B5B0",
    "accent": "#FD79A8",
    
    "background": "#0F0F1A",
    "surface": "#1A1A2E",
    "surface_light": "#252542",
    "surface_hover": "#2D2D4A",
    "card": "#16213E",
    
    "text": "#FFFFFF",
    "text_secondary": "#A0A0B0",
    "text_muted": "#6C6C80",
    
    "success": "#00B894",
    "warning": "#FDCB6E", 
    "error": "#E17055",
    "info": "#74B9FF",
    
    "border": "#2D3E5F",
    "border_light": "#3D4E6F",
    "divider": "#252542"
}


class Styles:
    """PyQt6 stylesheet definitions for ClipGenius."""
    
    @staticmethod
    def get_main_stylesheet() -> str:
        """Get the main application stylesheet."""
        return f"""
        /* ===== GLOBAL ===== */
        QWidget {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
            font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
            font-size: 14px;
        }}
        
        QMainWindow {{
            background-color: {COLORS['background']};
        }}
        
        /* ===== LABELS ===== */
        QLabel {{
            color: {COLORS['text']};
            background: transparent;
        }}
        
        QLabel[class="title"] {{
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text']};
        }}
        
        QLabel[class="subtitle"] {{
            font-size: 14px;
            color: {COLORS['text_secondary']};
        }}
        
        QLabel[class="section-header"] {{
            font-size: 16px;
            font-weight: 600;
            color: {COLORS['primary_light']};
            padding: 10px 0px;
        }}
        
        /* ===== BUTTONS ===== */
        QPushButton {{
            background-color: {COLORS['surface_light']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 500;
            min-height: 20px;
        }}
        
        QPushButton:hover {{
            background-color: {COLORS['surface_hover']};
            border-color: {COLORS['border_light']};
        }}
        
        QPushButton:pressed {{
            background-color: {COLORS['surface']};
        }}
        
        QPushButton:disabled {{
            background-color: {COLORS['surface']};
            color: {COLORS['text_muted']};
            border-color: {COLORS['surface_light']};
        }}
        
        QPushButton[class="primary"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
            border: none;
            color: white;
            font-weight: 600;
        }}
        
        QPushButton[class="primary"]:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary_hover']}, stop:1 {COLORS['secondary_hover']});
        }}
        
        QPushButton[class="success"] {{
            background-color: {COLORS['success']};
            border: none;
            color: white;
        }}
        
        QPushButton[class="danger"] {{
            background-color: {COLORS['error']};
            border: none;
            color: white;
        }}
        
        /* ===== LINE EDIT ===== */
        QLineEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px 15px;
            selection-background-color: {COLORS['primary']};
        }}
        
        QLineEdit:focus {{
            border-color: {COLORS['primary']};
        }}
        
        QLineEdit:disabled {{
            background-color: {COLORS['surface_light']};
            color: {COLORS['text_muted']};
        }}
        
        /* ===== TEXT EDIT ===== */
        QTextEdit, QPlainTextEdit {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px;
            selection-background-color: {COLORS['primary']};
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {COLORS['primary']};
        }}
        
        /* ===== COMBO BOX ===== */
        QComboBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px 15px;
            min-width: 150px;
        }}
        
        QComboBox:hover {{
            border-color: {COLORS['border_light']};
        }}
        
        QComboBox:focus {{
            border-color: {COLORS['primary']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {COLORS['text_secondary']};
            margin-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            selection-background-color: {COLORS['primary']};
            outline: none;
        }}
        
        /* ===== SPIN BOX ===== */
        QSpinBox, QDoubleSpinBox {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 8px 12px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {COLORS['primary']};
        }}
        
        QSpinBox::up-button, QSpinBox::down-button,
        QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
            background-color: {COLORS['surface_light']};
            border: none;
            width: 20px;
        }}
        
        /* ===== SLIDER ===== */
        QSlider::groove:horizontal {{
            background: {COLORS['surface_light']};
            height: 6px;
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
            width: 18px;
            height: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {COLORS['primary_light']};
        }}
        
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
            border-radius: 3px;
        }}
        
        /* ===== CHECK BOX ===== */
        QCheckBox {{
            color: {COLORS['text']};
            spacing: 10px;
        }}
        
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid {COLORS['border']};
            background-color: {COLORS['surface']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {COLORS['primary']};
            border-color: {COLORS['primary']};
        }}
        
        QCheckBox::indicator:hover {{
            border-color: {COLORS['primary']};
        }}
        
        /* ===== PROGRESS BAR ===== */
        QProgressBar {{
            background-color: {COLORS['surface_light']};
            border: none;
            border-radius: 8px;
            height: 16px;
            text-align: center;
            color: {COLORS['text']};
        }}
        
        QProgressBar::chunk {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
            border-radius: 8px;
        }}
        
        /* ===== SCROLL BAR ===== */
        QScrollBar:vertical {{
            background: {COLORS['surface']};
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background: {COLORS['surface_light']};
            border-radius: 5px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {COLORS['border']};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background: {COLORS['surface']};
            height: 10px;
            border-radius: 5px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {COLORS['surface_light']};
            border-radius: 5px;
            min-width: 30px;
        }}
        
        /* ===== GROUP BOX ===== */
        QGroupBox {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            margin-top: 20px;
            padding: 15px;
            font-weight: 600;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 10px;
            color: {COLORS['primary_light']};
        }}
        
        /* ===== TAB WIDGET ===== */
        QTabWidget::pane {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 10px;
        }}
        
        QTabBar::tab {{
            background-color: {COLORS['surface_light']};
            color: {COLORS['text_secondary']};
            border: none;
            padding: 10px 20px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {COLORS['surface']};
            color: {COLORS['text']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {COLORS['surface_hover']};
        }}
        
        /* ===== LIST WIDGET ===== */
        QListWidget {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 5px;
            outline: none;
        }}
        
        QListWidget::item {{
            background-color: transparent;
            color: {COLORS['text']};
            padding: 10px;
            border-radius: 6px;
            margin: 2px;
        }}
        
        QListWidget::item:selected {{
            background-color: {COLORS['primary']};
        }}
        
        QListWidget::item:hover:!selected {{
            background-color: {COLORS['surface_light']};
        }}
        
        /* ===== TABLE WIDGET ===== */
        QTableWidget {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            gridline-color: {COLORS['border']};
        }}
        
        QTableWidget::item {{
            padding: 8px;
            color: {COLORS['text']};
        }}
        
        QTableWidget::item:selected {{
            background-color: {COLORS['primary']};
        }}
        
        QHeaderView::section {{
            background-color: {COLORS['surface_light']};
            color: {COLORS['text']};
            padding: 10px;
            border: none;
            border-bottom: 1px solid {COLORS['border']};
            font-weight: 600;
        }}
        
        /* ===== TOOL TIP ===== */
        QToolTip {{
            background-color: {COLORS['surface_light']};
            color: {COLORS['text']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 8px;
        }}
        
        /* ===== MENU ===== */
        QMenu {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            padding: 5px;
        }}
        
        QMenu::item {{
            padding: 8px 30px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background-color: {COLORS['primary']};
        }}
        
        /* ===== FRAME (Card) ===== */
        QFrame[class="card"] {{
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 15px;
        }}
        
        /* ===== SPLITTER ===== */
        QSplitter::handle {{
            background-color: {COLORS['border']};
        }}
        
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        
        QSplitter::handle:vertical {{
            height: 2px;
        }}
        """
    
    @staticmethod
    def get_sidebar_style() -> str:
        """Get sidebar specific styles."""
        return f"""
        QFrame#sidebar {{
            background-color: {COLORS['surface']};
            border-right: 1px solid {COLORS['border']};
        }}
        
        QPushButton.nav-button {{
            background: transparent;
            border: none;
            border-radius: 8px;
            padding: 12px 15px;
            text-align: left;
            color: {COLORS['text_secondary']};
        }}
        
        QPushButton.nav-button:hover {{
            background-color: {COLORS['surface_light']};
            color: {COLORS['text']};
        }}
        
        QPushButton.nav-button:checked {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {COLORS['primary']}, stop:0.3 transparent);
            color: {COLORS['text']};
            border-left: 3px solid {COLORS['primary']};
        }}
        """
    
    @staticmethod
    def get_card_style() -> str:
        """Get card/panel styles."""
        return f"""
        .card {{
            background-color: {COLORS['card']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 20px;
        }}
        
        .card-header {{
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text']};
            margin-bottom: 15px;
        }}
        """
