#!/bin/bash
# ============================================
# PZ Server Manager - Run Script (macOS/Linux)
# ============================================

echo "Starting PZ Server Manager..."

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists and activate it
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the application
python3 "$SCRIPT_DIR/main.py" "$@"
