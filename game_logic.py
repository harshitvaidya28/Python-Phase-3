"""
Rock, Paper, Scissors - Game Logic Module
Handles core game rules, choices, round resolution, and match mode logic.
"""

import random
from typing import Dict, Tuple, Optional

# Choice definitions with labels and icons
CHOICES: Dict[str, Dict[str, str]] = {
    "rock": {"label": "Rock", "emoji": "✊", "beats": "scissors", "description": "Crushes Scissors"},
    "paper": {"label": "Paper", "emoji": "✋", "beats": "rock", "description": "Covers Rock"},
    "scissors": {"label": "Scissors", "emoji": "✌️", "beats": "paper", "description": "Cuts Paper"},
}

CHOICE_KEYS = list(CHOICES.keys())


def get_round_result(player_choice: str, computer_choice: str) -> str:
    """
    Evaluates a round of Rock, Paper, Scissors.
    Returns: 'win', 'lose', or 'draw'
    """
    player = player_choice.lower().strip()
    computer = computer_choice.lower().strip()

    if player == computer:
        return "draw"
    
    if CHOICES.get(player, {}).get("beats") == computer:
        return "win"
    
    return "lose"


def get_random_computer_choice() -> str:
    """Generates a random choice for the computer."""
    return random.choice(CHOICE_KEYS)


class GameMode:
    QUICK_PLAY = "Quick Play"
    BEST_OF_5 = "Best of 5"
    BEST_OF_10 = "Best of 10"

    ALL_MODES = [QUICK_PLAY, BEST_OF_5, BEST_OF_10]


class MatchSession:
    """
    Manages the state of an active match or session across rounds.
    """
    def __init__(self, mode: str = GameMode.QUICK_PLAY):
        self.mode = mode
        self.reset()

    def reset(self):
        """Resets scores and round counts for a new game or match."""
        self.round_number = 0
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0
        self.is_match_over = False
        self.match_winner: Optional[str] = None  # 'player', 'computer', 'tie', or None

    def play_round(self, player_choice: str, computer_choice: Optional[str] = None) -> Dict:
        """
        Executes one round, updates scores, and determines match completion.
        """
        if self.is_match_over:
            raise ValueError("Match is already over. Start a new match to continue.")

        if computer_choice is None:
            computer_choice = get_random_computer_choice()

        result = get_round_result(player_choice, computer_choice)
        self.round_number += 1

        if result == "win":
            self.player_score += 1
            message = "You won this round! Nice move!"
        elif result == "lose":
            self.computer_score += 1
            message = "Computer won this round. Better luck next time!"
        else:
            self.draws += 1
            message = "It's a draw! Both chose the same."

        # Check match completion based on game mode
        self._check_match_status()

        return {
            "round_number": self.round_number,
            "player_choice": player_choice,
            "computer_choice": computer_choice,
            "result": result,
            "message": message,
            "player_score": self.player_score,
            "computer_score": self.computer_score,
            "draws": self.draws,
            "is_match_over": self.is_match_over,
            "match_winner": self.match_winner,
            "mode": self.mode,
        }

    def _check_match_status(self):
        """Determines if Best of 5 or Best of 10 match conditions are met."""
        if self.mode == GameMode.QUICK_PLAY:
            # Unlimited rounds; never ends automatically
            self.is_match_over = False
            self.match_winner = None

        elif self.mode == GameMode.BEST_OF_5:
            # First to 3 wins wins the match
            if self.player_score >= 3:
                self.is_match_over = True
                self.match_winner = "player"
            elif self.computer_score >= 3:
                self.is_match_over = True
                self.match_winner = "computer"
            elif self.round_number >= 5:
                # If 5 rounds played and neither reached 3 (e.g. Due to draws)
                self.is_match_over = True
                if self.player_score > self.computer_score:
                    self.match_winner = "player"
                elif self.computer_score > self.player_score:
                    self.match_winner = "computer"
                else:
                    self.match_winner = "tie"

        elif self.mode == GameMode.BEST_OF_10:
            # Maximum 10 rounds played
            if self.round_number >= 10:
                self.is_match_over = True
                if self.player_score > self.computer_score:
                    self.match_winner = "player"
                elif self.computer_score > self.player_score:
                    self.match_winner = "computer"
                else:
                    self.match_winner = "tie"
            # Early clincher check: if one player has > 5 wins, opponent can't catch up
            elif self.player_score > 5:
                self.is_match_over = True
                self.match_winner = "player"
            elif self.computer_score > 5:
                self.is_match_over = True
                self.match_winner = "computer"
