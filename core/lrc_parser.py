import re
from typing import List, Tuple

class LRCParser:
    """Parses .lrc content into precise timestamped 16x2 LCD display pages."""

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        try:
            cleaned = timestamp_str.strip("[]")
            parts = cleaned.replace(":", ".").split(".")
            minutes = float(parts[0])
            seconds = float(parts[1]) if len(parts) > 1 else 0.0
            fraction = 0.0
            if len(parts) > 2 and parts[2]:
                frac_str = parts[2]
                fraction = float(frac_str) / (10 ** len(frac_str))
            return round(minutes * 60 + seconds + fraction, 2)
        except (ValueError, IndexError):
            return -1.0

    @classmethod
    def paginate_text(cls, text: str) -> List[Tuple[str, str]]:
        words = text.strip().split()
        if not words:
            return [("", "")]

        pages = []
        remaining_words = list(words)

        while remaining_words:
            line1_words = []
            l1_len = 0
            while remaining_words:
                w = remaining_words[0]
                added = len(w) if not line1_words else len(w) + 1
                if l1_len + added <= 16:
                    line1_words.append(remaining_words.pop(0))
                    l1_len += added
                else:
                    break

            line2_words = []
            l2_len = 0
            while remaining_words:
                w = remaining_words[0]
                added = len(w) if not line2_words else len(w) + 1
                if l2_len + added <= 16:
                    line2_words.append(remaining_words.pop(0))
                    l2_len += added
                else:
                    break

            if not line1_words and remaining_words:
                w = remaining_words.pop(0)
                pages.append((w[:16], w[16:32]))
                continue

            pages.append((" ".join(line1_words), " ".join(line2_words)))
        return pages

    @classmethod
    def parse_lrc_content(cls, lrc_text: str) -> List[Tuple[float, str, str]]:
        time_tag_regex = re.compile(r"\[\d{1,2}:\d{2}(?:[\.:]\d{1,3})?\]")
        raw_entries = []

        for line in lrc_text.splitlines():
            line_str = line.strip()
            if not line_str or re.match(r"^\[[a-zA-Z]+:", line_str):
                continue

            timestamps = time_tag_regex.findall(line_str)
            if not timestamps:
                continue

            lyric_text = time_tag_regex.sub("", line_str).strip()
            for ts_tag in timestamps:
                ts_val = cls.parse_timestamp(ts_tag)
                if ts_val >= 0.0:
                    raw_entries.append((ts_val, lyric_text))

        raw_entries.sort(key=lambda x: x[0])
        parsed_lyrics = []
        num_entries = len(raw_entries)

        for i, (current_ts, lyric) in enumerate(raw_entries):
            pages = cls.paginate_text(lyric)
            if not pages: continue

            if len(pages) == 1:
                parsed_lyrics.append((current_ts, pages[0][0], pages[0][1]))
            else:
                next_ts = raw_entries[i+1][0] if i+1 < num_entries else current_ts + (len(pages) * 2.5)
                available_time = max(next_ts - current_ts, len(pages) * 1.5)
                time_per_page = available_time / len(pages)

                for page_idx, (l1, l2) in enumerate(pages):
                    page_ts = round(current_ts + (page_idx * time_per_page), 2)
                    parsed_lyrics.append((page_ts, l1, l2))

        return parsed_lyrics