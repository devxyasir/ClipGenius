"""
ClipGenius - AI-Powered Short Video Generator
Main application entry point
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import selenium
    except ImportError:
        missing.append("selenium")
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    
    try:
        import moviepy
    except ImportError:
        missing.append("moviepy")
    
    if missing:
        print("=" * 50)
        print("Missing dependencies detected!")
        print("=" * 50)
        print("\nPlease install the missing packages:")
        print(f"\n  pip install {' '.join(missing)}")
        print("\nOr install all requirements:")
        print("\n  pip install -r requirements.txt")
        print("=" * 50)
        return False
    
    return True


def check_ffmpeg():
    """Check if FFmpeg is available."""
    import subprocess
    from utils.constants import FFMPEG_PATH
    
    try:
        subprocess.run(
            [FFMPEG_PATH, "-version"],
            capture_output=True,
            check=True
        )
        print("✅ FFmpeg found!")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("=" * 50)
        print("⚠️  FFmpeg not found!")
        print("=" * 50)
        print(f"\nLooked for FFmpeg at: {FFMPEG_PATH}")
        print("\nPlease update FFMPEG_PATH in utils/constants.py")
        print("or install FFmpeg and add it to your PATH.")
        print("\nDownload from: https://ffmpeg.org/download.html")
        print("=" * 50)
        return False


def main():
    """Main entry point."""
    print("""
    ╔═══════════════════════════════════════════════════╗
    ║                                                   ║
    ║   ✂️  ClipGenius - AI Video Clip Generator        ║
    ║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
    ║   Transform long videos into viral short clips   ║
    ║                                                   ║
    ╚═══════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Check FFmpeg (warning only, don't exit)
    check_ffmpeg()
    
    # Import and run application
    from ui.main_window import MainWindow
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    
    app = QApplication(sys.argv)
    app.setApplicationName("ClipGenius")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show splash screen
    from ui.splash_screen import SplashScreen
    splash = SplashScreen()
    splash.show()
    
    # Create main window (hidden initially)
    # We process events to ensure splash renders before potential blocking init
    app.processEvents()
    window = MainWindow()
    
    # Show main window when splash finishes
    splash.finished.connect(window.show)
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
