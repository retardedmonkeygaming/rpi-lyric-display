import re
from typing import List, Tuple


class LRCParser:
    """Parses .lrc content into precise timestamped 16x2 LCD display blocks."""

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """Converts [mm:ss.xx], [m:s.x], or [mm:ss:xx] to float seconds."""
        try:
            cleaned = timestamp_str.strip("[]")
            parts = cleaned.replace(":", ".").split(".")
            
            minutes = float(parts[0])
            seconds = float(parts[1]) if len(parts) > 1 else 0.0
            
            # Handle fraction/milliseconds
            fraction = 0.0
            if len(parts) > 2 and parts[2]:
                frac_str = parts[2]
                fraction = float(frac_str) / (10 ** len(frac_str))

            return round(minutes * 60 + seconds + fraction, 2)
        except (ValueError, IndexError):
            return -1.0

    @classmethod
    def split_to_16_chars(cls, text: str) -> Tuple[str, str]:
        """
        Splits text into line1 (<=16 chars) and line2 (<=16 chars).
        Ensures words are preserved across lines without deleting any text.
        """
        text = text.strip()
        if not text:
            return "", ""

        if len(text) <= 16:
            return text, ""

        words = text.split()
        line1_words = []
        line2_words = []
        current_len = 0

        # Build Line 1 word by word
        for word in words:
            word_len = len(word)
            added_len = word_len if not line1_words else word_len + 1

            if current_len + added_len <= 16:
                line1_words.append(word)
                current_len += added_len
            else:
                line2_words.append(word)

        line1 = " ".join(line1_words)
        line2 = " ".join(line2_words)

        # If a single word on Line 1 exceeds 16 chars, force slice it
        if not line1:
            line1 = text[:16]
            line2 = text[16:32]
        else:
            line2 = line2[:16]

        return line1, line2

    @classmethod
    def parse_lrc_content(cls, lrc_text: str) -> List[Tuple[float, str, str]]:
        """
        Parses LRC content, ignoring header tags ([ti:], [ar:], etc.)
        and accurately splitting lines for 1602 LCD displays.
        """
        # Matches any bracketed time tag: [00:12.34], [0:12], [00:12:34]
        time_tag_regex = re.compile(r"\[\d{1,2}:\d{2}(?:[\.:]\d{1,3})?\]")
        raw_entries = []

        for line in lrc_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            # Skip metadata lines like [ti:...], [ar:...], [length:...]
            if re.match(r"^\[[a-zA-Z]+:", line_str):
                continue

            # Find all timestamps on this line (supports inline/multiple tags)
            timestamps = time_tag_regex.findall(line_str)
            if not timestamps:
                continue

            # Strip out timestamp tags to extract the actual lyric text
            lyric_text = time_tag_regex.sub("", line_str).strip()

            for ts_tag in timestamps:
                ts_val = cls.parse_timestamp(ts_tag)
                if ts_val >= 0.0:
                    raw_entries.append((ts_val, lyric_text))

        # Sort chronologically by timestamp
        raw_entries.sort(key=lambda x: x[0])

        parsed_lyrics = []
        for timestamp, lyric in raw_entries:
            line1, line2 = cls.split_to_16_chars(lyric)
            parsed_lyrics.append((timestamp, line1, line2))

        return parsed_lyrics