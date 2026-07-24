-- Main Songs Table
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    duration REAL DEFAULT 0.0,
    lrc_path TEXT,
    play_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lyrics Timestamps Table (Parsed 16x2 dual-line layout)
CREATE TABLE IF NOT EXISTS song_lyrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    timestamp_sec REAL NOT NULL,
    line1 TEXT DEFAULT '',
    line2 TEXT DEFAULT '',
    FOREIGN KEY(song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Tags Table (mood, genre, series, etc.)
CREATE TABLE IF NOT EXISTS song_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    tag_name TEXT NOT NULL,
    FOREIGN KEY(song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Indexing for fast search during touch-sensor browsing
CREATE INDEX IF NOT EXISTS idx_song_title_artist ON songs(title, artist);
CREATE INDEX IF NOT EXISTS idx_lyric_song_time ON song_lyrics(song_id, timestamp_sec);