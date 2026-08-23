import re
from typing import Tuple

class ContentProcessor:
    """Strict Hardware-Only Emoji Mapping for 1602A LCD."""

    # These hex codes match the CUSTOM_CHARS indices (0-7) in LCDEngine
    LCD_ICONS = {
        "music": "\x00", 
        "heart": "\x01", 
        "broken_heart": "\x02",
        "star": "\x03", 
        "play": "\x04", 
        "pause": "\x05",
        "bell": "\x06", 
        "fire": "\x07"
    }

    # Keyword rules for auto-injection
    RULES = [
        (['love', 'heart', 'kiss', 'baby', 'yours', 'sweet'], LCD_ICONS["heart"]),
        (['fire', 'burn', 'hot', 'lit', 'flame', 'wild'], LCD_ICONS["fire"]),
        (['happy', 'smile', 'joy', 'shine', 'star', 'light'], LCD_ICONS["star"]),
        (['sad', 'cry', 'rain', 'dark', 'alone', 'tear', 'pain', 'broken'], LCD_ICONS["broken_heart"]),
        (['night', 'moon', 'dream', 'sleep'], LCD_ICONS["star"]),
        (['sing', 'song', 'voice', 'call', 'talk', 'music', 'dance'], LCD_ICONS["music"]),
    ]

    @classmethod
    def apply_alignment(cls, text: str, align: str = "center", width: int = 16) -> str:
        text = text[:width].strip()
        if align == "center": return text.center(width)
        if align == "right": return text.rjust(width)
        return text.ljust(width)

    @classmethod
    def pick_icon_for_text(cls, text: str) -> str:
        """Returns the specific hardware index character for a line."""
        clean_text = text.lower()
        for keywords, icon_char in cls.RULES:
            if any(kw in clean_text for kw in keywords):
                return icon_char
        return "" # No icon if no match
    
    @classmethod
    def process_line_with_icon(cls, text: str) -> str:
        """Prepends a 1-column hardware icon if keywords match and space allows."""
        icon = cls.pick_icon_for_text(text)
        if not icon: return text
        
        # If the line already starts with a custom char index, don't double up
        if text.startswith(tuple(cls.LCD_ICONS.values())):
            return text
            
        # Ensure we don't exceed 16 chars
        combined = f"{icon}{text.strip()}"
        return combined[:16]