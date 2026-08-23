import re

class ContentProcessor:
    # 0: Music, 1: Heart, 2: Broken Heart, 3: Star, 4: Play, 5: Pause, 6: Bell, 7: Fire
    RULES = [
        (r"\b(love|heart|kiss|baby|sweet|adore|mine)\b", 1, "ROMANTIC"),
        (r"\b(fire|burn|hot|lit|flame|wild|beast|power|rock)\b", 7, "HYPE"),
        (r"\b(star|night|shine|sky|glow|light|dream|moon)\b", 3, "CHILL"),
        (r"\b(break|hurt|sad|cry|alone|pain|tear|dead|ghost|dark)\b", 2, "SAD"),
        (r"\b(sing|song|music|dance|party|voice|talk|listen)\b", 0, "MUSICAL"),
    ]

    @classmethod
    def analyze(cls, text: str):
        clean = text.lower()
        for pattern, index, label in cls.RULES:
            if re.search(pattern, clean):
                return chr(index), label
        return "", "NEUTRAL"

    @classmethod
    def apply_alignment(cls, text: str, align: str = "center", width: int = 16) -> str:
        text = text[:width].strip()
        if align == "center": return text.center(width)
        if align == "right": return text.rjust(width)
        return text.ljust(width)

    @classmethod
    def process_line(cls, text: str) -> str:
        """Injects a single hardware character if match is found."""
        if not text: return ""
        
        # Check if line already starts with a hardware code (0-7)
        if ord(text[0]) < 8:
            return text
        
        icon_char, _ = cls.analyze(text)
        if icon_char:
            # Prepend the 1-column icon. 
            return f"{icon_char}{text.strip()}"[:16]
        return text