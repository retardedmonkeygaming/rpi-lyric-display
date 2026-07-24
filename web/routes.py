from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from database.db import DatabaseManager
from core.lrc_parser import LRCParser

web_bp = Blueprint("web", __name__)
db = DatabaseManager()

@web_bp.route("/")
def index():
    """Main Dashboard & Live Status View."""
    songs = db.get_all_songs()
    return render_template("index.html", songs=songs)

@web_bp.route("/library")
def library():
    """Song Library View."""
    songs = db.get_all_songs()
    return render_template("library.html", songs=songs)

@web_bp.route("/upload", methods=["POST"])
def upload_lrc():
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

    return redirect(url_for("web.editor", song_id=song_id))

@web_bp.route("/editor/<int:song_id>")
def editor(song_id: int):
    """Timestamp & Lyric Alignment Editor."""
    lyrics = db.get_song_lyrics(song_id)
    songs = db.get_all_songs()
    song = next((s for s in songs if s["id"] == song_id), None)
    
    if not song:
        return redirect(url_for("web.library"))

    return render_template("editor.html", song=song, lyrics=lyrics)

@web_bp.route("/api/songs/<int:song_id>/lyrics", methods=["POST"])
def update_lyrics(song_id: int):
    """API Endpoint to update modified timestamps."""
    updated_lyrics = request.json.get("lyrics", [])
    
    # Re-insert modified lyrics in database
    with db.get_connection() as conn:
        conn.execute("DELETE FROM song_lyrics WHERE song_id = ?", (song_id,))
        entries = [
            (song_id, round(float(item["timestamp"]), 2), item["line1"][:16], item["line2"][:16])
            for item in updated_lyrics
        ]
        conn.executemany(
            "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
            entries
        )

    return jsonify({"status": "success", "song_id": song_id})
@web_bp.route("/api/songs/<int:song_id>/delete", methods=["POST"])
def delete_song(song_id: int):
    """API Endpoint to delete a song and its associated lyrics."""
    with db.get_connection() as conn:
        conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        # Foreign key CASCADE handles deleting lyrics and tags automatically
    return jsonify({"status": "success", "deleted_id": song_id})
@web_bp.route("/api/songs/<int:song_id>/nudge", methods=["POST"])
def nudge_song_lyrics(song_id: int):
    """Shifts all timestamps for a song by offset_ms (+ or -)."""
    data = request.get_json() or {}
    offset_ms = data.get("offset_ms", 0)
    offset_sec = offset_ms / 1000.0

    with db.get_connection() as conn:
        conn.execute(
            "UPDATE song_lyrics SET timestamp_sec = MAX(0.0, timestamp_sec + ?) WHERE song_id = ?",
            (offset_sec, song_id)
        )
    return jsonify({"status": "success", "song_id": song_id, "shifted_by": offset_sec})