"""Configuration persistence module."""

import json
import os
from pathlib import Path
from typing import Optional
from .config import (
    Config,
    QualityMode,
    AudioEnhanceProfile,
    VADProfile,
    SubtitleFormat,
    VADConfig,
    ModelConfig,
)


class ConfigManager:
    """Manages configuration persistence and loading."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_dir: Directory to store configuration files
        """
        if config_dir is None:
            config_dir = Path.home() / ".video_subtitle"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.default_config_path = self.config_dir / "default_config.json"

    def save_config(self, config: Config, path: Optional[str] = None) -> str:
        """Save configuration to file.

        Args:
            config: Configuration to save
            path: Optional file path (defaults to default config path)

        Returns:
            Path to the saved configuration file
        """
        save_path = Path(path) if path else self.default_config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = self._config_to_dict(config)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)

        return str(save_path)

    def load_config(self, path: Optional[str] = None) -> Config:
        """Load configuration from file.

        Args:
            path: Optional file path (defaults to default config path)

        Returns:
            Loaded Configuration object
        """
        load_path = Path(path) if path else self.default_config_path

        if not load_path.exists():
            return Config()

        with open(load_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        return self._dict_to_config(config_dict)

    def _config_to_dict(self, config: Config) -> dict:
        """Convert Config object to dictionary."""
        return {
            "quality_mode": config.quality_mode.value,
            "audio_enhance_profile": config.audio_enhance_profile.value,
            "vad_profile": config.vad_profile.value,
            "vad_config": {
                "voice_enhance_threshold": config.vad_config.voice_enhance_threshold,
                "vad_min_silence_ms": config.vad_config.vad_min_silence_ms,
                "vad_speech_pad_ms": config.vad_config.vad_speech_pad_ms,
                "vad_min_speech_ms": config.vad_config.vad_min_speech_ms,
                "vad_max_speech_s": config.vad_config.vad_max_speech_s,
            },
            "model_config": {
                "model_name": config.model_config.model_name,
                "local_model_path": config.model_config.local_model_path,
                "device": config.model_config.device,
                "compute_type": config.model_config.compute_type,
                "language": config.model_config.language,
            },
            "output_dir": config.output_dir,
            "subtitle_format": config.subtitle_format.value,
            "overwrite": config.overwrite,
            "use_vad": config.use_vad,
            "language": config.language,
        }

    def _dict_to_config(self, config_dict: dict) -> Config:
        """Convert dictionary to Config object."""
        vad_config = VADConfig(
            voice_enhance_threshold=config_dict.get("vad_config", {}).get(
                "voice_enhance_threshold", 0.5
            ),
            vad_min_silence_ms=config_dict.get("vad_config", {}).get(
                "vad_min_silence_ms", 250
            ),
            vad_speech_pad_ms=config_dict.get("vad_config", {}).get(
                "vad_speech_pad_ms", 20
            ),
            vad_min_speech_ms=config_dict.get("vad_config", {}).get(
                "vad_min_speech_ms", 250
            ),
            vad_max_speech_s=config_dict.get("vad_config", {}).get(
                "vad_max_speech_s", 30.0
            ),
        )

        model_config = ModelConfig(
            model_name=config_dict.get("model_config", {}).get(
                "model_name", "large-v3-turbo"
            ),
            local_model_path=config_dict.get("model_config", {}).get(
                "local_model_path"
            ),
            device=config_dict.get("model_config", {}).get("device", "cuda"),
            compute_type=config_dict.get("model_config", {}).get(
                "compute_type", "float16"
            ),
            language=config_dict.get("model_config", {}).get("language", "auto"),
        )

        config = Config(
            quality_mode=QualityMode(
                config_dict.get("quality_mode", QualityMode.BALANCED.value)
            ),
            audio_enhance_profile=AudioEnhanceProfile(
                config_dict.get("audio_enhance_profile", AudioEnhanceProfile.OFF.value)
            ),
            vad_profile=VADProfile(
                config_dict.get("vad_profile", VADProfile.BALANCED.value)
            ),
            vad_config=vad_config,
            model_config=model_config,
            output_dir=config_dict.get("output_dir"),
            subtitle_format=SubtitleFormat(
                config_dict.get("subtitle_format", SubtitleFormat.SRT.value)
            ),
            overwrite=config_dict.get("overwrite", False),
            use_vad=config_dict.get("use_vad", True),
            language=config_dict.get("language"),
        )

        return config

    def get_config_path(self) -> str:
        """Get the default configuration file path."""
        return str(self.default_config_path)

    def config_exists(self) -> bool:
        """Check if default configuration file exists."""
        return self.default_config_path.exists()

    def delete_config(self, path: Optional[str] = None) -> bool:
        """Delete configuration file.

        Args:
            path: Optional file path (defaults to default config path)

        Returns:
            True if file was deleted, False if it didn't exist
        """
        delete_path = Path(path) if path else self.default_config_path

        if delete_path.exists():
            delete_path.unlink()
            return True
        return False
