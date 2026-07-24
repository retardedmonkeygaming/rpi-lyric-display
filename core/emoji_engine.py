import re
from typing import Tuple

class EmojiEngine:
    """Scans lyrics for keywords and injects 1602 LCD custom characters."""

    # Maps CGRAM slot numbers from LCDEngine (0-7)
    ICONS = {
        "music": "\x00",
        "heart": "\x01",
        "broken_heart": "\x02",
        "star": "\x03",
        "play": "\x04",
        "pause": "\x05",
        "bell": "\x06",
        "fire": "\x07",
    }

    KEYWORD_MAP = {
        r"\b(love|heart|miss|adore|baby|sweet)\b": "heart",
        r"\b(break|hurt|sad|cry|alone|pain|tear|tears)\b": "broken_heart",
        r"\b(fire|hot|burn|flame|lit|desire)\b": "fire",
        r"\b(star|night|shine|sky|glow|light)\b": "star",
        r"\b(sing|song|music|dance|party)\b": "music",
    }

    @classmethod
    def process_line(cls, text: str, mood_override: str = None) -> str:
        """Injects matching icon if room permits on line."""
        text_str = text.strip()
        if not text_str:
            return ""

        # Priority 1: Direct Mood Override
        icon_char = cls.ICONS.get(mood_override, "")

        # Priority 2: Keyword scanning
        if not icon_char:
            for pattern, icon_key in cls.KEYWORD_MAP.items():
                if re.search(pattern, text_str, re.IGNORECASE):
                    icon_char = cls.ICONS[icon_key]
                    break

        if icon_char:
            # Inject icon at start if within 16 chars limit
            if len(f"{icon_char} {text_str}") <= 16:
                return f"{icon_char} {text_str}"
            elif len(f"{text_str} {icon_char}") <= 16:
                return f"{text_str} {icon_char}"

        return text_str

    @classmethod
    def apply_to_page(cls, line1: str, line2: str) -> Tuple[str, str]:
        """Applies contextual emoji injection to a two-line display page."""
        return cls.process_line(line1), cls.process_line(line2)