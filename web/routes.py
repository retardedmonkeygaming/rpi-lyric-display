from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from database.db import DatabaseManager
from core.lrc_parser import LRCParser
from core.sentiment import SentimentScorer
from core.line_splitter import LineSplitter

web_bp = Blueprint("web", __name__)
db = DatabaseManager()

# ==========================================
# 1. PAGE NAVIGATION ROUTES
# ==========================================

@web_bp.route("/")
def index():
    """Redirect root access directly to the main library dashboard."""
    return redirect(url_for("web.library_page"))


@web_bp.route("/library")
def library_page():
    """Song Library View."""
    songs = db.get_all_songs()
    return render_template("library.html", songs=songs)


@web_bp.route("/editor/<int:song_id>")
def editor_page(song_id: int):
    """Timestamp & Lyric Alignment Editor."""
    song = db.get_song_by_id(song_id)
    if not song:
        return redirect(url_for("web.library_page"))

    lyrics = db.get_song_lyrics(song_id)
    return render_template("editor.html", song=song, lyrics=lyrics)


# ==========================================
# 2. UPLOAD & MANAGEMENT ROUTES
# ==========================================

@web_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handles .lrc file upload and parses content into SQLite."""
    title = request.form.get("title", "").strip()
    artist = request.form.get("artist", "").strip()
    tags_raw = request.form.get("tags", "")
    lrc_file = request.files.get("lrc_file")

    if not title or not artist or not lrc_file:
        return jsonify({"error": "Missing required title, artist, or LRC file"}), 400

    content = lrc_file.read().decode("utf-8", errors="ignore")
    parsed_lyrics = LRCParser.parse_lrc_content(content)
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

    song_id = db.add_song(
        title=title,
        artist=artist,
        lyrics=parsed_lyrics,
        tags=tags
    )

    return redirect(url_for("web.editor_page", song_id=song_id))


@web_bp.route("/api/songs/<int:song_id>/delete", methods=["POST"])
def delete_song(song_id: int):
    """API Endpoint to delete a song and its associated lyrics."""
    with db.get_connection() as conn:
        conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    return jsonify({"status": "success", "deleted_id": song_id})


# ==========================================
# 3. SEARCH & RECORDING API ENDPOINTS
# ==========================================

@web_bp.route("/api/songs/search", methods=["GET"])
def search_songs():
    """Search and filter songs by title, artist, or tags."""
    query = request.args.get("q", "").strip().lower()
    tag = request.args.get("tag", "").strip().lower()
    songs = db.get_all_songs()

    filtered = []
    for s in songs:
        matches_q = not query or (query in s["title"].lower() or query in s["artist"].lower())
        matches_tag = not tag or (tag in str(s.get("tags", "")).lower())
        if matches_q and matches_tag:
            filtered.append(s)

    return jsonify({"status": "success", "songs": filtered})


@web_bp.route("/api/recording/start", methods=["POST"])
def start_recording_mode():
    """Triggers the 1602 LCD recording countdown mode from web or remote HTTP."""
    data = request.get_json(silent=True) or {}
    song_id = data.get("song_id")
    countdown = data.get("countdown_sec", 3)

    if not song_id:
        return jsonify({"status": "error", "message": "Missing song_id"}), 400

    # Retrieve engine instance from Flask app config
    engine = current_app.config.get("LYRIC_APP")
    if engine:
        engine.trigger_recording_mode(int(song_id), countdown_sec=countdown)
        return jsonify({"status": "success", "recording_song_id": song_id, "countdown": countdown})

    return jsonify({"status": "error", "message": "App engine offline"}), 500


@web_bp.route("/api/remote/play", methods=["POST"])
def remote_play_trigger():
    """HTTP Remote Trigger for hands-free recording initiation."""
    return start_recording_mode()


# ==========================================
# 4. LYRIC TIMELINE & UTILITY ENDPOINTS
# ==========================================

@web_bp.route("/api/songs/<int:song_id>/lyrics", methods=["POST"])
def update_lyrics(song_id: int):
    """API Endpoint to update modified timestamps in bulk."""
    updated_lyrics = request.json.get("lyrics", [])

    with db.get_connection() as conn:
        conn.execute("DELETE FROM song_lyrics WHERE song_id = ?", (song_id,))
        entries = [
            (song_id, round(float(item["timestamp"]), 2), str(item["line1"])[:16], str(item["line2"])[:16])
            for item in updated_lyrics
        ]
        conn.executemany(
            "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
            entries
        )

    return jsonify({"status": "success", "song_id": song_id})


@web_bp.route("/api/lyrics/<int:song_id>/update-line", methods=["POST"])
def update_lyric_line(song_id: int):
    """Update a single line's timing or text."""
    data = request.get_json(silent=True) or {}
    line_index = data.get("index")
    new_timestamp = data.get("timestamp_sec")
    new_line1 = data.get("line1", "")[:16]
    new_line2 = data.get("line2", "")[:16]

    lyrics = db.get_song_lyrics(song_id)
    if line_index is None or line_index >= len(lyrics):
        return jsonify({"status": "error", "message": "Invalid line index"}), 400

    lyrics[line_index] = (float(new_timestamp), new_line1, new_line2)

    with db.get_connection() as conn:
        conn.execute("DELETE FROM song_lyrics WHERE song_id = ?", (song_id,))
        entries = [(song_id, ts, l1, l2) for ts, l1, l2 in lyrics]
        conn.executemany(
            "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
            entries
        )

    return jsonify({"status": "success", "updated_index": line_index})


@web_bp.route("/api/songs/<int:song_id>/nudge", methods=["POST"])
def nudge_song_lyrics(song_id: int):
    """Shifts all timestamps for a song by offset_ms (+ or -)."""
    data = request.get_json(silent=True) or {}
    offset_ms = data.get("offset_ms", 0)
    offset_sec = float(offset_ms) / 1000.0

    try:
        with db.get_connection() as conn:
            conn.execute(
                "UPDATE song_lyrics SET timestamp_sec = MAX(0.0, timestamp_sec + ?) WHERE song_id = ?",
                (offset_sec, song_id)
            )
        return jsonify({"status": "success", "song_id": song_id, "shifted_by": offset_sec})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@web_bp.route("/api/utils/split-text", methods=["POST"])
def split_text_utility():
    """Smart line splitting utility for 16-character LCD formatting."""
    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")
    line1, line2 = LineSplitter.split_text(raw_text)
    return jsonify({"status": "success", "line1": line1, "line2": line2})


@web_bp.route("/api/songs/<int:song_id>/analyze-sentiment", methods=["GET"])
def analyze_song_sentiment(song_id: int):
    """Scans song lyrics and returns suggested mood tags."""
    lyrics = db.get_song_lyrics(song_id)
    full_text = " ".join([f"{l1} {l2}" for _, l1, l2 in lyrics])
    mood, confidence = SentimentScorer.analyze_text(full_text)
    return jsonify({"status": "success", "suggested_mood": mood, "confidence": confidence})