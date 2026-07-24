import time
import digitalio
import adafruit_character_lcd.character_lcd as character_lcd
from typing import List, Tuple, Optional, Callable
from config import LCD_PINS


class LCDEngine:
    """Manages 1602A LCD rendering, timing synchronization, custom icons, and animations."""

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
        self.lcd_rs = digitalio.DigitalInOut(LCD_PINS["rs"])
        self.lcd_en = digitalio.DigitalInOut(LCD_PINS["en"])
        self.lcd_d4 = digitalio.DigitalInOut(LCD_PINS["d4"])
        self.lcd_d5 = digitalio.DigitalInOut(LCD_PINS["d5"])
        self.lcd_d6 = digitalio.DigitalInOut(LCD_PINS["d6"])
        self.lcd_d7 = digitalio.DigitalInOut(LCD_PINS["d7"])

        self.cols = LCD_PINS["cols"]
        self.rows = LCD_PINS["rows"]

        self.lcd = character_lcd.Character_LCD_Mono(
            self.lcd_rs,
            self.lcd_en,
            self.lcd_d4,
            self.lcd_d5,
            self.lcd_d6,
            self.lcd_d7,
            self.cols,
            self.rows,
        )

        self._load_custom_characters()
        self.clear()

    def _load_custom_characters(self):
        """Loads custom byte-array icons into CGRAM (slots 0-7)."""
        for index, (name, char_bytes) in enumerate(self.CUSTOM_CHARS.items()):
            if index < 8:
                self.lcd.create_char(index, char_bytes)

    def clear(self):
        """Forces a hard clear of both lines with blank padding to prevent visual artifacts."""
        self.lcd.message = "                \n                "
        self.lcd.clear()

    def display_lines(self, line1: str, line2: str = ""):
        """Pads lines strictly to 16 characters to overwrite residual text."""
        formatted_line1 = line1[:16].ljust(16)
        formatted_line2 = line2[:16].ljust(16)
        self.lcd.message = f"{formatted_line1}\n{formatted_line2}"

    def display_menu_item(self, title: str, subtitle: str = ""):
        """Helper to format menu titles with play icon (\x04)."""
        line1 = f"\x04 {title[:14]}"
        line2 = f"  {subtitle[:14]}" if subtitle else ""
        self.display_lines(line1, line2)

    def play_boot_animation(self):
        """Displays startup branding animation with dynamic loading bar."""
        self.clear()
        self.display_lines("\x00 LyricPulse", "  Booting Up...")
        time.sleep(1.2)

        loading_bar = ""
        for _ in range(16):
            loading_bar += "█"
            self.display_lines("\x00 LyricPulse", loading_bar)
            time.sleep(0.08)

        time.sleep(0.5)
        self.clear()

    def play_synced_lyrics(
        self,
        lyrics: List[Tuple[float, str, str]],
        stop_check_callback: Optional[Callable[[], bool]] = None,
    ):
        """Executes wall-clock sync loop with instant stop polling."""
        self.clear()
        start_time = time.time()

        for target_time, line1, line2 in lyrics:
            while (time.time() - start_time) < target_time:
                if stop_check_callback and stop_check_callback():
                    self.clear()
                    return
                time.sleep(0.005)

            if stop_check_callback and stop_check_callback():
                self.clear()
                return

            self.display_lines(line1, line2)

        time.sleep(1.5)
        self.clear()