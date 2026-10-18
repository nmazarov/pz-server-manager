#!/bin/bash
# ============================================================
# Project Zomboid Server Manager - Automated Setup (Linux)
# ============================================================

set -e

echo ""
echo "============================================================"
echo "  Project Zomboid Server Manager - Quick Setup (Linux)"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Check Python installation and version (3.8+)
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Please install Python 3.8+ using your package manager:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    echo "  Arch Linux:    sudo pacman -S python python-pip"
    echo "  Fedora:        sudo dnf install python3 python3-pip"
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[1/4] Found Python version: $PY_VER"

python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || {
    echo "[ERROR] Python 3.8 or higher is required. Found Python $PY_VER."
    exit 1
}

# 2. Create virtual environment
if [ ! -d "venv" ]; then
    echo "[2/4] Creating virtual environment (venv)..."
    python3 -m venv venv || {
        echo "[ERROR] Failed to create virtual environment."
        echo "Make sure python3-venv is installed: sudo apt install python3-venv"
        exit 1
    }
else
    echo "[2/4] Virtual environment already exists."
fi

# 3. Activate venv and install dependencies
echo "[3/4] Installing dependencies from requirements.txt and requirements-web.txt..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if [ -f "requirements-web.txt" ]; then
    pip install -r requirements-web.txt --quiet
fi

# 4. Make scripts executable
chmod +x run.sh run-web.sh build.sh setup.sh 2>/dev/null || true

# 5. Create optional desktop launcher
DESKTOP_FILE="$HOME/.local/share/applications/pz-server-manager.desktop"
if [ -d "$HOME/.local/share/applications" ]; then
    echo "[4/4] Creating desktop application shortcut..."
    ICON_PATH="utilities-system-monitor"
    if [ -f "$SCRIPT_DIR/assets/icon.png" ]; then
        ICON_PATH="$SCRIPT_DIR/assets/icon.png"
    fi
    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Project Zomboid Server Manager
Comment=Manage and configure Project Zomboid Dedicated Server
Exec=$SCRIPT_DIR/run.sh
Path=$SCRIPT_DIR
Terminal=false
Categories=Game;Utility;
Icon=$ICON_PATH
EOF
    chmod +x "$DESKTOP_FILE" 2>/dev/null || true
    echo "      Shortcut created at $DESKTOP_FILE"
else
    echo "[4/4] Skipping desktop launcher (directory ~/.local/share/applications not found)."
fi

echo ""
echo "============================================================"
echo "  Setup Completed Successfully!"
echo "============================================================"
echo "  You can now start the manager by running:"
echo "    ./run.sh"
echo ""
