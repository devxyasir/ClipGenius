"""
ClipGenius - Calibration Tool
Allows users to set up button coordinates for their specific monitor/screen
"""
import json
import time
import os
from pathlib import Path

try:
    import pyautogui
    from pynput import mouse
    import winsound  # Added for sound
except ImportError:
    print("Installing required packages...")
    os.system("pip install pyautogui pynput")
    import pyautogui
    from pynput import mouse
    import winsound


# Config file path
CONFIG_PATH = Path(__file__).parent / "gemini_coordinates.json"

# Default coordinates (will be overwritten by calibration)
DEFAULT_COORDS = {
    "upload_button": {"x": 0, "y": 0, "description": "The + or Upload button"},
    "upload_file_option": {"x": 0, "y": 0, "description": "Upload from computer option in menu"},
    "file_dialog_path": {"x": 0, "y": 0, "description": "File name input field in dialog"},
    "file_dialog_open": {"x": 0, "y": 0, "description": "Open button in file dialog"},
    "send_button": {"x": 0, "y": 0, "description": "Send message button"},
    "screen_resolution": {"width": 0, "height": 0}
}


def load_coordinates():
    """Load saved coordinates from config file."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_COORDS.copy()


def save_coordinates(coords):
    """Save coordinates to config file."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(coords, f, indent=2)
    print(f"\n✅ Coordinates saved to: {CONFIG_PATH}")


def get_click_position(prompt):
    """Wait for user to click and return the position. Allows click to propagate."""
    print(f"\n👆 {prompt}")
    
    clicked_pos = [None]
    
    def on_click(x, y, button, pressed):
        if pressed:
            clicked_pos[0] = (x, y)
            # IMPORTANT: Return True (or None) to allow the click to propagate
            # Stop the listener explicitly
            return False
            
    # Listen for mouse click
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()
        
    winsound.Beep(1000, 200)  # Beep on click capture
    return clicked_pos[0]


def run_calibration():
    """Run the calibration wizard."""
    print("\n" + "="*60)
    print("   🎯 ClipGenius Button Calibration Wizard")
    print("="*60)
    print("\nThis will help the software learn where buttons are on YOUR screen.")
    print("You'll click on each button when prompted.\n")
    print("⚠️  Make sure Gemini is open in Chrome and visible!\n")
    
    input("Press Enter to start calibration...")
    
    coords = load_coordinates()
    
    # Get screen resolution
    screen_width, screen_height = pyautogui.size()
    coords["screen_resolution"] = {"width": screen_width, "height": screen_height}
    print(f"\n📺 Screen resolution: {screen_width}x{screen_height}")
    
    # Calibrate each button
    buttons_to_calibrate = [
        ("upload_button", "Click on the + (Plus) or Upload button in Gemini"),
        ("upload_file_option", "Click on 'Upload from computer' or 'Upload file' in the menu"),
        ("send_button", "Click on the Send message button (arrow icon)"),
    ]
    
    print("\n" + "-"*40)
    
    for key, prompt in buttons_to_calibrate:
        pos = get_click_position(prompt)
        if pos:
            coords[key]["x"] = pos[0]
            coords[key]["y"] = pos[1]
            print(f"   ✅ Recorded: ({pos[0]}, {pos[1]})")
        else:
            print(f"   ❌ Failed to capture position")
        time.sleep(0.5)
    
    # File dialog calibration is optional
    print("\n" + "-"*40)
    print("\n📁 File Dialog Calibration (Optional)")
    print("   If you want to calibrate file dialog buttons, open a file dialog first.")
    
    calibrate_dialog = input("\nCalibrate file dialog? (y/n): ").lower().strip() == 'y'
    
    if calibrate_dialog:
        dialog_buttons = [
            ("file_dialog_path", "Click on the 'File name' input field"),
            ("file_dialog_open", "Click on the 'Open' button"),
        ]
        
        for key, prompt in dialog_buttons:
            pos = get_click_position(prompt)
            if pos:
                coords[key]["x"] = pos[0]
                coords[key]["y"] = pos[1]
                print(f"   ✅ Recorded: ({pos[0]}, {pos[1]})")
    
    # Save coordinates
    save_coordinates(coords)
    
    # Show summary
    print("\n" + "="*60)
    print("   📋 Calibration Summary")
    print("="*60)
    
    for key, value in coords.items():
        if key != "screen_resolution" and isinstance(value, dict) and "x" in value:
            desc = value.get("description", key)
            print(f"   {key}: ({value['x']}, {value['y']})")
    
    print(f"\n   Screen: {coords['screen_resolution']['width']}x{coords['screen_resolution']['height']}")
    print("\n✅ Calibration complete! You can now use the software.")
    print("   Run calibration again if buttons move or you change monitors.\n")


