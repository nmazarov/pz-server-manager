#!/bin/bash
# ============================================
# PZ Server Manager - Run Web Dashboard
# ============================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

python3 "$SCRIPT_DIR/web_main.py" "$@"
