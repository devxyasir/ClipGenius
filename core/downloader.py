"""
ClipGenius - Video Downloader
Downloads videos from YouTube and other platforms using yt-dlp
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Optional
import yt_dlp
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import FFMPEG_PATH


class VideoDownloader:
    """Downloads videos from YouTube and other platforms."""
    
    def __init__(self, output_dir: str = None):
        """Initialize the video downloader.
        
        Args:
            output_dir: Directory to save downloaded videos
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Get FFmpeg directory for yt-dlp
        self.ffmpeg_location = str(Path(FFMPEG_PATH).parent)
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid YouTube URL
        """
        youtube_patterns = [
            r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(https?://)?(www\.)?youtu\.be/[\w-]+',
            r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+'
        ]
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def get_video_info(self, url: str) -> dict:
        """Get video metadata without downloading.
        
        Args:
            url: Video URL
            
        Returns:
            Dictionary with video info (title, duration, etc.)
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'description': info.get('description', ''),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'id': info.get('id', '')
            }
    
    def download(
        self,
        url: str,
        filename: str = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Download video from URL.
        
        Args:
            url: Video URL to download
            filename: Optional custom filename (without extension)
            progress_callback: Optional callback function(progress_percent, status_text)
            
        Returns:
            Path to downloaded video file
        """
        # Create progress hook
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    speed = d.get('speed', 0)
                    speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "..."
                    progress_callback(percent, f"Downloading: {speed_str}")
            elif progress_callback and d['status'] == 'finished':
                progress_callback(100, "Download complete, processing...")
        
        # Configure yt-dlp options
        output_template = str(self.output_dir / (filename or '%(title)s')) + '.%(ext)s'
        
        # Use native formats with FFmpeg merge - avoid HLS which has fragment issues
        ydl_opts = {
            # Try formats in order: best pre-merged mp4 (H.264), or merge video(H.264)+audio using FFmpeg
            'format': 'bestvideo[ext=mp4][height<=1080][vcodec^=avc]+bestaudio[ext=m4a]/bestvideo[height<=1080][vcodec^=avc]+bestaudio/best[ext=mp4]/best',
            'outtmpl': output_template,
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',  # Merge to mp4 using FFmpeg
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
            'ffmpeg_location': self.ffmpeg_location,
            # Force native download to avoid HLS fragment issues
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],  # Skip HLS/DASH, use native formats
                }
            },
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual filename
            if filename:
                downloaded_file = self.output_dir / f"{filename}.mp4"
            else:
                # yt-dlp may sanitize the title
                sanitized_title = ydl.prepare_filename(info)
                downloaded_file = Path(sanitized_title).with_suffix('.mp4')
            
            # Find the actual downloaded file
            for ext in ['.mp4', '.mkv', '.webm']:
                potential_file = downloaded_file.with_suffix(ext)
                if potential_file.exists():
                    return str(potential_file)
            
            # Fallback: find any video file recently created
            for f in self.output_dir.glob('*.mp4'):
                return str(f)
        
        raise FileNotFoundError("Downloaded file not found")
    
    def download_with_options(
        self,
        url: str,
        quality: str = "best",
        audio_only: bool = False,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """Download video with specific quality options.
        
        Args:
            url: Video URL
            quality: Quality setting ('best', '1080p', '720p', '480p')
            audio_only: If True, download audio only
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded file
        """
        format_map = {
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
            '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480]'
        }
        
        if audio_only:
            format_str = 'bestaudio[ext=m4a]/bestaudio'
            ext = 'mp3'
        else:
            format_str = format_map.get(quality, format_map['best'])
            ext = 'mp4'
        
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    progress_callback(percent, "Downloading...")
        
        output_template = str(self.output_dir / '%(title)s') + f'.{ext}'
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': output_template,
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True
        }
        
        if audio_only:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return str(Path(filename).with_suffix(f'.{ext}'))
