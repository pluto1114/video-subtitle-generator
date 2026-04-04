"""Tests for video processor module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from video_subtitle.processor import VideoProcessor
from video_subtitle.config import Config, SubtitleFormat, QualityMode
from video_subtitle.subtitle import Subtitle


class TestVideoProcessor:
    """Test cases for VideoProcessor."""

    @pytest.fixture
    def config(self):
        """Create default configuration."""
        return Config()

    @pytest.fixture
    def processor(self, config):
        """Create VideoProcessor instance."""
        return VideoProcessor(config)

    def test_create_processor(self, processor):
        """Test creating VideoProcessor."""
        assert processor is not None
        assert processor.asr_engine is None

    def test_process_video_nonexistent_file(self, processor):
        """Test processing nonexistent video file."""
        with pytest.raises(FileNotFoundError):
            processor.process_video("/nonexistent/video.mp4")

    def test_process_video_mock(self, config):
        """Test processing video with mock ASR."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "test.mp4"
            video_path.write_bytes(b"fake video content")

            processor = VideoProcessor(config)

            mock_subtitle = Subtitle(title="Mock")
            mock_subtitle.add_segment(0, 5000, "Test segment")

            with patch.object(processor, "_load_asr_engine"):
                with patch.object(processor.audio_processor, 'extract_audio') as mock_extract:
                    mock_extract.return_value = str(Path(tmpdir) / "audio.wav")
                    
                    with patch.object(processor.audio_processor, 'enhance_audio') as mock_enhance:
                        mock_enhance.return_value = str(Path(tmpdir) / "audio.wav")

                        with patch.object(processor, 'asr_engine') as mock_engine:
                            mock_engine.transcribe.return_value = mock_subtitle

                            subtitle = processor.process_video(str(video_path))

                            assert isinstance(subtitle, Subtitle)
                            assert len(subtitle.segments) == 1

    def test_set_progress_callback(self, processor):
        """Test setting progress callback."""
        callback = Mock()
        processor.set_progress_callback(callback)
        assert processor.progress_callback == callback

    def test_report_progress(self, processor):
        """Test reporting progress."""
        callback = Mock()
        processor.set_progress_callback(callback)

        processor._report_progress("测试阶段", 50.0)

        callback.assert_called_once_with("测试阶段", 50.0)

    def test_report_progress_no_callback(self, processor):
        """Test reporting progress without callback."""
        processor._report_progress("测试阶段", 50.0)

    def test_save_subtitle_srt(self, processor):
        """Test saving subtitle in SRT format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subtitle = Subtitle(title="Test")
            subtitle.add_segment(0, 5000, "Hello")

            output_path = Path(tmpdir) / "test.srt"
            saved_path = processor.save_subtitle(
                subtitle,
                str(output_path),
                SubtitleFormat.SRT,
            )

            assert Path(saved_path).exists()
            content = Path(saved_path).read_text(encoding="utf-8")
            assert "00:00:00,000 --> 00:00:05,000" in content
            assert "Hello" in content

    def test_save_subtitle_ass(self, processor):
        """Test saving subtitle in ASS format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subtitle = Subtitle(title="Test ASS")
            subtitle.add_segment(0, 5000, "Hello")

            output_path = Path(tmpdir) / "test.ass"
            saved_path = processor.save_subtitle(
                subtitle,
                str(output_path),
                SubtitleFormat.ASS,
            )

            assert Path(saved_path).exists()
            content = Path(saved_path).read_text(encoding="utf-8")
            assert "[Script Info]" in content
            assert "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Hello" in content

    def test_save_subtitle_overwrite(self, processor):
        """Test saving subtitle with overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subtitle = Subtitle(title="Test")
            subtitle.add_segment(0, 5000, "Hello")

            output_path = Path(tmpdir) / "test.srt"
            output_path.write_text("existing content")

            processor.config.overwrite = True
            saved_path = processor.save_subtitle(
                subtitle,
                str(output_path),
                SubtitleFormat.SRT,
            )

            content = Path(saved_path).read_text(encoding="utf-8")
            assert "existing content" not in content

    def test_save_subtitle_no_overwrite(self, processor):
        """Test saving subtitle without overwrite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subtitle = Subtitle(title="Test")
            subtitle.add_segment(0, 5000, "Hello")

            output_path = Path(tmpdir) / "test.srt"
            output_path.write_text("existing content")

            with pytest.raises(FileExistsError):
                processor.save_subtitle(
                    subtitle,
                    str(output_path),
                    SubtitleFormat.SRT,
                )

    def test_save_subtitle_directory_output(self, processor):
        """Test saving subtitle to directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subtitle = Subtitle(title="Test")
            subtitle.add_segment(0, 5000, "Hello")
            
            video_path = Path(tmpdir) / "test_video.mp4"
            video_path.touch()

            saved_path = processor.save_subtitle(
                subtitle,
                tmpdir,
                SubtitleFormat.SRT,
                video_path=str(video_path),
            )

            assert Path(saved_path).exists()
            assert saved_path.endswith(".srt")
            assert "test_video.srt" in saved_path

    def test_post_process_subtitle(self, processor):
        """Test post-processing subtitle."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "First")
        subtitle.add_segment(4000, 10000, "Second")

        processor._post_process_subtitle(subtitle)

        assert subtitle.validate_timestamps() is True
        assert subtitle.segments[1].start_ms == 5000

    def test_cleanup_temp_files(self, processor):
        """Test cleaning up temporary files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        assert Path(temp_path).exists()
        processor._cleanup_temp_files(temp_path)
        assert not Path(temp_path).exists()

    def test_cleanup_temp_files_nonexistent(self, processor):
        """Test cleaning up nonexistent files."""
        processor._cleanup_temp_files("/nonexistent/file")

    def test_process_batch(self, config):
        """Test batch processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video1 = Path(tmpdir) / "video1.mp4"
            video2 = Path(tmpdir) / "video2.mp4"
            video1.write_bytes(b"fake video 1")
            video2.write_bytes(b"fake video 2")

            processor = VideoProcessor(config)

            mock_subtitle = Subtitle(title="Mock")
            mock_subtitle.add_segment(0, 5000, "Test")

            with patch.object(processor, "process_video", return_value=mock_subtitle):
                with patch.object(processor, "save_subtitle") as mock_save:
                    mock_save.return_value = str(Path(tmpdir) / "output.srt")

                    results = processor.process_batch(
                        [str(video1), str(video2)],
                        output_dir=tmpdir,
                    )

                    assert len(results) == 2
                    assert processor.process_video.call_count == 2

    def test_load_asr_engine(self, config):
        """Test loading ASR engine."""
        processor = VideoProcessor(config)

        with patch.object(processor.model_cache, 'get_or_load') as mock_load:
            mock_engine = Mock()
            mock_load.return_value = mock_engine

            processor._load_asr_engine()

            assert processor.asr_engine is mock_engine
            mock_load.assert_called_once()
