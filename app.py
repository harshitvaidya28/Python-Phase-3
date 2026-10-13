"""
Rock, Paper, Scissors — Phase 3 Arcade Edition
Streamlit Cloud & Render Web Application
Responsive browser-based arcade game with particle effects, custom CSS themes,
Web Audio synthesis, tournament modes, achievements, and persistent statistics.
"""

import os
import time
import random
from typing import Dict, Any, List

import streamlit as st
import streamlit.components.v1 as components

from game_logic import CHOICES, CHOICE_KEYS, GameMode, MatchSession, get_random_computer_choice
from storage import StorageManager, ACHIEVEMENT_DEFINITIONS
from ui_theme import get_theme, THEMES


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Rock, Paper, Scissors — Phase 3 Arcade",
    page_icon="✊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "storage" not in st.session_state:
    st.session_state.storage = StorageManager()

storage: StorageManager = st.session_state.storage
saved_settings = storage.get_settings()

if "theme" not in st.session_state:
    st.session_state.theme = saved_settings.get("theme", "dark")

if "sound_enabled" not in st.session_state:
    st.session_state.sound_enabled = saved_settings.get("sound_enabled", True)

if "player_name" not in st.session_state:
    st.session_state.player_name = saved_settings.get("player_name", "Player 1")

if "mode" not in st.session_state:
    st.session_state.mode = GameMode.QUICK_PLAY

if "match" not in st.session_state:
    st.session_state.match = MatchSession(mode=st.session_state.mode)

if "last_round" not in st.session_state:
    st.session_state.last_round = None

if "audio_cue" not in st.session_state:
    st.session_state.audio_cue = None

if "animating_choice" not in st.session_state:
    st.session_state.animating_choice = None


# ---------------------------------------------------------------------------
# Web Audio API Synthesizer (Zero external files needed)
# ---------------------------------------------------------------------------
def play_web_audio(cue: str):
    """Injects a tiny Web Audio API synthesizer snippet into the browser."""
    if not st.session_state.sound_enabled or not cue:
        return

    tones_map = {
        "click": "[{f: 800, d: 35, t: 'sine'}]",
        "tick": "[{f: 650, d: 80, t: 'triangle'}]",
        "go": "[{f: 980, d: 150, t: 'square'}]",
        "win": "[{f: 523.25, d: 100, t: 'triangle'}, {f: 659.25, d: 100, t: 'triangle'}, {f: 783.99, d: 100, t: 'triangle'}, {f: 1046.5, d: 250, t: 'triangle'}]",
        "lose": "[{f: 440, d: 130, t: 'sawtooth'}, {f: 349.23, d: 130, t: 'sawtooth'}, {f: 261.63, d: 240, t: 'sawtooth'}]",
        "draw": "[{f: 500, d: 120, t: 'sine'}, {f: 500, d: 160, t: 'sine'}]",
        "achievement": "[{f: 587.33, d: 90, t: 'sine'}, {f: 739.99, d: 90, t: 'sine'}, {f: 880.0, d: 90, t: 'sine'}, {f: 1174.66, d: 250, t: 'sine'}]",
    }

    tones = tones_map.get(cue)
    if not tones:
        return

    html_code = f"""
    <script>
    (function() {{
        try {{
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            const ctx = new AudioCtx();
            const sequence = {tones};
            let startTime = ctx.currentTime;
            sequence.forEach(item => {{
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = item.t || 'sine';
                osc.frequency.setValueAtTime(item.f, startTime);
                gain.gain.setValueAtTime(0.18, startTime);
                gain.gain.exponentialRampToValueAtTime(0.0001, startTime + (item.d / 1000));
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(startTime);
                osc.stop(startTime + (item.d / 1000));
                startTime += (item.d / 1000) * 1.05;
            }});
        }} catch(e) {{}}
    }})();
    </script>
    """
    components.html(html_code, height=0, width=0)


# ---------------------------------------------------------------------------
# Custom CSS Theming & Arcade Stylesheet
# ---------------------------------------------------------------------------
theme_colors = get_theme(st.session_state.theme)
is_dark = st.session_state.theme == "dark"

custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700;800;900&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background-color: {theme_colors["bg_main"]};
    color: {theme_colors["text_primary"]};
}}

