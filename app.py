"""
Rock, Paper, Scissors - Phase 3 Arcade Edition
A complete, premium, interactive desktop gaming application built with CustomTkinter.
Features:
- Neon Dark Arcade & Modern Light themes
- Animated 3-2-1 Countdown with computer choice shuffle
- Canvas particle explosion confetti celebration on victory
- 3 Playable Modes: Quick Play, Best of 5, Best of 10
- Advanced Statistics, Streaks, and Win Rate calculations
- 8 Unlockable Achievements with real-time unlock toasts
- Persistent local Round History and AI Match Leaderboard (JSON)
- Zero-dependency retro arcade sound effects via native winsound
"""

import math
import random
from typing import Optional, List, Dict, Any

try:
    import tkinter as tk
    from tkinter import messagebox
    import customtkinter as ctk
    HAS_GUI = True
except Exception:
    HAS_GUI = False
    tk = None
    messagebox = None
    ctk = None

from game_logic import CHOICES, CHOICE_KEYS, GameMode, MatchSession, get_round_result
from storage import StorageManager
from sound import SoundManager
from ui_theme import get_theme, THEMES


class Particle:
    """Represents a single confetti/sparkle particle for victory celebration."""
    def __init__(self, x: float, y: float, colors: List[str]):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 12)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(2, 6)
        self.gravity = 0.4
        self.color = random.choice(colors)
        self.size = random.uniform(4, 9)
        self.life = random.randint(30, 50)
        self.max_life = self.life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.98
        self.life -= 1


