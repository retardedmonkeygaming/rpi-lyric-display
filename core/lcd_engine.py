import time
import board
import digitalio
import adafruit_character_lcd.character_lcd as character_lcd
from typing import List, Tuple, Optional
from config import LCD_PINS


class LCDEngine:
    """Manages 1602A LCD rendering, timing synchronization, and custom character icons."""

    # 5x8 Custom Character Byte Maps (Max 8 slots on HD44780/1602A)
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
        # Configure Digital I/O Pins
        self.lcd_rs = digitalio.DigitalInOut(LCD_PINS["rs"])
        self.lcd_en = digitalio.DigitalInOut(LCD_PINS["en"])
        self.lcd_d4 = digitalio.DigitalInOut(LCD_PINS["d4"])
        self.lcd_d5 = digitalio.DigitalInOut(LCD_PINS["d5"])
        self.lcd_d6 = digitalio.DigitalInOut(LCD_PINS["d6"])
        self.lcd_d7 = digitalio.DigitalInOut(LCD_PINS["d7"])

        self.cols = LCD_PINS["cols"]
        self.rows = LCD_PINS["rows"]

        # Initialize Character LCD Driver
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
        """Loads custom byte-array icons into the 1602A CGRAM memory (slots 0-7)."""
        for index, (name, char_bytes) in enumerate(self.CUSTOM_CHARS.items()):
            if index < 8:
                self.lcd.create_char(index, char_bytes)

    def clear(self):
        """Clears the LCD screen."""
        self.lcd.clear()

    def display_lines(self, line1: str, line2: str = ""):
        """Pads and displays two lines of text (16 chars max per line)."""
        formatted_line1 = line1[:16].ljust(16)
        formatted_line2 = line2[:16].ljust(16)
        self.lcd.message = f"{formatted_line1}\n{formatted_line2}"

    def display_menu_item(self, title: str, subtitle: str = ""):
        """Helper to format menu titles on the screen."""
        line1 = f"\x04 {title[:14]}"  # \x04 displays the 'play' icon
        line2 = f"  {subtitle[:14]}" if subtitle else ""
        self.display_lines(line1, line2)

    def play_synced_lyrics(
        self,
        lyrics: List[Tuple[float, str, str]],
        stop_check_callback: Optional[Callable[[], bool]] = None,
    ):
        """
        Executes a high-precision wall-clock sync loop for displaying lyrics.
        `lyrics` format: [(timestamp_sec, line1, line2), ...]
        """
        self.clear()
        start_time = time.time()

        for target_time, line1, line2 in lyrics:
            # Wait precisely until current playback reaches the timestamp
            while (time.time() - start_time) < target_time:
                if stop_check_callback and stop_check_callback():
                    self.clear()
                    return
                time.sleep(0.005)  # 5ms polling for tight sync

            self.display_lines(line1, line2)

        time.sleep(2)
        self.clear()


if __name__ == "__main__":
    # Module test block
    print("Testing LCD Engine... Press Ctrl+C to stop.")
    engine = LCDEngine()
    
    # Test message with custom icon (\x00 = music note, \x01 = heart)
    engine.display_lines("\x00 BABYDOLL \x01", "DOMINIC FIKE")
    time.sleep(3)
    engine.clear()