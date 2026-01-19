"""
ClipGenius - Constants and Configuration
"""
import os

# Application Info
APP_NAME = "ClipGenius"
APP_VERSION = "1.0.0"
APP_AUTHOR = "ClipGenius Team"

# FFmpeg Path (set this if FFmpeg is not in PATH)
FFMPEG_PATH = r"C:\Users\jamya\Downloads\ffmpeg-2026-01-14-git-6c878f8b82-full_build\ffmpeg-2026-01-14-git-6c878f8b82-full_build\bin\ffmpeg.exe"
FFPROBE_PATH = r"C:\Users\jamya\Downloads\ffmpeg-2026-01-14-git-6c878f8b82-full_build\ffmpeg-2026-01-14-git-6c878f8b82-full_build\bin\ffprobe.exe"

# Default Paths
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_BASE_DIR = os.path.join(DESKTOP_PATH, APP_NAME)

# Video Settings
DEFAULT_MIN_CLIP_DURATION = 60  # 1 minute in seconds
DEFAULT_MAX_CLIP_DURATION = 120  # 2 minutes in seconds
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
OUTPUT_FPS = 30
OUTPUT_FORMAT = "mp4"
OUTPUT_CODEC = "libx264"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

# Gemini Settings
GEMINI_URL = "https://gemini.google.com"
GEMINI_UPLOAD_TIMEOUT = 300  # 5 minutes for video upload
GEMINI_RESPONSE_TIMEOUT = 1200  # 20 minutes for AI response

# Prompt Template
GEMINI_PROMPT_TEMPLATE = """Analyze this video and identify the most engaging, viral-worthy moments suitable for TikTok/YouTube Shorts.

Requirements:
- Each clip should be between {min_duration} to {max_duration} minutes long
- Focus on: emotional peaks, funny moments, valuable insights, surprising reveals, key takeaways
- Avoid: slow intros, repetitive content, low-energy sections, filler content

CRITICAL INSTRUCTIONS:
1. You MUST respond with ONLY valid JSON
2. Do NOT include any text before or after the JSON
3. Do NOT include markdown code blocks
4. Follow this EXACT format:

{{"clips": [{{"start_time": "MM:SS", "end_time": "MM:SS", "title": "Short catchy title", "reason": "Why this is engaging", "viral_score": 8}}]}}

Provide 3-10 clips depending on video length. Start analysis now:"""

# UI Colors (Dark Theme)
COLORS = {
    "primary": "#6C5CE7",
    "primary_hover": "#5B4CD6",
    "primary_light": "#A29BFE",  # Added for sidebar title
    "secondary": "#00CEC9",
    "background": "#1A1A2E",
    "surface": "#16213E",
    "surface_light": "#1F3460",
    "text": "#FFFFFF",
    "text_secondary": "#A0A0A0",
    "success": "#00B894",
    "warning": "#FDCB6E",
    "error": "#E17055",
    "border": "#2D3E5F"
}

# File Extensions
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"]
AUDIO_EXTENSIONS = [".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"]
