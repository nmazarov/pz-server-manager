#!/bin/bash
# ============================================
# PZ Server Manager - Run Script (macOS/Linux)
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists and activate it
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# If --web argument passed or no X11/Wayland display detected, launch Web Dashboard
if [ "$1" == "--web" ] || [ -z "$DISPLAY" -a "$OSTYPE" != "darwin"* ]; then
    echo "🌐 No GUI display detected or --web specified. Starting Web Dashboard (FastAPI)..."
    python3 "$SCRIPT_DIR/web_main.py" --host 0.0.0.0 --port 8080 "$@"
else
    echo "Starting PZ Server Manager GUI..."
    python3 "$SCRIPT_DIR/main.py" "$@"
fi