/* Arcade Header */
.arcade-header-box {{
    background: {theme_colors["bg_card"]};
    border: 1px solid {theme_colors["border_color"]};
    border-radius: 18px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
}}

.arcade-title {{
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 2rem;
    letter-spacing: 1px;
    background: linear-gradient(135deg, {theme_colors["accent_cyan"]}, {theme_colors["accent_pink"]});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}}

.arcade-subtag {{
    color: {theme_colors["accent_cyan"]};
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    background: rgba(0, 245, 255, 0.1);
    padding: 3px 10px;
    border-radius: 99px;
    border: 1px solid rgba(0, 245, 255, 0.3);
}}

/* Arena Cards */
.combat-card {{
    background: {theme_colors["bg_card"]};
    border: 1px solid {theme_colors["border_color"]};
    border-radius: 20px;
    padding: 1.6rem;
    text-align: center;
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
    transition: transform 0.2s ease;
}}

.combat-card:hover {{
    border-color: {theme_colors["border_accent"]};
}}

.weapon-preview-large {{
    font-size: 4.8rem;
    line-height: 1;
    margin: 0.8rem 0;
    filter: drop-shadow(0 4px 15px rgba(0, 0, 0, 0.5));
}}

.card-tag {{
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 800;
    padding: 3px 12px;
    border-radius: 99px;
    margin-bottom: 0.4rem;
}}

.tag-player {{
    background: rgba(0, 245, 255, 0.15);
    color: {theme_colors["accent_cyan"]};
    border: 1px solid {theme_colors["accent_cyan"]};
}}

.tag-ai {{
    background: rgba(255, 0, 127, 0.15);
    color: {theme_colors["accent_pink"]};
    border: 1px solid {theme_colors["accent_pink"]};
}}

/* Outcome Banners */
.outcome-banner {{
    border-radius: 16px;
    padding: 1.1rem;
    text-align: center;
    margin: 1rem 0;
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
}}

.outcome-win {{
    background: rgba(0, 255, 157, 0.12);
    border: 2px solid {theme_colors["result_win"]};
    color: {theme_colors["result_win"]};
    box-shadow: 0 0 20px rgba(0, 255, 157, 0.3);
}}

.outcome-lose {{
    background: rgba(255, 0, 127, 0.12);
    border: 2px solid {theme_colors["result_lose"]};
    color: {theme_colors["result_lose"]};
    box-shadow: 0 0 20px rgba(255, 0, 127, 0.3);
}}

.outcome-draw {{
    background: rgba(255, 215, 0, 0.12);
    border: 2px solid {theme_colors["result_draw"]};
    color: {theme_colors["result_draw"]};
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
}}

/* Achievement Cards */
.ach-badge-card {{
    background: {theme_colors["bg_card_secondary"]};
    border: 1px solid {theme_colors["border_color"]};
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.8rem;
}}

.ach-unlocked {{
    border-color: {theme_colors["accent_yellow"]};
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.25);
}}

.ach-locked {{
    opacity: 0.55;
    filter: grayscale(0.7);
}}

.streak-flame {{
    color: {theme_colors["accent_yellow"]};
    font-size: 1.3rem;
}}

/* Button styles */
div.stButton > button {{
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    border-radius: 12px;
    padding: 0.7rem 1.2rem;
    transition: all 0.2s ease;
}}

