"""
ClipGenius - Caption Generator
Generates and burns captions/subtitles onto videos
"""
import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import OUTPUT_CODEC, AUDIO_CODEC, AUDIO_BITRATE, FFMPEG_PATH


class CaptionGenerator:
    """Generates captions from audio and burns them onto video."""
    
    def __init__(self, ffmpeg_path: str = None):
        """Initialize caption generator.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable. Uses FFMPEG_PATH from constants if not provided.
        """
        self.ffmpeg_path = ffmpeg_path or FFMPEG_PATH
        self.whisper_available = self._check_whisper()
    
    def _check_whisper(self) -> bool:
        """Check if Whisper is available for transcription."""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    def transcribe_video(
        self,
        video_path: str,
        model_size: str = "base",
        language: str = "en"
    ) -> List[dict]:
        """Transcribe video audio to text segments.
        
        Args:
            video_path: Path to video file
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (en, es, fr, etc.)
            
        Returns:
            List of segment dictionaries with start, end, text
        """
        if not self.whisper_available:
            raise RuntimeError("Whisper is not installed. Run: pip install openai-whisper")
        
        import whisper
        
        # Load model
        model = whisper.load_model(model_size)
        
        # Transcribe
        result = model.transcribe(
            video_path,
            language=language,
            verbose=False
        )
        
        # Format segments
        segments = []
        for seg in result.get('segments', []):
            segments.append({
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            })
        
        return segments
    
    def generate_srt(self, segments: List[dict], output_path: str) -> str:
        """Generate SRT subtitle file from segments.
        
        Args:
            segments: List of segment dictionaries
            output_path: Path to save SRT file
            
        Returns:
            Path to SRT file
        """
        def format_time(seconds: float) -> str:
            """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        srt_content = []
        for i, seg in enumerate(segments, 1):
            start_time = format_time(seg['start'])
            end_time = format_time(seg['end'])
            text = seg['text']
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between subtitles
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        
        return output_path
    
    def generate_ass(
        self,
        segments: List[dict],
        output_path: str,
        font_name: str = "Arial",
        font_size: int = 24,
        primary_color: str = "&H00FFFFFF",  # White in ASS format
        outline_color: str = "&H00000000",  # Black outline
        outline_width: int = 2,
        position: str = "bottom"  # bottom, top, center
    ) -> str:
        """Generate ASS subtitle file with styling.
        
        Args:
            segments: List of segment dictionaries
            output_path: Path to save ASS file
            font_name: Font face name
            font_size: Font size
            primary_color: Text color in ASS format
            outline_color: Outline color in ASS format
            outline_width: Outline thickness
            position: Subtitle position
            
        Returns:
            Path to ASS file
        """
        # Position mapping (ASS alignment)
        pos_map = {
            'bottom': '2',      # Bottom center
            'top': '8',         # Top center
            'center': '5'       # Middle center
        }
        alignment = pos_map.get(position, '2')
        
        # ASS header
        ass_header = f"""[Script Info]
Title: ClipGenius Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,{outline_width},1,{alignment},10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        def format_time_ass(seconds: float) -> str:
            """Convert seconds to ASS time format (H:MM:SS.cc)."""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            centis = int((seconds % 1) * 100)
            return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
        
        events = []
        for seg in segments:
            start = format_time_ass(seg['start'])
            end = format_time_ass(seg['end'])
            text = seg['text'].replace('\n', '\\N')
            
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
        
        ass_content = ass_header + '\n'.join(events)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        return output_path
    
    def burn_captions(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        style_override: dict = None
    ) -> str:
        """Burn subtitles onto video (hardcoded).
        
        Args:
            video_path: Input video path
            subtitle_path: Path to SRT or ASS file
            output_path: Output video path
            style_override: Override style for SRT (font, size, color)
            
        Returns:
            Path to output video
        """
        # Determine subtitle format
        sub_ext = Path(subtitle_path).suffix.lower()
        
        # Escape path for ffmpeg filter
        escaped_sub_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
        
        if sub_ext == '.ass':
            # Use ASS subtitles directly
            subtitle_filter = f"ass='{escaped_sub_path}'"
        else:
            # SRT with optional styling
            style = style_override or {}
            font = style.get('font', 'Arial')
            size = style.get('size', 24)
            color = style.get('color', 'white')
            outline = style.get('outline_color', 'black')
            
            subtitle_filter = (
                f"subtitles='{escaped_sub_path}':"
                f"force_style='FontName={font},FontSize={size},"
                f"PrimaryColour={color},OutlineColour={outline},Outline=2'"
            )
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", video_path,
            "-vf", subtitle_filter,
            "-c:v", OUTPUT_CODEC,
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-preset", "fast",
            "-crf", "23",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to burn captions: {e}")
    
    def auto_caption_video(
        self,
        video_path: str,
        output_path: str,
        model_size: str = "base",
        language: str = "en",
        style: dict = None
    ) -> str:
        """Complete workflow: transcribe and burn captions.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            model_size: Whisper model size
            language: Language code
            style: Caption style options
            
        Returns:
            Path to captioned video
        """
        # Generate temp subtitle file
        video_name = Path(video_path).stem
        temp_dir = Path(video_path).parent
        ass_path = temp_dir / f"{video_name}_captions.ass"
        
        # Transcribe
        segments = self.transcribe_video(video_path, model_size, language)
        
        # Generate styled ASS file
        style = style or {}
        self.generate_ass(
            segments,
            str(ass_path),
            font_name=style.get('font', 'Arial'),
            font_size=style.get('size', 24),
            primary_color=style.get('primary_color', '&H00FFFFFF'),
            outline_color=style.get('outline_color', '&H00000000'),
            position=style.get('position', 'bottom')
        )
        
        # Burn captions
        result = self.burn_captions(video_path, str(ass_path), output_path)
        
        # Clean up temp file
        try:
            os.remove(ass_path)
        except:
            pass
        
        return result
