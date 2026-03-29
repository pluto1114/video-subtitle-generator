"""Audio processing module for extraction and enhancement."""

import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional
from .config import AudioEnhanceProfile


class AudioProcessor:
    """Handles audio extraction and enhancement from video files."""

    SUPPORTED_FORMATS = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"]

    def __init__(self):
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=False,
                encoding='utf-8',
                errors='replace',
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg is not installed or not in PATH")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg is not installed. Please install FFmpeg and add it to your PATH."
            )

    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> str:
        """Extract audio from video file.

        Args:
            video_path: Path to the video file
            output_path: Optional output path for the audio file
            sample_rate: Target sample rate (default: 16000Hz)
            channels: Number of audio channels (default: 1 for mono)

        Returns:
            Path to the extracted audio file
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = Path(temp_dir) / f"{video_path.stem}_audio.wav"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            str(sample_rate),
            "-ac",
            str(channels),
            "-y",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=False,
                encoding='utf-8',
                errors='replace',
            )
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio: {str(e)}")

        if not output_path.exists():
            raise RuntimeError("Audio extraction failed: output file not created")

        return str(output_path)

    def enhance_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        profile: AudioEnhanceProfile = AudioEnhanceProfile.VOICE,
    ) -> str:
        """Enhance audio using FFmpeg filters.

        Args:
            input_path: Path to input audio file
            output_path: Optional output path for enhanced audio
            profile: Audio enhancement profile to apply

        Returns:
            Path to the enhanced audio file
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Audio file not found: {input_path}")

        if output_path is None:
            temp_dir = tempfile.gettempdir()
            output_path = Path(temp_dir) / f"{input_path.stem}_enhanced.wav"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        filter_complex = self._build_filter_chain(profile)

        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-af",
            filter_complex,
            "-y",
            str(output_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=False,
                encoding='utf-8',
                errors='replace',
            )
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")
        except Exception as e:
            raise RuntimeError(f"Failed to enhance audio: {str(e)}")

        if not output_path.exists():
            raise RuntimeError("Audio enhancement failed: output file not created")

        return str(output_path)

    def _build_filter_chain(self, profile: AudioEnhanceProfile) -> str:
        """Build FFmpeg filter chain for audio enhancement."""
        if profile == AudioEnhanceProfile.OFF:
            return "anull"

        filters = []

        if profile in [AudioEnhanceProfile.VOICE, AudioEnhanceProfile.STRONG]:
            filters.append("highpass=f=60")
            filters.append("lowpass=f=4000")

        if profile == AudioEnhanceProfile.STRONG:
            filters.append("acompressor=threshold=0.089:ratio=6:attack=200:release=1000")
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
            filters.append("equalizer=f=200:width_type=o:width=2:g=3")
            filters.append("equalizer=f=1000:width_type=o:width=2:g=2")

        return ",".join(filters) if filters else "anull"

    def validate_audio_file(self, audio_path: str) -> bool:
        """Validate that an audio file exists and is readable."""
        path = Path(audio_path)
        if not path.exists():
            return False
        if not path.is_file():
            return False
        if path.stat().st_size == 0:
            return False
        return True

    def get_audio_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                check=False,
                encoding='utf-8',
                errors='replace',
            )
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe error: {result.stderr}")
            return float(result.stdout.strip())
        except Exception as e:
            raise RuntimeError(f"Failed to get audio duration: {str(e)}")
