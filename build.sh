#!/bin/bash
# ============================================
# PZ Server Manager - Build Script (macOS/Linux)
# ============================================

echo ""
echo "========================================"
echo "  PZ Server Manager - Build Script"
echo "========================================"
echo ""

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Install Python 3.8+ from https://python.org or your package manager"
    exit 1
fi

echo "[1/4] Checking Python version..."
python3 --version

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "[2/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[2/4] Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "[3/4] Installing dependencies..."
pip install -r requirements.txt --quiet
pip install pyinstaller --quiet

# Build executable
echo "[4/4] Building executable..."
echo ""

pyinstaller --clean --noconfirm pz_server_manager.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "  Build Complete!"
echo "========================================"
echo ""

SYSTEM=$(uname -s)
if [ "$SYSTEM" = "Darwin" ]; then
    echo "Executable location:"
    echo "  dist/PZ Server Manager"
    echo ""
    echo "You can now copy this file anywhere and run it."
else
    echo "Executable location:"
    echo "  dist/PZ Server Manager"
    echo ""
    echo "You can now copy this file anywhere and run it."
fi
echo ""

# Deactivate virtual environment
deactivate
