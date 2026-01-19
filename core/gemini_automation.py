"""
ClipGenius - Gemini Automation
Automates Gemini interaction via Selenium for video analysis
Uses cookies-based authentication and drag-drop upload
"""
import json
import re
import time
import pyperclip
from pathlib import Path
from typing import Optional, List, Callable
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import (
    GEMINI_URL, 
    GEMINI_UPLOAD_TIMEOUT, 
    GEMINI_RESPONSE_TIMEOUT
)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


# Detailed prompt for video analysis
GEMINI_ANALYSIS_PROMPT = """You are a video content analyst used inside an automated video-editing pipeline.

Your task:
- Analyze the uploaded video titled: "{video_name}"
- Identify the BEST short, engaging segments suitable for short-form content (Reels / Shorts / TikTok).
- Focus on moments that are:
  - Informative
  - Emotional
  - High energy
  - Clear topic boundaries
  - Strong hook potential

STRICT RULES:
1. You MUST return ONLY valid JSON.
2. DO NOT include explanations, markdown, comments, or text outside JSON.
3. The JSON structure MUST ALWAYS be exactly the same.
4. Time format MUST be mm:ss.
5. Start time MUST be less than end time.
6. Each clip should be between {min_duration} to {max_duration} seconds unless the content strongly requires otherwise.
7. If no good clips exist, return an empty clips array (do NOT change schema).

OUTPUT JSON SCHEMA (DO NOT CHANGE):

{{
  "video_duration": "mm:ss",
  "analysis_summary": "short one-line summary of the video",
  "clips": [
    {{
      "clip_id": 1,
      "start_time": "mm:ss",
      "end_time": "mm:ss",
      "reason": "why this segment is good for a short clip",
      "content_type": "hook | explanation | story | highlight | emotional | tutorial",
      "confidence_score": 0.0
    }}
  ]
}}

CONFIDENCE SCORE RULES:
- Range: 0.0 to 1.0
- 1.0 = extremely strong short-form clip
- 0.5 = usable but average
- Below 0.4 = weak (avoid unless needed)

IMPORTANT:
- Return clips in chronological order.
- Do NOT overlap time ranges.
- Prefer fewer high-quality clips over many weak ones.
- Return ONLY the JSON object, nothing else."""

# YouTube URL specific prompt
GEMINI_YOUTUBE_PROMPT = """You are a video content analyst used inside an automated video-editing pipeline.

Your task:
- Watch and analyze this YouTube video: {youtube_url}
- Identify the BEST short, engaging segments suitable for short-form content (Reels / Shorts / TikTok).
- Focus on moments that are:
  - Informative
  - Emotional
  - High energy
  - Clear topic boundaries
  - Strong hook potential

STRICT RULES:
1. You MUST return ONLY valid JSON.
2. DO NOT include explanations, markdown, comments, or text outside JSON.
3. The JSON structure MUST ALWAYS be exactly the same.
4. Time format MUST be mm:ss.
5. Start time MUST be less than end time.
6. Each clip should be between {min_duration} to {max_duration} seconds unless the content strongly requires otherwise.
7. If no good clips exist, return an empty clips array (do NOT change schema).

OUTPUT JSON SCHEMA (DO NOT CHANGE):

{{
  "video_duration": "mm:ss",
  "analysis_summary": "short one-line summary of the video",
  "clips": [
    {{
      "clip_id": 1,
      "start_time": "mm:ss",
      "end_time": "mm:ss",
      "reason": "why this segment is good for a short clip",
      "content_type": "hook | explanation | story | highlight | emotional | tutorial",
      "confidence_score": 0.0
    }}
  ]
}}

CONFIDENCE SCORE RULES:
- Range: 0.0 to 1.0
- 1.0 = extremely strong short-form clip
- 0.5 = usable but average
- Below 0.4 = weak (avoid unless needed)

IMPORTANT:
- Return clips in chronological order.
- Do NOT overlap time ranges.
- Prefer fewer high-quality clips over many weak ones.
- Return ONLY the JSON object, nothing else."""


