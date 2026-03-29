"""Tests for ASR engines."""

import pytest
from video_subtitle.asr import MockASREngine, FasterWhisperEngine
from video_subtitle.subtitle import Subtitle


class TestMockASREngine:
    """Test cases for MockASREngine."""

    def test_create_mock_engine(self):
        """Test creating mock ASR engine."""
        engine = MockASREngine()
        assert engine.model_loaded is False

    def test_load_model(self):
        """Test loading mock model."""
        engine = MockASREngine()
        engine.load_model()
        assert engine.model_loaded is True

    def test_transcribe_without_load(self):
        """Test transcription without explicit model load."""
        engine = MockASREngine()
        subtitle = engine.transcribe("/fake/path.wav")

        assert isinstance(subtitle, Subtitle)
        assert len(subtitle.segments) == 2
        assert subtitle.title == "Mock Subtitle"

    def test_transcribe_with_language(self):
        """Test transcription with language parameter."""
        engine = MockASREngine()
        subtitle = engine.transcribe("/fake/path.wav", language="en")

        assert len(subtitle.segments) == 2
        assert subtitle.segments[0].text == "This is a mock subtitle segment for testing."

    def test_detect_language(self):
        """Test language detection."""
        engine = MockASREngine()
        language = engine.detect_language("/fake/path.wav")
        assert language == "en"

    def test_transcribe_segments_valid(self):
        """Test that transcribed segments are valid."""
        engine = MockASREngine()
        subtitle = engine.transcribe("/fake/path.wav")

        for segment in subtitle.segments:
            assert segment.validate() is True
            assert segment.duration() > 0


class TestFasterWhisperEngine:
    """Test cases for FasterWhisperEngine."""

    def test_create_engine(self):
        """Test creating Faster Whisper engine."""
        engine = FasterWhisperEngine(
            model_name="tiny",
            device="cpu",
            compute_type="int8",
        )
        assert engine.model_name == "tiny"
        assert engine.device == "cpu"
        assert engine.compute_type == "int8"
        assert engine.model is None

    def test_default_engine_config(self):
        """Test default engine configuration."""
        engine = FasterWhisperEngine()
        assert engine.model_name == "large-v3-turbo"
        assert engine.device == "cuda"
        assert engine.compute_type == "float16"

    @pytest.mark.skip(reason="Requires actual model download")
    def test_load_model(self):
        """Test loading actual model (skipped in CI)."""
        engine = FasterWhisperEngine(model_name="tiny", device="cpu")
        engine.load_model()
        assert engine.model is not None

    @pytest.mark.skip(reason="Requires actual model download")
    def test_transcribe_real(self):
        """Test real transcription (skipped in CI)."""
        engine = FasterWhisperEngine(model_name="tiny", device="cpu")
        subtitle = engine.transcribe("/fake/path.wav")
        assert isinstance(subtitle, Subtitle)
