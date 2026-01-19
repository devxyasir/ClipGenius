"""
ClipGenius - Video Processor
Handles video clipping, format conversion, and enhancement using FFmpeg
"""
import json
import os
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, List, Optional, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import (
    OUTPUT_WIDTH, OUTPUT_HEIGHT, OUTPUT_FPS, 
    OUTPUT_CODEC, AUDIO_CODEC, AUDIO_BITRATE,
    FFMPEG_PATH, FFPROBE_PATH
)


class VideoProcessor:
    """Processes videos: clipping, format conversion, enhancement."""
    
    def __init__(self, ffmpeg_path: str = None):
        """Initialize video processor.
        
        Args:
            ffmpeg_path: Path to ffmpeg executable. Uses FFMPEG_PATH from constants if not provided.
        """
        self.ffmpeg_path = ffmpeg_path or FFMPEG_PATH
        self.ffprobe_path = FFPROBE_PATH
        self._verify_ffmpeg()
        
        # Detect GPU for hardware encoding
        self.gpu_encoder = self._detect_gpu()
        if self.gpu_encoder:
            print(f"⚡ GPU detected! Using {self.gpu_encoder} for hardware encoding (3-5x faster)")
        else:
            print("💻 Using CPU encoding (libx264)")
    
    def _detect_gpu(self) -> Optional[str]:
        """Detect available GPU encoder.
        
        Returns:
            Encoder name (h264_nvenc, h264_amf, h264_qsv) or None for CPU
        """
        # Check for available encoders in order of preference
        encoders = [
            ('h264_nvenc', 'NVIDIA'),   # NVIDIA NVENC
            ('h264_amf', 'AMD'),        # AMD AMF
            ('h264_qsv', 'Intel'),      # Intel QuickSync
        ]
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-encoders'],
                capture_output=True,
                text=True
            )
            
            for encoder, gpu_name in encoders:
                if encoder in result.stdout:
                    # Verify encoder actually works
                    test = subprocess.run(
                        [self.ffmpeg_path, '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=1',
                         '-c:v', encoder, '-f', 'null', '-'],
                        capture_output=True,
                        timeout=10
                    )
                    if test.returncode == 0:
                        return encoder
        except Exception as e:
            print(f"GPU detection error: {e}")
        
        return None
    
    def _verify_ffmpeg(self) -> bool:
        """Verify FFmpeg is installed and accessible."""
        try:
            subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Warning: FFmpeg not found. Video processing may fail.")
            return False
    
    def _get_encoder_args(self, high_quality: bool = False) -> list:
        """Get encoder arguments based on GPU availability.
        
        Args:
            high_quality: Use higher quality settings
            
        Returns:
            List of FFmpeg arguments for video encoding
        """
        if self.gpu_encoder:
            # GPU encoding - use bitrate control
            bitrate = "8M" if high_quality else "5M"
            return ["-c:v", self.gpu_encoder, "-b:v", bitrate]
        else:
            # CPU encoding - use CRF for quality
            crf = "18" if high_quality else "23"
            return ["-c:v", OUTPUT_CODEC, "-preset", "fast", "-crf", crf]
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video metadata using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with duration, width, height, fps, etc.
        """
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            audio_stream = None
            for stream in data.get('streams', []):
                if stream['codec_type'] == 'video' and not video_stream:
                    video_stream = stream
                elif stream['codec_type'] == 'audio' and not audio_stream:
                    audio_stream = stream
            
            format_info = data.get('format', {})
            
            return {
                'duration': float(format_info.get('duration', 0)),
                'width': video_stream.get('width', 0) if video_stream else 0,
                'height': video_stream.get('height', 0) if video_stream else 0,
                'fps': self._parse_fps(video_stream.get('r_frame_rate', '30/1')) if video_stream else 30,
                'codec': video_stream.get('codec_name', '') if video_stream else '',
                'bitrate': int(format_info.get('bit_rate', 0)),
                'has_audio': audio_stream is not None,
                'audio_codec': audio_stream.get('codec_name', '') if audio_stream else ''
            }
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError, OSError) as e:
            print(f"DEBUG: get_video_info failed: {e}")
            return {'duration': 0, 'width': 0, 'height': 0, 'fps': 30, 'error': str(e)}
    
    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS from ffprobe format (e.g., '30/1')."""
        try:
            if '/' in fps_str:
                num, den = fps_str.split('/')
                return float(num) / float(den)
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 30.0
    
    def time_to_seconds(self, time_str: any) -> float:
        """Convert time string (MM:SS or HH:MM:SS) or number to seconds.
        
        Args:
            time_str: Time string or number
            
        Returns:
            Time in seconds
        """
        if isinstance(time_str, (int, float)):
            return float(time_str)
            
        try:
            time_str = str(time_str).strip()
            parts = time_str.split(':')
            parts = [float(p) for p in parts]
            
            if len(parts) == 2:
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 1:
                return parts[0]
        except Exception as e:
            print(f"Error parsing time '{time_str}': {e}")
            
        return 0
    
    def seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to time string (HH:MM:SS).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    def clip_video(
        self,
        input_path: str,
        output_path: str,
        start_time: str,
        end_time: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """Clip a segment from video.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            start_time: Start time (MM:SS or HH:MM:SS)
            end_time: End time (MM:SS or HH:MM:SS)
            progress_callback: Optional progress callback
            
        Returns:
            Path to clipped video
        """
        start_sec = self.time_to_seconds(start_time)
        end_sec = self.time_to_seconds(end_time)
        duration = end_sec - start_sec
        
        cmd = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-ss", str(start_sec),  # Start time (before input for faster seeking)
            "-i", input_path,
            "-t", str(duration),  # Duration
            "-c:v", OUTPUT_CODEC,
            "-pix_fmt", "yuv420p",  # Ensure compatibility
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
            "-preset", "fast",
            "-crf", "23",
            output_path
        ]
        
        # Validate paths
        if not os.path.exists(self.ffmpeg_path):
            raise RuntimeError(f"FFmpeg executable not found at: {self.ffmpeg_path}")
        
        if not os.path.exists(input_path):
            raise RuntimeError(f"Input video file not found at: {input_path}")

        print(f"DEBUG: Running FFmpeg command: {' '.join(cmd)}")
        
        try:
            # Use shell=True for Windows if needed, but usually better without if full path provided
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"FFmpeg stderr: {stderr}")
                raise RuntimeError(f"FFmpeg error: {stderr}")
            
            return output_path
        except FileNotFoundError:
             raise RuntimeError(f"Subprocess failed to find executable: {self.ffmpeg_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to clip video: {e}")
    
    def convert_to_vertical(
        self,
        input_path: str,
        output_path: str,
        blur_background: bool = True,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """Convert video to 9:16 vertical format for TikTok/Shorts.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            blur_background: If True, add blurred background for letterboxing
            progress_callback: Optional progress callback
            
        Returns:
            Path to converted video
        """
        # Get source dimensions
        info = self.get_video_info(input_path)
        src_width = info.get('width', 0)
        src_height = info.get('height', 0)
        
        print(f"DEBUG: Video dimensions: {src_width}x{src_height}")
        
        # If dimensions unknown or horizontal video, use blur background
        # Most videos are horizontal, so default to blur when uncertain
        is_horizontal = src_width > src_height or (src_width == 0 and src_height == 0)
        
        # Get encoder args (GPU or CPU)
        encoder_args = self._get_encoder_args()
        
        if blur_background and is_horizontal:
            # Create blurred background effect for horizontal videos
            # This is a COMPLEX filter (multiple inputs) - use -filter_complex
            filter_complex = (
                f"[0:v]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},boxblur=20:20[bg];"
                f"[0:v]scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
            )
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "0:a?",  # Map audio if exists (? = optional)
            ] + encoder_args + [
                "-pix_fmt", "yuv420p",
                "-c:a", AUDIO_CODEC,
                "-b:a", AUDIO_BITRATE,
                "-r", str(OUTPUT_FPS),
                output_path
            ]
        else:
            # Simple scale and pad - use regular -vf
            simple_filter = (
                f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
                f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
            )
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-i", input_path,
                "-vf", simple_filter,
            ] + encoder_args + [
                "-pix_fmt", "yuv420p",
                "-c:a", AUDIO_CODEC,
                "-b:a", AUDIO_BITRATE,
                "-r", str(OUTPUT_FPS),
                output_path
            ]
        
        print(f"DEBUG: Running vertical conversion: {' '.join(cmd)}")
        
        try:
            # text=True ensures stdout/stderr are strings, not bytes
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg conversion stderr: {e.stderr}")
            raise RuntimeError(f"Failed to convert video: {e.stderr}")
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to convert video subprocess error: {e}")
        except FileNotFoundError:
             raise RuntimeError(f"Subprocess failed to find executable: {self.ffmpeg_path}")
    
    def enhance_video(
        self,
        input_path: str,
        output_path: str,
        brightness: float = 0,
        contrast: float = 1,
        saturation: float = 1,
        sharpen: bool = True
    ) -> str:
        """Apply video enhancements.
        
        Args:
            input_path: Source video path
            output_path: Output video path
            brightness: Brightness adjustment (-1 to 1)
            contrast: Contrast multiplier (0.5 to 2)
            saturation: Saturation multiplier (0 to 2)
            sharpen: Apply sharpening filter
            
        Returns:
            Path to enhanced video
        """
        filters = []
        
        # Color adjustments
        eq_parts = []
        if brightness != 0:
            eq_parts.append(f"brightness={brightness}")
        if contrast != 1:
            eq_parts.append(f"contrast={contrast}")
        if saturation != 1:
            eq_parts.append(f"saturation={saturation}")
        
        if eq_parts:
            filters.append(f"eq={':'.join(eq_parts)}")
        
        # Sharpening
        if sharpen:
            filters.append("unsharp=5:5:1.0:5:5:0.0")
        
        if not filters:
            # No enhancements, just copy
            filters.append("null")
        
        filter_str = ",".join(filters)
        
        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-vf", filter_str,
            "-c:v", OUTPUT_CODEC,
            "-c:a", "copy",
            "-preset", "fast",
            "-crf", "23",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Failed to enhance video: {e}")
    
    def process_clips_batch(
        self,
        input_path: str,
        clips: List[dict],
        output_dir: str,
        vertical: bool = True,
        enhance: bool = True,
        max_workers: int = None,  # Auto-detect if None
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancel_check: Callable = None
    ) -> List[str]:
        """Process multiple clips in parallel using ThreadPoolExecutor.
        
        Args:
            input_path: Source video path
            clips: List of clip dictionaries with start_time, end_time, title
            output_dir: Output directory for clips
            vertical: Convert to 9:16 vertical format
            enhance: Apply video enhancement
            max_workers: Number of parallel workers (auto-detects CPU cores if None)
            progress_callback: Callback(completed, total, current_title)
            
        Returns:
            List of output file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect optimal worker count based on CPU cores
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            # Rule: (workers) x (2 threads per FFmpeg) <= CPU cores
            # So workers = CPU cores / 2, minimum 2, maximum 6
            max_workers = max(2, min(6, cpu_count // 2))
        
        print(f"🚀 Processing {len(clips)} clips with {max_workers} parallel workers")
        
        results = []
        total = len(clips)
        
        def process_single_clip(idx: int, clip: dict) -> Tuple[int, str]:
            title = clip.get('title', f'clip_{idx+1}')
            safe_title = self._sanitize_filename(title)
            start = clip.get('start_time', '0:00')
            end = clip.get('end_time', '1:00')
            
            print(f"📹 [{idx+1}/{total}] Processing clip: {title} ({start} - {end})")
            start_sec = self.time_to_seconds(start)
            end_sec = self.time_to_seconds(end)
            print(f"   ℹ️  Timestamps: {start} -> {start_sec}s, {end} -> {end_sec}s")
            
            try:
                # Step 1: Clip
                clip_path = output_dir / f"temp_{safe_title}.mp4"
                self.clip_video(input_path, str(clip_path), start, end)
                
                if not clip_path.exists() or clip_path.stat().st_size < 1000:
                    raise RuntimeError("Clip file is empty or too small (splitting failed)")
                    
                print(f"   ✓ Clipped: {safe_title}")
                
                # Step 2: Convert to vertical if needed
                if vertical:
                    vertical_path = output_dir / f"vertical_{safe_title}.mp4"
                    self.convert_to_vertical(str(clip_path), str(vertical_path))
                    os.remove(clip_path)
                    clip_path = vertical_path
                    print(f"   ✓ Converted to vertical: {safe_title}")
                
                # Step 3: Enhance if needed
                if enhance:
                    enhanced_path = output_dir / f"{safe_title}.mp4"
                    self.enhance_video(str(clip_path), str(enhanced_path))
                    os.remove(clip_path)
                    print(f"   ✓ Enhanced: {safe_title}")
                    return idx, str(enhanced_path)
                
                # Rename to final
                final_path = output_dir / f"{safe_title}.mp4"
                if clip_path != final_path:
                    os.rename(clip_path, final_path)
                print(f"   ✅ Complete: {safe_title}")
                return idx, str(final_path)
                
            except Exception as e:
                print(f"   ❌ Failed: {title} - {str(e)}")
                raise
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single_clip, i, clip): i 
                for i, clip in enumerate(clips)
            }
            
            completed = 0
            failed = 0
            for future in as_completed(futures):
                if cancel_check and cancel_check():
                    print("🛑 Processing cancelled by user")
                    executor.shutdown(wait=False, cancel_futures=True)
                    return []

                try:
                    idx, output_path = future.result()
                    results.append((idx, output_path))
                    completed += 1
                except Exception as e:
                    failed += 1
                    print(f"⚠️ Clip processing failed, continuing with others...")
                
                if progress_callback:
                    clip_idx = futures[future]
                    clip_title = clips[clip_idx].get('title', f'clip_{clip_idx+1}')
                    progress_callback(completed + failed, total, clip_title)
        
        print(f"✨ Batch complete: {completed} succeeded, {failed} failed")
        
        # Sort by original index and return paths
        results.sort(key=lambda x: x[0])
        return [path for _, path in results]
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize string for use as filename."""
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Limit length
        return name.strip()[:100]
