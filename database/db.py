import sqlite3
import os
import time
from config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
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

    def get_all_songs(self):
        with self.get_connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM songs ORDER BY title ASC").fetchall()]

    def get_song_lyrics(self, song_id: int):
        with self.get_connection() as conn:
            cursor = conn.execute(
                "SELECT timestamp_sec, line1, line2 FROM song_lyrics WHERE song_id = ? ORDER BY timestamp_sec ASC",
                (song_id,)
            )
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    def bulk_update_lyrics(self, song_id: int, lyric_data: list):
        """lyric_data: list of (timestamp, line1, line2)"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM song_lyrics WHERE song_id = ?", (song_id,))
            conn.executemany(
                "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
                [(song_id, ts, l1, l2) for ts, l1, l2 in lyric_data]
            )
            conn.commit()

    def add_song(self, title, artist, lyrics):
        with self.get_connection() as conn:
            cursor = conn.execute("INSERT INTO songs (title, artist) VALUES (?, ?)", (title, artist))
            sid = cursor.lastrowid
            self.bulk_update_lyrics(sid, lyrics)
            return sid

    def increment_play_count(self, song_id):
        with self.get_connection() as conn:
            conn.execute("UPDATE songs SET play_count = play_count + 1 WHERE id = ?", (song_id,))