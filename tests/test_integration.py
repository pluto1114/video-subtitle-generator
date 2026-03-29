"""Integration tests for subtitle format generation."""

import pytest
import tempfile
from pathlib import Path
from video_subtitle.subtitle import Subtitle, SubtitleSegment
from video_subtitle.config import SubtitleFormat


class TestSubtitleFormatIntegration:
    """Integration tests for subtitle format generation."""

    def test_srt_format_complete_workflow(self):
        """Test complete SRT generation workflow."""
        subtitle = Subtitle(title="Integration Test")
        subtitle.add_segment(0, 3000, "First subtitle")
        subtitle.add_segment(3000, 6000, "Second subtitle")
        subtitle.add_segment(6000, 9000, "Third subtitle with multiple lines")

        srt_content = subtitle.to_srt()
        lines = srt_content.strip().split("\n")

        assert len(lines) == 11
        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:03,000"
        assert lines[2] == "First subtitle"
        assert lines[4] == "2"
        assert lines[5] == "00:00:03,000 --> 00:00:06,000"
        assert lines[6] == "Second subtitle"

    def test_ass_format_complete_workflow(self):
        """Test complete ASS generation workflow."""
        subtitle = Subtitle(title="ASS Integration Test")
        subtitle.add_segment(0, 3000, "First ASS subtitle")
        subtitle.add_segment(3000, 6000, "Second ASS subtitle")

        ass_content = subtitle.to_ass()

        assert "[Script Info]" in ass_content
        assert "Title: ASS Integration Test" in ass_content
        assert "[V4+ Styles]" in ass_content
        assert "Format: Name, Fontname, Fontsize" in ass_content
        assert "Style: Default,Arial,48" in ass_content
        assert "[Events]" in ass_content
        assert "Format: Layer, Start, End, Style" in ass_content
        assert "Dialogue: 0,0:00:00.00,0:00:03.00,Default,,0,0,0,,First ASS subtitle" in ass_content
        assert "Dialogue: 0,0:00:03.00,0:00:06.00,Default,,0,0,0,,Second ASS subtitle" in ass_content

    def test_srt_timestamp_format_compliance(self):
        """Test SRT timestamp format compliance."""
        segment = SubtitleSegment(start_ms=3661000, end_ms=3665500, text="Test")
        timestamp = segment.to_srt_timestamp()

        assert timestamp == "01:01:01,000"

        segment2 = SubtitleSegment(start_ms=123, end_ms=456, text="Test")
        timestamp2 = segment2.to_srt_timestamp()
        assert timestamp2 == "00:00:00,123"

    def test_ass_timestamp_format_compliance(self):
        """Test ASS timestamp format compliance."""
        segment = SubtitleSegment(start_ms=3661000, end_ms=3665500, text="Test")
        start, end = segment.to_ass_timestamp()

        assert start == "1:01:01.00"

        segment2 = SubtitleSegment(start_ms=123, end_ms=456, text="Test")
        start2, _ = segment2.to_ass_timestamp()
        assert start2 == "0:00:00.12"

    def test_srt_and_ass_timestamp_consistency(self):
        """Test that SRT and ASS timestamps represent same time values."""
        subtitle = Subtitle()
        subtitle.add_segment(123456, 789012, "Test segment")

        srt_content = subtitle.to_srt()
        ass_content = subtitle.to_ass()

        assert "00:02:03,456" in srt_content
        assert "0:02:03.45" in ass_content

    def test_srt_format_with_multiline_text(self):
        """Test SRT format handles multiline text."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "Line 1\nLine 2\nLine 3")

        srt_content = subtitle.to_srt()
        assert "Line 1\nLine 2\nLine 3" in srt_content

    def test_ass_format_with_multiline_text(self):
        """Test ASS format converts newlines properly."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "Line 1\nLine 2\nLine 3")

        ass_content = subtitle.to_ass()
        assert "Line 1\\NLine 2\\NLine 3" in ass_content

    def test_subtitle_with_many_segments(self):
        """Test subtitle with many segments."""
        subtitle = Subtitle(title="Long Subtitle")
        for i in range(100):
            start = i * 5000
            end = start + 4000
            subtitle.add_segment(start, end, f"Segment {i+1}")

        srt_content = subtitle.to_srt()
        ass_content = subtitle.to_ass()

        srt_lines = srt_content.strip().split("\n")
        assert len(srt_lines) == (100 * 4) - 1

        assert "Segment 1" in srt_content
        assert "Segment 100" in srt_content
        assert "Dialogue: 0," in ass_content
        assert "Segment 1" in ass_content

    def test_subtitle_format_enum_usage(self):
        """Test using SubtitleFormat enum."""
        assert SubtitleFormat.SRT.value == "srt"
        assert SubtitleFormat.ASS.value == "ass"

        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "Test")

        if SubtitleFormat.SRT == SubtitleFormat.SRT:
            content = subtitle.to_srt()
            assert "00:00:00,000" in content

    def test_empty_subtitle(self):
        """Test empty subtitle generation."""
        subtitle = Subtitle()

        srt_content = subtitle.to_srt()
        assert srt_content == ""

        ass_content = subtitle.to_ass()
        assert "[Script Info]" in ass_content
        assert "Dialogue:" not in ass_content
