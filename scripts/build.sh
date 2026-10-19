#!/bin/bash
# ============================================
# PZ Server Manager - Build Script (macOS/Linux)
# ============================================

echo ""
echo "========================================"
echo "  PZ Server Manager - Build Script"
echo "========================================"
echo ""

# Determine script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

pyinstaller --clean --noconfirm scripts/pz_server_manager.spec

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

if [ -f "dist/PZ Server Manager" ]; then
    cp "dist/PZ Server Manager" "PZ Server Manager"
    chmod +x "PZ Server Manager"
fi

echo "Executable location:"
echo "  ./PZ Server Manager"
echo ""
echo "You can now run it directly: './PZ Server Manager'"
echo ""

# Deactivate virtual environment
deactivate
