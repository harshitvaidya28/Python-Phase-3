"""
Rock, Paper, Scissors - Main Entry Point
Runs the Streamlit web arcade application.
"""

import os
import sys
import subprocess


def main():
    port = os.environ.get("PORT", "8501")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        f"--server.port={port}",
        "--server.address=0.0.0.0",
    ]
    print(f"Starting Streamlit Rock, Paper, Scissors Arcade on port {port}...")
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
