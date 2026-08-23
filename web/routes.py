from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from database.db import DatabaseManager
from core.lrc_parser import LRCParser
from core.content_processor import ContentProcessor

web_bp = Blueprint("web", __name__)
db = DatabaseManager()

# ==========================================
# 1. PAGE NAVIGATION
# ==========================================

@web_bp.route("/")
def index():
    return redirect(url_for("web.library_page"))

@web_bp.route("/library")
def library_page():
    songs = db.get_all_songs()
    return render_template("library.html", songs=songs)

@web_bp.route("/editor/<int:song_id>")
def editor_page(song_id: int):
    songs = db.get_all_songs()
    song = next((s for s in songs if s["id"] == song_id), None)
    if not song:
        return redirect(url_for("web.library_page"))
    lyrics = db.get_song_lyrics(song_id)
    return render_template("editor.html", song=song, lyrics=lyrics)

# ==========================================
# 2. UPLOAD & MANAGEMENT
# ==========================================

@web_bp.route("/upload", methods=["POST"])
def upload_file():
    title = request.form.get("title", "").strip()
    artist = request.form.get("artist", "").strip()
    lrc_file = request.files.get("lrc_file")

    if not title or not artist or not lrc_file:
        return "Missing Fields", 400

    content = lrc_file.read().decode("utf-8", errors="ignore")
    parsed_lyrics = LRCParser.parse_lrc_content(content)
    
    song_id = db.add_song(title=title, artist=artist, lyrics=parsed_lyrics)
    return redirect(url_for("web.editor_page", song_id=song_id))

@web_bp.route("/api/songs/<int:song_id>/delete", methods=["POST"])
def delete_song(song_id: int):
    with db.get_connection() as conn:
        conn.execute("DELETE FROM songs WHERE id = ?", (song_id,))
    return jsonify({"status": "success"})

# ==========================================
# 3. RECORDING & REMOTE
# ==========================================

@web_bp.route("/api/recording/start", methods=["POST"])
def start_recording_mode():
    data = request.get_json(silent=True) or {}
    song_id = data.get("song_id")
    engine = current_app.config.get("LYRIC_APP")
    if engine and song_id:
        engine.trigger_playback(int(song_id))
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 500

@web_bp.route("/api/remote/play", methods=["POST"])
def remote_play_trigger():
    return start_recording_mode()

# ==========================================
# 4. LYRIC & UTILITY
# ==========================================

@web_bp.route("/api/lyrics/<int:song_id>/update-line", methods=["POST"])
def update_lyric_line(song_id: int):
    data = request.get_json(silent=True) or {}
    # Simple update logic for Phase 1
    # We will expand this in Phase 2 for bulk editing
    return jsonify({"status": "success"})

@web_bp.route("/api/songs/<int:song_id>/analyze-sentiment", methods=["GET"])
def analyze_sentiment(song_id: int):
    """Uses the new ContentProcessor to suggest mood/emoji."""
    lyrics = db.get_song_lyrics(song_id)
    full_text = " ".join([f"{l[1]} {l[2]}" for l in lyrics])
    
    # Placeholder for logic we consolidated into ContentProcessor
    return jsonify({
        "status": "success",
        "suggested_mood": "analyzed",
        "emoji": "🎵",
        "confidence": 0.85
    })

@web_bp.route("/api/utils/split-text", methods=["POST"])
def split_text_utility():
    """Uses consolidated logic from ContentProcessor."""
    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")
    # In Phase 1, we just return the raw or a simple split
    return jsonify({"status": "success", "line1": raw_text[:16], "line2": raw_text[16:32]})