@echo off
title Rock Paper Scissors - Phase 3 Streamlit Edition
echo Starting Rock, Paper, Scissors Streamlit Web App...
python -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo An error occurred running Streamlit. Press any key to exit.
    pause
)
