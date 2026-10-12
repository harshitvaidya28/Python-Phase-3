"""
Rock, Paper, Scissors - UI Theme & Style Definitions
Defines color palettes, font configurations, and styling tokens for Neon Dark Arcade
and Modern Light themes.
"""

from typing import Dict, Any

THEMES: Dict[str, Dict[str, Any]] = {
    "dark": {
        "name": "Neon Dark Arcade",
        "bg_main": "#0B0F19",
        "bg_card": "#141C2E",
        "bg_card_secondary": "#1A2338",
        "border_color": "#24324D",
        "border_accent": "#00F5FF",
        
        "text_primary": "#FFFFFF",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        
        # Accents
        "accent_cyan": "#00F5FF",
        "accent_pink": "#FF007F",
        "accent_green": "#00FF9D",
        "accent_yellow": "#FFD700",
        "accent_purple": "#8B5CF6",
        
        # Action buttons
        "btn_primary_bg": "#00F5FF",
        "btn_primary_text": "#070B14",
        "btn_primary_hover": "#38BDF8",
        
        "btn_secondary_bg": "#1E293B",
        "btn_secondary_text": "#F8FAFC",
        "btn_secondary_hover": "#334155",
        
        "btn_danger_bg": "#EF4444",
        "btn_danger_text": "#FFFFFF",
        "btn_danger_hover": "#DC2626",

        # Choices styling
        "rock_color": "#FF007F",
        "paper_color": "#00F5FF",
        "scissors_color": "#FFD700",

        # Win / Lose / Draw
        "result_win": "#00FF9D",
        "result_lose": "#FF007F",
        "result_draw": "#FFD700",
    },
    "light": {
        "name": "Modern Light",
        "bg_main": "#F1F5F9",
        "bg_card": "#FFFFFF",
        "bg_card_secondary": "#F8FAFC",
        "border_color": "#CBD5E1",
        "border_accent": "#0284C7",
        
        "text_primary": "#0F172A",
        "text_secondary": "#475569",
        "text_muted": "#94A3B8",
        
        # Accents
        "accent_cyan": "#0284C7",
        "accent_pink": "#DB2777",
        "accent_green": "#16A34A",
        "accent_yellow": "#CA8A04",
        "accent_purple": "#7C3AED",
        
        # Action buttons
        "btn_primary_bg": "#0284C7",
        "btn_primary_text": "#FFFFFF",
        "btn_primary_hover": "#0369A1",
        
        "btn_secondary_bg": "#E2E8F0",
        "btn_secondary_text": "#0F172A",
        "btn_secondary_hover": "#CBD5E1",
        
        "btn_danger_bg": "#EF4444",
        "btn_danger_text": "#FFFFFF",
        "btn_danger_hover": "#DC2626",

        # Choices styling
        "rock_color": "#DB2777",
        "paper_color": "#0284C7",
        "scissors_color": "#CA8A04",

        # Win / Lose / Draw
        "result_win": "#16A34A",
        "result_lose": "#DC2626",
        "result_draw": "#CA8A04",
    }
}


def get_theme(theme_name: str = "dark") -> Dict[str, Any]:
    """Retrieves color dictionary for the given theme name."""
    return THEMES.get(theme_name.lower(), THEMES["dark"])
