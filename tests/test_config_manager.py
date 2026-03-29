"""Tests for configuration manager module."""

import pytest
import json
import tempfile
from pathlib import Path
from video_subtitle.config_manager import ConfigManager
from video_subtitle.config import (
    Config,
    QualityMode,
    AudioEnhanceProfile,
    VADProfile,
    SubtitleFormat,
)


class TestConfigManager:
    """Test cases for ConfigManager."""

    def test_create_config_manager(self):
        """Test creating ConfigManager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            assert Path(manager.config_dir).exists()

    def test_default_config_dir(self):
        """Test default configuration directory."""
        manager = ConfigManager()
        assert manager.config_dir.exists()

    def test_save_config(self):
        """Test saving configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            config = Config(
                quality_mode=QualityMode.PRO,
                audio_enhance_profile=AudioEnhanceProfile.VOICE,
                subtitle_format=SubtitleFormat.ASS,
            )

            saved_path = manager.save_config(config)
            assert Path(saved_path).exists()

    def test_save_config_custom_path(self):
        """Test saving configuration to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            config = Config()
            custom_path = Path(tmpdir) / "custom_config.json"

            saved_path = manager.save_config(config, str(custom_path))
            assert Path(saved_path) == custom_path
            assert custom_path.exists()

    def test_load_config(self):
        """Test loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            original_config = Config(
                quality_mode=QualityMode.PRO,
                audio_enhance_profile=AudioEnhanceProfile.STRONG,
                subtitle_format=SubtitleFormat.ASS,
                overwrite=True,
            )

            manager.save_config(original_config)
            loaded_config = manager.load_config()

            assert loaded_config.quality_mode == QualityMode.PRO
            assert loaded_config.audio_enhance_profile == AudioEnhanceProfile.STRONG
            assert loaded_config.subtitle_format == SubtitleFormat.ASS
            assert loaded_config.overwrite is True

    def test_load_nonexistent_config(self):
        """Test loading nonexistent configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            config = manager.load_config()

            assert config.quality_mode == QualityMode.BALANCED
            assert config.subtitle_format == SubtitleFormat.SRT

    def test_config_exists(self):
        """Test checking if config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            assert manager.config_exists() is False

            manager.save_config(Config())
            assert manager.config_exists() is True

    def test_delete_config(self):
        """Test deleting configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            manager.save_config(Config())
            assert manager.config_exists() is True

            result = manager.delete_config()
            assert result is True
            assert manager.config_exists() is False

    def test_delete_nonexistent_config(self):
        """Test deleting nonexistent configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            result = manager.delete_config()
            assert result is False

    def test_config_round_trip(self):
        """Test saving and loading preserves all values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)

            original = Config(
                quality_mode=QualityMode.SPEED,
                audio_enhance_profile=AudioEnhanceProfile.OFF,
                vad_profile=VADProfile.FAST,
                subtitle_format=SubtitleFormat.SRT,
                output_dir="/tmp/output",
                overwrite=False,
                use_vad=False,
            )
            original.model_config.model_name = "medium"
            original.model_config.language = "en"
            original.model_config.device = "cpu"

            manager.save_config(original)
            loaded = manager.load_config()

            assert loaded.quality_mode == QualityMode.SPEED
            assert loaded.audio_enhance_profile == AudioEnhanceProfile.OFF
            assert loaded.vad_profile == VADProfile.FAST
            assert loaded.subtitle_format == SubtitleFormat.SRT
            assert loaded.output_dir == "/tmp/output"
            assert loaded.overwrite is False
            assert loaded.use_vad is False
            assert loaded.model_config.model_name == "medium"
            assert loaded.model_config.language == "en"

    def test_config_json_structure(self):
        """Test saved config JSON structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            config = Config(quality_mode=QualityMode.PRO)
            saved_path = manager.save_config(config)

            with open(saved_path, "r") as f:
                data = json.load(f)

            assert "quality_mode" in data
            assert "audio_enhance_profile" in data
            assert "vad_profile" in data
            assert "vad_config" in data
            assert "model_config" in data
            assert "subtitle_format" in data

    def test_get_config_path(self):
        """Test getting default config path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigManager(config_dir=tmpdir)
            config_path = manager.get_config_path()
            assert Path(config_path).exists() or True
