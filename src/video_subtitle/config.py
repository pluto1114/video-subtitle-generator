"""Configuration module for video subtitle generator."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QualityMode(str, Enum):
    """Quality mode presets for subtitle generation."""

    PRO = "pro"
    QUALITY = "quality"
    BALANCED = "balanced"
    SPEED = "speed"


class AudioEnhanceProfile(str, Enum):
    """Audio enhancement profiles."""

    OFF = "off"
    VOICE = "voice"
    STRONG = "strong"


class VADProfile(str, Enum):
    """VAD (Voice Activity Detection) profiles."""

    VOICE_FOCUS = "voice_focus"
    BALANCED = "balanced"
    NOISE_ROBUST = "noise_robust"
    FAST = "fast"
    SENSITIVE = "sensitive"
    ULTRA_SENSITIVE = "ultra_sensitive"


class SubtitleFormat(str, Enum):
    """Subtitle output formats."""

    SRT = "srt"
    ASS = "ass"


@dataclass
class VADConfig:
    """VAD configuration settings."""

    voice_enhance_threshold: float = 0.3
    vad_min_silence_ms: int = 100
    vad_speech_pad_ms: int = 30
    vad_min_speech_ms: int = 50
    vad_max_speech_s: float = 40.0


@dataclass
class ModelConfig:
    """ASR model configuration."""

    model_name: str = "large-v3-turbo"
    local_model_path: Optional[str] = None
    device: str = "auto"
    compute_type: str = "float16"
    language: str = "auto"

    @staticmethod
    def get_model_download_info(model_name: str = "large-v3-turbo") -> dict:
        """Get download information for faster-whisper models."""
        models_info = {
            "large-v3-turbo": {
                "huggingface": "https://huggingface.co/Systran/faster-whisper-large-v3-turbo",
                "modelscope": "https://modelscope.cn/models/OpenAI/whisper",
                "github_release": "https://github.com/SYSTRAN/faster-whisper/releases",
                "description": "Faster Whisper Large V3 Turbo - 平衡速度和精度的推荐模型",
            },
            "large-v3": {
                "huggingface": "https://huggingface.co/Systran/faster-whisper-large-v3",
                "modelscope": "https://modelscope.cn/models/OpenAI/whisper",
                "github_release": "https://github.com/SYSTRAN/faster-whisper/releases",
                "description": "Faster Whisper Large V3 - 精度最高的模型",
            },
            "medium": {
                "huggingface": "https://huggingface.co/Systran/faster-whisper-medium",
                "modelscope": "https://modelscope.cn/models/OpenAI/whisper",
                "github_release": "https://github.com/SYSTRAN/faster-whisper/releases",
                "description": "Faster Whisper Medium - 中等规模模型",
            },
            "small": {
                "huggingface": "https://huggingface.co/Systran/faster-whisper-small",
                "modelscope": "https://modelscope.cn/models/OpenAI/whisper",
                "github_release": "https://github.com/SYSTRAN/faster-whisper/releases",
                "description": "Faster Whisper Small - 轻量级模型",
            },
            "base": {
                "huggingface": "https://huggingface.co/Systran/faster-whisper-base",
                "modelscope": "https://modelscope.cn/models/OpenAI/whisper",
                "github_release": "https://github.com/SYSTRAN/faster-whisper/releases",
                "description": "Faster Whisper Base - 基础模型",
            },
            "tiny": {
                "huggingface": "https://huggingface.co/Systran/faster-whisper-tiny",
                "modelscope": "https://modelscope.cn/models/OpenAI/whisper",
                "github_release": "https://github.com/SYSTRAN/faster-whisper/releases",
                "description": "Faster Whisper Tiny - 最小模型",
            },
        }
        return models_info.get(model_name, models_info["large-v3-turbo"])

    def __post_init__(self):
        """Set default local model path if not provided."""
        if self.local_model_path is None:
            import os
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            default_model_path = project_root / "models" / f"faster-whisper-{self.model_name}"
            if default_model_path.exists():
                self.local_model_path = str(default_model_path)


@dataclass
class Config:
    """Main configuration for video subtitle generation."""

    quality_mode: QualityMode = QualityMode.PRO
    audio_enhance_profile: AudioEnhanceProfile = AudioEnhanceProfile.OFF
    vad_profile: VADProfile = VADProfile.SENSITIVE
    vad_config: VADConfig = field(default_factory=VADConfig)
    model_config: ModelConfig = field(default_factory=ModelConfig)
    output_dir: Optional[str] = None
    subtitle_format: SubtitleFormat = SubtitleFormat.SRT
    overwrite: bool = False
    use_vad: bool = False

    @classmethod
    def apply_quality_mode(cls, config: "Config", mode: QualityMode) -> "Config":
        """Apply quality mode preset to configuration."""
        if mode == QualityMode.PRO:
            config.vad_profile = VADProfile.SENSITIVE
            config.audio_enhance_profile = AudioEnhanceProfile.OFF
            config.vad_config.vad_min_speech_ms = 30
            config.vad_config.vad_max_speech_s = 60.0
            config.vad_config.voice_enhance_threshold = 0.2
            config.vad_config.vad_min_silence_ms = 50
            config.vad_config.vad_speech_pad_ms = 40
            config.use_vad = False
        elif mode == QualityMode.QUALITY:
            config.vad_profile = VADProfile.BALANCED
            config.audio_enhance_profile = AudioEnhanceProfile.VOICE
            config.vad_config.vad_min_speech_ms = 50
            config.vad_config.vad_max_speech_s = 40.0
        elif mode == QualityMode.SPEED:
            config.vad_profile = VADProfile.FAST
            config.audio_enhance_profile = AudioEnhanceProfile.OFF
            config.vad_config.vad_min_speech_ms = 100
            config.vad_config.vad_max_speech_s = 30.0

        config.quality_mode = mode
        return config

    @classmethod
    def apply_vad_profile(cls, config: "Config", profile: VADProfile) -> "Config":
        """Apply VAD profile preset to configuration."""
        if profile == VADProfile.VOICE_FOCUS:
            config.vad_config.voice_enhance_threshold = 0.3
            config.vad_config.vad_min_silence_ms = 200
            config.vad_config.vad_speech_pad_ms = 30
            config.vad_config.vad_min_speech_ms = 100
            config.vad_config.vad_max_speech_s = 20.0
        elif profile == VADProfile.BALANCED:
            config.vad_config.voice_enhance_threshold = 0.3
            config.vad_config.vad_min_silence_ms = 100
            config.vad_config.vad_speech_pad_ms = 30
            config.vad_config.vad_min_speech_ms = 50
            config.vad_config.vad_max_speech_s = 40.0
        elif profile == VADProfile.NOISE_ROBUST:
            config.vad_config.voice_enhance_threshold = 0.7
            config.vad_config.vad_min_silence_ms = 400
            config.vad_config.vad_speech_pad_ms = 10
            config.vad_config.vad_min_speech_ms = 300
            config.vad_config.vad_max_speech_s = 30.0
        elif profile == VADProfile.FAST:
            config.vad_config.voice_enhance_threshold = 0.6
            config.vad_config.vad_min_silence_ms = 150
            config.vad_config.vad_speech_pad_ms = 15
            config.vad_config.vad_min_speech_ms = 100
            config.vad_config.vad_max_speech_s = 30.0
        elif profile == VADProfile.SENSITIVE:
            config.vad_config.voice_enhance_threshold = 0.2
            config.vad_config.vad_min_silence_ms = 50
            config.vad_config.vad_speech_pad_ms = 40
            config.vad_config.vad_min_speech_ms = 30
            config.vad_config.vad_max_speech_s = 60.0
            config.use_vad = False
        elif profile == VADProfile.ULTRA_SENSITIVE:
            config.vad_config.voice_enhance_threshold = 0.01
            config.vad_config.vad_min_silence_ms = 50
            config.vad_config.vad_speech_pad_ms = 100
            config.vad_config.vad_min_speech_ms = 10
            config.vad_config.vad_max_speech_s = 25.0

        config.vad_profile = profile
        return config

    @classmethod
    def apply_audio_enhance_profile(
        cls, config: "Config", profile: AudioEnhanceProfile
    ) -> "Config":
        """Apply audio enhance profile preset to configuration."""
        config.audio_enhance_profile = profile
        return config

    @classmethod
    def voice_priority_template(cls) -> "Config":
        """Create a configuration with voice priority template (deprecated - now uses default config)."""
        # 注意：此方法已弃用，因为默认配置已使用优化后的参数
        return cls()
