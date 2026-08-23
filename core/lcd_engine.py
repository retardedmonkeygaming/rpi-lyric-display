import time
import digitalio
import adafruit_character_lcd.character_lcd as character_lcd
from typing import List, Tuple, Optional, Callable
from config import LCD_PINS
from core.content_processor import ContentProcessor

class LCDEngine:
    CUSTOM_CHARS = {
        "music_note": [0x04, 0x06, 0x05, 0x05, 0x04, 0x1C, 0x1C, 0x00],
        "heart":      [0x00, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x00, 0x00],
        "broken_heart": [0x00, 0x0A, 0x1B, 0x0E, 0x0E, 0x04, 0x00, 0x00],
        "star":       [0x04, 0x0E, 0x1F, 0x0E, 0x0A, 0x0A, 0x00, 0x00],
        "play":       [0x08, 0x0C, 0x0E, 0x0F, 0x0E, 0x0C, 0x08, 0x00],
        "pause":      [0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x1B, 0x00],
        "bell":       [0x04, 0x0E, 0x0E, 0x0E, 0x1F, 0x00, 0x04, 0x00],
        "fire":       [0x04, 0x0A, 0x0A, 0x11, 0x15, 0x15, 0x0E, 0x00],
    }

    def __init__(self):
        # Setup Pins
        self.pins = {k: digitalio.DigitalInOut(v) for k, v in LCD_PINS.items() if hasattr(v, 'value') or isinstance(v, board.Pin)}
        self.lcd = character_lcd.Character_LCD_Mono(
            self.pins["rs"], self.pins["en"], self.pins["d4"], self.pins["d5"], self.pins["d6"], self.pins["d7"],
            LCD_PINS["cols"], LCD_PINS["rows"]
        )
        
        self._current_buffer = ["", ""]
        self._load_custom_characters()
        self.clear()

    def _load_custom_characters(self):
        for index, (name, char_bytes) in enumerate(self.CUSTOM_CHARS.items()):
            if index < 8: self.lcd.create_char(index, char_bytes)

    def clear(self):
        self.lcd.clear()
        self._current_buffer = [" " * 16, " " * 16]

    def display_lines(self, l1: str, l2: str = "", align: str = "center"):
        """Differential Refresh: Only updates if text changed to eliminate flicker."""
        f_l1 = ContentProcessor.apply_alignment(l1, align)
        f_l2 = ContentProcessor.apply_alignment(l2, align)

        if f_l1 != self._current_buffer[0] or f_l2 != self._current_buffer[1]:
            self.lcd.message = f"{f_l1}\n{f_l2}"
            self._current_buffer = [f_l1, f_l2]

    def play_boot_animation(self, ip_addr: str):
        self.clear()
        # Stage 1: Music Note + Brand
        self.display_lines("\x00 LyricPulse", "v2.0 Starting")
        time.sleep(1.0)
        
        # Stage 2: Progressive Loading
        bar = ""
        for _ in range(16):
            bar += "█"
            self.display_lines("\x00 LyricPulse", bar)
            time.sleep(0.05)

        # Stage 3: IP Flash
        self.display_lines("SYSTEM ONLINE", ip_addr)
        time.sleep(1.5)
        self.clear()

    def play_synced_lyrics(self, lyrics: List[Tuple[float, str, str]], stop_check_callback: Optional[Callable[[], bool]] = None):
        self.clear()
        start_time = time.time()

        for target_time, line1, line2 in lyrics:
            while (time.time() - start_time) < target_time:
                if stop_check_callback and stop_check_callback():
                    self.clear()
                    return
                time.sleep(0.002) # Higher precision polling

            self.display_lines(line1, line2, align="center") # Alignment pulled from config later

        time.sleep(1.5)
        self.clear()