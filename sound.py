"""
Rock, Paper, Scissors - Sound Effects Module
Uses Windows built-in winsound for zero-dependency retro arcade audio effects.
Runs sound playback in background threads to guarantee zero GUI freezing.
"""

import threading
import sys
import time
from typing import Optional

# Try importing winsound (available natively on Windows)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class SoundManager:
    """Manages audio cues for clicks, countdowns, victories, defeats, and draws."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def _play_tones_worker(self, tones):
        """Worker thread executing frequency, duration pairs."""
        if not self.enabled or not HAS_WINSOUND:
            return

        try:
            for freq, duration_ms in tones:
                if not self.enabled:
                    break
                winsound.Beep(int(freq), int(duration_ms))
        except Exception:
            # Fallback gracefully if hardware audio fails or is muted
            pass

    def _run_async(self, tones):
        if not self.enabled or not HAS_WINSOUND:
            return
        thread = threading.Thread(target=self._play_tones_worker, args=(tones,), daemon=True)
        thread.start()

    def play_click(self):
        """Crisp UI button feedback."""
        self._run_async([(800, 30)])

    def play_countdown_tick(self):
        """Ticking sound for countdown numbers 3, 2, 1."""
        self._run_async([(650, 90)])

    def play_countdown_go(self):
        """High energy chime for FIGHT / REVEAL!"""
        self._run_async([(980, 160)])

    def play_win(self):
        """Joyous ascending victory arpeggio."""
        tones = [
            (523, 80),   # C5
            (659, 80),   # E5
            (784, 100),  # G5
            (1046, 220), # C6
        ]
        self._run_async(tones)

    def play_lose(self):
        """Descending defeat tone."""
        tones = [
            (620, 100),
            (460, 120),
            (310, 220),
        ]
        self._run_async(tones)

    def play_draw(self):
        """Neutral dual pulse for a tie."""
        tones = [
            (480, 80),
            (480, 80),
        ]
        self._run_async(tones)

    def play_achievement(self):
        """Grand celebratory fanfare for unlocking an achievement or match win."""
        tones = [
            (587, 80),   # D5
            (740, 80),   # F#5
            (880, 90),   # A5
            (1174, 280), # D6
        ]
        self._run_async(tones)
