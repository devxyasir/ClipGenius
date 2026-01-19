"""
Test script to validate calibrated button coordinates
This will click each button with delays so you can see if they're correct
"""
import time
import pyautogui
import pyperclip

# Your calibrated coordinates
COORDS = {
    "upload_button": (648, 580),
    "upload_file_option": (660, 641),
    "file_dialog_path": (232, 226),
    "file_dialog_open": (793, 924),
    "send_button": (1336, 632),
}

# Test video path (change this to a real video on your system)
TEST_VIDEO_PATH = r"C:\Users\jamya\Desktop\ClipGenius\Podcast_20260119_083552\source\STARDUMB ACTOR ｜ zayn saifi  ｜ talib saifi.mp4"


def highlight_position(x, y, duration=2):
    """Move mouse to position to show where it will click."""
    print(f"Moving to ({x}, {y})...")
    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(duration)


def test_coordinates_visual():
    """Visual test - just moves mouse to each position WITHOUT clicking."""
    print("\n" + "="*50)
    print("VISUAL TEST - Moving mouse to each position")
    print("="*50)
    print("\nWatch where the mouse moves. NO CLICKING will happen.")
    print("Make sure Gemini is open and visible!\n")
    
    input("Press Enter to start visual test...")
    
    for name, (x, y) in COORDS.items():
        print(f"\n➡️  {name}: ({x}, {y})")
        highlight_position(x, y, duration=2)
        print(f"   ✓ Mouse is at: {name}")
    
    print("\n✅ Visual test complete!")
    print("Did the mouse hover over the correct buttons?")


def test_upload_flow():
    """Test the actual upload flow by clicking buttons."""
    print("\n" + "="*50)
    print("CLICK TEST - Will actually click buttons!")
    print("="*50)
    print("\n⚠️  Make sure:")
    print("   1. Gemini is open in Chrome")
    print("   2. You're logged in")
    print("   3. Chrome window is in the same position as during calibration\n")
    
    confirm = input("Ready to test clicking? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("\nStarting in 3 seconds... Switch to Chrome!")
    time.sleep(3)
    
    # Step 1: Click upload button
    print("\n1️⃣ Clicking Upload Button...")
    x, y = COORDS["upload_button"]
    pyautogui.click(x, y)
    time.sleep(1.5)
    print(f"   Clicked at ({x}, {y})")
    
    # Step 2: Click upload file option
    print("\n2️⃣ Clicking 'Upload from computer' option...")
    x, y = COORDS["upload_file_option"]
    pyautogui.click(x, y)
    time.sleep(2)
    print(f"   Clicked at ({x}, {y})")
    
    # Step 3: In file dialog, paste path
    print("\n3️⃣ File dialog should be open. Pasting path...")
    pyperclip.copy(TEST_VIDEO_PATH)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    print(f"   Pasted: {TEST_VIDEO_PATH}")
    
    # Step 4: Press Enter to confirm
    print("\n4️⃣ Pressing Enter to select file...")
    pyautogui.press('enter')
    time.sleep(3)
    print("   Pressed Enter")
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)
    print("\n✅ Check if:")
    print("   - File was selected in the dialog")
    print("   - Upload started/completed in Gemini")
    print("\n❌ If something went wrong:")
    print("   - Run calibration.py again")
    print("   - Make sure Chrome is in the exact same position")


def test_send_button():
    """Test just the send button."""
    print("\n" + "="*50)
    print("SEND BUTTON TEST")
    print("="*50)
    print("\n⚠️  Make sure there's text in the Gemini input field first!\n")
    
    confirm = input("Ready to test send button? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    print("\nClicking send button in 3 seconds... Switch to Chrome!")
    time.sleep(3)
    
    x, y = COORDS["send_button"]
    pyautogui.click(x, y)
    print(f"Clicked send button at ({x}, {y})")


def main():
    print("\n" + "="*60)
    print("   🧪 Coordinate Testing Tool")
    print("="*60)
    print("\nYour calibrated coordinates:")
    for name, (x, y) in COORDS.items():
        print(f"   {name}: ({x}, {y})")
    
    print("\nOptions:")
    print("   1. Visual test (mouse moves only, no clicking)")
    print("   2. Upload flow test (clicks buttons)")
    print("   3. Send button test only")
    print("   4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        test_coordinates_visual()
    elif choice == "2":
        test_upload_flow()
    elif choice == "3":
        test_send_button()
    else:
        print("Exiting.")


if __name__ == "__main__":
    main()
