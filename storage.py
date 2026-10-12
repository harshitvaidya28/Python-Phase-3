"""
Rock, Paper, Scissors - Storage & Persistence Module
Handles persistent JSON storage for statistics, achievements, round history,
leaderboard records, and user preferences.
"""

import json
import os
import datetime
from typing import Dict, List, Any, Optional

DATA_FILE = "game_data.json"

ACHIEVEMENT_DEFINITIONS = [
    {
        "id": "first_victory",
        "title": "First Victory",
        "desc": "Win your first round against the computer.",
        "icon": "🏆",
    },
    {
        "id": "winning_streak",
        "title": "Winning Streak",
        "desc": "Win 3 rounds consecutively in a single run.",
        "icon": "🔥",
    },
    {
        "id": "hot_streak",
        "title": "Hot Streak",
        "desc": "Win 5 rounds consecutively without losing or drawing.",
        "icon": "⚡",
    },
    {
        "id": "champion",
        "title": "Match Champion",
        "desc": "Emerge victorious in a Best of 5 or Best of 10 match.",
        "icon": "👑",
    },
    {
        "id": "clean_sweep",
        "title": "Clean Sweep",
        "desc": "Win a Best of 5 match 3-0 without any computer wins.",
        "icon": "💎",
    },
    {
        "id": "veteran",
        "title": "Veteran Player",
        "desc": "Play at least 25 total rounds.",
        "icon": "🎖️",
    },
    {
        "id": "rps_master",
        "title": "RPS Master",
        "desc": "Complete 50 total rounds across any modes.",
        "icon": "⚔️",
    },
    {
        "id": "peacemaker",
        "title": "Peace Maker",
        "desc": "Experience 5 draws total.",
        "icon": "🕊️",
    },
]


def get_default_data() -> Dict[str, Any]:
    """Returns initial fresh data structure."""
    return {
        "settings": {
            "theme": "dark",
            "sound_enabled": True,
            "player_name": "Player 1",
        },
        "statistics": {
            "total_rounds": 0,
            "player_wins": 0,
            "computer_wins": 0,
            "draws": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "match_wins": 0,
            "match_losses": 0,
            "match_ties": 0,
        },
        "achievements": {
            ach["id"]: {"unlocked": False, "unlocked_at": None}
            for ach in ACHIEVEMENT_DEFINITIONS
        },
        "history": [],
        "leaderboard": [],
    }


