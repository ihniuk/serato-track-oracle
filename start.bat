@echo off
title Serato Track Oracle
cd /d "%~dp0"

echo ======================================================
echo        SERATO TRACK ORACLE - DJ COMPANION
echo   Live Serato Detection - Camelot Wheel - Tempo Radar
echo ======================================================
echo.

python -m pip install -q -r requirements.txt
start "" "http://127.0.0.1:5000"
python app.py
pause
