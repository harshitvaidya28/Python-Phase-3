"""
Unit tests for Rock, Paper, Scissors game logic, storage, and rules.
Tests all scenarios specified in requirements:
- Player win, computer win, draw rules
- Quick Play, Best of 5, Best of 10 modes
- Streak calculations
- Achievement unlocks
- Win percentage calculations (including division by zero)
- JSON persistence, loading, resetting, clearing history
"""

import os
import unittest
from game_logic import get_round_result, MatchSession, GameMode, CHOICES
from storage import StorageManager, get_default_data, DATA_FILE


class TestGameLogic(unittest.TestCase):
    def test_rules(self):
        # Rock beats scissors
        self.assertEqual(get_round_result("rock", "scissors"), "win")
        self.assertEqual(get_round_result("scissors", "rock"), "lose")
        # Scissors beats paper
        self.assertEqual(get_round_result("scissors", "paper"), "win")
        self.assertEqual(get_round_result("paper", "scissors"), "lose")
        # Paper beats rock
        self.assertEqual(get_round_result("paper", "rock"), "win")
        self.assertEqual(get_round_result("rock", "paper"), "lose")
        # Draws
        self.assertEqual(get_round_result("rock", "rock"), "draw")
        self.assertEqual(get_round_result("paper", "paper"), "draw")
        self.assertEqual(get_round_result("scissors", "scissors"), "draw")

    def test_quick_play_unlimited(self):
        session = MatchSession(GameMode.QUICK_PLAY)
        for i in range(12):
            res = session.play_round("rock", "scissors")
            self.assertEqual(res["result"], "win")
            self.assertFalse(res["is_match_over"])
            self.assertIsNone(res["match_winner"])
        self.assertEqual(session.player_score, 12)
        self.assertEqual(session.round_number, 12)

    def test_best_of_5_first_to_3(self):
        session = MatchSession(GameMode.BEST_OF_5)
        # Player wins 3 in a row
        session.play_round("rock", "scissors")
        session.play_round("rock", "scissors")
        res = session.play_round("rock", "scissors")
        self.assertTrue(res["is_match_over"])
        self.assertEqual(res["match_winner"], "player")
        self.assertEqual(session.player_score, 3)

    def test_best_of_5_tie_handling(self):
        session = MatchSession(GameMode.BEST_OF_5)
        # 5 draws in a row
        for _ in range(4):
            session.play_round("rock", "rock")
        res = session.play_round("rock", "rock")
        self.assertTrue(res["is_match_over"])
        self.assertEqual(res["match_winner"], "tie")

    def test_best_of_10_completion(self):
        session = MatchSession(GameMode.BEST_OF_10)
        # 6 wins for player -> early clinch or 10 rounds
        for _ in range(6):
            res = session.play_round("rock", "scissors")
        self.assertTrue(res["is_match_over"])
        self.assertEqual(res["match_winner"], "player")


class TestStorageAndStats(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_game_data.json"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        self.storage = StorageManager(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_zero_division_safety(self):
        stats = self.storage.get_statistics()
        self.assertEqual(stats["total_rounds"], 0)
        self.assertEqual(stats["win_rate"], 0.0)

    def test_streaks_and_achievements(self):
        # Round 1: Win -> unlocks first_victory
        unlocked = self.storage.record_round({
            "round_number": 1,
            "player_choice": "rock",
            "computer_choice": "scissors",
            "result": "win",
            "mode": "Quick Play",
        })
        self.assertTrue(any(a["id"] == "first_victory" for a in unlocked))
        stats = self.storage.get_statistics()
        self.assertEqual(stats["current_streak"], 1)
        self.assertEqual(stats["longest_streak"], 1)

        # Round 2: Win
        self.storage.record_round({
            "round_number": 2,
            "player_choice": "paper",
            "computer_choice": "rock",
            "result": "win",
            "mode": "Quick Play",
        })

        # Round 3: Win -> unlocks winning_streak (streak of 3)
        unlocked = self.storage.record_round({
            "round_number": 3,
            "player_choice": "scissors",
            "computer_choice": "paper",
            "result": "win",
            "mode": "Quick Play",
        })
        self.assertTrue(any(a["id"] == "winning_streak" for a in unlocked))
        stats = self.storage.get_statistics()
        self.assertEqual(stats["current_streak"], 3)
        self.assertEqual(stats["longest_streak"], 3)
        self.assertEqual(stats["win_rate"], 100.0)

        # Round 4: Draw -> resets current streak, keeps longest streak
        self.storage.record_round({
            "round_number": 4,
            "player_choice": "rock",
            "computer_choice": "rock",
            "result": "draw",
            "mode": "Quick Play",
        })
        stats = self.storage.get_statistics()
        self.assertEqual(stats["current_streak"], 0)
        self.assertEqual(stats["longest_streak"], 3)
        self.assertEqual(stats["draws"], 1)

    def test_persistence_reloading(self):
        self.storage.update_settings(theme="light", sound_enabled=False)
        self.storage.record_round({
            "round_number": 1,
            "player_choice": "rock",
            "computer_choice": "scissors",
            "result": "win",
            "mode": "Quick Play",
        })

        # Create new manager pointing to same file
        reloaded = StorageManager(self.test_file)
        settings = reloaded.get_settings()
        self.assertEqual(settings["theme"], "light")
        self.assertFalse(settings["sound_enabled"])
        self.assertEqual(reloaded.get_statistics()["total_rounds"], 1)

    def test_clear_history(self):
        self.storage.record_round({
            "round_number": 1,
            "player_choice": "rock",
            "computer_choice": "scissors",
            "result": "win",
            "mode": "Quick Play",
        })
        self.assertGreater(len(self.storage.get_history()), 0)
        self.storage.clear_history()
        self.assertEqual(len(self.storage.get_history()), 0)


if __name__ == "__main__":
    unittest.main()