class StorageManager:
    """Manages loading, updating, and persisting game data."""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Loads data from disk, creating defaults if not present or corrupt."""
        default = get_default_data()
        if not os.path.exists(self.filepath):
            return default

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Ensure all keys and subkeys exist to avoid missing key errors
            for top_key, default_val in default.items():
                if top_key not in loaded:
                    loaded[top_key] = default_val
                elif isinstance(default_val, dict):
                    for sub_key, sub_val in default_val.items():
                        if sub_key not in loaded[top_key]:
                            loaded[top_key][sub_key] = sub_val
            return loaded
        except Exception as e:
            print(f"[Warning] Failed to load {self.filepath}: {e}. Initializing fresh defaults.")
            return default

    def save(self):
        """Persists current data to JSON file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] Failed saving game data: {e}")

    # --- Settings ---
    def get_settings(self) -> Dict[str, Any]:
        return self.data.get("settings", {})

    def update_settings(self, **kwargs):
        settings = self.data.setdefault("settings", {})
        for k, v in kwargs.items():
            settings[k] = v
        self.save()

    # --- Statistics ---
    def get_statistics(self) -> Dict[str, Any]:
        stats = self.data.setdefault("statistics", {})
        total = stats.get("total_rounds", 0)
        wins = stats.get("player_wins", 0)
        
        # Calculate win percentage safely preventing divide-by-zero
        win_rate = (wins / total * 100) if total > 0 else 0.0

        return {
            **stats,
            "win_rate": round(win_rate, 1),
        }

    def reset_statistics(self):
        """Resets gameplay counters while preserving settings."""
        self.data["statistics"] = {
            "total_rounds": 0,
            "player_wins": 0,
            "computer_wins": 0,
            "draws": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "match_wins": 0,
            "match_losses": 0,
            "match_ties": 0,
        }
        self.save()

    # --- Gameplay Recording ---
    def record_round(self, round_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Records a played round, updates stats, streak, history, and awards achievements.
        Returns list of newly unlocked achievements.
        """
        stats = self.data["statistics"]
        result = round_data["result"]

        stats["total_rounds"] += 1

        if result == "win":
            stats["player_wins"] += 1
            stats["current_streak"] += 1
            if stats["current_streak"] > stats["longest_streak"]:
                stats["longest_streak"] = stats["current_streak"]
        elif result == "lose":
            stats["computer_wins"] += 1
            stats["current_streak"] = 0
        else:
            stats["draws"] += 1
            # In RPS, draw generally breaks or halts active win streak
            stats["current_streak"] = 0

        # Append to history (keep latest 100)
        history_item = {
            "round": round_data.get("round_number", stats["total_rounds"]),
            "mode": round_data.get("mode", "Quick Play"),
            "player_choice": round_data.get("player_choice", ""),
            "computer_choice": round_data.get("computer_choice", ""),
            "result": result,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.data.setdefault("history", []).insert(0, history_item)
        if len(self.data["history"]) > 100:
            self.data["history"] = self.data["history"][:100]

        # Check for newly unlocked achievements
        unlocked_now = self._evaluate_achievements(round_data)

        self.save()
        return unlocked_now

    def record_match(self, match_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Records completion of a Best of 5 or Best of 10 match.
        """
        stats = self.data["statistics"]
        winner = match_data.get("match_winner")

        if winner == "player":
            stats["match_wins"] += 1
        elif winner == "computer":
            stats["match_losses"] += 1
        else:
            stats["match_ties"] += 1

        # Record in match leaderboard / performance log
        entry = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "mode": match_data.get("mode", ""),
            "player_score": match_data.get("player_score", 0),
            "computer_score": match_data.get("computer_score", 0),
            "draws": match_data.get("draws", 0),
            "rounds_played": match_data.get("round_number", 0),
            "outcome": "Victory" if winner == "player" else ("Defeat" if winner == "computer" else "Tie"),
            "player_name": self.data.get("settings", {}).get("player_name", "Player 1"),
        }
        self.data.setdefault("leaderboard", []).insert(0, entry)
        if len(self.data["leaderboard"]) > 50:
            self.data["leaderboard"] = self.data["leaderboard"][:50]

        unlocked_now = self._evaluate_achievements(match_data, is_match_end=True)
        self.save()
        return unlocked_now

    def _evaluate_achievements(self, context: Dict[str, Any], is_match_end: bool = False) -> List[Dict[str, str]]:
        """Checks conditions for all achievements and unlocks if met."""
        stats = self.data["statistics"]
        ach_state = self.data.setdefault("achievements", {})
        newly_unlocked = []

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        checks = {
            "first_victory": stats["player_wins"] >= 1,
            "winning_streak": stats["current_streak"] >= 3,
            "hot_streak": stats["current_streak"] >= 5,
            "veteran": stats["total_rounds"] >= 25,
            "rps_master": stats["total_rounds"] >= 50,
            "peacemaker": stats["draws"] >= 5,
        }

        if is_match_end:
            winner = context.get("match_winner")
            p_score = context.get("player_score", 0)
            c_score = context.get("computer_score", 0)
            mode = context.get("mode", "")

            if winner == "player" and mode in ["Best of 5", "Best of 10"]:
                checks["champion"] = True
            
            if winner == "player" and mode == "Best of 5" and p_score >= 3 and c_score == 0:
                checks["clean_sweep"] = True

        for ach_id, condition_met in checks.items():
            if condition_met:
                current = ach_state.setdefault(ach_id, {"unlocked": False, "unlocked_at": None})
                if not current.get("unlocked", False):
                    current["unlocked"] = True
                    current["unlocked_at"] = now_str
                    # Find info
                    info = next((a for a in ACHIEVEMENT_DEFINITIONS if a["id"] == ach_id), None)
                    if info:
                        newly_unlocked.append(info)

        return newly_unlocked

    # --- Achievements & History Queries ---
    def get_achievements(self) -> List[Dict[str, Any]]:
        state = self.data.get("achievements", {})
        result = []
        for defn in ACHIEVEMENT_DEFINITIONS:
            ach_id = defn["id"]
            user_data = state.get(ach_id, {"unlocked": False, "unlocked_at": None})
            result.append({
                **defn,
                "unlocked": user_data.get("unlocked", False),
                "unlocked_at": user_data.get("unlocked_at"),
            })
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        return self.data.get("history", [])

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        return self.data.get("leaderboard", [])

    def clear_history(self):
        """Clears round history and match leaderboard records."""
        self.data["history"] = []
        self.data["leaderboard"] = []
        self.save()
