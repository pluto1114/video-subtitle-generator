"""Tests for CLI module."""

import pytest
import tempfile
from pathlib import Path
from video_subtitle.cli import parse_args, create_config_from_args, main
from video_subtitle.config import QualityMode, AudioEnhanceProfile, SubtitleFormat


class TestParseArgs:
    """Test command-line argument parsing."""

    def test_basic_args(self):
        """Test parsing basic arguments."""
        args = parse_args(["video.mp4"])
        assert args.videos == ["video.mp4"]
        assert args.subtitle_format == "srt"
        assert args.quality_mode == "balanced"

    def test_multiple_videos(self):
        """Test parsing multiple video files."""
        args = parse_args(["video1.mp4", "video2.mkv"])
        assert len(args.videos) == 2
        assert args.videos == ["video1.mp4", "video2.mkv"]

    def test_output_dir(self):
        """Test parsing output directory."""
        args = parse_args(["video.mp4", "-o", "/tmp/output"])
        assert args.output_dir == "/tmp/output"

    def test_subtitle_format(self):
        """Test parsing subtitle format."""
        args = parse_args(["video.mp4", "-f", "ass"])
        assert args.subtitle_format == "ass"

    def test_model_name(self):
        """Test parsing model name."""
        args = parse_args(["video.mp4", "-m", "medium"])
        assert args.model_name == "medium"

    def test_language(self):
        """Test parsing language."""
        args = parse_args(["video.mp4", "-l", "en"])
        assert args.language == "en"

    def test_quality_mode(self):
        """Test parsing quality mode."""
        args = parse_args(["video.mp4", "-q", "pro"])
        assert args.quality_mode == "pro"

    def test_audio_enhance(self):
        """Test parsing audio enhance profile."""
        args = parse_args(["video.mp4", "--audio-enhance", "strong"])
        assert args.audio_enhance == "strong"

    def test_vad_profile(self):
        """Test parsing VAD profile."""
        args = parse_args(["video.mp4", "--vad-profile", "voice_focus"])
        assert args.vad_profile == "voice_focus"

    def test_no_vad(self):
        """Test parsing --no-vad flag."""
        args = parse_args(["video.mp4", "--no-vad"])
        assert args.use_vad is False

    def test_overwrite(self):
        """Test parsing overwrite flag."""
        args = parse_args(["video.mp4", "--overwrite"])
        assert args.overwrite is True

    def test_device(self):
        """Test parsing device."""
        args = parse_args(["video.mp4", "--device", "cpu"])
        assert args.device == "cpu"

    def test_verbose(self):
        """Test parsing verbose flag."""
        args = parse_args(["video.mp4", "-v"])
        assert args.verbose is True

    def test_save_config(self):
        """Test parsing save-config flag."""
        args = parse_args(["video.mp4", "--save-config"])
        assert args.save_config is True

    def test_load_config(self):
        """Test parsing load-config option."""
        args = parse_args(["video.mp4", "--load-config", "/path/to/config.json"])
        assert args.load_config == "/path/to/config.json"


class TestCreateConfigFromArgs:
    """Test configuration creation from arguments."""

    def test_default_config(self):
        """Test creating default configuration."""
        args = parse_args(["video.mp4"])
        config = create_config_from_args(args)

        assert config.quality_mode == QualityMode.BALANCED
        assert config.subtitle_format == SubtitleFormat.SRT

    def test_custom_config(self):
        """Test creating custom configuration."""
        args = parse_args([
            "video.mp4",
            "-q", "pro",
            "-f", "ass",
            "-l", "en",
            "--audio-enhance", "strong",
            "--overwrite",
        ])
        config = create_config_from_args(args)

        assert config.quality_mode == QualityMode.PRO
        assert config.subtitle_format == SubtitleFormat.ASS
        assert config.model_config.language == "en"
        assert config.overwrite is True


class TestMain:
    """Test main CLI function."""

    def test_main_with_nonexistent_file(self):
        """Test CLI with nonexistent video file."""
        result = main(["nonexistent.mp4"])
        assert result == 1

    def test_main_help(self):
        """Test CLI help message."""
        with pytest.raises(SystemExit):
            main(["--help"])

    def test_main_no_args(self):
        """Test CLI with no arguments."""
        with pytest.raises(SystemExit):
            main([])
