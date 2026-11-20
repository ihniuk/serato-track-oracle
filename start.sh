#!/usr/bin/env bash
# =========================================================
# Serato Track Oracle - macOS (OSX) Launcher
# Harmonic & Tempo Next-Track DJ Companion for Serato DJ Pro
# =========================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "======================================================"
echo "       ⚡ SERATO TRACK ORACLE - DJ COMPANION ⚡        "
echo "  Live Serato Detection • Camelot Wheel • Tempo Radar "
echo "======================================================"
echo ""

# Find Python 3 on macOS
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "❌ Error: Python 3 not found on your Mac."
    echo "Please install Python from https://www.python.org or via Homebrew (brew install python)."
    exit 1
fi

echo "Using Python: $($PY_CMD --version)"

# Check / install lightweight dependencies
echo "Checking dependencies..."
$PY_CMD -m pip install -q -r requirements.txt 2>/dev/null || {
    echo "Note: Running with system packages or virtual environment..."
}

# Auto-open browser on macOS after short pause
(sleep 1.5 && open "http://127.0.0.1:5000") &

echo ""
echo "🚀 Starting Serato Track Oracle Server on http://127.0.0.1:5000 ..."
echo "Press Ctrl+C in this terminal to stop."
echo ""

$PY_CMD app.py
