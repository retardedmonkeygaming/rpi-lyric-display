import time
import socket
import threading
from flask import Flask
from config import FLASK_HOST, FLASK_PORT
from database.db import DatabaseManager
from core.lcd_engine import LCDEngine
from core.touch_input import TouchInputHandler
from web.routes import web_bp

class LyricSyncApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.lcd = LCDEngine()
        
        # Initialize Application State
        self.state = "IDLE" 
        self.songs_list = []
        self.selected_index = 0
        self.stop_playback = False
        self.local_ip = self._get_local_ip()

        # Web Setup
        self.flask_app = Flask(__name__, template_folder="web/templates", static_folder="web/static")
        self.flask_app.config["LYRIC_APP"] = self
        self.flask_app.register_blueprint(web_bp)

        # Touch Interface
        self.touch = TouchInputHandler(
            on_short_press=self._handle_next,
            on_double_tap=self._handle_select,
            on_long_press=self._handle_stop
        )

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except: return "127.0.0.1"

    def _handle_next(self):
        if self.state == "IDLE":
            self.state = "MENU"
            self.songs_list = self.db.get_all_songs()
            self._update_display()
        elif self.state == "MENU":
            if self.songs_list:
                self.selected_index = (self.selected_index + 1) % len(self.songs_list)
                self._update_display()

    def _handle_select(self):
        if self.state == "MENU" and self.songs_list:
            song = self.songs_list[self.selected_index]
            self.trigger_playback(song["id"])

    def _handle_stop(self):
        self.stop_playback = True
        self.state = "IDLE"
        self.lcd.clear()

    def _update_display(self):
        if self.state == "MENU":
            song = self.songs_list[self.selected_index]
            self.lcd.display_lines(f"\x04 {song['title']}", song['artist'][:16])

    def trigger_playback(self, song_id: int):
        self.state = "PLAYING"
        self.stop_playback = False
        
        def run():
            lyrics = self.db.get_song_lyrics(song_id)
            if not lyrics:
                self.lcd.display_lines("EMPTY TRACK", "ADD LRC VIA WEB")
                time.sleep(2)
                self.state = "IDLE"
                return

            self.db.increment_play_count(song_id)
            self.lcd.play_synced_lyrics(lyrics, stop_check_callback=lambda: self.stop_playback)
            if not self.stop_playback:
                self.state = "IDLE"

        threading.Thread(target=run, daemon=True).start()

    def _idle_loop(self):
        pages = [
            lambda: self.lcd.display_lines("LYRIC PULSE v2", "READY FOR SYNC"),
            lambda: self.lcd.display_lines("WEB ACCESS AT:", f"{self.local_ip}:{FLASK_PORT}"),
            lambda: self.lcd.display_lines("TRACKS LOADED:", str(len(self.db.get_all_songs())))
        ]
        curr = 0
        while True:
            if self.state == "IDLE":
                pages[curr]()
                curr = (curr + 1) % len(pages)
            time.sleep(5)

    def run(self):
        self.touch.start_listening()
        
        # Start Web Server
        threading.Thread(target=lambda: self.flask_app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False), daemon=True).start()
        
        # Start HW Animation and Idle Task
        self.lcd.play_boot_animation(self.local_ip)
        threading.Thread(target=self._idle_loop, daemon=True).start()

        print(f"Server: http://{self.local_ip}:{FLASK_PORT}")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            self.touch.cleanup()
            self.lcd.clear()

if __name__ == "__main__":
    app = LyricSyncApp()
    app.run()