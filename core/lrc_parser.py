import re
from typing import List, Tuple

class LRCParser:
    """Parses .lrc strings and formats lyrics into 16x2 LCD dual-line blocks."""

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """Converts [mm:ss.xx] or [mm:ss:xx] format into total seconds float."""
        try:
            parts = timestamp_str.strip("[]").split(":")
            minutes = float(parts[0])
            seconds_parts = parts[1].split(".")
            seconds = float(seconds_parts[0])
            hundredths = float(seconds_parts[1]) if len(seconds_parts) > 1 else 0.0
            
            # Normalize hundredths if given as 2 or 3 digits
            if len(seconds_parts) > 1 and len(seconds_parts[1]) == 3:
                hundredths = hundredths / 10.0

            return round(minutes * 60 + seconds + (hundredths / 100.0), 2)
        except (ValueError, IndexError):
            return 0.0

    @classmethod
    def split_to_16_chars(cls, text: str) -> Tuple[str, str]:
        """
        Splits a single lyric string into two display lines of <= 16 characters each.
        Tries to split on spaces cleanly.
        """
        text = text.strip()
        if not text:
            return "", ""

        if len(text) <= 16:
            return text, ""

        # Find word boundary near the 16-character split point
        words = text.split(" ")
        line1, line2 = "", ""

        for word in words:
            if len((line1 + " " + word).strip()) <= 16 and not line2:
                line1 = (line1 + " " + word).strip()
            else:
                line2 = (line2 + " " + word).strip()

        # Hard truncate line 2 if it still exceeds 16 chars
        return line1[:16], line2[:16]

    @classmethod
    def parse_lrc_content(cls, lrc_text: str) -> List[Tuple[float, str, str]]:
        """
        Parses full LRC file content into a list of tuples:
        [(timestamp_seconds, line1_16char, line2_16char), ...]
        """
        pattern = re.compile(r"(\[\d{2}:\d{2}[\.:]\d{2,3}\])(.*)")
        raw_entries = []

        for line in lrc_text.splitlines():
            match = pattern.match(line.strip())
            if match:
                time_str, lyric_str = match.groups()
                timestamp = cls.parse_timestamp(time_str)
                cleaned_lyric = lyric_str.strip()
                if cleaned_lyric:
                    raw_entries.append((timestamp, cleaned_lyric))

        # Sort entries strictly by timestamp
        raw_entries.sort(key=lambda x: x[0])

        parsed_lyrics = []
        for timestamp, lyric in raw_entries:
            line1, line2 = cls.split_to_16_chars(lyric)
            parsed_lyrics.append((timestamp, line1, line2))

        return parsed_lyrics


if __name__ == "__main__":
    # Quick module check
    sample_lrc = """
    [00:11.15] BABYDOLL DOMINIC FIKE
    [00:13.52] I can't move on, babydoll
    [00:16.09] Waitin' on calls flippin' through
    """
    parsed = LRCParser.parse_lrc_content(sample_lrc)
    for entry in parsed:
        print(entry)