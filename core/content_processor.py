import re
from typing import Tuple

class ContentProcessor:
    """Consolidated engine for Emojis, Sentiment, and Text Formatting."""

    ICONS = {
        "music": "\x00", "heart": "\x01", "broken_heart": "\x02",
        "star": "\x03", "play": "\x04", "pause": "\x05",
        "bell": "\x06", "fire": "\x07"
    }

    MOOD_MAP = {
        r"\b(love|heart|miss|adore|baby|sweet)\b": "heart",
        r"\b(break|hurt|sad|cry|alone|pain|tear)\b": "broken_heart",
        r"\b(fire|hot|burn|flame|lit|desire)\b": "fire",
        r"\b(star|night|shine|sky|glow|light)\b": "star",
        r"\b(sing|song|music|dance|party)\b": "music",
    }

    @classmethod
    def apply_alignment(cls, text: str, align: str = "center", width: int = 16) -> str:
        """Pads text to fixed width based on alignment choice."""
        text = text[:width].strip()
        if align == "center":
            return text.center(width)
        elif align == "right":
            return text.rjust(width)
        return text.ljust(width)

    @classmethod
    def inject_context_icons(cls, text: str) -> str:
        """Finds keywords and prepends icons if space permits."""
        for pattern, icon_key in cls.MOOD_MAP.items():
            if re.search(pattern, text, re.IGNORECASE):
                icon = cls.ICONS[icon_key]
                if len(f"{icon} {text}") <= 16:
                    return f"{icon} {text}"
                break
        return text