"""Command-line interface for Video Subtitle Generator."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import (
    Config,
    QualityMode,
    AudioEnhanceProfile,
    VADProfile,
    SubtitleFormat,
)
from .processor import VideoProcessor
from .config_manager import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="video-subtitle",
        description="Generate subtitles from video files using AI speech recognition",
    )

    parser.add_argument(
        "videos",
        nargs="+",
        help="Video file(s) to process",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        help="Output directory for subtitle files",
    )

    parser.add_argument(
        "-f",
        "--format",
        dest="subtitle_format",
        choices=["srt", "ass"],
        default="srt",
        help="Subtitle output format (default: srt)",
    )

    parser.add_argument(
        "-m",
        "--model",
        dest="model_name",
        default="large-v3-turbo",
        help="ASR model name (default: large-v3-turbo)",
    )

    parser.add_argument(
        "--model-path",
        dest="model_path",
        default=None,
        help="Local model path (default: models folder in project root)",
    )

    parser.add_argument(
        "-l",
        "--language",
        dest="language",
        default="auto",
        help="Language code (default: auto)",
    )

    parser.add_argument(
        "-q",
        "--quality",
        dest="quality_mode",
        choices=["pro", "quality", "balanced", "speed"],
        default="balanced",
        help="Quality mode preset (default: balanced)",
    )

    parser.add_argument(
        "--audio-enhance",
        dest="audio_enhance",
        choices=["off", "voice", "strong"],
        default="off",
        help="Audio enhancement profile (default: off)",
    )

    parser.add_argument(
        "--vad-profile",
        dest="vad_profile",
        choices=["voice_focus", "balanced", "noise_robust", "fast", "sensitive", "ultra_sensitive"],
        default="balanced",
        help="VAD profile (default: balanced)",
    )

    parser.add_argument(
        "--no-vad",
        dest="use_vad",
        action="store_false",
        default=None,
        help="Disable VAD (Voice Activity Detection)",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing subtitle files",
    )

    parser.add_argument(
        "--device",
        dest="device",
        default="cuda",
        help="Device to use for inference (default: cuda)",
    )

    parser.add_argument(
        "--save-config",
        dest="save_config",
        action="store_true",
        help="Save current configuration as default",
    )

    parser.add_argument(
        "--load-config",
        dest="load_config",
        metavar="PATH",
        help="Load configuration from file",
    )

    parser.add_argument(
        "--standard-mode",
        dest="voice_priority",
        action="store_true",
        help="Use standard mode instead of voice priority template",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args(args)


def create_config_from_args(args: argparse.Namespace) -> Config:
    """Create Config object from parsed arguments."""
    # 默认使用人声优先模板
    use_voice_priority = not args.voice_priority
    
    if use_voice_priority:
        config = Config.voice_priority_template()
        # 人声优先模板已经设置了所有参数，不需要再应用预设
    else:
        config = Config()
        # 如果用户显式指定了参数，才应用预设
        if args.quality_mode:
            config.quality_mode = QualityMode(args.quality_mode)
            Config.apply_quality_mode(config, config.quality_mode)
        if args.vad_profile:
            config.vad_profile = VADProfile(args.vad_profile)
            Config.apply_vad_profile(config, config.vad_profile)
        if args.audio_enhance:
            config.audio_enhance_profile = AudioEnhanceProfile(args.audio_enhance)
            Config.apply_audio_enhance_profile(config, config.audio_enhance_profile)
    
    local_model_path = args.model_path
    
    # 覆盖基础配置
    config.subtitle_format = SubtitleFormat(args.subtitle_format)
    config.model_config.model_name = args.model_name
    config.model_config.language = args.language
    config.model_config.device = args.device
    config.output_dir = args.output_dir
    config.overwrite = args.overwrite
    
    # use_vad 参数优先级最高
    if args.use_vad is not None:
        config.use_vad = args.use_vad
    
    if local_model_path:
        config.model_config.local_model_path = local_model_path
    
    return config


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point for CLI."""
    parsed_args = parse_args(args)

    if parsed_args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config_manager = ConfigManager()

        if parsed_args.load_config:
            config = config_manager.load_config(parsed_args.load_config)
            logger.info(f"Loaded configuration from: {parsed_args.load_config}")
        else:
            config = create_config_from_args(parsed_args)

        if parsed_args.save_config:
            config_manager.save_config(config)
            logger.info(f"Configuration saved to: {config_manager.get_config_path()}")

        video_paths = [Path(v).resolve() for v in parsed_args.videos]

        for video_path in video_paths:
            if not video_path.exists():
                logger.error(f"Video file not found: {video_path}")
                return 1

        processor = VideoProcessor(config)

        def progress_callback(stage: str, progress: float):
            print(f"\r[{stage}] {progress:.1f}%", end="", flush=True)

        processor.set_progress_callback(progress_callback)

        if len(video_paths) == 1:
            subtitle = processor.process_video(str(video_paths[0]))
            output_path = processor.save_subtitle(
                subtitle,
                parsed_args.output_dir or str(video_paths[0].parent),
                video_path=str(video_paths[0]),
            )
            print(f"\nSubtitle saved to: {output_path}")
        else:
            output_dir = parsed_args.output_dir or str(video_paths[0].parent)
            results = processor.process_batch(
                [str(p) for p in video_paths],
                output_dir=output_dir,
            )
            print(f"\nProcessed {len(results)} videos:")
            for video_path, subtitle_path in results:
                print(f"  {Path(video_path).name} -> {Path(subtitle_path).name}")

        return 0

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except FileExistsError as e:
        logger.error(str(e))
        return 1
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
