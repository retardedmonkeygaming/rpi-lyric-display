import time
import threading
from flask import Flask
from config import FLASK_HOST, FLASK_PORT
from database.db import DatabaseManager
from core.lcd_engine import LCDEngine
from core.touch_input import TouchInputHandler
from web.routes import web_bp


# At the top of app.py
current_app_instance = None

class LyricSyncApp:
    def __init__(self):
        global current_app_instance
        current_app_instance = self
        
        # [Existing initialization logic stays the same...]

    def trigger_remote_playback(self, song_id: int):
        """Allows external HTTP endpoints to trigger timed playback runs."""
        if self.state != "PLAYING":
            self.state = "PLAYING"
            playback_thread = threading.Thread(
                target=self._start_song_playback, args=(song_id,)
            )
            playback_thread.daemon = True
            playback_thread.start()
        
class LyricSyncApp:
    """LyricPulse Main Service Application."""

    def __init__(self):
        self.db = DatabaseManager()
        self.lcd = LCDEngine()

        self.state = "IDLE"
        self.songs_list = []
        self.selected_index = 0
        self.stop_playback = False

        self.touch = TouchInputHandler(
            on_short_press=self._handle_short_press,
            on_double_tap=self._handle_double_tap,
            on_triple_tap=self._handle_triple_tap,
            on_long_press=self._handle_long_press,
        )

        self.flask_app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
        self.flask_app.register_blueprint(web_bp)

    def _handle_short_press(self):
        if self.state == "IDLE":
            self.state = "MENU"
            self.songs_list = self.db.get_all_songs()
            self.selected_index = 0
            self._update_menu_display()

        elif self.state == "MENU":
            if self.songs_list:
                self.selected_index = (self.selected_index + 1) % len(self.songs_list)
                self._update_menu_display()

    def _handle_double_tap(self):
        if self.state == "MENU" and self.songs_list:
            self.state = "PLAYING"
            selected_song = self.songs_list[self.selected_index]

            playback_thread = threading.Thread(
                target=self._start_song_playback, args=(selected_song["id"],)
            )
            playback_thread.daemon = True
            playback_thread.start()

    def _handle_triple_tap(self):
        """Triple Tap: Stop active lyric playback immediately without screen artifacts."""
        if self.state == "PLAYING":
            self.stop_playback = True
            self.state = "IDLE"
            self.lcd.clear()
            self.lcd.display_lines("PLAYBACK STOPPED", "READY FOR SYNC")

    def _handle_long_press(self):
        """Long Press: Cancel and return to Ready screen."""
        if self.state in ["MENU", "PLAYING"]:
            self.stop_playback = True
            self.state = "IDLE"
            self.lcd.clear()
            self.lcd.display_lines("READY FOR SYNC", "SELECT A TRACK")

    def _update_menu_display(self):
        if not self.songs_list:
            self.lcd.display_lines("NO SONGS FOUND", "UPLOAD VIA WEB")
            return

        song = self.songs_list[self.selected_index]
        self.lcd.display_menu_item(song["title"], song["artist"])

    def _start_song_playback(self, song_id: int):
        lyrics = self.db.get_song_lyrics(song_id)
        if not lyrics:
            self.lcd.display_lines("NO LYRICS FOUND", "ADD LRC VIA WEB")
            time.sleep(2)
            self.state = "IDLE"
            self.lcd.display_lines("READY FOR SYNC", "SELECT A TRACK")
            return

        self.db.increment_play_count(song_id)
        self.stop_playback = False

        def check_stopped():
            return self.stop_playback

        self.lcd.play_synced_lyrics(lyrics, stop_check_callback=check_stopped)

        if not self.stop_playback:
            self.state = "IDLE"
            self.lcd.display_lines("READY FOR SYNC", "SELECT A TRACK")

    def run(self):
        self.touch.start_listening()

        server_thread = threading.Thread(
            target=lambda: self.flask_app.run(
                host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False
            )
        )
        server_thread.daemon = True
        server_thread.start()

        # Startup Loading Animation
        self.lcd.play_boot_animation()
        self.lcd.display_lines("READY FOR SYNC", "SELECT A TRACK")

        print("=== LyricPulse Online ===")
        print(f"Web Dashboard: http://localhost:{FLASK_PORT}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down service...")
            self.touch.cleanup()
            self.lcd.clear()


if __name__ == "__main__":
    app = LyricSyncApp()
    app.run()