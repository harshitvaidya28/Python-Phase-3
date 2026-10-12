# ✊✋✌️ Rock, Paper, Scissors — Phase 3 Arcade Edition

A complete, premium, interactive desktop gaming application built entirely in **Python** using **CustomTkinter**.

---

## 🎮 Highlights & Features

1. **Pure Python Architecture**:
   - Zero web dependencies: No HTML, CSS, JavaScript, or Flask.
   - High-performance, modern GUI built with **CustomTkinter 6.0**.
   - Built-in multi-threaded synthesizer using Windows `winsound` for zero-dependency audio cues.

2. **Arcade Visuals & Animations**:
   - **Neon Dark Arcade** and **Modern Light** themes.
   - Large visual emojis (`✊`, `✋`, `✌️`) and responsive card layouts.
   - **Non-blocking 3-2-1 Animated Countdown** with live opponent shuffle before reveal.
   - **Canvas Particle Physics Confetti Celebration** upon victory!
   - Defeat, tie, and victory visual banners and sound cues.

3. **3 Playable Game Modes**:
   - **⚡ Quick Play**: Unlimited casual rounds; stop whenever you like.
   - **🏆 Best of 5**: Tournament rules — first to 3 wins takes the match.
   - **⚔️ Best of 10**: Endurance battle — 10 rounds maximum; highest score wins.

4. **Advanced Statistics & Streaks**:
   - Total rounds, Player wins, Computer wins, and Draws.
   - Real-time win rate percentage with zero-division safety.
   - Current consecutive winning streak and all-time longest streak.
   - Complete tournament match win/loss/tie tally.

5. **Achievements System (8 Badges)**:
   - Unlockable trophies with animated real-time toast notifications:
     - 🏆 **First Victory**: Win your first round.
     - 🔥 **Winning Streak**: Win 3 rounds consecutively.
     - ⚡ **Hot Streak**: Win 5 rounds consecutively.
     - 👑 **Match Champion**: Win a Best of 5 or Best of 10 match.
     - 💎 **Clean Sweep**: Win a Best of 5 match 3-0.
     - 🎖️ **Veteran Player**: Complete 25 rounds.
     - ⚔️ **RPS Master**: Complete 50 total rounds.
     - 🕊️ **Peace Maker**: Record 5 draws.

6. **Round History & Match Leaderboard**:
   - Detailed round logs with player weapon, AI weapon, outcome badge, and timestamp.
   - Local match tournament performance board against the AI opponent.
   - Atomic persistent storage using `game_data.json`.
   - Clear history with confirmation safeguard.

---

## 🛠️ Requirements & Installation

- **Python 3.9+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- **Windows / macOS / Linux**

Install the single GUI dependency via terminal:

```bash
pip install -r requirements.txt
```

*(Note: CustomTkinter is the only lightweight external library needed. Sound uses Python's built-in `winsound` on Windows).*

---

## 🚀 How to Run in VS Code

1. Open this project folder in **VS Code**.
2. Open the built-in terminal (`Ctrl + ~` or `Terminal -> New Terminal`).
3. Run either of the following commands:

```bash
python main.py
```
*(or `python app.py`)*

---

## 📁 Project Structure

```text
rock_paper_scissors_phase3/
├── app.py             # Main CustomTkinter GUI application with all screens & animations
├── main.py            # Standard entry point for launching the app
├── game_logic.py      # Core game rules, weapon definitions, and match session manager
├── storage.py         # Persistent JSON storage for statistics, achievements & history
├── sound.py           # Multi-threaded zero-dependency retro audio synthesizer
├── ui_theme.py        # Color palettes and styling tokens for Neon Dark & Light themes
├── test_game.py       # Automated unit test suite verifying rules, modes & persistence
├── requirements.txt   # Lightweight requirements file (customtkinter)
├── game_data.json     # Auto-generated persistent data file (created at runtime)
└── README.md          # Project documentation
```

---

## 🧪 Running Automated Tests

To verify rules, modes, win rates, achievements, and JSON persistence:

```bash
python test_game.py
```
