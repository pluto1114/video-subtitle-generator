"""Tests for subtitle module."""

import pytest
from video_subtitle.subtitle import Subtitle, SubtitleSegment


class TestSubtitleSegment:
    """Test cases for SubtitleSegment class."""

    def test_create_segment(self):
        """Test creating a subtitle segment."""
        segment = SubtitleSegment(
            start_ms=1000,
            end_ms=5000,
            text="Hello World",
        )
        assert segment.start_ms == 1000
        assert segment.end_ms == 5000
        assert segment.text == "Hello World"
        assert segment.speaker is None

    def test_create_segment_with_speaker(self):
        """Test creating a subtitle segment with speaker."""
        segment = SubtitleSegment(
            start_ms=0,
            end_ms=3000,
            text="Speaker 1: Hello",
            speaker="Speaker 1",
        )
        assert segment.speaker == "Speaker 1"

    def test_to_srt_timestamp(self):
        """Test SRT timestamp conversion."""
        segment = SubtitleSegment(start_ms=0, end_ms=5000, text="Test")
        assert segment.to_srt_timestamp() == "00:00:00,000"

        segment2 = SubtitleSegment(start_ms=123456, end_ms=5000, text="Test")
        assert segment2.to_srt_timestamp() == "00:02:03,456"

        segment3 = SubtitleSegment(start_ms=3661000, end_ms=5000, text="Test")
        assert segment3.to_srt_timestamp() == "01:01:01,000"

    def test_to_ass_timestamp(self):
        """Test ASS timestamp conversion."""
        segment = SubtitleSegment(start_ms=0, end_ms=5000, text="Test")
        start, end = segment.to_ass_timestamp()
        assert start == "0:00:00.00"

        segment2 = SubtitleSegment(start_ms=123456, end_ms=5000, text="Test")
        start2, _ = segment2.to_ass_timestamp()
        assert start2 == "0:02:03.45"

    def test_validate(self):
        """Test segment validation."""
        valid_segment = SubtitleSegment(start_ms=1000, end_ms=5000, text="Test")
        assert valid_segment.validate() is True

        invalid_segment = SubtitleSegment(start_ms=5000, end_ms=1000, text="Test")
        assert invalid_segment.validate() is False

        negative_segment = SubtitleSegment(start_ms=-1000, end_ms=5000, text="Test")
        assert negative_segment.validate() is False

    def test_duration(self):
        """Test segment duration calculation."""
        segment = SubtitleSegment(start_ms=1000, end_ms=5000, text="Test")
        assert segment.duration() == 4000


class TestSubtitle:
    """Test cases for Subtitle class."""

    def test_create_subtitle(self):
        """Test creating an empty subtitle."""
        subtitle = Subtitle()
        assert subtitle.segments == []
        assert subtitle.title is None

    def test_add_segment(self):
        """Test adding segments to subtitle."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "First segment")
        assert len(subtitle.segments) == 1
        assert subtitle.segments[0].text == "First segment"

        subtitle.add_segment(5000, 10000, "Second segment")
        assert len(subtitle.segments) == 2

    def test_to_srt(self):
        """Test SRT format conversion."""
        subtitle = Subtitle(title="Test Subtitle")
        subtitle.add_segment(0, 5000, "Hello")
        subtitle.add_segment(5000, 10000, "World")

        srt_content = subtitle.to_srt()
        lines = srt_content.strip().split("\n")

        assert lines[0] == "1"
        assert lines[1] == "00:00:00,000 --> 00:00:05,000"
        assert lines[2] == "Hello"
        assert lines[4] == "2"
        assert lines[5] == "00:00:05,000 --> 00:00:10,000"
        assert lines[6] == "World"

    def test_to_ass(self):
        """Test ASS format conversion."""
        subtitle = Subtitle(title="Test ASS")
        subtitle.add_segment(0, 5000, "Hello")
        subtitle.add_segment(5000, 10000, "World")

        ass_content = subtitle.to_ass()

        assert "[Script Info]" in ass_content
        assert "[V4+ Styles]" in ass_content
        assert "[Events]" in ass_content
        assert "Title: Test ASS" in ass_content
        assert "Dialogue: 0,0:00:00.00,0:00:05.00,Default,,0,0,0,,Hello" in ass_content
        assert "Dialogue: 0,0:00:05.00,0:00:10.00,Default,,0,0,0,,World" in ass_content

    def test_validate_timestamps_empty(self):
        """Test timestamp validation with empty subtitle."""
        subtitle = Subtitle()
        assert subtitle.validate_timestamps() is True

    def test_validate_timestamps_valid(self):
        """Test timestamp validation with valid segments."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "First")
        subtitle.add_segment(5000, 10000, "Second")
        assert subtitle.validate_timestamps() is True

    def test_validate_timestamps_overlapping(self):
        """Test timestamp validation with overlapping segments."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "First")
        subtitle.add_segment(4000, 10000, "Second")
        assert subtitle.validate_timestamps() is False

    def test_fix_timestamps(self):
        """Test timestamp fixing."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "First")
        subtitle.add_segment(4000, 10000, "Second")

        subtitle.fix_timestamps()

        assert subtitle.segments[1].start_ms == 5000
        assert subtitle.validate_timestamps() is True

    def test_get_hash(self):
        """Test subtitle hash generation."""
        subtitle1 = Subtitle()
        subtitle1.add_segment(0, 5000, "Hello")

        subtitle2 = Subtitle()
        subtitle2.add_segment(0, 5000, "Hello")

        subtitle3 = Subtitle()
        subtitle3.add_segment(0, 5000, "World")

        assert subtitle1.get_hash() == subtitle2.get_hash()
        assert subtitle1.get_hash() != subtitle3.get_hash()

    def test_ass_newlines_handling(self):
        """Test ASS format handles newlines in text."""
        subtitle = Subtitle()
        subtitle.add_segment(0, 5000, "Line 1\nLine 2")

        ass_content = subtitle.to_ass()
        assert "\\N" in ass_content