def run_guided_calibration():
    """Run the guided calibration wizard as requested."""
    print("\n" + "="*60)
    print("   🎯 ClipGenius Guided Calibration")
    print("="*60)
    print("\nThis will learn the button positions on YOUR screen.")
    print("Please follow the instructions carefully.")
    print("\n⚠️  Steps:")
    print("1. Open Gemini in Chrome")
    print("2. Collapse the side menu")
    print("3. Wait for the beep to start")
    
    print("\nStarting in 5 seconds...")
    for i in range(5, 0, -1):
        print(f" {i}...")
        time.sleep(1)
    
    winsound.Beep(800, 500)  # Start sound
    print("\n🚀 Calibration Started!")
    
    coords = load_coordinates()
    
    # Get screen resolution
    screen_width, screen_height = pyautogui.size()
    coords["screen_resolution"] = {"width": screen_width, "height": screen_height}
    
    # 1. Plus Button
    pos = get_click_position("Click the PLUS (+) icon")
    if pos:
        coords["upload_button"] = {"x": pos[0], "y": pos[1], "description": "Plus button"}
        print(f"   ✅ Saved Plus button: {pos}")
    
    time.sleep(1)
    
    # 2. Upload Option (User must have clicked + so menu should be open)
    pos = get_click_position("Click 'Upload from computer' option")
    if pos:
        coords["upload_file_option"] = {"x": pos[0], "y": pos[1], "description": "Upload option"}
        print(f"   ✅ Saved Upload option: {pos}")
        
    time.sleep(1)
    
    # 3. File Input (Dialog should be open now)
    pos = get_click_position("Click the 'File name' input field on dialog")
    if pos:
        coords["file_dialog_path"] = {"x": pos[0], "y": pos[1], "description": "File input"}
        print(f"   ✅ Saved Dialog input: {pos}")

    time.sleep(1)

    # 4. Open Button
    pos = get_click_position("Click the 'Open' button on dialog")
    if pos:
        coords["file_dialog_open"] = {"x": pos[0], "y": pos[1], "description": "Open button"}
        print(f"   ✅ Saved Open button: {pos}")
        
    time.sleep(1)
    
    # 5. Send Button
    pos = get_click_position("Click the 'Send' button (arrow icon)")
    if pos:
        coords["send_button"] = {"x": pos[0], "y": pos[1], "description": "Send button"}
        print(f"   ✅ Saved Send button: {pos}")
    
    winsound.Beep(800, 300)
    winsound.Beep(1200, 300)
    
    save_coordinates(coords)
    print("\n✅ Calibration Complete! Coordinates saved.")


def is_calibrated():
    """Check if calibration has been done."""
    coords = load_coordinates()
    return coords.get("upload_button", {}).get("x", 0) != 0


def get_button_coords(button_name):
    """Get coordinates for a specific button."""
    coords = load_coordinates()
    if button_name in coords:
        return coords[button_name].get("x", 0), coords[button_name].get("y", 0)
    return 0, 0


if __name__ == "__main__":
    run_guided_calibration()