class GeminiAutomation:
    """Automates Gemini browser interaction for video analysis."""
    
    def __init__(
        self,
        cookies_file: str = None,
        headless: bool = False
    ):
        """Initialize Gemini automation.
        
        Args:
            cookies_file: Path to Netscape format cookies.txt file
            headless: Run in headless mode (not recommended for Gemini)
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is not installed. Run: pip install selenium webdriver-manager")
        
        # Default cookies file path
        self.cookies_file = cookies_file or str(Path(__file__).parent.parent / "cookies.txt")
        self.headless = headless
        self.driver = None
        self.wait = None
    
    def load_netscape_cookies(self, cookie_path: str):
        """Load cookies from Netscape format file."""
        if not self.driver or not Path(cookie_path).exists():
            print(f"Cookies file not found: {cookie_path}")
            return
        
        with open(cookie_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                
                parts = line.strip().split("\t")
                if len(parts) != 7:
                    continue
                
                domain, flag, path, secure, expiry, name, value = parts
                
                cookie = {
                    "name": name,
                    "value": value,
                    "domain": domain.lstrip("."),
                    "path": path,
                    "secure": secure.upper() == "TRUE"
                }
                
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
    
    def start_browser(self) -> bool:
        """Start Chrome browser with cookies authentication."""
        options = Options()
        
        # Use a clean selenium profile
        selenium_profile = r"C:\selenium_gemini_profile"
        options.add_argument(f"--user-data-dir={selenium_profile}")
        
        # Match real Chrome User-Agent
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
        
        # Anti-detection options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        if self.headless:
            options.add_argument("--headless=new")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 60)
            
            # Hide webdriver flag
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            return True
        except Exception as e:
            print(f"Failed to start browser: {e}")
            return False
    
    def close_browser(self):
        """Close the browser instance."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def navigate_to_gemini(self) -> bool:
        """Navigate to Gemini and log in using cookies."""
        if not self.driver:
            return False
        
        try:
            # Navigate to the domain first
            self.driver.get(GEMINI_URL)
            time.sleep(2)
            
            # Load cookies
            if Path(self.cookies_file).exists():
                print(f"Loading cookies from: {self.cookies_file}")
                self.load_netscape_cookies(self.cookies_file)
                self.driver.refresh()
                time.sleep(3)
            
            # Check for chat input (rich-textarea)
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "rich-textarea"))
                )
                print("✅ Successfully logged into Gemini!")
                return True
            except TimeoutException:
                print("Could not find chat input. Login may have failed.")
                return False
                
        except Exception as e:
            print(f"Failed to navigate to Gemini: {e}")
            return False
    
    def drag_drop_video(self, video_path: str, progress_callback: Callable = None) -> bool:
        """Upload video file to Gemini using calibrated coordinates.
        
        Args:
            video_path: Path to video file
            progress_callback: Optional progress callback
            
        Returns:
            True if upload successful
        """
        if not self.driver:
            return False
        
        try:
            import pyautogui
            import pyperclip
            pyautogui.FAILSAFE = False
        except ImportError:
            print("pyautogui not installed. Install with: pip install pyautogui")
            return False
        
        # Try to load calibrated coordinates
        try:
            from core.calibration import load_coordinates, is_calibrated
            use_calibration = is_calibrated()
            coords = load_coordinates() if use_calibration else {}
        except:
            use_calibration = False
            coords = {}
        
        try:
            abs_path = str(Path(video_path).absolute())
            print(f"Uploading video: {abs_path}")
            
            if use_calibration:
                print("Using calibrated coordinates for upload...")
                
                if progress_callback:
                    progress_callback(5, "Using calibrated positions...")
                
                # Step 1: Click upload button at calibrated position
                upload_x = coords.get("upload_button", {}).get("x", 0)
                upload_y = coords.get("upload_button", {}).get("y", 0)
                
                if upload_x and upload_y:
                    time.sleep(1)
                    pyautogui.click(upload_x, upload_y)
                    print(f"Clicked upload button at ({upload_x}, {upload_y})")
                    time.sleep(1)
                    
                    if progress_callback:
                        progress_callback(15, "Clicked upload button...")
                    
                    # Step 2: Click "Upload file" option
                    file_x = coords.get("upload_file_option", {}).get("x", 0)
                    file_y = coords.get("upload_file_option", {}).get("y", 0)
                    
                    if file_x and file_y:
                        pyautogui.click(file_x, file_y)
                        print(f"Clicked upload file option at ({file_x}, {file_y})")
                        time.sleep(2)  # Wait for file dialog
                        
                        if progress_callback:
                            progress_callback(25, "Opening file dialog...")
                        
                        # Step 3: Paste file path and press Enter
                        pyperclip.copy(abs_path)
                        time.sleep(0.5)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.5)
                        pyautogui.press('enter')
                        print("File path pasted and confirmed")
                        
                        if progress_callback:
                            progress_callback(50, "File selected, uploading...")
                        
                        # Wait for upload
                        time.sleep(5)
                        
                        if progress_callback:
                            progress_callback(90, "Upload complete!")
                        
                        print("Video upload completed via calibration")
                        return True
            
            # Fallback: Use Selenium selectors (less reliable)
            print("No calibration found, using Selenium selectors...")
            
            if progress_callback:
                progress_callback(5, "Looking for upload button...")
            
            try:
                add_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                        "button.upload-card-button, button[aria-label*='upload' i]"))
                )
                add_button.click()
                time.sleep(1)
                print("Clicked upload button via Selenium")
                
                # Wait for file dialog and paste path
                time.sleep(2)
                pyperclip.copy(abs_path)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                pyautogui.press('enter')
                
                time.sleep(5)
                if progress_callback:
                    progress_callback(90, "Upload complete!")
                
                return True
                
            except Exception as e:
                print(f"Selenium approach failed: {e}")
            
            if progress_callback:
                progress_callback(100, "Upload failed, continuing...")
            
            return True  # Continue anyway
            
        except Exception as e:
            print(f"Upload failed: {e}")
            import traceback
            traceback.print_exc()
            if progress_callback:
                progress_callback(100, "Upload failed, continuing...")
            return True
    
    def send_prompt(self, video_name: str = None, youtube_url: str = None, 
                     min_duration: int = 30, max_duration: int = 90) -> bool:
        """Send analysis prompt to Gemini using the specific selectors.
        
        Args:
            video_name: Name of the video file for the prompt (used when uploading video)
            youtube_url: YouTube URL to analyze (when provided, skips video upload)
            min_duration: Minimum clip duration in seconds
            max_duration: Maximum clip duration in seconds
            
        Returns:
            True if prompt sent successfully
        """
        if not self.driver:
            return False
        
        try:
            # Build prompt based on whether we have YouTube URL or video
            # Include duration settings from UI
            if youtube_url:
                prompt = GEMINI_YOUTUBE_PROMPT.format(
                    youtube_url=youtube_url,
                    min_duration=min_duration,
                    max_duration=max_duration
                )
                print(f"Using YouTube URL prompt: {youtube_url}")
            else:
                prompt = GEMINI_ANALYSIS_PROMPT.format(
                    video_name=video_name or "video",
                    min_duration=min_duration,
                    max_duration=max_duration
                )
            
            print(f"Clip duration settings: {min_duration}s - {max_duration}s")
            
            # Find the rich-textarea element
            try:
                rich_textarea = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "rich-textarea"))
                )
            except TimeoutException:
                print("Could not find rich-textarea")
                return False
            
            # Find the contenteditable div inside (.ql-editor with contenteditable='true')
            # Based on actual HTML: div.ql-editor.textarea with contenteditable="true"
            try:
                editor = rich_textarea.find_element(By.CSS_SELECTOR, "div.ql-editor[contenteditable='true']")
            except:
                try:
                    editor = rich_textarea.find_element(By.CSS_SELECTOR, ".ql-editor")
                except:
                    editor = rich_textarea.find_element(By.CSS_SELECTOR, "[contenteditable='true']")
            
            # Click to focus
            editor.click()
            time.sleep(0.5)
            
            # IMPORTANT: Use send_keys instead of innerHTML to avoid TrustedHTML error!
            # Clear existing content first
            editor.clear()
            
            # Send the prompt using keyboard input
            # This avoids the TrustedHTML security restriction
            print("Typing prompt...")
            editor.send_keys(prompt)
            
            time.sleep(1)
            
            # Dispatch input event to ensure the page recognizes the text
            self.driver.execute_script("""
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            """, editor)
            
            time.sleep(0.5)
            
            # Find and click send button
            # FIRST: Wait for video upload to complete (check aria-disabled)
            print("Waiting for video upload to complete...")
            upload_wait_start = time.time()
            upload_wait_timeout = 300  # 5 minutes for large videos
            
            while time.time() - upload_wait_start < upload_wait_timeout:
                try:
                    send_btn = self.driver.find_element(By.CSS_SELECTOR, "button.send-button, button[aria-label='Send message']")
                    aria_disabled = send_btn.get_attribute("aria-disabled")
                    
                    if aria_disabled == "false" or aria_disabled is None:
                        print("✅ Video upload complete! Send button is enabled.")
                        break
                    else:
                        elapsed = int(time.time() - upload_wait_start)
                        if elapsed % 10 == 0:  # Log every 10 seconds
                            print(f"Still uploading video... ({elapsed}s)")
                        time.sleep(2)
                except Exception as e:
                    time.sleep(2)
            
            # 1. Try PyAutoGUI with calibrated coordinates (MOST RELIABLE)
            button_clicked = False
            
            try:
                from core.calibration import load_coordinates, is_calibrated
                if is_calibrated():
                    coords = load_coordinates()
                    send_x = coords.get("send_button", {}).get("x", 0)
                    send_y = coords.get("send_button", {}).get("y", 0)
                    send_x2 = coords.get("send_button_2", {}).get("x", 0)
                    send_y2 = coords.get("send_button_2", {}).get("y", 0)
                    
                    import pyautogui
                    
                    # Try Primary Coordinate
                    if send_x and send_y:
                        print(f"Clicking Send button at calibrated pos: ({send_x}, {send_y})")
                        time.sleep(1) 
                        pyautogui.click(send_x, send_y)
                        time.sleep(1)
                        
                        # Verify if text is gone
                        try:
                            if not editor.text.strip():
                                print("✅ Prompt sent via PyAutoGUI (Primary)!")
                                return True
                        except: pass
                    
                    # Try Secondary Coordinate (if text still there)
                    if send_x2 and send_y2:
                        print(f"Primary failed? Clicking Secondary Send button at: ({send_x2}, {send_y2})")
                        pyautogui.click(send_x2, send_y2)
                        time.sleep(1)
                        try:
                            if not editor.text.strip():
                                print("✅ Prompt sent via PyAutoGUI (Secondary)!")
                                return True
                        except: pass
                        
                    # If we got here, maybe manual click worked or coordinate failed but we proceed to fallback
            except Exception as e:
                print(f"PyAutoGUI click logic failed: {e}")

            # 2. Fallback to Selenium if not clicked
            if not button_clicked:
                try:
                    # Try main selector first
                    send_button = self.driver.find_element(By.CSS_SELECTOR, "button.send-button, button[aria-label='Send message']")
                    if send_button: # and send_button.get_attribute('aria-disabled') != 'true':
                        send_button.click()
                        button_clicked = True
                        print("✅ Prompt sent via Selenium!")
                except Exception as e:
                    print(f"Selenium send click failed: {e}")
            
            # 3. Last resort: keyboard shortcut
            if not button_clicked:
                try:
                    print("Trying Ctrl+Enter fallback...")
                    editor.send_keys(Keys.CONTROL + Keys.RETURN)
                    button_clicked = True
                    print("✅ Prompt sent via Ctrl+Enter!")
                except:
                    pass
            
            return button_clicked
            
        except Exception as e:
            print(f"Failed to send prompt: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def wait_for_response_and_copy(self, timeout: int = None, cancel_check: Callable = None) -> str:
        """Wait for response and copy JSON using copy button.
        
        Args:
            timeout: Maximum wait time in seconds
            cancel_check: Optional function that returns True if operation should be cancelled
            
        Returns:
            Copied JSON string
        """
        if not self.driver:
            return ""
        
        timeout = timeout or GEMINI_RESPONSE_TIMEOUT
        
        try:
            print("Waiting for Gemini response...")
            
            # Wait initial time for response to start
            for _ in range(10):
                if cancel_check and cancel_check():
                    print("Wait cancelled by user")
                    return ""
                time.sleep(1)
            
            start_time = time.time()
            last_check = ""
            stable_count = 0
            
            while time.time() - start_time < timeout:
                if cancel_check and cancel_check():
                    print("Wait cancelled by user")
                    return ""

                # Check for copy button (appears when code/JSON is in response)
                try:
                    copy_buttons = self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "button.copy-button, button[aria-label='Copy code'], mat-icon[fonticon='content_copy'], .embedded-copy-icon"
                    )
                    
                    if copy_buttons:
                        # Response has code block, check if stable
                        current_text = self.driver.page_source
                        
                        if current_text == last_check:
                            stable_count += 1
                            if stable_count >= 3:
                                # Response is stable, click copy button
                                print("✅ Response complete, copying JSON...")
                                
                                # Click the last copy button (most recent code block)
                                copy_buttons[-1].click()
                                time.sleep(1)
                                
                                # Get clipboard content
                                try:
                                    json_content = pyperclip.paste()
                                    if json_content and "{" in json_content:
                                        return json_content
                                except:
                                    pass
                                
                                # Fallback: extract from page
                                return self._extract_json_from_page()
                        else:
                            last_check = current_text
                            stable_count = 0
                    
                except Exception as e:
                    pass
                
                time.sleep(2)
                
                # Print status every 30 seconds
                if int(time.time() - start_time) % 30 == 0:
                    print(f"Still waiting for response... ({int(time.time() - start_time)}s)")
            
            # Timeout - try to extract JSON anyway
            return self._extract_json_from_page()
            
        except Exception as e:
            print(f"Failed to get response: {e}")
            return ""
    
    def _extract_json_from_page(self) -> str:
        """Extract JSON from the page source."""
        try:
            # Find code blocks
            code_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "code-block, pre code, .code-block"
            )
            
            for elem in code_elements:
                text = elem.text
                if "clips" in text and "{" in text:
                    return text
            
            # Try to find JSON pattern in response
            response_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "message-content, .response-content, .model-response"
            )
            
            for elem in response_elements:
                text = elem.text
                # Look for JSON pattern
                match = re.search(r'\{[\s\S]*"clips"[\s\S]*\}', text)
                if match:
                    return match.group(0)
            
            return ""
        except:
            return ""
    
    def parse_json_response(self, response_text: str) -> List[dict]:
        """Parse JSON clips from Gemini response."""
        if not response_text:
            return []
        
        try:
            # Clean JSON string
            json_str = response_text.strip()
            
            # Remove markdown code block markers if present
            if "```json" in json_str:
                json_str = re.sub(r'```json\s*', '', json_str)
                json_str = re.sub(r'```\s*$', '', json_str)
            elif "```" in json_str:
                json_str = re.sub(r'```\s*', '', json_str)
            
            data = json.loads(json_str)
            
            clips = data.get('clips', [])
            
            # Convert to our format
            valid_clips = []
            for clip in clips:
                start_time = clip.get('start_time', '0:00')
                end_time = clip.get('end_time', '1:00')
                
                valid_clips.append({
                    'clip_id': clip.get('clip_id', len(valid_clips) + 1),
                    'start_time': start_time,
                    'end_time': end_time,
                    'title': f"Clip {clip.get('clip_id', len(valid_clips) + 1)}",
                    'reason': clip.get('reason', ''),
                    'content_type': clip.get('content_type', 'highlight'),
                    'viral_score': int(clip.get('confidence_score', 0.5) * 10)
                })
            
            return valid_clips
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            print(f"Response was: {response_text[:500]}...")
            return []
    
    def save_clips_json(self, clips_data: dict, output_path: str):
        """Save clips data to JSON file.
        
        Args:
            clips_data: Raw clips data from Gemini
            output_path: Path to save JSON file
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(clips_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved clips to: {output_path}")
        except Exception as e:
            print(f"Failed to save clips: {e}")
    
    def analyze_video(
        self,
        video_path: str = None,
        youtube_url: str = None,
        output_folder: str = None,
        progress_callback: Callable = None,
        cancel_check: Callable = None,
        min_duration: int = 30,
        max_duration: int = 90
    ) -> List[dict]:
        """Complete workflow: Upload video or use YouTube URL and get clip suggestions.
        
        Args:
            video_path: Path to video file (optional if youtube_url provided)
            youtube_url: YouTube URL to analyze (optional, if provided skips upload)
            output_folder: Folder to save clips.json
            progress_callback: Optional callback(percent, status)
            min_duration: Minimum clip duration in seconds (default 30)
            max_duration: Maximum clip duration in seconds (default 90)
            
        Returns:
            List of clip dictionaries with timestamps
        """
        clips = []
        video_name = Path(video_path).stem if video_path else "YouTube Video"
        
        try:
            if progress_callback:
                progress_callback(0, "Starting browser...")
            
            if not self.start_browser():
                raise RuntimeError("Failed to start browser")
            
            if progress_callback:
                progress_callback(5, "Navigating to Gemini...")
            
            if not self.navigate_to_gemini():
                raise RuntimeError("Failed to navigate to Gemini or login failed")
            
            # If we have a YouTube URL, skip video upload
            if youtube_url:
                if progress_callback:
                    progress_callback(30, "Using YouTube URL (no upload needed)...")
                print(f"Analyzing YouTube URL: {youtube_url}")
            else:
                # Upload video via drag-drop simulation
                if progress_callback:
                    progress_callback(10, "Uploading video...")
                
                if not self.drag_drop_video(video_path, progress_callback):
                    print("Video upload may have failed, continuing with prompt...")
            
            if cancel_check and cancel_check():
                return []
            
            if progress_callback:
                progress_callback(40, "Sending analysis prompt...")
            
            # Wait a bit before sending prompt
            time.sleep(3)
            
            # Send prompt with either YouTube URL or video name + duration settings
            if not self.send_prompt(
                video_name=video_name, 
                youtube_url=youtube_url,
                min_duration=min_duration,
                max_duration=max_duration
            ):
                raise RuntimeError("Failed to send prompt")
            
            if progress_callback:
                progress_callback(50, "Waiting for AI analysis...")
            
            # Wait for response and copy JSON
            json_response = self.wait_for_response_and_copy(cancel_check=cancel_check)
            
            if cancel_check and cancel_check():
                return []
            
            if progress_callback:
                progress_callback(85, "Parsing response...")
            
            # Save raw JSON to file
            if output_folder and json_response:
                clips_json_path = Path(output_folder) / "clips.json"
                try:
                    raw_data = json.loads(json_response)
                    self.save_clips_json(raw_data, str(clips_json_path))
                except:
                    # Save as raw text if not valid JSON
                    with open(clips_json_path, 'w') as f:
                        f.write(json_response)
            
            # Parse response
            clips = self.parse_json_response(json_response)
            
            if progress_callback:
                progress_callback(100, f"Found {len(clips)} clips!")
            
            return clips
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {e}")
            return []
        finally:
            # Keep browser open for debugging (optional)
            # self.close_browser()
            pass
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close_browser()
