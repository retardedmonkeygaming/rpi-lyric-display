import re
from typing import List, Tuple


class LRCParser:
    """Parses .lrc strings and formats lyrics into clean 16x2 LCD dual-line blocks."""

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """Converts flexible [m:s.xx] or [mm:ss.xx] formats into seconds float."""
        try:
            cleaned = timestamp_str.strip("[]")
            parts = cleaned.split(":")
            minutes = float(parts[0])
            seconds_parts = parts[1].split(".")
            seconds = float(seconds_parts[0])

            # Handle fractional seconds (1, 2, or 3 digits)
            frac_str = seconds_parts[1] if len(seconds_parts) > 1 else "0"
            fraction = float(frac_str) / (10 ** len(frac_str)) if frac_str else 0.0

            return round(minutes * 60 + seconds + fraction, 2)
        except (ValueError, IndexError):
            return 0.0

    @classmethod
    def split_to_16_chars(cls, text: str) -> Tuple[str, str]:
        """
        Splits a single lyric string into two display lines of <= 16 characters each
        without cutting words in half whenever possible.
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

        # Fill Line 1 up to 16 characters by word boundaries
        for word in words:
            # Check length with space added
            addition = len(word) if not line1_words else len(word) + 1
            if current_len + addition <= 16:
                line1_words.append(word)
                current_len += addition
            else:
                line2_words.append(word)

        line1 = " ".join(line1_words)
        line2 = " ".join(line2_words)

        # Handle Line 2 formatting cleanly without cutting words if possible
        if len(line2) > 16:
            l2_words = line2.split()
            l2_formatted = []
            l2_len = 0
            for w in l2_words:
                add = len(w) if not l2_formatted else len(w) + 1
                if l2_len + add <= 16:
                    l2_formatted.append(w)
                    l2_len += add
                else:
                    break
            line2 = " ".join(l2_formatted)

        return line1[:16], line2[:16]

    @classmethod
    def parse_lrc_content(cls, lrc_text: str) -> List[Tuple[float, str, str]]:
        """
        Parses LRC content, capturing flexible timestamps and returning
        sorted [(timestamp, line1, line2), ...].
        """
        # Flexible regex supporting single or double digit minutes/seconds/milliseconds
        pattern = re.compile(r"(\[\d{1,2}:\d{1,2}(?:[\.:]\d{1,3})?\])(.*)")
        raw_entries = []

        for line in lrc_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            match = pattern.match(line_str)
            if match:
                time_str, lyric_str = match.groups()
                timestamp = cls.parse_timestamp(time_str)
                cleaned_lyric = lyric_str.strip()
                # Keep entry even if empty line to allow timing gaps
                raw_entries.append((timestamp, cleaned_lyric))

        # Sort entries strictly by timestamp
        raw_entries.sort(key=lambda x: x[0])

        parsed_lyrics = []
        for timestamp, lyric in raw_entries:
            line1, line2 = cls.split_to_16_chars(lyric)
            parsed_lyrics.append((timestamp, line1, line2))

        return parsed_lyrics


if __name__ == "__main__":
    sample = """
    [0:05.1] Intro opening line test
    [0:11.15] BABYDOLL DOMINIC FIKE
    [0:36.80] Lookin' for somebody different
    """
    for entry in LRCParser.parse_lrc_content(sample):
        print(entry)