div.stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 245, 255, 0.3);
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar Settings & Customization
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Arcade Settings")

    # Player Name
    new_player_name = st.text_input("Player Tag", value=st.session_state.player_name, max_chars=20)
    if new_player_name != st.session_state.player_name:
        st.session_state.player_name = new_player_name.strip() or "Player 1"
        storage.update_settings(player_name=st.session_state.player_name)
        st.rerun()

    # Theme Toggle
    theme_options = ["Neon Dark Arcade", "Modern Light"]
    current_idx = 0 if st.session_state.theme == "dark" else 1
    selected_theme_label = st.radio("Theme Palette", theme_options, index=current_idx)
    new_theme = "dark" if selected_theme_label == "Neon Dark Arcade" else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        storage.update_settings(theme=new_theme)
        st.rerun()

    # Sound Toggle
    sound_toggle = st.toggle("Audio Synthesizer", value=st.session_state.sound_enabled)
    if sound_toggle != st.session_state.sound_enabled:
        st.session_state.sound_enabled = sound_toggle
        storage.update_settings(sound_enabled=sound_toggle)
        st.rerun()

    st.divider()

    st.markdown("### 📜 Rules Quick Guide")
    st.markdown("""
    - ✊ **Rock** crushes ✌️ **Scissors**
    - ✋ **Paper** covers ✊ **Rock**
    - ✌️ **Scissors** cuts ✋ **Paper**
    """)

    st.markdown("### 🎮 Game Modes")
    st.markdown("""
    - **⚡ Quick Play**: Casual unlimited clashes.
    - **🏆 Best of 5**: Tournament (First to 3 wins).
    - **⚔️ Best of 10**: Endurance (10 rounds max).
    """)

    st.divider()
    st.caption("Rock, Paper, Scissors — Phase 3 Complete Streamlit Edition\nDeployable on Render Cloud 🚀")


# ---------------------------------------------------------------------------
# Header Section
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="arcade-header-box">
    <div>
        <h1 class="arcade-title">✊✋✌️ RPS ARCADE</h1>
        <span class="arcade-subtag">PHASE 3 COMPLETE &bull; STREAMLIT EDITION</span>
    </div>
    <div style="text-align: right;">
        <span style="font-weight: 700; font-size: 1.1rem; color: {theme_colors['text_primary']};">👤 {st.session_state.player_name}</span>
        <br>
        <span style="font-size: 0.8rem; color: {theme_colors['text_secondary']};">Audio: {'🔊 On' if st.session_state.sound_enabled else '🔇 Muted'} &bull; Theme: {theme_colors['name']}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Mode Selection Bar
# ---------------------------------------------------------------------------
mode_cols = st.columns([1, 1, 1, 1])

mode_list = [GameMode.QUICK_PLAY, GameMode.BEST_OF_5, GameMode.BEST_OF_10]
current_mode = st.session_state.mode

with mode_cols[0]:
    if st.button("⚡ Quick Play", use_container_width=True, type="primary" if current_mode == GameMode.QUICK_PLAY else "secondary"):
        if current_mode != GameMode.QUICK_PLAY:
            st.session_state.mode = GameMode.QUICK_PLAY
            st.session_state.match = MatchSession(GameMode.QUICK_PLAY)
            st.session_state.last_round = None
            st.rerun()

with mode_cols[1]:
    if st.button("🏆 Best of 5", use_container_width=True, type="primary" if current_mode == GameMode.BEST_OF_5 else "secondary"):
        if current_mode != GameMode.BEST_OF_5:
            st.session_state.mode = GameMode.BEST_OF_5
            st.session_state.match = MatchSession(GameMode.BEST_OF_5)
            st.session_state.last_round = None
            st.rerun()

with mode_cols[2]:
    if st.button("⚔️ Best of 10", use_container_width=True, type="primary" if current_mode == GameMode.BEST_OF_10 else "secondary"):
        if current_mode != GameMode.BEST_OF_10:
            st.session_state.mode = GameMode.BEST_OF_10
            st.session_state.match = MatchSession(GameMode.BEST_OF_10)
            st.session_state.last_round = None
            st.rerun()

with mode_cols[3]:
    if st.button("🔄 Reset Match", use_container_width=True):
        st.session_state.match.reset()
        st.session_state.last_round = None
        st.session_state.audio_cue = "click"
        st.rerun()


# ---------------------------------------------------------------------------
# Active Match Progress Tracker (Best of 5 & Best of 10)
# ---------------------------------------------------------------------------
active_match: MatchSession = st.session_state.match

