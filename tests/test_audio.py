"""Tests for audio processor module."""

import pytest
import tempfile
from pathlib import Path
from video_subtitle.audio import AudioProcessor
from video_subtitle.config import AudioEnhanceProfile


class TestAudioProcessor:
    """Test cases for AudioProcessor."""

    @pytest.fixture
    def processor(self):
        """Create AudioProcessor instance."""
        return AudioProcessor()

    def test_create_processor(self, processor):
        """Test creating AudioProcessor."""
        assert processor is not None

    def test_check_ffmpeg(self, processor):
        """Test FFmpeg availability check."""
        processor._check_ffmpeg()

    def test_validate_audio_file_nonexistent(self, processor):
        """Test validating nonexistent audio file."""
        assert processor.validate_audio_file("/nonexistent/file.wav") is False

    def test_validate_audio_file_directory(self, processor):
        """Test validating directory as audio file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert processor.validate_audio_file(tmpdir) is False

    def test_validate_audio_file_empty(self, processor):
        """Test validating empty audio file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            assert processor.validate_audio_file(temp_path) is False
        finally:
            Path(temp_path).unlink()

    def test_validate_audio_file_valid(self, processor):
        """Test validating valid audio file."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFF")
            temp_path = f.name

        try:
            assert processor.validate_audio_file(temp_path) is True
        finally:
            Path(temp_path).unlink()

    def test_extract_audio_nonexistent_video(self, processor):
        """Test extracting audio from nonexistent video."""
        with pytest.raises(FileNotFoundError):
            processor.extract_audio("/nonexistent/video.mp4")

    def test_extract_audio_with_output_path(self, processor):
        """Test extracting audio with custom output path."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video content")
            video_path = f.name

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "output.wav"
                with pytest.raises(RuntimeError):
                    processor.extract_audio(video_path, str(output_path))
        finally:
            Path(video_path).unlink()

    def test_enhance_audio_nonexistent_file(self, processor):
        """Test enhancing nonexistent audio file."""
        with pytest.raises(FileNotFoundError):
            processor.enhance_audio("/nonexistent/audio.wav")

    def test_enhance_audio_off_profile(self, processor):
        """Test enhancing audio with OFF profile."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"RIFFfake audio content")
            audio_path = f.name

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "enhanced.wav"
                with pytest.raises(RuntimeError):
                    processor.enhance_audio(
                        audio_path,
                        str(output_path),
                        AudioEnhanceProfile.OFF,
                    )
        finally:
            Path(audio_path).unlink()

    def test_build_filter_chain_off(self, processor):
        """Test building filter chain for OFF profile."""
        filter_chain = processor._build_filter_chain(AudioEnhanceProfile.OFF)
        assert filter_chain == "anull"

    def test_build_filter_chain_voice(self, processor):
        """Test building filter chain for VOICE profile."""
        filter_chain = processor._build_filter_chain(AudioEnhanceProfile.VOICE)
        assert "highpass" in filter_chain
        assert "lowpass" in filter_chain

    def test_build_filter_chain_strong(self, processor):
        """Test building filter chain for STRONG profile."""
        filter_chain = processor._build_filter_chain(AudioEnhanceProfile.STRONG)
        assert "highpass" in filter_chain
        assert "lowpass" in filter_chain
        assert "acompressor" in filter_chain
        assert "loudnorm" in filter_chain

    def test_get_audio_duration_nonexistent(self, processor):
        """Test getting duration of nonexistent audio file."""
        with pytest.raises(RuntimeError):
            processor.get_audio_duration("/nonexistent/file.wav")
