import sqlite3
import os
import shutil
import time
from typing import List, Tuple, Dict, Optional
from config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema_sql)

    def add_song(self, title: str, artist: str, lyrics: List[Tuple[float, str, str]], tags: Optional[List[str]] = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO songs (title, artist) VALUES (?, ?)", (title, artist)
            )
            song_id = cursor.lastrowid
            
            lyric_entries = [(song_id, ts, l1, l2) for ts, l1, l2 in lyrics]
            cursor.executemany(
                "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
                lyric_entries
            )
            return song_id

    def get_all_songs(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM songs ORDER BY title ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_song_lyrics(self, song_id: int) -> List[Tuple[float, str, str]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp_sec, line1, line2 FROM song_lyrics WHERE song_id = ? ORDER BY timestamp_sec ASC",
                (song_id,)
            )
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    def get_setting(self, key: str, default: str) -> str:
        with self.get_connection() as conn:
            res = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return res[0] if res else default

    def set_setting(self, key: str, value: str):
        with self.get_connection() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))

    def log_session(self, song_id: int, duration_sec: float, status: str = "COMPLETED"):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO session_logs (song_id, timestamp, duration_sec, status) VALUES (?, ?, ?, ?)",
                (song_id, time.strftime("%Y-%m-%d %H:%M:%S"), duration_sec, status)
            )

    def increment_play_count(self, song_id: int):
        with self.get_connection() as conn:
            conn.execute("UPDATE songs SET play_count = play_count + 1, last_used = CURRENT_TIMESTAMP WHERE id = ?", (song_id,))