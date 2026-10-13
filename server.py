"""
Rock, Paper, Scissors - Web Server for Render Cloud Deployment
Provides Flask web application, REST API endpoints, and production WSGI entry.
"""

import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, session

from game_logic import CHOICES, CHOICE_KEYS, GameMode, MatchSession, get_round_result, get_random_computer_choice
from storage import StorageManager, ACHIEVEMENT_DEFINITIONS
from ui_theme import THEMES

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "rps-phase3-arcade-secret-key-2026")

storage = StorageManager()

# In-memory match session cache keyed by session ID
active_sessions = {}


def get_or_create_match(mode: str = GameMode.QUICK_PLAY) -> MatchSession:
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    sid = session["session_id"]

    if sid not in active_sessions or active_sessions[sid].mode != mode:
        active_sessions[sid] = MatchSession(mode=mode)
    return active_sessions[sid]


@app.route("/")
def index():
    """Serves the main Arcade Web Application."""
    settings = storage.get_settings()
    return render_template("index.html", initial_theme=settings.get("theme", "dark"))


@app.route("/health")
def health_check():
    """Render health check endpoint ensuring 200 OK."""
    return jsonify({
        "status": "ok",
        "service": "rock-paper-scissors-arcade",
        "version": "3.0"
    }), 200


@app.route("/api/state", methods=["GET"])
def get_state():
    """Returns persistent statistics, settings, achievements, and recent history."""
    stats = storage.get_statistics()
    settings = storage.get_settings()
    history = storage.data.get("history", [])[:20]
    leaderboard = storage.data.get("leaderboard", [])[:20]
    
    # Achievements with full metadata
    ach_state = storage.data.get("achievements", {})
    achievements = []
    for defn in ACHIEVEMENT_DEFINITIONS:
        ach_id = defn["id"]
        ach_info = ach_state.get(ach_id, {"unlocked": False, "unlocked_at": None})
        achievements.append({
            **defn,
            "unlocked": ach_info.get("unlocked", False),
            "unlocked_at": ach_info.get("unlocked_at"),
        })

    # Active match state
    mode = request.args.get("mode", GameMode.QUICK_PLAY)
    match = get_or_create_match(mode)

    return jsonify({
        "settings": settings,
        "statistics": stats,
        "achievements": achievements,
        "history": history,
        "leaderboard": leaderboard,
        "match": {
            "mode": match.mode,
            "round_number": match.round_number,
            "player_score": match.player_score,
            "computer_score": match.computer_score,
            "draws": match.draws,
            "is_match_over": match.is_match_over,
            "match_winner": match.match_winner,
        }
    })


@app.route("/api/play", methods=["POST"])
def play():
    """Executes a round of RPS and updates stats and achievements."""
    data = request.get_json() or {}
    player_choice = (data.get("player_choice") or "rock").lower().strip()
    mode = data.get("mode") or GameMode.QUICK_PLAY

    if player_choice not in CHOICES:
        return jsonify({"error": f"Invalid choice '{player_choice}'"}), 400

    match = get_or_create_match(mode)

    # If the previous match concluded, reset for new match
    if match.is_match_over:
        match.reset()

    # Determine computer weapon
    computer_choice = get_random_computer_choice()
    
    # Execute round
    round_outcome = match.play_round(player_choice, computer_choice)

    # Record in persistent storage
    newly_unlocked = storage.record_round({
        "round_number": match.round_number,
        "mode": match.mode,
        "player_choice": player_choice,
        "computer_choice": computer_choice,
        "result": round_outcome["result"],
    })

    # If match just completed (Bo5 or Bo10), record match outcome
    if match.is_match_over:
        match_unlocked = storage.record_match({
            "mode": match.mode,
            "match_winner": match.match_winner,
            "player_score": match.player_score,
            "computer_score": match.computer_score,
            "draws": match.draws,
            "round_number": match.round_number,
        })
        newly_unlocked.extend(match_unlocked)

    return jsonify({
        "round_outcome": round_outcome,
        "statistics": storage.get_statistics(),
        "newly_unlocked": newly_unlocked,
        "player_meta": CHOICES[player_choice],
        "computer_meta": CHOICES[computer_choice],
    })


@app.route("/api/reset-match", methods=["POST"])
def reset_match():
    """Resets the active match session for the selected mode."""
    data = request.get_json() or {}
    mode = data.get("mode") or GameMode.QUICK_PLAY
    match = get_or_create_match(mode)
    match.reset()
    return jsonify({
        "success": True,
        "match": {
            "mode": match.mode,
            "round_number": match.round_number,
            "player_score": match.player_score,
            "computer_score": match.computer_score,
            "draws": match.draws,
            "is_match_over": match.is_match_over,
            "match_winner": match.match_winner,
        }
    })


@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Updates user preferences (theme, sound, player name)."""
    data = request.get_json() or {}
    storage.update_settings(**data)
    return jsonify({"success": True, "settings": storage.get_settings()})


@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    """Resets all gameplay history, leaderboard, and statistics."""
    storage.reset_statistics()
    storage.data["history"] = []
    storage.data["leaderboard"] = []
    storage.save()
    return jsonify({"success": True, "statistics": storage.get_statistics()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
