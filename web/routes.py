from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from database.db import DatabaseManager
from core.content_processor import ContentProcessor

web_bp = Blueprint("web", __name__)
db = DatabaseManager()


@web_bp.route("/api/songs/<int:song_id>/auto-emoji-lines", methods=["POST"])
def auto_emoji_lines(song_id: int):
    """Analyzes every line and injects hardware icons (\x00-\x07) into the DB."""
    lyrics = db.get_song_lyrics(song_id)
    if not lyrics:
        return jsonify({"status": "error", "message": "No lyrics"}), 400

    updated_lyrics = []
    for ts, l1, l2 in lyrics:
        # Process Line 1: Inject hardware-specific icon index
        new_l1 = ContentProcessor.process_line_with_icon(l1)
        updated_lyrics.append((ts, new_l1, l2))

    # Perform the database update
    with db.get_connection() as conn:
        conn.execute("DELETE FROM song_lyrics WHERE song_id = ?", (song_id,))
        conn.executescript("BEGIN TRANSACTION;")
        conn.executemany(
            "INSERT INTO song_lyrics (song_id, timestamp_sec, line1, line2) VALUES (?, ?, ?, ?)",
            [(song_id, ts, l1, l2) for ts, l1, l2 in updated_lyrics]
        )
        conn.execute("COMMIT;")

    return jsonify({"status": "success", "line_count": len(updated_lyrics)})

@web_bp.route("/api/songs/<int:song_id>/analyze-sentiment", methods=["GET"])
def analyze_sentiment(song_id: int):
    """Returns a purely hardware-compatible icon suggestion."""
    lyrics = db.get_song_lyrics(song_id)
    full_text = " ".join([f"{l[1]} {l[2]}" for l in lyrics])
    
    icon_char = ContentProcessor.pick_icon_for_text(full_text)
    
    # We send a readable name to the Web UI, but use the icon_char for hardware
    return jsonify({
        "status": "success",
        "suggested_mood": "Detected",
        "emoji": "Icon Assigned" if icon_char else "None",
        "confidence": 1.0
    })


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

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from database.db import DatabaseManager
from core.content_processor import ContentProcessor

web_bp = Blueprint("web", __name__)
db = DatabaseManager()

@web_bp.route("/library")
def library_page():
    return render_template("library.html", songs=db.get_all_songs())

@web_bp.route("/editor/<int:song_id>")
def editor_page(song_id: int):
    songs = db.get_all_songs()
    song = next((s for s in songs if s["id"] == song_id), None)
    if not song: return redirect(url_for("web.library_page"))
    return render_template("editor.html", song=song, lyrics=db.get_song_lyrics(song_id))

@web_bp.route("/api/songs/<int:song_id>/analyze-sentiment", methods=["GET"])
def analyze_sentiment(song_id: int):
    lyrics = db.get_song_lyrics(song_id)
    full_text = " ".join([f"{l[1]} {l[2]}" for l in lyrics])
    icon, mood = ContentProcessor.analyze(full_text)
    
    return jsonify({
        "status": "success",
        "suggested_mood": mood,
        "emoji": "Icon Found" if icon else "None",
        "confidence": 0.85
    })

@web_bp.route("/api/songs/<int:song_id>/auto-emoji-lines", methods=["POST"])
def auto_emoji_lines(song_id: int):
    lyrics = db.get_song_lyrics(song_id)
    new_data = []
    for ts, l1, l2 in lyrics:
        # Prepend hardware code (\x01 etc) based on content
        new_l1 = ContentProcessor.process_line(l1)
        new_data.append((ts, new_l1, l2))
    
    db.bulk_update_lyrics(song_id, new_data)
    return jsonify({"status": "success", "line_count": len(new_data)})

@web_bp.route("/api/recording/start", methods=["POST"])
def start_rec():
    sid = request.json.get("song_id")
    engine = current_app.config.get("LYRIC_APP")
    if engine:
        engine.trigger_playback(sid)
        return jsonify({"status": "success"})
    return jsonify({"status": "offline"}), 500