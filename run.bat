@echo off
title Rock Paper Scissors - Phase 3
echo Starting Rock, Paper, Scissors...
python main.py
if errorlevel 1 (
    echo.
    echo An error occurred running python main.py. Press any key to exit.
    pause
)
