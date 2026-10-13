"""
Rock, Paper, Scissors - Main Entry Point
Supports both Web Server (for cloud deployment on Render or browser play)
and Desktop GUI (CustomTkinter) when a display is available.
"""

import os
import sys


def main():
    # If deployed on Render or PORT is specified or --web flag is given
    is_render = "RENDER" in os.environ or "PORT" in os.environ
    force_web = "--web" in sys.argv
    force_desktop = "--desktop" in sys.argv

    if (is_render or force_web) and not force_desktop:
        from server import app
        port = int(os.environ.get("PORT", 5000))
        print(f"Starting Rock, Paper, Scissors Web Arcade on port {port}...")
        app.run(host="0.0.0.0", port=port)
        return

    # Attempt desktop GUI; if headless or Tkinter fails, fallback to web server
    try:
        from app import RockPaperScissorsApp
        gui = RockPaperScissorsApp()
        gui.mainloop()
    except Exception as e:
        print(f"[Notice] Desktop GUI unavailable ({e}). Starting Web Server instead...")
        from server import app
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
