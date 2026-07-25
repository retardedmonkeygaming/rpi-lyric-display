import time
import socket
import threading
from flask import Flask
from config import FLASK_HOST, FLASK_PORT
from database.db import DatabaseManager
from core.lcd_engine import LCDEngine
from core.touch_input import TouchInputHandler
from core.plugin_loader import PluginLoader
from web.routes import web_bp

current_app_instance = None


def get_local_ip() -> str:
    """Retrieves the Raspberry Pi's local network IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class LyricSyncApp:
    def __init__(self):
        # 1. Declare global reference FIRST
        global current_app_instance
        current_app_instance = self

        # 2. Initialize database, LCD, and plugins
        self.db = DatabaseManager()
        self.lcd = LCDEngine()
        self.plugins = PluginLoader().load_plugins()

        # 3. Setup Flask application
        self.flask_app = Flask(
            __name__,
            template_folder="web/templates",
            static_folder="web/static"
        )
        self.flask_app.config["LYRIC_APP"] = self
        self.flask_app.register_blueprint(web_bp)

        # 4. State & networking variables
        self.state = "IDLE"  # IDLE, MENU, PLAYING
        self.songs_list = []
        self.selected_index = 0
        self.stop_playback = False
        self.local_ip = get_local_ip()

        # 5. Touch sensor hardware setup
        self.touch = TouchInputHandler(
            on_short_press=self._handle_short_press,
            on_double_tap=self._handle_double_tap,
            on_triple_tap=self._handle_triple_tap,
            on_long_press=self._handle_long_press,
        )

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
            selected_song = self.songs_list[self.selected_index]
            self.trigger_recording_mode(selected_song["id"], countdown_sec=3)

    def _handle_triple_tap(self):
        if self.state == "PLAYING":
            self.stop_playback = True
            self.state = "IDLE"
            self.lcd.clear()

    def _handle_long_press(self):
        if self.state in ["MENU", "PLAYING"]:
            self.stop_playback = True
            self.state = "IDLE"
            self.lcd.clear()

    def _update_menu_display(self):
        if not self.songs_list:
            self.lcd.display_lines("NO SONGS FOUND", "UPLOAD VIA WEB")
            return
        song = self.songs_list[self.selected_index]
        self.lcd.display_menu_item(song["title"], song["artist"])

    def trigger_recording_mode(self, song_id: int, countdown_sec: int = 3):
        """Executes a visual countdown lock before starting timed playback on LCD."""
        self.stop_playback = False
        self.state = "PLAYING"

        def recording_thread():
            self.lcd.clear()
            for count in range(countdown_sec, 0, -1):
                if self.stop_playback:
                    break
                self.lcd.display_lines("RECORDING IN...", f"      {count}      ")
                time.sleep(1.0)

            if not self.stop_playback:
                self.lcd.display_lines("  RECORDING!  ", "    ACTION    ")
                time.sleep(0.8)

                start_time = time.time()
                self._start_song_playback(int(song_id))
                duration = round(time.time() - start_time, 2)

                status = "STOPPED" if self.stop_playback else "COMPLETED"
                self.db.log_session(int(song_id), duration, status)

        t = threading.Thread(target=recording_thread, daemon=True)
        t.start()

    def _start_song_playback(self, song_id: int):
        lyrics = self.db.get_song_lyrics(song_id)
        if not lyrics:
            self.lcd.display_lines("NO LYRICS FOUND", "ADD LRC VIA WEB")
            time.sleep(2)
            self.state = "IDLE"
            return

        self.db.increment_play_count(song_id)
        self.stop_playback = False

        def check_stopped():
            return self.stop_playback

        self.lcd.play_synced_lyrics(lyrics, stop_check_callback=check_stopped)

        if not self.stop_playback:
            self.state = "IDLE"

    def _start_idle_display_loop(self):
        def idle_loop():
            page = 0
            while True:
                if self.state == "IDLE":
                    if page == 0:
                        self.lcd.display_lines("READY FOR SYNC", "SELECT A TRACK")
                    else:
                        ip_line = f"{self.local_ip}:{FLASK_PORT}"
                        self.lcd.display_lines("WEB UI ACCESS", ip_line)
                    page = (page + 1) % 2
                time.sleep(5)

        threading.Thread(target=idle_loop, daemon=True).start()

    def run(self):
        self.touch.start_listening()

        server_thread = threading.Thread(
            target=lambda: self.flask_app.run(
                host=FLASK_HOST, port=FLASK_PORT, debug=False, use_reloader=False
            )
        )
        server_thread.daemon = True
        server_thread.start()

        self.lcd.play_boot_animation()
        self._start_idle_display_loop()

        print("=== LyricPulse 1602 Online ===")
        print(f"Web Dashboard: http://{self.local_ip}:{FLASK_PORT}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.touch.cleanup()
            self.lcd.clear()


if __name__ == "__main__":
    app = LyricSyncApp()
    app.run()