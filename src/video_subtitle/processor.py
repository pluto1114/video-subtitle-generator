"""Main video processor that orchestrates the subtitle generation pipeline."""

import logging
import time
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
        self._start_time: Optional[float] = None
        self._last_progress_time: Optional[float] = None

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
        current_time = time.time()
        
        if progress == 0.0:
            self._start_time = current_time
            self._last_progress_time = current_time
        
        if self.progress_callback:
            elapsed_str = ""
            if self._start_time and progress > 0:
                elapsed = current_time - self._start_time
                if progress < 100:
                    estimated_total = elapsed / (progress / 100)
                    remaining = estimated_total - elapsed
                    if remaining > 60:
                        elapsed_str = f" | 已用：{elapsed:.0f}s | 剩余：{remaining:.0f}s"
                    else:
                        elapsed_str = f" | 已用：{elapsed:.0f}s | 剩余：{remaining:.0f}s"
                else:
                    elapsed_str = f" | 总耗时：{elapsed:.0f}s"
            
            stage_with_time = f"{stage}{elapsed_str}"
            self.progress_callback(stage_with_time, progress)
            self._last_progress_time = current_time

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

        logger.info(f"🎬 开始处理视频：{video_path.name}")
        self._report_progress("📋 准备处理", 0.0)

        temp_audio_path = None
        enhanced_audio_path = None

        try:
            self._report_progress("🎵 提取音频", 10.0)
            logger.info("正在从视频中提取音频...")
            temp_audio_path = self.audio_processor.extract_audio(str(video_path))
            logger.info(f"✅ 音频提取完成：{Path(temp_audio_path).name}")

            self._report_progress("🔊 音频增强", 20.0)
            if (
                self.config.audio_enhance_profile
                and self.config.audio_enhance_profile != "off"
            ):
                logger.info(f"正在应用音频增强配置：{self.config.audio_enhance_profile.value}")
                enhanced_audio_path = self.audio_processor.enhance_audio(
                    temp_audio_path, profile=self.config.audio_enhance_profile
                )
                audio_path = enhanced_audio_path
                logger.info(f"✅ 音频增强完成")
            else:
                audio_path = temp_audio_path
                logger.info("⏭️ 跳过音频增强")

            self._report_progress("🎙️ 加载模型", 30.0)
            if self.asr_engine is None:
                logger.info("正在加载语音识别模型...")
                self._load_asr_engine()
                logger.info("✅ 模型加载完成")

            self._report_progress("🗣️ 语音识别", 40.0)
            subtitle = self.asr_engine.transcribe(
                audio_path,
                language=self.config.model_config.language,
                model_path=self.config.model_config.local_model_path,
            )
            logger.info(f"✅ 语音识别完成，生成 {len(subtitle.segments)} 条字幕")

            self._report_progress("✨ 后处理", 80.0)
            logger.info("正在优化字幕时间轴...")
            self._post_process_subtitle(subtitle)
            logger.info("✅ 后处理完成")

            self._report_progress("💾 保存结果", 90.0)
            logger.info("准备保存字幕文件...")

            self._report_progress("✅ 全部完成", 100.0)
            return subtitle

        except Exception as e:
            logger.error(f"❌ 处理失败：{e}")
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
        
        logger.info(f"正在初始化 ASR 引擎：{engine_type}")
        logger.info(f"模型名称：{self.config.model_config.model_name}")
        logger.info(f"设备：{self.config.model_config.device}")
        
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
        logger.info(f"✅ ASR 引擎初始化成功：{engine_type}")

    def _post_process_subtitle(self, subtitle: Subtitle) -> None:
        """Apply post-processing to the subtitle."""
        logger.info("正在修复时间轴...")
        subtitle.fix_timestamps()
        
        logger.info("正在分割长片段...")
        added_count = subtitle.split_long_segments(max_duration_ms=4000, preferred_duration_ms=2500)
        if added_count > 0:
            logger.info(f"分割了 {added_count} 条长片段")
        
        logger.info("正在移除无效片段...")
        subtitle.remove_invalid_segments(min_duration_ms=30, min_text_length=0)
        
        logger.info("正在移除拟声词片段...")
        removed_count = subtitle.remove_onomatopoeia_segments()
        if removed_count > 0:
            logger.info(f"移除了 {removed_count} 条拟声词片段")
        else:
            logger.info("无需移除拟声词片段")
        
        if not subtitle.validate_timestamps():
            logger.warning("⚠️ 字幕时间轴验证失败")

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
            logger.info(f"正在生成 SRT 格式字幕...")
        elif fmt == SubtitleFormat.ASS:
            content = subtitle.to_ass()
            logger.info(f"正在生成 ASS 格式字幕...")
        else:
            raise ValueError(f"Unknown subtitle format: {fmt}")

        logger.info(f"正在写入文件：{output_path.name}")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ 字幕已保存：{output_path}")
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
        
        logger.info(f"🎬 开始批量处理，共 {total} 个视频文件")

        for i, video_path in enumerate(video_paths):
            logger.info(f"📹 处理进度：{i + 1}/{total} - {Path(video_path).name}")
            self._report_progress(f"📹 处理中：{i + 1}/{total}", (i / total) * 100)

            subtitle = self.process_video(video_path)

            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path(video_path).parent

            subtitle_path = self.save_subtitle(
                subtitle, str(output_path), video_path=video_path
            )
            results.append((video_path, subtitle_path))
            logger.info(f"✅ 已完成 {i + 1}/{total}")

        self._report_progress("✅ 批量处理完成", 100.0)
        logger.info(f"🎉 批量处理完成，共处理 {len(results)} 个文件")
        return results
