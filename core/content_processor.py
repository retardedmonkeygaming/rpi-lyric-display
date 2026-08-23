import re

class ContentProcessor:
    # Strict mapping to the 8 slots in your LCDEngine.CUSTOM_CHARS
    # 0: Music, 1: Heart, 2: Broken Heart, 3: Star, 4: Play, 5: Pause, 6: Bell, 7: Fire
    MAP = [
        (r"\b(love|heart|kiss|baby|sweet|adore)\b", "\x01", "ROMANTIC"),
        (r"\b(fire|burn|hot|lit|flame|wild|beast|power)\b", "\x07", "HYPE"),
        (r"\b(star|night|shine|sky|glow|light|dream)\b", "\x03", "CHILL"),
        (r"\b(break|hurt|sad|cry|alone|pain|tear|dead|ghost)\b", "\x02", "SAD"),
        (r"\b(sing|song|music|dance|party|voice|talk)\b", "\x00", "MUSICAL"),
    ]

    @classmethod
    def analyze(cls, text: str):
        """Returns (icon_char, mood_label) based on text content."""
        clean = text.lower()
        for pattern, icon, label in cls.MAP:
            if re.search(pattern, clean):
                return icon, label
        return "", "NEUTRAL"

    @classmethod
    def apply_alignment(cls, text: str, align: str = "center", width: int = 16) -> str:
        text = text[:width].strip()
        if align == "center": return text.center(width)
        if align == "right": return text.rjust(width)
        return text.ljust(width)

    @classmethod
    def process_line(cls, text: str) -> str:
        """Injects hardware icon index if a match is found."""
        if not text or text.startswith(("\x00","\x01","\x02","\x03","\x04","\x05","\x06","\x07")):
            return text
        
        icon, _ = cls.analyze(text)
        if icon:
            # Prepend icon. Ensure it doesn't push text past 16 chars.
            return f"{icon}{text.strip()}"[:16]
        return text