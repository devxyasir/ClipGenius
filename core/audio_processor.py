"""
ClipGenius - Audio Processor
Handles audio enhancement, background music mixing, and volume control
"""
import os
import subprocess
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import AUDIO_CODEC, AUDIO_BITRATE, FFMPEG_PATH


class AudioProcessor:
    """Processes audio: enhancement, music mixing, volume control."""
    
    def __init__(self, ffmpeg_path: str = None):
        """Initialize audio processor.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable. Uses FFMPEG_PATH from constants if not provided.
        """
        self.ffmpeg_path = ffmpeg_path or FFMPEG_PATH
    
    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        """Extract audio from video file.
        
        Args:
            video_path: Path to video file
            output_path: Optional output path. Defaults to same name with .mp3
            
        Returns:
            Path to extracted audio file
        """
        if output_path is None:
            output_path = str(Path(video_path).with_suffix('.mp3'))
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "libmp3lame",
            "-ab", AUDIO_BITRATE,
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to extract audio: {e}")
    
    def enhance_audio(
        self,
        input_path: str,
        output_path: str = None,
        normalize: bool = True,
        noise_reduction: bool = True,
        bass_boost: float = 0,
        treble_boost: float = 0
    ) -> str:
        """Apply audio enhancements.
        
        Args:
            input_path: Input audio/video file
            output_path: Output path
            normalize: Normalize audio levels
            noise_reduction: Apply basic noise reduction
            bass_boost: Bass boost in dB (-20 to 20)
            treble_boost: Treble boost in dB (-20 to 20)
            
        Returns:
            Path to enhanced audio/video
        """
        if output_path is None:
            path = Path(input_path)
            output_path = str(path.parent / f"{path.stem}_enhanced{path.suffix}")
        
        filters = []
        
        # Noise reduction using highpass and lowpass
        if noise_reduction:
            filters.append("highpass=f=80")  # Remove very low rumble
            filters.append("lowpass=f=15000")  # Remove high freq noise
        
        # Bass/treble adjustment
        if bass_boost != 0:
            filters.append(f"bass=g={bass_boost}")
        if treble_boost != 0:
            filters.append(f"treble=g={treble_boost}")
        
        # Normalize audio (loudnorm)
        if normalize:
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        
        # Compressor to even out volume
        filters.append("acompressor=threshold=-20dB:ratio=4:attack=5:release=50")
        
        filter_str = ",".join(filters) if filters else "anull"
        
        # Check if input is video or audio
        is_video = Path(input_path).suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.webm']
        
        if is_video:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-af", filter_str,
                "-c:v", "copy",  # Copy video stream
                "-c:a", AUDIO_CODEC,
                "-b:a", AUDIO_BITRATE,
                output_path
            ]
        else:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-af", filter_str,
                output_path
            ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to enhance audio: {e}")
    
    def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume: int = 30,
        fade_in: float = 2.0,
        fade_out: float = 2.0
    ) -> str:
        """Add background music to video with volume control.
        
        Args:
            video_path: Path to video file
            music_path: Path to background music file
            output_path: Output video path
            music_volume: Music volume as percentage (0-100)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            
        Returns:
            Path to output video
        """
        # Get video duration for fade out timing
        duration = self._get_duration(video_path)
        
        # Calculate volume (0-100 to 0-1)
        vol = music_volume / 100.0
        
        # Build audio filter for music track
        fade_out_start = max(0, duration - fade_out)
        music_filter = f"afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out},volume={vol}"
        
        # Mix original audio with background music
        filter_complex = (
            f"[1:a]{music_filter}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-stream_loop", "-1",  # Loop music if shorter than video
            "-i", music_path,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-shortest",  # End when video ends
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to add background music: {e}")
    
    def adjust_volume(
        self,
        input_path: str,
        output_path: str,
        volume: float = 1.0
    ) -> str:
        """Adjust audio volume.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            volume: Volume multiplier (1.0 = original, 0.5 = half, 2.0 = double)
            
        Returns:
            Path to output file
        """
        is_video = Path(input_path).suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov', '.webm']
        
        if is_video:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-af", f"volume={volume}",
                "-c:v", "copy",
                "-c:a", AUDIO_CODEC,
                "-b:a", AUDIO_BITRATE,
                output_path
            ]
        else:
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-af", f"volume={volume}",
                output_path
            ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to adjust volume: {e}")
    
    def merge_audio_video(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ) -> str:
        """Merge separate audio and video files.
        
        Args:
            video_path: Path to video file (can have existing audio)
            audio_path: Path to audio file to use
            output_path: Output path
            
        Returns:
            Path to merged file
        """
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to merge audio/video: {e}")
    
    def _get_duration(self, file_path: str) -> float:
        """Get duration of audio/video file in seconds."""
        cmd = [
            self.ffmpeg_path.replace("ffmpeg", "ffprobe"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError):
            return 0.0
