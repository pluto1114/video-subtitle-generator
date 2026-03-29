"""Main video processor that orchestrates the subtitle generation pipeline."""

import logging
from pathlib import Path
from typing import Optional, Callable
from .config import Config, SubtitleFormat
from .subtitle import Subtitle
from .asr import ASREngine
from .audio import AudioProcessor
from .cache import ModelCache

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Main processor for generating subtitles from video files."""

    def __init__(self, config: Config):
        """Initialize the video processor.

        Args:
            config: Configuration for subtitle generation
        """
        self.config = config
        self.audio_processor = AudioProcessor()
        self.model_cache = ModelCache()
        self.asr_engine: Optional[ASREngine] = None
        self.progress_callback: Optional[Callable[[str, float], None]] = None

    def set_progress_callback(
        self, callback: Optional[Callable[[str, float], None]]
    ) -> None:
        """Set a callback function for progress updates.

        Args:
            callback: Function that takes (stage_name, progress_percentage)
        """
        self.progress_callback = callback

    def _report_progress(self, stage: str, progress: float) -> None:
        """Report progress to callback if set."""
        if self.progress_callback:
            self.progress_callback(stage, progress)

    def process_video(self, video_path: str) -> Subtitle:
        """Process a single video file and generate subtitles.

        Args:
            video_path: Path to the video file

        Returns:
            Generated Subtitle object
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Processing video: {video_path}")
        self._report_progress("准备", 0.0)

        temp_audio_path = None
        enhanced_audio_path = None

        try:
            self._report_progress("提取音频", 10.0)
            temp_audio_path = self.audio_processor.extract_audio(str(video_path))
            logger.info(f"Audio extracted to: {temp_audio_path}")

            self._report_progress("音频增强", 20.0)
            if (
                self.config.audio_enhance_profile
                and self.config.audio_enhance_profile != "off"
            ):
                enhanced_audio_path = self.audio_processor.enhance_audio(
                    temp_audio_path, profile=self.config.audio_enhance_profile
                )
                audio_path = enhanced_audio_path
                logger.info(f"Audio enhanced: {enhanced_audio_path}")
            else:
                audio_path = temp_audio_path
                logger.info("Skipping audio enhancement")

            self._report_progress("语音识别", 30.0)
            if self.asr_engine is None:
                self._load_asr_engine()

            subtitle = self.asr_engine.transcribe(
                audio_path,
                language=self.config.model_config.language,
                model_path=self.config.model_config.local_model_path,
            )
            logger.info(f"Transcription completed with {len(subtitle.segments)} segments")

            self._report_progress("后处理", 80.0)
            self._post_process_subtitle(subtitle)

            self._report_progress("完成", 100.0)
            return subtitle

        except Exception as e:
            logger.error(f"Error processing video: {e}")
            raise
        finally:
            self._cleanup_temp_files(temp_audio_path, enhanced_audio_path)

    def _load_asr_engine(self) -> None:
        """Load the ASR engine based on configuration."""
        engine_type = "faster_whisper"
        
        vad_parameters = {
            "min_silence_duration_ms": self.config.vad_config.vad_min_silence_ms,
            "speech_pad_ms": self.config.vad_config.vad_speech_pad_ms,
            "min_speech_duration_ms": self.config.vad_config.vad_min_speech_ms,
            "max_speech_duration_s": self.config.vad_config.vad_max_speech_s,
        } if self.config.use_vad else {}
        
        self.asr_engine = self.model_cache.get_or_load(
            engine_type=engine_type,
            model_name=self.config.model_config.model_name,
            device=self.config.model_config.device,
            compute_type=self.config.model_config.compute_type,
            local_model_path=self.config.model_config.local_model_path,
            vad_filter=self.config.use_vad,
            vad_parameters=vad_parameters if self.config.use_vad else None,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            length_penalty=1.0,
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,
            condition_on_previous_text=False,
            prompt_reset_on_temperature=0.5,
        )
        logger.info(f"ASR engine loaded: {engine_type}")

    def _post_process_subtitle(self, subtitle: Subtitle) -> None:
        """Apply post-processing to the subtitle."""
        subtitle.fix_timestamps()
        subtitle.remove_invalid_segments(min_duration_ms=30, min_text_length=0)
        removed_count = subtitle.remove_onomatopoeia_segments()
        logger.info(f"Removed {removed_count} onomatopoeia segments")
        if not subtitle.validate_timestamps():
            logger.warning("Subtitle timestamps validation failed after fixing")

    def _cleanup_temp_files(
        self, *paths: Optional[str]
    ) -> None:
        """Clean up temporary files."""
        for path in paths:
            if path and Path(path).exists():
                try:
                    Path(path).unlink()
                    logger.debug(f"Cleaned up temp file: {path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {path}: {e}")

    def save_subtitle(
        self,
        subtitle: Subtitle,
        output_path: str,
        subtitle_format: Optional[SubtitleFormat] = None,
        video_path: Optional[str] = None,
    ) -> str:
        """Save subtitle to file.

        Args:
            subtitle: Subtitle object to save
            output_path: Output file path (directory or full path)
            subtitle_format: Subtitle format (SRT or ASS)
            video_path: Optional video path to derive filename from

        Returns:
            Path to the saved subtitle file
        """
        output_path = Path(output_path)

        if output_path.is_dir():
            if video_path:
                base_name = Path(video_path).stem
            else:
                base_name = output_path.name
            fmt = subtitle_format or self.config.subtitle_format
            output_path = output_path / f"{base_name}.{fmt.value}"

        if output_path.exists() and not self.config.overwrite:
            raise FileExistsError(
                f"Output file already exists: {output_path}. Use overwrite=True to override."
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = subtitle_format or self.config.subtitle_format
        if fmt == SubtitleFormat.SRT:
            content = subtitle.to_srt()
        elif fmt == SubtitleFormat.ASS:
            content = subtitle.to_ass()
        else:
            raise ValueError(f"Unknown subtitle format: {fmt}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Subtitle saved to: {output_path}")
        return str(output_path)

    def process_batch(
        self,
        video_paths: list[str],
        output_dir: Optional[str] = None,
    ) -> list[tuple[str, str]]:
        """Process multiple video files.

        Args:
            video_paths: List of video file paths
            output_dir: Optional output directory for all subtitles

        Returns:
            List of tuples (video_path, subtitle_path)
        """
        results = []
        total = len(video_paths)

        for i, video_path in enumerate(video_paths):
            logger.info(f"Processing {i + 1}/{total}: {video_path}")
            self._report_progress(f"处理中 {i + 1}/{total}", (i / total) * 100)

            subtitle = self.process_video(video_path)

            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path(video_path).parent

            subtitle_path = self.save_subtitle(
                subtitle, str(output_path), video_path=video_path
            )
            results.append((video_path, subtitle_path))

        self._report_progress("批量处理完成", 100.0)
        return results
