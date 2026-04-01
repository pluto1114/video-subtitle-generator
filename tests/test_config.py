"""Tests for configuration module."""

import pytest
from video_subtitle.config import (
    Config,
    QualityMode,
    AudioEnhanceProfile,
    VADProfile,
    VADConfig,
    ModelConfig,
    SubtitleFormat,
)


class TestQualityMode:
    """Test QualityMode enum."""

    def test_quality_mode_values(self):
        """Test quality mode enum values."""
        assert QualityMode.PRO.value == "pro"
        assert QualityMode.QUALITY.value == "quality"
        assert QualityMode.BALANCED.value == "balanced"
        assert QualityMode.SPEED.value == "speed"


class TestAudioEnhanceProfile:
    """Test AudioEnhanceProfile enum."""

    def test_enhance_profile_values(self):
        """Test audio enhance profile enum values."""
        assert AudioEnhanceProfile.OFF.value == "off"
        assert AudioEnhanceProfile.VOICE.value == "voice"
        assert AudioEnhanceProfile.STRONG.value == "strong"


class TestVADProfile:
    """Test VADProfile enum."""

    def test_vad_profile_values(self):
        """Test VAD profile enum values."""
        assert VADProfile.VOICE_FOCUS.value == "voice_focus"
        assert VADProfile.BALANCED.value == "balanced"
        assert VADProfile.NOISE_ROBUST.value == "noise_robust"
        assert VADProfile.FAST.value == "fast"


class TestSubtitleFormat:
    """Test SubtitleFormat enum."""

    def test_subtitle_format_values(self):
        """Test subtitle format enum values."""
        assert SubtitleFormat.SRT.value == "srt"
        assert SubtitleFormat.ASS.value == "ass"


class TestVADConfig:
    """Test VADConfig dataclass."""

    def test_default_vad_config(self):
        """Test default VAD configuration."""
        config = VADConfig()
        assert config.voice_enhance_threshold == 0.3
        assert config.vad_min_silence_ms == 100
        assert config.vad_speech_pad_ms == 30
        assert config.vad_min_speech_ms == 50
        assert config.vad_max_speech_s == 40.0

    def test_custom_vad_config(self):
        """Test custom VAD configuration."""
        config = VADConfig(
            voice_enhance_threshold=0.3,
            vad_min_silence_ms=200,
            vad_speech_pad_ms=30,
            vad_min_speech_ms=100,
            vad_max_speech_s=20.0,
        )
        assert config.voice_enhance_threshold == 0.3
        assert config.vad_min_silence_ms == 200


class TestModelConfig:
    """Test ModelConfig dataclass."""

    def test_default_model_config(self):
        """Test default model configuration."""
        config = ModelConfig()
        assert config.model_name == "large-v3-turbo"
        assert config.device == "auto"
        assert config.compute_type == "float16"
        assert config.language == "auto"
        assert config.local_model_path is not None
        assert "models" in config.local_model_path
        assert "faster-whisper-large-v3-turbo" in config.local_model_path

    def test_custom_model_config(self):
        """Test custom model configuration."""
        config = ModelConfig(
            model_name="medium",
            device="cpu",
            language="en",
        )
        assert config.model_name == "medium"
        assert config.device == "cpu"
        assert config.language == "en"

    def test_model_config_with_nonexistent_model(self):
        """Test model config when model path doesn't exist."""
        config = ModelConfig(model_name="nonexistent-model")
        assert config.model_name == "nonexistent-model"
        assert config.local_model_path is None


class TestConfig:
    """Test Config dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.quality_mode == QualityMode.PRO
        assert config.audio_enhance_profile == AudioEnhanceProfile.OFF
        assert config.vad_profile == VADProfile.SENSITIVE
        assert config.subtitle_format == SubtitleFormat.SRT
        assert config.overwrite is False
        assert config.use_vad is False

    def test_apply_quality_mode_pro(self):
        """Test applying PRO quality mode."""
        config = Config()
        Config.apply_quality_mode(config, QualityMode.PRO)

        assert config.quality_mode == QualityMode.PRO
        assert config.vad_profile == VADProfile.SENSITIVE
        assert config.audio_enhance_profile == AudioEnhanceProfile.OFF
        assert config.vad_config.vad_min_speech_ms == 30
        assert config.vad_config.vad_max_speech_s == 60.0

    def test_apply_quality_mode_quality(self):
        """Test applying QUALITY quality mode."""
        config = Config()
        Config.apply_quality_mode(config, QualityMode.QUALITY)

        assert config.quality_mode == QualityMode.QUALITY
        assert config.vad_profile == VADProfile.BALANCED
        assert config.audio_enhance_profile == AudioEnhanceProfile.VOICE

    def test_apply_quality_mode_speed(self):
        """Test applying SPEED quality mode."""
        config = Config()
        Config.apply_quality_mode(config, QualityMode.SPEED)

        assert config.quality_mode == QualityMode.SPEED
        assert config.vad_profile == VADProfile.FAST
        assert config.audio_enhance_profile == AudioEnhanceProfile.OFF

    def test_apply_vad_profile_voice_focus(self):
        """Test applying VOICE_FOCUS VAD profile."""
        config = Config()
        Config.apply_vad_profile(config, VADProfile.VOICE_FOCUS)

        assert config.vad_profile == VADProfile.VOICE_FOCUS
        assert config.vad_config.voice_enhance_threshold == 0.3
        assert config.vad_config.vad_min_silence_ms == 200

    def test_apply_vad_profile_noise_robust(self):
        """Test applying NOISE_ROBUST VAD profile."""
        config = Config()
        Config.apply_vad_profile(config, VADProfile.NOISE_ROBUST)

        assert config.vad_profile == VADProfile.NOISE_ROBUST
        assert config.vad_config.voice_enhance_threshold == 0.7
        assert config.vad_config.vad_min_silence_ms == 400

    def test_voice_priority_template(self):
        """Test voice priority template."""
        config = Config.voice_priority_template()

        assert config.quality_mode == QualityMode.PRO
        assert config.audio_enhance_profile == AudioEnhanceProfile.OFF
        assert config.vad_profile == VADProfile.SENSITIVE
        assert config.vad_config.vad_min_speech_ms == 50
        assert config.vad_config.voice_enhance_threshold == 0.3

    def test_custom_config(self):
        """Test custom configuration."""
        config = Config(
            quality_mode=QualityMode.PRO,
            audio_enhance_profile=AudioEnhanceProfile.VOICE,
            subtitle_format=SubtitleFormat.ASS,
            output_dir="/tmp/output",
            overwrite=True,
        )

        assert config.quality_mode == QualityMode.PRO
        assert config.audio_enhance_profile == AudioEnhanceProfile.VOICE
        assert config.subtitle_format == SubtitleFormat.ASS
        assert config.output_dir == "/tmp/output"
        assert config.overwrite is True
