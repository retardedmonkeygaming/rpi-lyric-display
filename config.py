import board

# ==========================================
# GPIO PIN MAPPINGS (BCM NUMBERING)
# ==========================================

# 1602A Character LCD (Non-I2C 4-bit mode)
LCD_PINS = {
    "rs": board.D22,
    "en": board.D17,
    "d4": board.D25,
    "d5": board.D24,
    "d6": board.D23,
    "d7": board.D18,
    "cols": 16,
    "rows": 2,
}

TOUCH_BUTTON_PIN = 27
BUZZER_PIN = 2
DHT_SENSOR_PIN = board.D4

# ==========================================
# APP & SYSTEM CONFIGURATION
# ==========================================
DB_PATH = "data/lyrics.db"
NEW_SONGS_DIR = "data/new_songs"
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"

# Phase 1 Additions
DEFAULT_ALIGN = "center"  # Options: "left", "center", "right"
IDLE_ROTATION_SPEED = 5   # Seconds per page
BOOT_ANIMATION_ENABLED = True