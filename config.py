import board

# ==========================================
# GPIO PIN MAPPINGS (BCM NUMBERING)
# ==========================================

# 1602A Character LCD (Non-I2C 4-bit mode)
LCD_PINS = {
    "rs": board.D22,  # Physical Pin 15
    "en": board.D17,  # Physical Pin 11
    "d4": board.D25,  # Physical Pin 22
    "d5": board.D24,  # Physical Pin 18
    "d6": board.D23,  # Physical Pin 16
    "d7": board.D18,  # Physical Pin 12
    "cols": 16,
    "rows": 2,
}

# Navigation / Touch Input
TOUCH_BUTTON_PIN = 27  # GPIO 27 / Physical Pin 13

# Optional Peripherals (from your weather station/sensors setup)
BUZZER_PIN = 2  # GPIO 2 / Physical Pin 3
DHT_SENSOR_PIN = board.D4  # GPIO 4 / Physical Pin 7

# ==========================================
# APP & SYSTEM CONFIGURATION
# ==========================================
DB_PATH = "data/lyrics.db"
NEW_SONGS_DIR = "data/new_songs"
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"