if active_match.mode != GameMode.QUICK_PLAY:
    max_pts = 3 if active_match.mode == GameMode.BEST_OF_5 else 10
    target_text = "First to 3 Wins" if active_match.mode == GameMode.BEST_OF_5 else "Maximum 10 Rounds"

    st.markdown(f"""
    <div style="background: {theme_colors['bg_card_secondary']}; border: 1px solid {theme_colors['border_color']}; border-radius: 14px; padding: 0.9rem 1.4rem; margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; font-weight: 700; font-size: 0.9rem; margin-bottom: 0.5rem;">
            <span style="color: {theme_colors['accent_cyan']};">Round {active_match.round_number + 1} &bull; {active_match.mode}</span>
            <span style="color: {theme_colors['text_secondary']};">{target_text}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-weight: 800; font-size: 1.1rem;">
            <span style="color: {theme_colors['accent_cyan']};">YOU: {active_match.player_score}</span>
            <span style="color: {theme_colors['text_muted']};">VS</span>
            <span style="color: {theme_colors['accent_pink']};">AI: {active_match.computer_score}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Battle Arena Section
# ---------------------------------------------------------------------------
arena_col1, arena_col2, arena_col3 = st.columns([1.2, 1, 1.2])

last_res = st.session_state.last_round

# Column 1: Player Station
with arena_col1:
    st.markdown(f"""
    <div class="combat-card">
        <span class="card-tag tag-player">YOU</span>
        <h3 style="font-family: 'Outfit'; margin: 0.2rem 0;">{st.session_state.player_name}</h3>
        <div class="weapon-preview-large">
            {CHOICES[last_res['player_choice']]['emoji'] if last_res else '✊'}
        </div>
        <div style="font-weight: 600; font-size: 0.9rem; color: {theme_colors['text_secondary']};">
            {CHOICES[last_res['player_choice']]['label'] if last_res else 'Choose Your Weapon'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; font-weight: 700; font-size: 0.85rem;'>SELECT YOUR MOVE:</p>", unsafe_allow_html=True)
    w_btn_cols = st.columns(3)

    chosen_weapon = None
    with w_btn_cols[0]:
        if st.button("✊\nROCK", use_container_width=True, key="btn_rock", help="Crushes Scissors"):
            chosen_weapon = "rock"

    with w_btn_cols[1]:
        if st.button("✋\nPAPER", use_container_width=True, key="btn_paper", help="Covers Rock"):
            chosen_weapon = "paper"

    with w_btn_cols[2]:
        if st.button("✌️\nSCISSORS", use_container_width=True, key="btn_scissors", help="Cuts Paper"):
            chosen_weapon = "scissors"


# Column 2: Center Stage / Countdown & Result
with arena_col2:
    st.markdown("<div style='text-align: center; padding-top: 1.5rem;'>", unsafe_allow_html=True)

    if last_res:
        res = last_res["result"]
        if res == "win":
            st.markdown(f"""
            <div class="outcome-banner outcome-win">
                <div style="font-size: 2rem;">🏆</div>
                <div style="font-size: 1.3rem;">ROUND VICTORY!</div>
                <div style="font-size: 0.85rem; font-weight: 500; margin-top: 0.3rem;">{last_res['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        elif res == "lose":
            st.markdown(f"""
            <div class="outcome-banner outcome-lose">
                <div style="font-size: 2rem;">💀</div>
                <div style="font-size: 1.3rem;">ROUND DEFEAT</div>
                <div style="font-size: 0.85rem; font-weight: 500; margin-top: 0.3rem;">{last_res['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="outcome-banner outcome-draw">
                <div style="font-size: 2rem;">🤝</div>
                <div style="font-size: 1.3rem;">STALEMATE DRAW</div>
                <div style="font-size: 0.85rem; font-weight: 500; margin-top: 0.3rem;">{last_res['message']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: {theme_colors['bg_card']}; border: 1px dashed {theme_colors['border_color']}; border-radius: 16px; padding: 2rem 1rem;">
            <div style="font-size: 2.5rem;">⚡</div>
            <div style="font-family: 'Outfit'; font-weight: 800; font-size: 1.2rem; color: {theme_colors['accent_cyan']};">ARENA READY</div>
            <div style="font-size: 0.82rem; color: {theme_colors['text_muted']}; margin-top: 0.3rem;">Click Rock, Paper, or Scissors to clash!</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# Column 3: Computer AI Station
with arena_col3:
    st.markdown(f"""
    <div class="combat-card">
        <span class="card-tag tag-ai">OPPONENT</span>
        <h3 style="font-family: 'Outfit'; margin: 0.2rem 0;">Arcade AI</h3>
        <div class="weapon-preview-large">
            {CHOICES[last_res['computer_choice']]['emoji'] if last_res else '🤖'}
        </div>
        <div style="font-weight: 600; font-size: 0.9rem; color: {theme_colors['text_secondary']};">
            {CHOICES[last_res['computer_choice']]['label'] if last_res else 'Waiting for move...'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background: {theme_colors['bg_card_secondary']}; border: 1px solid {theme_colors['border_color']}; border-radius: 12px; padding: 0.8rem 1rem; font-size: 0.82rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
            <span style="color: {theme_colors['text_muted']};">AI Algorithm:</span>
            <span style="font-weight: 700; color: {theme_colors['accent_pink']};">Dynamic Randomizer</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: {theme_colors['text_muted']};">Total Computer Wins:</span>
            <span style="font-weight: 700; color: {theme_colors['text_primary']};">{storage.get_statistics()['computer_wins']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Gameplay Round Resolution
# ---------------------------------------------------------------------------
if chosen_weapon:
    # If the active match already ended, restart
    if active_match.is_match_over:
        active_match.reset()

    # Generate computer choice & play round
    comp_choice = get_random_computer_choice()
    outcome = active_match.play_round(chosen_weapon, comp_choice)

    # Persist in storage
    newly_unlocked = storage.record_round({
        "round_number": active_match.round_number,
        "mode": active_match.mode,
        "player_choice": chosen_weapon,
        "computer_choice": comp_choice,
        "result": outcome["result"],
    })

    # If match finished, record tournament outcome
    if active_match.is_match_over:
        match_unlocked = storage.record_match({
            "mode": active_match.mode,
            "match_winner": active_match.match_winner,
            "player_score": active_match.player_score,
            "computer_score": active_match.computer_score,
            "draws": active_match.draws,
            "round_number": active_match.round_number,
        })
        newly_unlocked.extend(match_unlocked)

    st.session_state.last_round = outcome

    # Audio cue trigger
    if outcome["result"] == "win":
        st.session_state.audio_cue = "win"
        st.balloons()  # Particle explosion confetti on win
    elif outcome["result"] == "lose":
        st.session_state.audio_cue = "lose"
    else:
        st.session_state.audio_cue = "draw"

    # Display achievement unlock toasts
    for ach in newly_unlocked:
        st.toast(f"🏅 Achievement Unlocked: {ach['title']} - {ach['desc']}", icon=ach.get("icon", "🏆"))
        st.session_state.audio_cue = "achievement"

    st.rerun()


# Play audio cue if pending
if st.session_state.audio_cue:
    play_web_audio(st.session_state.audio_cue)
    st.session_state.audio_cue = None


# ---------------------------------------------------------------------------
# Match Completion Announcement Card
# ---------------------------------------------------------------------------
if active_match.is_match_over:
    if active_match.match_winner == "player":
        st.success(f"🎉 **TOURNAMENT CHAMPION!** You won the {active_match.mode} match with {active_match.player_score} wins vs AI {active_match.computer_score}!")
    elif active_match.match_winner == "computer":
        st.error(f"💀 **MATCH DEFEATED!** The AI won the {active_match.mode} match with {active_match.computer_score} wins vs your {active_match.player_score}.")
    else:
        st.warning(f"🤝 **TOURNAMENT TIE!** The {active_match.mode} ended in a draw ({active_match.player_score} - {active_match.computer_score}).")


# ---------------------------------------------------------------------------
# Statistics Dashboard
# ---------------------------------------------------------------------------
st.divider()
st.subheader("📊 Live Combat Statistics")

stats = storage.get_statistics()
stat_cols = st.columns(6)

with stat_cols[0]:
    st.metric("Total Rounds", stats["total_rounds"])
with stat_cols[1]:
    st.metric("Win Rate", f"{stats['win_rate']}%")
with stat_cols[2]:
    st.metric("Player Wins", stats["player_wins"])
with stat_cols[3]:
    st.metric("Computer Wins", stats["computer_wins"])
with stat_cols[4]:
    st.metric("Draws", stats["draws"])
with stat_cols[5]:
    st.metric("Streak 🔥", stats["current_streak"], help=f"All-time longest streak: {stats['longest_streak']}")


# ---------------------------------------------------------------------------
# Achievements Showcase (8 Badges)
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🏅 Trophies & Achievements (8 Badges)")

ach_state = storage.data.get("achievements", {})
ach_cols = st.columns(4)

for i, ach_def in enumerate(ACHIEVEMENT_DEFINITIONS):
    col = ach_cols[i % 4]
    ach_id = ach_def["id"]
    is_unlocked = ach_state.get(ach_id, {}).get("unlocked", False)
    status_label = "✨ Unlocked" if is_unlocked else "🔒 Locked"
    border_color = theme_colors["accent_yellow"] if is_unlocked else theme_colors["border_color"]
    opacity = "1" if is_unlocked else "0.55"

    with col:
        st.markdown(f"""
        <div style="background: {theme_colors['bg_card_secondary']}; border: 1px solid {border_color}; border-radius: 14px; padding: 1rem; margin-bottom: 0.8rem; opacity: {opacity};">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
                <span style="font-size: 1.8rem;">{ach_def['icon']}</span>
                <div>
                    <strong style="font-family: 'Outfit'; font-size: 0.95rem; color: {theme_colors['text_primary']};">{ach_def['title']}</strong>
                    <div style="font-size: 0.72rem; color: {theme_colors['accent_yellow']}; font-weight: 700;">{status_label}</div>
                </div>
            </div>
            <p style="font-size: 0.76rem; color: {theme_colors['text_muted']}; margin: 0.4rem 0 0 0;">{ach_def['desc']}</p>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Round History & Tournament Leaderboard Tabs
# ---------------------------------------------------------------------------
st.divider()
tab1, tab2, tab3 = st.tabs(["📜 Round History", "🏆 Tournament Leaderboard", "🗑️ Clear Data"])

with tab1:
    history = storage.data.get("history", [])
    if history:
        history_rows = []
        for h in history[:30]:
            p_emo = CHOICES.get(h.get("player_choice", ""), {}).get("emoji", "")
            c_emo = CHOICES.get(h.get("computer_choice", ""), {}).get("emoji", "")
            res_str = "WIN 🏆" if h.get("result") == "win" else ("LOSS 💀" if h.get("result") == "lose" else "DRAW 🤝")
            history_rows.append({
                "Round": f"#{h.get('round', '')}",
                "Mode": h.get("mode", ""),
                "Your Weapon": f"{p_emo} {h.get('player_choice', '').capitalize()}",
                "AI Weapon": f"{c_emo} {h.get('computer_choice', '').capitalize()}",
                "Outcome": res_str,
                "Time": h.get("timestamp", ""),
            })
        st.dataframe(history_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No combat rounds logged yet. Pick your weapon and play!")

with tab2:
    leaderboard = storage.data.get("leaderboard", [])
    if leaderboard:
        lb_rows = []
        for lb in leaderboard[:30]:
            lb_rows.append({
                "Date": lb.get("date", ""),
                "Player": lb.get("player_name", "Player 1"),
                "Mode": lb.get("mode", ""),
                "Score": f"{lb.get('player_score', 0)} - {lb.get('computer_score', 0)}",
                "Rounds": lb.get("rounds_played", 0),
                "Outcome": lb.get("outcome", ""),
            })
        st.dataframe(lb_rows, use_container_width=True, hide_index=True)
    else:
        st.info("No completed tournament matches yet. Play Best of 5 or Best of 10 to record matches!")

with tab3:
    st.markdown("### Danger Zone: Reset Data")
    st.warning("This action permanently erases round statistics, streak counters, history logs, and leaderboard rankings.")
    confirm_clear = st.checkbox("I confirm I want to erase all game history and statistics.")
    if st.button("Clear All Data", disabled=not confirm_clear, type="primary"):
        storage.reset_statistics()
        storage.data["history"] = []
        storage.data["leaderboard"] = []
        storage.save()
        st.session_state.match.reset()
        st.session_state.last_round = None
        st.success("All game history and statistics have been cleared!")
        time.sleep(1)
        st.rerun()


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0; color: {theme_colors['text_muted']}; font-size: 0.8rem; border-top: 1px solid {theme_colors['border_color']}; margin-top: 3rem;">
    Rock, Paper, Scissors — Phase 3 Complete Streamlit Edition &copy; 2026<br>
    Render Free Cloud Web Ready &bull; Native Audio Synthesizer &bull; Custom CSS Theming
</div>
""", unsafe_allow_html=True)
