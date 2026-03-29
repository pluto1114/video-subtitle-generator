"""Video Subtitle Generator - A professional video subtitle generation tool."""

__version__ = "1.0.0"
__author__ = "Tech Team"

from .config import Config, QualityMode, AudioEnhanceProfile, VADProfile, SubtitleFormat
from .asr import ASREngine, MockASREngine, FasterWhisperEngine
from .subtitle import Subtitle, SubtitleSegment
from .processor import VideoProcessor
from .cache import ModelCache
from .config_manager import ConfigManager
from .audio import AudioProcessor

__all__ = [
    "Config",
    "QualityMode",
    "AudioEnhanceProfile",
    "VADProfile",
    "SubtitleFormat",
    "ASREngine",
    "MockASREngine",
    "FasterWhisperEngine",
    "Subtitle",
    "SubtitleSegment",
    "VideoProcessor",
    "ModelCache",
    "ConfigManager",
    "AudioProcessor",
]
