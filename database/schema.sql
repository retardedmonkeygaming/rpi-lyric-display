CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT,
    duration REAL DEFAULT 0.0,
    play_count INTEGER DEFAULT 0,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lrc_path TEXT,
    mood_tag TEXT,
    default_align TEXT DEFAULT 'center'
);

CREATE TABLE IF NOT EXISTS song_lyrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER,
    timestamp_sec REAL,
    line1 TEXT,
    line2 TEXT,
    align_override TEXT,
    FOREIGN KEY(song_id) REFERENCES songs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS session_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER,
    timestamp TEXT,
    duration_sec REAL,
    status TEXT
);

-- Default Settings
INSERT OR IGNORE INTO settings (key, value) VALUES ('boot_anim', 'true');
INSERT OR IGNORE INTO settings (key, value) VALUES ('idle_speed', '5');
INSERT OR IGNORE INTO settings (key, value) VALUES ('global_align', 'center');