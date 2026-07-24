import sqlite3
import os
import shutil
from typing import List, Tuple, Dict, Optional
from config import DB_PATH

class DatabaseManager:
    """Handles all SQLite database operations for songs, lyrics, and metadata."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes database schema from schema.sql."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema_sql)

    def add_song(
        self,
        title: str,
        artist: str,
        lyrics: List[Tuple[float, str, str]],
        duration: float = 0.0,
        lrc_path: str = "",
        tags: Optional[List[str]] = None
    ) -> int:
        """Inserts a new song with its parsed lyrics and optional tags."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO songs (title, artist, duration, lrc_path) VALUES (?, ?, ?, ?)",
                (title, artist, duration, lrc_path)
            )
            song_id = cursor.lastrowid

            lyric_entries = [
                (song_id, timestamp, line1, line2)
                for timestamp, line1, line2 in lyrics
            ]
            cursor.executemany(
                "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
                lyric_entries
            )

            if tags:
                tag_entries = [(song_id, tag.strip().lower()) for tag in tags if tag.strip()]
                cursor.executemany(
                    "INSERT INTO song_tags (song_id, tag_name) VALUES (?, ?)",
                    tag_entries
                )

            return song_id

    def get_all_songs(self) -> List[Dict]:
        """Returns all songs ordered by title."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, artist, duration, play_count, last_used FROM songs ORDER BY title ASC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def search_songs(self, query: str) -> List[Dict]:
        """Search songs by title or artist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_pattern = f"%{query}%"
            cursor.execute(
                "SELECT id, title, artist, duration FROM songs "
                "WHERE title LIKE ? OR artist LIKE ? ORDER BY title ASC",
                (search_pattern, search_pattern)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_song_lyrics(self, song_id: int) -> List[Tuple[float, str, str]]:
        """Fetches all timed lyric blocks for a song ordered by timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp_sec, line1, line2 FROM song_lyrics "
                "WHERE song_id = ? ORDER BY timestamp_sec ASC",
                (song_id,)
            )
            return [(row["timestamp_sec"], row["line1"], row["line2"]) for row in cursor.fetchall()]

    def increment_play_count(self, song_id: int):
        """Updates play count and last_used timestamp when played."""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE songs SET play_count = play_count + 1, last_used = CURRENT_TIMESTAMP WHERE id = ?",
                (song_id,)
            )

    def backup_database(self, destination_path: str) -> bool:
        """Backs up the SQLite database file to a destination path."""
        try:
            shutil.copy2(self.db_path, destination_path)
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False
        import os
import shutil
import time

# Add these methods to DatabaseManager inside database/db.py:

def create_backup(self, backup_dir: str = "backups") -> str:
    """Creates a timestamped snapshot of the SQLite database file."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"lyricpulse_backup_{timestamp}.db")
    shutil.copy2(self.db_path, backup_path)
    return backup_path

def log_session(self, song_id: int, duration_sec: float, status: str = "COMPLETED"):
    """Records recording session telemetry for Meta Edits reference."""
    with self.get_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS session_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, timestamp TEXT, duration_sec REAL, status TEXT)"
        )
        conn.execute(
            "INSERT INTO session_logs (song_id, timestamp, duration_sec, status) VALUES (?, ?, ?, ?)",
            (song_id, time.strftime("%Y-%m-%d %H:%M:%S"), duration_sec, status)
        )