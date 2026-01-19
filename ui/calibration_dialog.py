"""
ClipGenius - Calibration Dialog
UI for guiding users through the button calibration process
"""
import json
import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QProgressBar, QMessageBox, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

try:
    from pynput import mouse
    import winsound
    import pyautogui
except ImportError:
    pass

from utils.constants import COLORS

class ClickListenerThread(QThread):
    """Thread to listen for a single mouse click."""
    clicked = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self.listener = None
    
    def run(self):
        # Allow a short delay before listening to avoid immediate clicks
        time.sleep(0.5)
        
        clicked_pos = [None]
        
        def on_click(x, y, button, pressed):
            if pressed:
                clicked_pos[0] = (x, y)
                return False  # Stop listener
        
        with mouse.Listener(on_click=on_click) as self.listener:
            self.listener.join()
            
        if clicked_pos[0]:
            # Play beep sound
            try:
                winsound.Beep(1000, 200)
            except:
                pass
            self.clicked.emit(clicked_pos[0][0], clicked_pos[0][1])

    def stop(self):
        """Stop the mouse listener."""
        if self.listener:
            self.listener.stop()

class CalibrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Calibrate Uploader")
        self.setFixedSize(400, 500)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
            }}
            QProgressBar {{
                background-color: {COLORS['surface']};
                border: none;
                border-radius: 3px;
                height: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['secondary']};
                border-radius: 3px;
            }}
        """)
        
        self.steps = [
            {
                "id": "upload_button",
                "title": "1. Plus (+) Button",
                "desc": "Click the Plus (+) icon in Gemini"
            },
            {
                "id": "upload_file_option",
                "title": "2. Upload Option",
                "desc": "Click 'Upload from computer' in the menu"
            },
            {
                "id": "file_dialog_path",
                "title": "3. File Input Field",
                "desc": "Click the 'File name' input field in the dialog"
            },
            {
                "id": "file_dialog_open",
                "title": "4. Open Button",
                "desc": "Click the 'Open' button in the dialog"
            },
            {
                "id": "send_button",
                "title": "5. Send Button",
                "desc": "Click the Send (arrow) button in Gemini"
            }
        ]
        
        self.current_step_index = 0
        self.captured_coords = {}
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("Calibration Wizard")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        desc = QLabel(
            "This wizard will help you teach the software where the Gemini buttons are on your screen."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)
        
        # Step Indicator
        self.step_label = QLabel("Ready to start")
        self.step_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.step_label.setStyleSheet(f"color: {COLORS['secondary']}; margin-top: 10px;")
        layout.addWidget(self.step_label)
        
        # Instruction Box
        self.instruction_frame = QFrame()
        self.instruction_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['secondary']};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        inst_layout = QVBoxLayout(self.instruction_frame)
        
        self.instruction_text = QLabel("Make sure Gemini is open in Chrome.\n\nClick 'Start Calibration' when ready.")
        self.instruction_text.setWordWrap(True)
        self.instruction_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instruction_text.setFont(QFont("Segoe UI", 11))
        inst_layout.addWidget(self.instruction_text)
        
        self.coord_label = QLabel("")
        self.coord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.coord_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-family: monospace;")
        inst_layout.addWidget(self.coord_label)
        
        layout.addWidget(self.instruction_frame)
        
        layout.addStretch()
        
        # Coordinates List (Hidden initially)
        self.results_label = QLabel("")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet(f"""
            background-color: {COLORS['secondary']};
            border-radius: 5px;
            padding: 10px;
            font-family: monospace;
            font-size: 10px;
        """)
        self.results_label.hide()
        layout.addWidget(self.results_label)
        
        # Buttons
        self.btn_action = QPushButton("Start Calibration")
        self.btn_action.setFixedHeight(45)
        self.btn_action.clicked.connect(self._on_action_click)
        layout.addWidget(self.btn_action)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                color: {COLORS['text']};
            }}
        """)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_cancel)

    def _on_action_click(self):
        btn_text = self.btn_action.text()
        
        if btn_text == "Start Calibration":
            self._start_calibration_sequence()
        elif btn_text == "Next Step":
            self._start_listening()
        elif btn_text == "Save Configuration":
            self._save_configuration()
            
    def _start_calibration_sequence(self):
        self.current_step_index = 0
        self.captured_coords = {}
        self.btn_action.setText("Starting in 5s...")
        self.btn_action.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        
        # Countdown
        self.countdown_val = 5
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_countdown)
        self.timer.start(1000)
    
    def _update_countdown(self):
        self.countdown_val -= 1
        self.btn_action.setText(f"Starting in {self.countdown_val}s...")
        if self.countdown_val <= 0:
            self.timer.stop()
            self._prepare_step()
        
    def _prepare_step(self):
        if self.current_step_index >= len(self.steps):
            self._show_summary()
            return
            
        step = self.steps[self.current_step_index]
        
        self.step_label.setText(f"Step {self.current_step_index + 1}/{len(self.steps)}")
        self.instruction_text.setText(f"{step['title']}\n\n{step['desc']}")
        self.coord_label.setText("Waiting for click...")
        
        # Start countdown before listening to give user time to move mouse
        QTimer.singleShot(1000, self._start_listening)
        
    def _start_listening(self):
        self.btn_action.setText("Click the button now...")
        self.thread = ClickListenerThread()
        self.thread.clicked.connect(self._on_coords_captured)
        self.thread.start()
        
    def _on_coords_captured(self, x, y):
        step = self.steps[self.current_step_index]
        self.captured_coords[step['id']] = {
            "x": x, 
            "y": y,
            "description": step['desc']
        }
        
        self.coord_label.setText(f"Captured: ({x}, {y})")
        
        # Move to next step
        self.current_step_index += 1
        
        if self.current_step_index < len(self.steps):
            # Brief delay before next step
            QTimer.singleShot(1000, self._prepare_step)
        else:
            self._show_summary()
            
    def _show_summary(self):
        self.step_label.setText("Calibration Complete!")
        self.instruction_text.setText("Review your captured coordinates below.")
        self.coord_label.hide()
        
        # Show results
        summary = "Captured Coordinates:\n\n"
        for step in self.steps:
            coords = self.captured_coords.get(step['id'])
            if coords:
                summary += f"{step['title']}: ({coords['x']}, {coords['y']})\n"
        
        self.results_label.setText(summary)
        self.results_label.show()
        self.instruction_frame.hide()
        
        self.btn_action.setText("Save Configuration")
        self.btn_action.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        
        # Add screen resolution
        try:
            w, h = pyautogui.size()
            self.captured_coords["screen_resolution"] = {"width": w, "height": h}
        except:
            pass

    def _save_configuration(self):
        try:
            config_path = Path(__file__).parent.parent / "core" / "gemini_coordinates.json"
            
            with open(config_path, 'w') as f:
                json.dump(self.captured_coords, f, indent=2)
                
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

    def _stop_listener(self):
        """Stop the click listener thread if running."""
        # Stop timer if running
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
            
        # Stop thread
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.thread.quit()
            self.thread.wait()

    def reject(self):
        """Handle Cancel button or Esc key."""
        self._stop_listener()
        super().reject()

    def closeEvent(self, event):
        """Handle window close event."""
        self._stop_listener()
        event.accept()