class RockPaperScissorsApp(ctk.CTk):
    """Main Application Window and Screen Controller."""

    def __init__(self):
        super().__init__()

        # Managers
        self.storage = StorageManager()
        self.settings = self.storage.get_settings()
        
        # Audio
        sound_enabled = self.settings.get("sound_enabled", True)
        self.sound = SoundManager(enabled=sound_enabled)

        # Active Session
        self.session = MatchSession(GameMode.QUICK_PLAY)
        self.is_round_animating = False
        self.particles: List[Particle] = []
        self.anim_timer_id = None
        self.countdown_step = 0
        self.selected_player_choice = None
        self.target_computer_choice = None

        # Setup Window
        self.title("Rock, Paper, Scissors — Phase 3 Arcade Edition")
        self.geometry("1060x780")
        self.minsize(920, 680)

        # Apply Theme
        current_theme_key = self.settings.get("theme", "dark")
        self.theme_name = current_theme_key
        self.theme = get_theme(self.theme_name)
        ctk.set_appearance_mode("dark" if self.theme_name == "dark" else "light")
        self.configure(fg_color=self.theme["bg_main"])

        # Main Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=16, pady=16)

        # Build screens
        self.current_screen = None
        self.show_main_menu()

    # =========================================================================
    # THEME SWITCHER
    # =========================================================================
    def switch_theme(self, new_theme_name: str):
        """Switches the UI theme between dark and light modes."""
        self.theme_name = new_theme_name
        self.theme = get_theme(self.theme_name)
        self.storage.update_settings(theme=self.theme_name)
        ctk.set_appearance_mode("dark" if self.theme_name == "dark" else "light")
        self.configure(fg_color=self.theme["bg_main"])
        # Refresh current screen
        if self.current_screen == "game":
            self.show_game_screen(mode=self.session.mode)
        elif self.current_screen == "stats":
            self.show_stats_screen()
        elif self.current_screen == "achievements":
            self.show_achievements_screen()
        elif self.current_screen == "history":
            self.show_history_screen()
        elif self.current_screen == "settings":
            self.show_settings_screen()
        else:
            self.show_main_menu()

    def toggle_sound(self):
        """Toggles sound on and off and updates storage."""
        new_state = not self.sound.enabled
        self.sound.set_enabled(new_state)
        self.storage.update_settings(sound_enabled=new_state)
        if new_state:
            self.sound.play_click()
        return new_state

    def clear_container(self):
        """Removes all widgets from the central container."""
        if self.anim_timer_id:
            try:
                self.after_cancel(self.anim_timer_id)
            except Exception:
                pass
            self.anim_timer_id = None
        for widget in self.container.winfo_children():
            widget.destroy()

    # =========================================================================
    # TOAST NOTIFICATIONS (ACHIEVEMENTS)
    # =========================================================================
    def show_achievement_toast(self, ach_info: Dict[str, str]):
        """Displays an animated floating banner when an achievement is unlocked."""
        self.sound.play_achievement()
        toast = ctk.CTkFrame(
            self,
            fg_color=self.theme["bg_card"],
            border_width=2,
            border_color=self.theme["accent_yellow"],
            corner_radius=14,
        )
        toast.place(relx=0.5, rely=0.08, anchor="center")

        icon_lbl = ctk.CTkLabel(toast, text=ach_info.get("icon", "🏆"), font=("Segoe UI Emoji", 26))
        icon_lbl.pack(side="left", padx=(16, 8), pady=10)

        text_frame = ctk.CTkFrame(toast, fg_color="transparent")
        text_frame.pack(side="left", padx=(0, 20), pady=10)

        title_lbl = ctk.CTkLabel(
            text_frame,
            text=f"ACHIEVEMENT UNLOCKED: {ach_info.get('title')}",
            font=("Segoe UI", 13, "bold"),
            text_color=self.theme["accent_yellow"],
        )
        title_lbl.pack(anchor="w")

        desc_lbl = ctk.CTkLabel(
            text_frame,
            text=ach_info.get("desc", ""),
            font=("Segoe UI", 11),
            text_color=self.theme["text_secondary"],
        )
        desc_lbl.pack(anchor="w")

        # Auto dismiss after 4 seconds
        self.after(4200, lambda: toast.destroy() if toast.winfo_exists() else None)

    # =========================================================================
    # SCREEN 1: MAIN MENU / START SCREEN
    # =========================================================================
    def show_main_menu(self):
        self.current_screen = "main_menu"
        self.clear_container()

        # Hero Banner Frame
        hero_frame = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card"],
            corner_radius=20,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        hero_frame.pack(fill="x", padx=20, pady=(10, 16))

        # Title Emojis & Neon Header
        icons_label = ctk.CTkLabel(
            hero_frame,
            text="✊   ✋   ✌️",
            font=("Segoe UI Emoji", 38),
        )
        icons_label.pack(pady=(20, 4))

        title_label = ctk.CTkLabel(
            hero_frame,
            text="ROCK • PAPER • SCISSORS",
            font=("Segoe UI", 32, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        title_label.pack(pady=(0, 4))

        subtitle_label = ctk.CTkLabel(
            hero_frame,
            text="PHASE 3 ARCADIA — TOURNAMENT & CASUAL EDITION",
            font=("Segoe UI", 12, "bold"),
            text_color=self.theme["accent_pink"],
        )
        subtitle_label.pack(pady=(0, 16))

        # Content split: Left = Mode selection, Right = Quick Stats & Navigation
        content_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        content_frame.grid_columnconfigure(0, weight=3)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # LEFT: Game Modes Panel
        modes_card = ctk.CTkFrame(
            content_frame,
            fg_color=self.theme["bg_card"],
            corner_radius=18,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        modes_card.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        modes_title = ctk.CTkLabel(
            modes_card,
            text="SELECT GAME MODE",
            font=("Segoe UI", 18, "bold"),
            text_color=self.theme["text_primary"],
        )
        modes_title.pack(anchor="w", padx=24, pady=(20, 14))

        # Mode Options Buttons
        mode_items = [
            (
                GameMode.QUICK_PLAY,
                "⚡ QUICK PLAY",
                "Play unlimited rounds at your own pace. Stop anytime.",
                self.theme["accent_cyan"],
            ),
            (
                GameMode.BEST_OF_5,
                "🏆 BEST OF 5",
                "Tournament style! First player to 3 round wins takes the trophy.",
                self.theme["accent_pink"],
            ),
            (
                GameMode.BEST_OF_10,
                "⚔️ BEST OF 10",
                "Endurance match! 10 total rounds. Most wins claims victory.",
                self.theme["accent_yellow"],
            ),
        ]

        for mode_val, mode_title_txt, mode_desc_txt, accent in mode_items:
            m_frame = ctk.CTkFrame(
                modes_card,
                fg_color=self.theme["bg_card_secondary"],
                corner_radius=12,
                border_width=1,
                border_color=self.theme["border_color"],
            )
            m_frame.pack(fill="x", padx=20, pady=7)

            info_f = ctk.CTkFrame(m_frame, fg_color="transparent")
            info_f.pack(side="left", fill="both", expand=True, padx=16, pady=12)

            t_lbl = ctk.CTkLabel(
                info_f,
                text=mode_title_txt,
                font=("Segoe UI", 15, "bold"),
                text_color=accent,
            )
            t_lbl.pack(anchor="w")

            d_lbl = ctk.CTkLabel(
                info_f,
                text=mode_desc_txt,
                font=("Segoe UI", 11),
                text_color=self.theme["text_secondary"],
                wraplength=320,
                justify="left",
            )
            d_lbl.pack(anchor="w", pady=(2, 0))

            play_btn = ctk.CTkButton(
                m_frame,
                text="PLAY",
                font=("Segoe UI", 13, "bold"),
                fg_color=accent,
                text_color="#070B14" if self.theme_name == "dark" else "#FFFFFF",
                hover_color=self.theme["accent_green"],
                corner_radius=10,
                width=88,
                height=36,
                command=lambda m=mode_val: self.start_game_mode(m),
            )
            play_btn.pack(side="right", padx=16, pady=12)

        # RIGHT: Quick Overview & Menu Navigation
        nav_card = ctk.CTkFrame(
            content_frame,
            fg_color=self.theme["bg_card"],
            corner_radius=18,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        nav_card.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        # Quick Stats Overview Card
        stats = self.storage.get_statistics()
        quick_stats_box = ctk.CTkFrame(
            nav_card,
            fg_color=self.theme["bg_card_secondary"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border_color"],
        )
        quick_stats_box.pack(fill="x", padx=20, pady=(20, 16))

        qs_title = ctk.CTkLabel(
            quick_stats_box,
            text="CAREER SNAPSHOT",
            font=("Segoe UI", 12, "bold"),
            text_color=self.theme["accent_green"],
        )
        qs_title.pack(anchor="w", padx=14, pady=(10, 4))

        qs_row = ctk.CTkFrame(quick_stats_box, fg_color="transparent")
        qs_row.pack(fill="x", padx=10, pady=(0, 10))

        def add_stat_mini(parent, label, value, color):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(side="left", expand=True)
            v = ctk.CTkLabel(f, text=str(value), font=("Segoe UI", 18, "bold"), text_color=color)
            v.pack()
            l = ctk.CTkLabel(f, text=label, font=("Segoe UI", 10), text_color=self.theme["text_secondary"])
            l.pack()

        add_stat_mini(qs_row, "Rounds", stats["total_rounds"], self.theme["text_primary"])
        add_stat_mini(qs_row, "Win Rate", f"{stats['win_rate']}%", self.theme["accent_cyan"])
        add_stat_mini(qs_row, "Best Streak", f"🔥 {stats['longest_streak']}", self.theme["accent_pink"])

        # Navigation Buttons
        nav_title = ctk.CTkLabel(
            nav_card,
            text="MENU & FEATURES",
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["text_primary"],
        )
        nav_title.pack(anchor="w", padx=24, pady=(6, 10))

        menu_buttons = [
            ("📊 Statistics & Records", self.show_stats_screen, self.theme["btn_secondary_bg"]),
            ("🏅 Achievements & Badges", self.show_achievements_screen, self.theme["btn_secondary_bg"]),
            ("📜 Round History & Leaderboard", self.show_history_screen, self.theme["btn_secondary_bg"]),
            ("⚙️ Game Settings & Theme", self.show_settings_screen, self.theme["btn_secondary_bg"]),
        ]

        for text_b, cmd_b, bg_b in menu_buttons:
            btn = ctk.CTkButton(
                nav_card,
                text=text_b,
                font=("Segoe UI", 13, "bold"),
                fg_color=bg_b,
                text_color=self.theme["text_primary"],
                hover_color=self.theme["btn_secondary_hover"],
                corner_radius=10,
                height=40,
                anchor="w",
                command=lambda c=cmd_b: [self.sound.play_click(), c()],
            )
            btn.pack(fill="x", padx=20, pady=5)

    def start_game_mode(self, mode: str):
        """Starts a game session with the chosen mode."""
        self.sound.play_click()
        self.session = MatchSession(mode=mode)
        self.show_game_screen(mode=mode)

    # =========================================================================
    # SCREEN 2: GAMEPLAY ARENA SCREEN
    # =========================================================================
    def show_game_screen(self, mode: str = GameMode.QUICK_PLAY):
        self.current_screen = "game"
        self.clear_container()
        self.is_round_animating = False

        # Top Bar: Navigation + Mode Badge + Sound Toggle
        top_bar = ctk.CTkFrame(self.container, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 10))

        back_btn = ctk.CTkButton(
            top_bar,
            text="◀ MAIN MENU",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=120,
            height=34,
            command=lambda: [self.sound.play_click(), self.show_main_menu()],
        )
        back_btn.pack(side="left")

        # Mode Badge
        mode_badge = ctk.CTkLabel(
            top_bar,
            text=f"MODE: {self.session.mode.upper()}",
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        mode_badge.pack(side="left", padx=20)

        # Sound & Theme Quick Toggles on Right
        sound_icon = "🔊 SOUND ON" if self.sound.enabled else "🔇 MUTED"
        self.game_sound_btn = ctk.CTkButton(
            top_bar,
            text=sound_icon,
            font=("Segoe UI", 11, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=110,
            height=34,
            command=self._on_toggle_sound_game,
        )
        self.game_sound_btn.pack(side="right", padx=(8, 0))

        # Reset Match Button
        reset_btn = ctk.CTkButton(
            top_bar,
            text="🔄 NEW MATCH",
            font=("Segoe UI", 11, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=110,
            height=34,
            command=self._on_reset_game,
        )
        reset_btn.pack(side="right")

        # Scoreboard Row
        score_row = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card"],
            corner_radius=16,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        score_row.pack(fill="x", pady=(0, 12))

        # Player Score Card
        player_name = self.settings.get("player_name", "Player 1")
        self.player_score_lbl = self._create_score_col(
            score_row,
            f"👤 {player_name.upper()}",
            str(self.session.player_score),
            self.theme["accent_cyan"],
        )

        # Center Match Status / Target
        center_status_box = ctk.CTkFrame(score_row, fg_color="transparent")
        center_status_box.pack(side="left", expand=True, pady=10)

        self.match_goal_lbl = ctk.CTkLabel(
            center_status_box,
            text=self._get_match_goal_text(),
            font=("Segoe UI", 12, "bold"),
            text_color=self.theme["accent_yellow"],
        )
        self.match_goal_lbl.pack()

        self.round_badge_lbl = ctk.CTkLabel(
            center_status_box,
            text=f"ROUND {self.session.round_number}",
            font=("Segoe UI", 18, "bold"),
            text_color=self.theme["text_primary"],
        )
        self.round_badge_lbl.pack(pady=(2, 2))

        self.draws_lbl = ctk.CTkLabel(
            center_status_box,
            text=f"Draws: {self.session.draws}",
            font=("Segoe UI", 11),
            text_color=self.theme["text_muted"],
        )
        self.draws_lbl.pack()

        # Computer Score Card
        self.computer_score_lbl = self._create_score_col(
            score_row,
            "🤖 AI OPPONENT",
            str(self.session.computer_score),
            self.theme["accent_pink"],
        )

        # Versus Arena
        self.arena_frame = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card_secondary"],
            corner_radius=20,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        self.arena_frame.pack(fill="both", expand=True, pady=(0, 12))
        self.arena_frame.grid_columnconfigure(0, weight=1)
        self.arena_frame.grid_columnconfigure(1, weight=1)
        self.arena_frame.grid_columnconfigure(2, weight=1)
        self.arena_frame.grid_rowconfigure(0, weight=1)

        # Canvas overlay for particles/confetti
        self.canvas = tk.Canvas(
            self.arena_frame,
            bg=self.theme["bg_card_secondary"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Left: Player Fighter Box
        self.player_box = ctk.CTkFrame(
            self.arena_frame,
            fg_color=self.theme["bg_card"],
            corner_radius=16,
            border_width=2,
            border_color=self.theme["accent_cyan"],
        )
        self.player_box.grid(row=0, column=0, padx=24, pady=24, sticky="nsew")

        p_title = ctk.CTkLabel(
            self.player_box,
            text="YOUR CHOICE",
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        p_title.pack(pady=(16, 6))

        self.player_emoji_lbl = ctk.CTkLabel(
            self.player_box,
            text="❓",
            font=("Segoe UI Emoji", 72),
        )
        self.player_emoji_lbl.pack(expand=True)

        self.player_choice_name_lbl = ctk.CTkLabel(
            self.player_box,
            text="Make your move!",
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["text_secondary"],
        )
        self.player_choice_name_lbl.pack(pady=(0, 16))

        # Center: Countdown & VS Box
        center_arena = ctk.CTkFrame(self.arena_frame, fg_color="transparent")
        center_arena.grid(row=0, column=1, padx=10, pady=20, sticky="nsew")

        self.vs_lbl = ctk.CTkLabel(
            center_arena,
            text="V S",
            font=("Segoe UI", 28, "bold"),
            text_color=self.theme["text_muted"],
        )
        self.vs_lbl.pack(pady=(14, 4))

        self.countdown_lbl = ctk.CTkLabel(
            center_arena,
            text="READY",
            font=("Segoe UI", 36, "bold"),
            text_color=self.theme["accent_yellow"],
        )
        self.countdown_lbl.pack(expand=True)

        self.result_message_lbl = ctk.CTkLabel(
            center_arena,
            text="Select Rock, Paper, or Scissors below to start!",
            font=("Segoe UI", 13, "bold"),
            text_color=self.theme["text_primary"],
            wraplength=260,
            justify="center",
        )
        self.result_message_lbl.pack(pady=(0, 16))

        # Right: Computer Fighter Box
        self.computer_box = ctk.CTkFrame(
            self.arena_frame,
            fg_color=self.theme["bg_card"],
            corner_radius=16,
            border_width=2,
            border_color=self.theme["accent_pink"],
        )
        self.computer_box.grid(row=0, column=2, padx=24, pady=24, sticky="nsew")

        c_title = ctk.CTkLabel(
            self.computer_box,
            text="AI OPPONENT",
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["accent_pink"],
        )
        c_title.pack(pady=(16, 6))

        self.computer_emoji_lbl = ctk.CTkLabel(
            self.computer_box,
            text="❓",
            font=("Segoe UI Emoji", 72),
        )
        self.computer_emoji_lbl.pack(expand=True)

        self.computer_choice_name_lbl = ctk.CTkLabel(
            self.computer_box,
            text="Waiting for input...",
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["text_secondary"],
        )
        self.computer_choice_name_lbl.pack(pady=(0, 16))

        # Bottom Selection Cards (Rock, Paper, Scissors)
        self.choices_frame = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card"],
            corner_radius=18,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        self.choices_frame.pack(fill="x", pady=(0, 6))

        prompt_lbl = ctk.CTkLabel(
            self.choices_frame,
            text="CHOOSE YOUR WEAPON",
            font=("Segoe UI", 12, "bold"),
            text_color=self.theme["text_secondary"],
        )
        prompt_lbl.pack(pady=(10, 4))

        buttons_row = ctk.CTkFrame(self.choices_frame, fg_color="transparent")
        buttons_row.pack(fill="x", padx=20, pady=(0, 14))

        self.choice_buttons = {}
        for key in CHOICE_KEYS:
            info = CHOICES[key]
            btn = ctk.CTkButton(
                buttons_row,
                text=f"{info['emoji']}  {info['label'].upper()}",
                font=("Segoe UI Emoji", 16, "bold"),
                fg_color=self.theme["bg_card_secondary"],
                text_color=self.theme["text_primary"],
                hover_color=self.theme[f"{key}_color"],
                border_width=2,
                border_color=self.theme[f"{key}_color"],
                corner_radius=14,
                height=56,
                command=lambda k=key: self._on_player_select_choice(k),
            )
            btn.pack(side="left", expand=True, fill="x", padx=8)
            self.choice_buttons[key] = btn

    def _create_score_col(self, parent, title: str, score: str, color: str):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        col.pack(side="left" if "Player" in title or "PLAYER" in title else "right", expand=True, pady=12)

        t_lbl = ctk.CTkLabel(col, text=title, font=("Segoe UI", 12, "bold"), text_color=color)
        t_lbl.pack()

        s_lbl = ctk.CTkLabel(col, text=score, font=("Segoe UI", 32, "bold"), text_color=self.theme["text_primary"])
        s_lbl.pack()
        return s_lbl

    def _get_match_goal_text(self) -> str:
        if self.session.mode == GameMode.BEST_OF_5:
            return "Best of 5: First to 3 wins takes match"
        elif self.session.mode == GameMode.BEST_OF_10:
            return "Best of 10: Most wins after 10 rounds"
        return "Quick Play: Play unlimited rounds"

    def _on_toggle_sound_game(self):
        new_state = self.toggle_sound()
        self.game_sound_btn.configure(text="🔊 SOUND ON" if new_state else "🔇 MUTED")

    def _on_reset_game(self):
        self.sound.play_click()
        self.session.reset()
        self.show_game_screen(mode=self.session.mode)

    # =========================================================================
    # ROUND EXECUTION & ANIMATED COUNTDOWN
    # =========================================================================
    def _on_player_select_choice(self, player_choice: str):
        """Triggered when the player clicks Rock, Paper, or Scissors."""
        if self.is_round_animating:
            return  # Prevent accidental double-clicks

        if self.session.is_match_over:
            messagebox.showinfo("Match Finished", "This match is over! Start a new match or return to the menu.")
            return

        self.sound.play_click()
        self.is_round_animating = True
        self.selected_player_choice = player_choice
        self.target_computer_choice = random.choice(CHOICE_KEYS)

        # Disable choice buttons during animation
        for btn in self.choice_buttons.values():
            btn.configure(state="disabled")

        # Show player's immediate choice
        self.player_emoji_lbl.configure(text=CHOICES[player_choice]["emoji"])
        self.player_choice_name_lbl.configure(
            text=CHOICES[player_choice]["label"].upper(),
            text_color=self.theme["accent_cyan"],
        )

        # Clear computer display and start countdown
        self.computer_emoji_lbl.configure(text="❓")
        self.computer_choice_name_lbl.configure(text="Thinking...", text_color=self.theme["text_secondary"])
        self.result_message_lbl.configure(text="Brace yourself!", text_color=self.theme["text_secondary"])

        # Start 3-2-1 countdown sequence
        self.countdown_step = 3
        self._countdown_tick()

    def _countdown_tick(self):
        """Advances the 3-2-1 countdown using non-blocking Tkinter after() callbacks."""
        if self.countdown_step > 0:
            self.sound.play_countdown_tick()
            self.countdown_lbl.configure(
                text=str(self.countdown_step),
                text_color=self.theme["accent_yellow"],
            )
            # Shuffle computer emoji during countdown for excitement
            shuffle_choice = random.choice(CHOICE_KEYS)
            self.computer_emoji_lbl.configure(text=CHOICES[shuffle_choice]["emoji"])

            self.countdown_step -= 1
            self.after(520, self._countdown_tick)
        else:
            # Countdown finished -> Reveal results!
            self.sound.play_countdown_go()
            self.countdown_lbl.configure(text="FIGHT!", text_color=self.theme["accent_green"])
            self.after(350, self._resolve_round)

    def _resolve_round(self):
        """Resolves round outcome, calculates stats, streaks, achievements, and updates UI."""
        round_info = self.session.play_round(
            self.selected_player_choice,
            self.target_computer_choice,
        )

        # Reveal computer choice
        comp_choice = self.target_computer_choice
        self.computer_emoji_lbl.configure(text=CHOICES[comp_choice]["emoji"])
        self.computer_choice_name_lbl.configure(
            text=CHOICES[comp_choice]["label"].upper(),
            text_color=self.theme["accent_pink"],
        )

        # Update scores
        self.player_score_lbl.configure(text=str(self.session.player_score))
        self.computer_score_lbl.configure(text=str(self.session.computer_score))
        self.draws_lbl.configure(text=f"Draws: {self.session.draws}")
        self.round_badge_lbl.configure(text=f"ROUND {self.session.round_number}")

        # Record to storage
        unlocked_achievements = self.storage.record_round(round_info)

        # Display result styling and play sound
        result = round_info["result"]
        if result == "win":
            self.sound.play_win()
            self.countdown_lbl.configure(text="YOU WIN!", text_color=self.theme["result_win"])
            self.result_message_lbl.configure(
                text=f"Victory! {CHOICES[self.selected_player_choice]['label']} {CHOICES[self.selected_player_choice]['description'].lower()}.",
                text_color=self.theme["result_win"],
            )
            self._trigger_celebration_confetti()
        elif result == "lose":
            self.sound.play_lose()
            self.countdown_lbl.configure(text="DEFEAT!", text_color=self.theme["result_lose"])
            self.result_message_lbl.configure(
                text=f"Defeat! Computer's {CHOICES[comp_choice]['label']} {CHOICES[comp_choice]['description'].lower()}.",
                text_color=self.theme["result_lose"],
            )
        else:
            self.sound.play_draw()
            self.countdown_lbl.configure(text="DRAW!", text_color=self.theme["result_draw"])
            self.result_message_lbl.configure(
                text="Stalemate! Both chose the exact same weapon.",
                text_color=self.theme["result_draw"],
            )

        # Show achievement toasts if unlocked
        for ach in unlocked_achievements:
            self.show_achievement_toast(ach)

        # Check if match is finished (Best of 5 or Best of 10)
        if self.session.is_match_over:
            match_unlocked = self.storage.record_match(round_info)
            for ach in match_unlocked:
                self.show_achievement_toast(ach)
            self.after(900, lambda: self._show_match_over_modal(round_info))

        # Re-enable buttons
        self.is_round_animating = False
        for btn in self.choice_buttons.values():
            btn.configure(state="normal")

    # =========================================================================
    # CELEBRATION CONFETTI / PARTICLES
    # =========================================================================
    def _trigger_celebration_confetti(self):
        """Spawns confetti particles on victory."""
        w = self.canvas.winfo_width() or 800
        h = self.canvas.winfo_height() or 300
        colors = [
            self.theme["accent_cyan"],
            self.theme["accent_pink"],
            self.theme["accent_yellow"],
            self.theme["accent_green"],
            self.theme["accent_purple"],
        ]
        self.particles = [
            Particle(w * 0.5 + random.uniform(-100, 100), h * 0.4 + random.uniform(-50, 50), colors)
            for _ in range(45)
        ]
        self._update_particles()

    def _update_particles(self):
        """Animates particles using Tkinter after() callbacks."""
        self.canvas.delete("all")
        alive = []
        for p in self.particles:
            p.update()
            if p.life > 0:
                alive.append(p)
                self.canvas.create_oval(
                    p.x, p.y, p.x + p.size, p.y + p.size,
                    fill=p.color, outline="",
                )
        self.particles = alive
        if self.particles:
            self.anim_timer_id = self.after(25, self._update_particles)
        else:
            self.canvas.delete("all")

    # =========================================================================
    # MATCH OVER MODAL
    # =========================================================================
    def _show_match_over_modal(self, match_info: Dict[str, Any]):
        """Displays match outcome dialog when Best of 5 or 10 ends."""
        winner = match_info.get("match_winner")
        p_score = match_info.get("player_score", 0)
        c_score = match_info.get("computer_score", 0)

        modal = ctk.CTkToplevel(self)
        modal.title("Match Over")
        modal.geometry("480x380")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        # Modal colors
        modal.configure(fg_color=self.theme["bg_card"])

        if winner == "player":
            title_text = "🏆 MATCH VICTORY!"
            title_color = self.theme["result_win"]
            msg = f"Congratulations! You defeated the computer {p_score} - {c_score}."
        elif winner == "computer":
            title_text = "💀 MATCH DEFEAT!"
            title_color = self.theme["result_lose"]
            msg = f"Computer won the match {c_score} - {p_score}. Try again!"
        else:
            title_text = "🤝 MATCH TIED!"
            title_color = self.theme["result_draw"]
            msg = f"The match ended in an even deadlock ({p_score} - {c_score})."

        t_lbl = ctk.CTkLabel(modal, text=title_text, font=("Segoe UI", 24, "bold"), text_color=title_color)
        t_lbl.pack(pady=(28, 10))

        score_badge = ctk.CTkLabel(
            modal,
            text=f"Final Score: {p_score} - {c_score}  (Draws: {match_info.get('draws', 0)})",
            font=("Segoe UI", 16, "bold"),
            text_color=self.theme["text_primary"],
        )
        score_badge.pack(pady=4)

        m_lbl = ctk.CTkLabel(
            modal,
            text=msg,
            font=("Segoe UI", 13),
            text_color=self.theme["text_secondary"],
            wraplength=380,
            justify="center",
        )
        m_lbl.pack(pady=12)

        # Action Buttons
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=20)

        play_again_btn = ctk.CTkButton(
            btn_frame,
            text="PLAY AGAIN",
            font=("Segoe UI", 13, "bold"),
            fg_color=self.theme["accent_cyan"],
            text_color="#070B14" if self.theme_name == "dark" else "#FFFFFF",
            hover_color=self.theme["accent_green"],
            corner_radius=10,
            width=140,
            height=40,
            command=lambda: [modal.destroy(), self.start_game_mode(self.session.mode)],
        )
        play_again_btn.pack(side="left", padx=8)

        menu_btn = ctk.CTkButton(
            btn_frame,
            text="MAIN MENU",
            font=("Segoe UI", 13, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=10,
            width=140,
            height=40,
            command=lambda: [modal.destroy(), self.show_main_menu()],
        )
        menu_btn.pack(side="left", padx=8)

    # =========================================================================
    # SCREEN 3: STATISTICS SCREEN
    # =========================================================================
    def show_stats_screen(self):
        self.current_screen = "stats"
        self.clear_container()

        stats = self.storage.get_statistics()

        # Header
        hdr = ctk.CTkFrame(self.container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 14))

        back_btn = ctk.CTkButton(
            hdr,
            text="◀ MAIN MENU",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=120,
            height=34,
            command=lambda: [self.sound.play_click(), self.show_main_menu()],
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            hdr,
            text="STATISTICS DASHBOARD",
            font=("Segoe UI", 22, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        title.pack(side="left", padx=20)

        reset_stats_btn = ctk.CTkButton(
            hdr,
            text="RESET STATS",
            font=("Segoe UI", 11, "bold"),
            fg_color=self.theme["btn_danger_bg"],
            text_color=self.theme["btn_danger_text"],
            hover_color=self.theme["btn_danger_hover"],
            corner_radius=8,
            width=110,
            height=34,
            command=self._confirm_reset_stats,
        )
        reset_stats_btn.pack(side="right")

        # Top Hero Card: Win Percentage
        hero = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card"],
            corner_radius=18,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        hero.pack(fill="x", pady=(0, 16))

        h_col = ctk.CTkFrame(hero, fg_color="transparent")
        h_col.pack(pady=20)

        wr_val = ctk.CTkLabel(
            h_col,
            text=f"{stats['win_rate']}%",
            font=("Segoe UI", 48, "bold"),
            text_color=self.theme["accent_green"],
        )
        wr_val.pack()

        wr_lbl = ctk.CTkLabel(
            h_col,
            text="PLAYER OVERALL WIN RATE",
            font=("Segoe UI", 12, "bold"),
            text_color=self.theme["text_secondary"],
        )
        wr_lbl.pack(pady=(2, 0))

        # 2x2 Grid of Stat Cards
        grid_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_columnconfigure(2, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)

        stat_cards = [
            ("TOTAL ROUNDS", str(stats["total_rounds"]), self.theme["text_primary"], 0, 0),
            ("PLAYER WINS", str(stats["player_wins"]), self.theme["result_win"], 0, 1),
            ("COMPUTER WINS", str(stats["computer_wins"]), self.theme["result_lose"], 0, 2),
            ("DRAWS RECORDED", str(stats["draws"]), self.theme["result_draw"], 1, 0),
            ("CURRENT STREAK", f"🔥 {stats['current_streak']}", self.theme["accent_pink"], 1, 1),
            ("LONGEST STREAK", f"⚡ {stats['longest_streak']}", self.theme["accent_yellow"], 1, 2),
        ]

        for label_t, val_t, col_t, r, c in stat_cards:
            card = ctk.CTkFrame(
                grid_frame,
                fg_color=self.theme["bg_card"],
                corner_radius=14,
                border_width=1,
                border_color=self.theme["border_color"],
            )
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")

            val_label = ctk.CTkLabel(
                card,
                text=val_t,
                font=("Segoe UI", 28, "bold"),
                text_color=col_t,
            )
            val_label.pack(expand=True, pady=(16, 4))

            title_label = ctk.CTkLabel(
                card,
                text=label_t,
                font=("Segoe UI", 11, "bold"),
                text_color=self.theme["text_secondary"],
            )
            title_label.pack(pady=(0, 16))

        # Bottom Match Records Banner
        m_banner = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=self.theme["border_color"],
        )
        m_banner.pack(fill="x", pady=(12, 0))

        mb_row = ctk.CTkFrame(m_banner, fg_color="transparent")
        mb_row.pack(pady=12)

        mb_text = ctk.CTkLabel(
            mb_row,
            text=f"MATCH TOURNAMENTS RECORD:  {stats['match_wins']} Won   |   {stats['match_losses']} Lost   |   {stats['match_ties']} Tied",
            font=("Segoe UI", 13, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        mb_text.pack()

    def _confirm_reset_stats(self):
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all gameplay statistics to zero?"):
            self.sound.play_click()
            self.storage.reset_statistics()
            self.show_stats_screen()

    # =========================================================================
    # SCREEN 4: ACHIEVEMENTS SCREEN
    # =========================================================================
    def show_achievements_screen(self):
        self.current_screen = "achievements"
        self.clear_container()

        achievements = self.storage.get_achievements()
        unlocked_count = sum(1 for a in achievements if a["unlocked"])
        total_count = len(achievements)

        # Header
        hdr = ctk.CTkFrame(self.container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))

        back_btn = ctk.CTkButton(
            hdr,
            text="◀ MAIN MENU",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=120,
            height=34,
            command=lambda: [self.sound.play_click(), self.show_main_menu()],
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            hdr,
            text="ACHIEVEMENTS & TROPHIES",
            font=("Segoe UI", 22, "bold"),
            text_color=self.theme["accent_yellow"],
        )
        title.pack(side="left", padx=20)

        # Progress Pill
        prog_lbl = ctk.CTkLabel(
            hdr,
            text=f"UNLOCKED: {unlocked_count} / {total_count}",
            font=("Segoe UI", 13, "bold"),
            text_color=self.theme["accent_green"],
        )
        prog_lbl.pack(side="right")

        # Scrollable Achievements List
        scroll_frame = ctk.CTkScrollableFrame(
            self.container,
            fg_color="transparent",
            corner_radius=14,
        )
        scroll_frame.pack(fill="both", expand=True)

        for ach in achievements:
            is_unlocked = ach["unlocked"]
            border_c = self.theme["accent_yellow"] if is_unlocked else self.theme["border_color"]
            card_bg = self.theme["bg_card"] if is_unlocked else self.theme["bg_card_secondary"]

            card = ctk.CTkFrame(
                scroll_frame,
                fg_color=card_bg,
                corner_radius=14,
                border_width=2 if is_unlocked else 1,
                border_color=border_c,
            )
            card.pack(fill="x", pady=6, padx=8)

            icon_lbl = ctk.CTkLabel(
                card,
                text=ach["icon"] if is_unlocked else "🔒",
                font=("Segoe UI Emoji", 28),
            )
            icon_lbl.pack(side="left", padx=18, pady=14)

            text_box = ctk.CTkFrame(card, fg_color="transparent")
            text_box.pack(side="left", fill="both", expand=True, pady=12)

            t_col = self.theme["accent_yellow"] if is_unlocked else self.theme["text_muted"]
            a_title = ctk.CTkLabel(
                text_box,
                text=ach["title"].upper(),
                font=("Segoe UI", 14, "bold"),
                text_color=t_col,
            )
            a_title.pack(anchor="w")

            a_desc = ctk.CTkLabel(
                text_box,
                text=ach["desc"],
                font=("Segoe UI", 12),
                text_color=self.theme["text_secondary"],
            )
            a_desc.pack(anchor="w", pady=(2, 0))

            status_text = f"Unlocked: {ach['unlocked_at']}" if is_unlocked else "LOCKED"
            status_col = self.theme["accent_green"] if is_unlocked else self.theme["text_muted"]
            status_lbl = ctk.CTkLabel(
                card,
                text=status_text,
                font=("Segoe UI", 11, "bold"),
                text_color=status_col,
            )
            status_lbl.pack(side="right", padx=20)

    # =========================================================================
    # SCREEN 5: GAME HISTORY & MATCH LEADERBOARD
    # =========================================================================
    def show_history_screen(self):
        self.current_screen = "history"
        self.clear_container()

        # Header
        hdr = ctk.CTkFrame(self.container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))

        back_btn = ctk.CTkButton(
            hdr,
            text="◀ MAIN MENU",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=120,
            height=34,
            command=lambda: [self.sound.play_click(), self.show_main_menu()],
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            hdr,
            text="ROUND HISTORY & LEADERBOARD",
            font=("Segoe UI", 20, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        title.pack(side="left", padx=20)

        clear_btn = ctk.CTkButton(
            hdr,
            text="CLEAR HISTORY",
            font=("Segoe UI", 11, "bold"),
            fg_color=self.theme["btn_danger_bg"],
            text_color=self.theme["btn_danger_text"],
            hover_color=self.theme["btn_danger_hover"],
            corner_radius=8,
            width=120,
            height=34,
            command=self._confirm_clear_history,
        )
        clear_btn.pack(side="right")

        # Tabview for switching between Round History and Match Leaderboard
        tabview = ctk.CTkTabview(
            self.container,
            fg_color=self.theme["bg_card"],
            segmented_button_selected_color=self.theme["accent_cyan"],
            segmented_button_selected_hover_color=self.theme["accent_green"],
        )
        tabview.pack(fill="both", expand=True)

        tab_history = tabview.add("📜 Recent Rounds")
        tab_leaderboard = tabview.add("🏆 AI Match Records")

        # TAB 1: ROUND HISTORY
        history_list = self.storage.get_history()
        if not history_list:
            no_h_lbl = ctk.CTkLabel(
                tab_history,
                text="No round history recorded yet. Play some matches to see your logs!",
                font=("Segoe UI", 14),
                text_color=self.theme["text_muted"],
            )
            no_h_lbl.pack(expand=True)
        else:
            h_scroll = ctk.CTkScrollableFrame(tab_history, fg_color="transparent")
            h_scroll.pack(fill="both", expand=True, padx=4, pady=4)

            for item in history_list:
                row_f = ctk.CTkFrame(
                    h_scroll,
                    fg_color=self.theme["bg_card_secondary"],
                    corner_radius=10,
                    border_width=1,
                    border_color=self.theme["border_color"],
                )
                row_f.pack(fill="x", pady=4, padx=4)

                r_num = ctk.CTkLabel(
                    row_f,
                    text=f"Round #{item.get('round', '-')}",
                    font=("Segoe UI", 12, "bold"),
                    text_color=self.theme["text_primary"],
                    width=90,
                    anchor="w",
                )
                r_num.pack(side="left", padx=12, pady=10)

                m_name = ctk.CTkLabel(
                    row_f,
                    text=f"[{item.get('mode', 'Quick')}]",
                    font=("Segoe UI", 11),
                    text_color=self.theme["accent_cyan"],
                    width=100,
                    anchor="w",
                )
                m_name.pack(side="left", padx=4)

                p_c = item.get("player_choice", "")
                c_c = item.get("computer_choice", "")
                choices_txt = f"You: {CHOICES.get(p_c, {}).get('emoji', '')} {p_c.capitalize()}   vs   AI: {CHOICES.get(c_c, {}).get('emoji', '')} {c_c.capitalize()}"
                ch_lbl = ctk.CTkLabel(
                    row_f,
                    text=choices_txt,
                    font=("Segoe UI Emoji", 12),
                    text_color=self.theme["text_primary"],
                )
                ch_lbl.pack(side="left", padx=16)

                # Result Badge
                res = item.get("result", "")
                if res == "win":
                    res_col = self.theme["result_win"]
                    res_text = "WIN"
                elif res == "lose":
                    res_col = self.theme["result_lose"]
                    res_text = "LOSS"
                else:
                    res_col = self.theme["result_draw"]
                    res_text = "DRAW"

                res_lbl = ctk.CTkLabel(
                    row_f,
                    text=res_text,
                    font=("Segoe UI", 12, "bold"),
                    text_color=res_col,
                    width=60,
                )
                res_lbl.pack(side="right", padx=14)

                time_lbl = ctk.CTkLabel(
                    row_f,
                    text=item.get("timestamp", ""),
                    font=("Segoe UI", 10),
                    text_color=self.theme["text_muted"],
                )
                time_lbl.pack(side="right", padx=10)

        # TAB 2: MATCH LEADERBOARD
        leaderboard = self.storage.get_leaderboard()
        if not leaderboard:
            no_lb_lbl = ctk.CTkLabel(
                tab_leaderboard,
                text="No match records yet. Complete a Best of 5 or Best of 10 match to log records!",
                font=("Segoe UI", 14),
                text_color=self.theme["text_muted"],
            )
            no_lb_lbl.pack(expand=True)
        else:
            lb_scroll = ctk.CTkScrollableFrame(tab_leaderboard, fg_color="transparent")
            lb_scroll.pack(fill="both", expand=True, padx=4, pady=4)

            # Disclaimer banner per requirement
            disc_lbl = ctk.CTkLabel(
                lb_scroll,
                text="ℹ️ Single-Player Local Records: Logged match performances of Player vs AI Opponent.",
                font=("Segoe UI", 11, "italic"),
                text_color=self.theme["text_muted"],
            )
            disc_lbl.pack(anchor="w", padx=8, pady=(0, 6))

            for entry in leaderboard:
                row_f = ctk.CTkFrame(
                    lb_scroll,
                    fg_color=self.theme["bg_card_secondary"],
                    corner_radius=10,
                    border_width=1,
                    border_color=self.theme["border_color"],
                )
                row_f.pack(fill="x", pady=4, padx=4)

                date_lbl = ctk.CTkLabel(
                    row_f,
                    text=entry.get("date", ""),
                    font=("Segoe UI", 11),
                    text_color=self.theme["text_muted"],
                    width=120,
                    anchor="w",
                )
                date_lbl.pack(side="left", padx=12, pady=10)

                mode_lbl = ctk.CTkLabel(
                    row_f,
                    text=entry.get("mode", ""),
                    font=("Segoe UI", 12, "bold"),
                    text_color=self.theme["accent_cyan"],
                    width=110,
                    anchor="w",
                )
                mode_lbl.pack(side="left", padx=8)

                score_txt = f"Score: You {entry.get('player_score', 0)} - {entry.get('computer_score', 0)} AI  (Draws: {entry.get('draws', 0)})"
                score_lbl = ctk.CTkLabel(
                    row_f,
                    text=score_txt,
                    font=("Segoe UI", 12),
                    text_color=self.theme["text_primary"],
                )
                score_lbl.pack(side="left", padx=16)

                outcome = entry.get("outcome", "")
                if outcome == "Victory":
                    out_col = self.theme["result_win"]
                elif outcome == "Defeat":
                    out_col = self.theme["result_lose"]
                else:
                    out_col = self.theme["result_draw"]

                out_lbl = ctk.CTkLabel(
                    row_f,
                    text=outcome.upper(),
                    font=("Segoe UI", 13, "bold"),
                    text_color=out_col,
                    width=80,
                )
                out_lbl.pack(side="right", padx=14)

    def _confirm_clear_history(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all round history and leaderboard records?"):
            self.sound.play_click()
            self.storage.clear_history()
            self.show_history_screen()

    # =========================================================================
    # SCREEN 6: SETTINGS SCREEN
    # =========================================================================
    def show_settings_screen(self):
        self.current_screen = "settings"
        self.clear_container()

        # Header
        hdr = ctk.CTkFrame(self.container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 16))

        back_btn = ctk.CTkButton(
            hdr,
            text="◀ MAIN MENU",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            width=120,
            height=34,
            command=lambda: [self.sound.play_click(), self.show_main_menu()],
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            hdr,
            text="GAME SETTINGS & PREFERENCES",
            font=("Segoe UI", 22, "bold"),
            text_color=self.theme["accent_cyan"],
        )
        title.pack(side="left", padx=20)

        # Settings Card Container
        settings_card = ctk.CTkFrame(
            self.container,
            fg_color=self.theme["bg_card"],
            corner_radius=18,
            border_width=2,
            border_color=self.theme["border_color"],
        )
        settings_card.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. THEME SELECTION
        theme_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=24, pady=18)

        t_info = ctk.CTkFrame(theme_row, fg_color="transparent")
        t_info.pack(side="left", fill="both", expand=True)

        t_title = ctk.CTkLabel(
            t_info,
            text="Visual Theme",
            font=("Segoe UI", 15, "bold"),
            text_color=self.theme["text_primary"],
        )
        t_title.pack(anchor="w")

        t_desc = ctk.CTkLabel(
            t_info,
            text="Select between Neon Dark Arcade and Modern Light themes.",
            font=("Segoe UI", 12),
            text_color=self.theme["text_secondary"],
        )
        t_desc.pack(anchor="w", pady=(2, 0))

        theme_seg = ctk.CTkSegmentedButton(
            theme_row,
            values=["Neon Dark", "Modern Light"],
            selected_color=self.theme["accent_cyan"],
            selected_hover_color=self.theme["accent_green"],
            command=self._on_theme_select,
        )
        theme_seg.set("Neon Dark" if self.theme_name == "dark" else "Modern Light")
        theme_seg.pack(side="right")

        # 2. SOUND EFFECTS TOGGLE
        sound_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        sound_row.pack(fill="x", padx=24, pady=18)

        s_info = ctk.CTkFrame(sound_row, fg_color="transparent")
        s_info.pack(side="left", fill="both", expand=True)

        s_title = ctk.CTkLabel(
            s_info,
            text="Sound Effects & Audio",
            font=("Segoe UI", 15, "bold"),
            text_color=self.theme["text_primary"],
        )
        s_title.pack(anchor="w")

        s_desc = ctk.CTkLabel(
            s_info,
            text="Toggle retro arcade countdown, victory, and button tones.",
            font=("Segoe UI", 12),
            text_color=self.theme["text_secondary"],
        )
        s_desc.pack(anchor="w", pady=(2, 0))

        sound_switch = ctk.CTkSwitch(
            sound_row,
            text="Enabled" if self.sound.enabled else "Muted",
            command=lambda: self._on_sound_switch(sound_switch),
            progress_color=self.theme["accent_green"],
        )
        if self.sound.enabled:
            sound_switch.select()
        else:
            sound_switch.deselect()
        sound_switch.pack(side="right")

        # Audio Test Button
        test_audio_btn = ctk.CTkButton(
            settings_card,
            text="🔊 Test Victory Fanfare",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["btn_secondary_bg"],
            text_color=self.theme["text_primary"],
            hover_color=self.theme["btn_secondary_hover"],
            corner_radius=8,
            height=32,
            command=lambda: self.sound.play_win(),
        )
        test_audio_btn.pack(anchor="w", padx=24, pady=(0, 16))

        # 3. PLAYER NAME CUSTOMIZATION
        name_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        name_row.pack(fill="x", padx=24, pady=18)

        n_info = ctk.CTkFrame(name_row, fg_color="transparent")
        n_info.pack(side="left", fill="both", expand=True)

        n_title = ctk.CTkLabel(
            n_info,
            text="Player Display Name",
            font=("Segoe UI", 15, "bold"),
            text_color=self.theme["text_primary"],
        )
        n_title.pack(anchor="w")

        n_desc = ctk.CTkLabel(
            n_info,
            text="Personalize your name on the scoreboard and match history.",
            font=("Segoe UI", 12),
            text_color=self.theme["text_secondary"],
        )
        n_desc.pack(anchor="w", pady=(2, 0))

        self.name_entry = ctk.CTkEntry(
            name_row,
            placeholder_text="Enter player name",
            width=180,
            corner_radius=8,
        )
        current_name = self.settings.get("player_name", "Player 1")
        self.name_entry.insert(0, current_name)
        self.name_entry.pack(side="right", padx=(0, 10))

        save_name_btn = ctk.CTkButton(
            name_row,
            text="SAVE",
            font=("Segoe UI", 12, "bold"),
            fg_color=self.theme["accent_cyan"],
            text_color="#070B14" if self.theme_name == "dark" else "#FFFFFF",
            hover_color=self.theme["accent_green"],
            corner_radius=8,
            width=70,
            command=self._save_player_name,
        )
        save_name_btn.pack(side="right")

        # 4. APP VERSION & INFO
        info_frame = ctk.CTkFrame(
            settings_card,
            fg_color=self.theme["bg_card_secondary"],
            corner_radius=12,
        )
        info_frame.pack(fill="x", padx=24, pady=(20, 20))

        app_info_lbl = ctk.CTkLabel(
            info_frame,
            text="Rock, Paper, Scissors — Phase 3 Complete Python Desktop Edition\nEngine: CustomTkinter 6.0 | Audio: Native Winsound Synthesizer | Storage: Atomic JSON",
            font=("Segoe UI", 11),
            text_color=self.theme["text_muted"],
            justify="center",
        )
        app_info_lbl.pack(pady=12)

    def _on_theme_select(self, choice: str):
        theme_key = "dark" if choice == "Neon Dark" else "light"
        self.switch_theme(theme_key)

    def _on_sound_switch(self, switch_widget):
        new_state = switch_widget.get() == 1
        self.sound.set_enabled(new_state)
        self.storage.update_settings(sound_enabled=new_state)
        switch_widget.configure(text="Enabled" if new_state else "Muted")
        if new_state:
            self.sound.play_click()

    def _save_player_name(self):
        new_name = self.name_entry.get().strip()
        if not new_name:
            new_name = "Player 1"
        self.storage.update_settings(player_name=new_name)
        self.settings["player_name"] = new_name
        self.sound.play_click()
        messagebox.showinfo("Saved", f"Player name updated to '{new_name}'!")


def main():
    if not HAS_GUI:
        print("[Notice] GUI library not available. Starting Web Server...")
        from server import app as web_app
        import os
        port = int(os.environ.get("PORT", 5000))
        web_app.run(host="0.0.0.0", port=port)
        return

    try:
        app = RockPaperScissorsApp()
        app.mainloop()
    except Exception as e:
        print(f"[Notice] Desktop GUI unavailable ({e}). Starting Web Server...")
        from server import app as web_app
        import os
        port = int(os.environ.get("PORT", 5000))
        web_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
