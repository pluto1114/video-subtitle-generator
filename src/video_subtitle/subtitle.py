"""Subtitle module for handling subtitle segments and formatting."""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SubtitleSegment:
    """Represents a single subtitle segment."""

    start_ms: int
    end_ms: int
    text: str
    speaker: Optional[str] = None

    def to_srt_timestamp(self) -> str:
        """Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm)."""
        return self._ms_to_srt_time(self.start_ms)

    def to_ass_timestamp(self) -> tuple[str, str]:
        """Convert milliseconds to ASS timestamp format (H:MM:SS.cc)."""
        start = self._ms_to_ass_time(self.start_ms)
        end = self._ms_to_ass_time(self.end_ms)
        return start, end

    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        """Convert milliseconds to SRT time format."""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @staticmethod
    def _ms_to_ass_time(ms: int) -> str:
        """Convert milliseconds to ASS time format (H:MM:SS.cc)."""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        centiseconds = milliseconds // 10
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def validate(self) -> bool:
        """Validate the segment has valid timestamps."""
        return self.start_ms >= 0 and self.end_ms > self.start_ms

    def duration(self) -> int:
        """Return segment duration in milliseconds."""
        return self.end_ms - self.start_ms


@dataclass
class Subtitle:
    """Represents a complete subtitle with multiple segments."""

    segments: List[SubtitleSegment] = field(default_factory=list)
    title: Optional[str] = None

    def add_segment(
        self, start_ms: int, end_ms: int, text: str, speaker: Optional[str] = None
    ) -> None:
        """Add a new subtitle segment."""
        segment = SubtitleSegment(
            start_ms=start_ms, end_ms=end_ms, text=text, speaker=speaker
        )
        self.segments.append(segment)

    def to_srt(self) -> str:
        """Convert subtitle to SRT format string."""
        lines = []
        for i, segment in enumerate(self.segments, start=1):
            lines.append(str(i))
            lines.append(
                f"{segment.to_srt_timestamp()} --> {self._ms_to_srt_time(segment.end_ms)}"
            )
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines)

    def to_ass(self) -> str:
        """Convert subtitle to ASS format string."""
        header = self._generate_ass_header()
        events = self._generate_events()
        return f"{header}\n{events}"

    def _generate_ass_header(self) -> str:
        """Generate ASS file header with Script Info and Styles."""
        return """[Script Info]
Title: {title}
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
Timer: 100.0000

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""".format(
            title=self.title or "Video Subtitle"
        )

    def _generate_events(self) -> str:
        """Generate ASS Events section."""
        lines = []
        for segment in self.segments:
            start, end = segment.to_ass_timestamp()
            text = segment.text.replace("\n", "\\N")
            lines.append(
                f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
            )
        return "\n".join(lines)

    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        """Convert milliseconds to SRT time format."""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def validate_timestamps(self) -> bool:
        """Validate all timestamps are monotonically increasing and valid."""
        if not self.segments:
            return True

        prev_end = 0
        for segment in self.segments:
            if not segment.validate():
                return False
            if segment.start_ms < prev_end:
                return False
            prev_end = segment.end_ms

        return True

    def fix_timestamps(self) -> None:
        """Fix timestamp issues to ensure monotonic increase."""
        if not self.segments:
            return

        prev_end = 0
        for i, segment in enumerate(self.segments):
            if segment.start_ms < prev_end:
                segment.start_ms = prev_end
            if segment.end_ms <= segment.start_ms:
                segment.end_ms = segment.start_ms + max(1000, int((segment.end_ms - segment.start_ms) * 10))
            prev_end = segment.end_ms

    def remove_invalid_segments(self, min_duration_ms: int = 50, min_text_length: int = 0) -> None:
        """Remove segments that are truly invalid.
        
        Args:
            min_duration_ms: Minimum segment duration in milliseconds
            min_text_length: Minimum text length (0 means keep all segments even if empty)
        """
        valid_segments = []
        for segment in self.segments:
            duration = segment.duration()
            text_len = len(segment.text.strip())
            
            if duration >= min_duration_ms and text_len >= min_text_length:
                valid_segments.append(segment)
        
        self.segments = valid_segments

    def remove_onomatopoeia_segments(self) -> int:
        """Remove onomatopoeia and non-speech segments.
        
        This filters out:
        - Repeated characters (e.g., "啊啊啊啊啊", "えええええ")
        - Single character repetitions lasting too long
        - Non-linguistic vocal sounds
        - Consecutive repeated short utterances
        
        Returns:
            Number of removed segments
        """
        import re
        
        valid_segments = []
        removed_count = 0
        prev_text = None
        prev_duration = 0
        consecutive_count = 0
        
        for segment in self.segments:
            text = segment.text.strip()
            duration = segment.duration()
            
            if not text:
                valid_segments.append(segment)
                prev_text = None
                consecutive_count = 0
                continue
            
            is_onomatopoeia = False
            
            # 只过滤极端长的重复（单字符重复 100 次以上，非常罕见）
            repeated_char_pattern = r'^(.)\1{99,}$'
            if re.match(repeated_char_pattern, text):
                is_onomatopoeia = True
                logger.debug(f"Removed repeated char: {text[:50]}...")
            
            # 只过滤极端长的重复短语（1-2 字符短语重复 50 次以上）
            repeated_pattern = r'^(.{1,2})\1{49,}$'
            if re.match(repeated_pattern, text):
                is_onomatopoeia = True
                logger.debug(f"Removed repeated pattern: {text[:50]}...")
            
            # 只过滤超长时段（>120 秒）且字符种类极少（<=2）的片段
            if duration > 120000 and len(set(text)) <= 2:
                is_onomatopoeia = True
                logger.debug(f"Removed long duration with few chars: {text}")
            
            # 只过滤大量重复标点（100 个以上）且字符种类极少（<=2）的片段
            comma_count = text.count('、') + text.count('，')
            if comma_count >= 100 and len(set(text.replace('、', '').replace('，', ''))) <= 2:
                is_onomatopoeia = True
                logger.debug(f"Removed repeated commas: {text[:50]}...")
            
            # 只过滤连续重复 50 次以上的短片段
            if prev_text and text == prev_text and duration < 2000:
                consecutive_count += 1
                if consecutive_count >= 50:
                    is_onomatopoeia = True
                    logger.debug(f"Removed consecutive repeat: {text}")
            else:
                consecutive_count = 0
            
            if not is_onomatopoeia:
                valid_segments.append(segment)
            else:
                removed_count += 1
            
            prev_text = text
            prev_duration = duration
        
        self.segments = valid_segments
        return removed_count

    def get_hash(self) -> str:
        """Generate a hash for the subtitle content."""
        content = "".join(
            f"{s.start_ms}{s.end_ms}{s.text}" for s in self.segments
        )
        return hashlib.md5(content.encode()).hexdigest()
