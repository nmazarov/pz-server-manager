#!/bin/bash
# ==============================================================================
# 🧟 Project Zomboid Server Manager - Automated VPS Setup & Installer
# Works on: Ubuntu 20.04/22.04/24.04, Debian 11/12, Fedora, Arch Linux
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   🧟 Project Zomboid Server Manager - VPS Web Installer      ║"
echo "║          Automated Linux VPS Setup & Systemd Service         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Require root or sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERROR] Please run this script with sudo or as root:${NC}"
    echo "  sudo ./setup_vps.sh"
    exit 1
fi

REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(eval echo "~$REAL_USER")

echo -e "${BLUE}[1/6] Installing system packages & 32-bit SteamCMD libraries...${NC}"

if command -v apt-get &> /dev/null; then
    dpkg --add-architecture i386 || true
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv curl tar gzip openjdk-17-jre-headless lib32gcc-s1 || apt-get install -y lib32gcc1
elif command -v dnf &> /dev/null; then
    dnf install -y python3 python3-pip curl tar gzip java-17-openjdk-headless glibc.i686 libstdc++.i686
elif command -v pacman &> /dev/null; then
    pacman -Sy --noconfirm python python-pip curl tar gzip jre17-openjdk-headless
fi

echo -e "${GREEN}✓ System dependencies installed.${NC}"

# 2. Setup Python virtual environment
echo -e "${BLUE}[2/6] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    sudo -u "$REAL_USER" python3 -m venv venv
fi

sudo -u "$REAL_USER" "$SCRIPT_DIR/venv/bin/pip" install --upgrade pip --quiet
sudo -u "$REAL_USER" "$SCRIPT_DIR/venv/bin/pip" install -r requirements.txt --quiet
if [ -f "requirements-web.txt" ]; then
    sudo -u "$REAL_USER" "$SCRIPT_DIR/venv/bin/pip" install -r requirements-web.txt --quiet
fi

echo -e "${GREEN}✓ Python dependencies installed.${NC}"

# 3. Prompt or generate Web Panel password
echo -e "${BLUE}[3/6] Configuring Web Dashboard password...${NC}"
ADMIN_PW=""
if [ -z "$ADMIN_PW" ]; then
    echo -e "${YELLOW}Enter desired Web Panel admin password (leave empty to generate random):${NC}"
    read -r -p "Password: " USER_INPUT_PW
    if [ -n "$USER_INPUT_PW" ]; then
        ADMIN_PW="$USER_INPUT_PW"
    else
        ADMIN_PW=$(openssl rand -base64 9 | tr -dc 'a-zA-Z0-9' | head -c 10)
    fi
fi

# Initialize web auth configuration
sudo -u "$REAL_USER" "$SCRIPT_DIR/venv/bin/python3" web_main.py --password "$ADMIN_PW" --port 8080 > /dev/null 2>&1 &
INIT_PID=$!
sleep 2
kill $INIT_PID 2>/dev/null || true

# 4. Configure Firewall (UFW / Firewalld)
echo -e "${BLUE}[4/6] Configuring firewall rules...${NC}"
if command -v ufw &> /dev/null && ufw status | grep -q "Status: active"; then
    ufw allow 8080/tcp comment "PZ Web Dashboard" > /dev/null 2>&1 || true
    ufw allow 16261/udp comment "PZ Game Port UDP" > /dev/null 2>&1 || true
    ufw allow 16261/tcp comment "PZ Handshake TCP" > /dev/null 2>&1 || true
    ufw allow 16262/udp comment "PZ Direct Port UDP" > /dev/null 2>&1 || true
    ufw allow 8766/udp comment "Steam Master Server" > /dev/null 2>&1 || true
    ufw reload > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ UFW firewall rules updated.${NC}"
fi

# 5. Create Systemd Service
echo -e "${BLUE}[5/6] Creating systemd service: pz-web-manager.service...${NC}"
SERVICE_FILE="/etc/systemd/system/pz-web-manager.service"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Project Zomboid Server Manager Web Dashboard
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/web_main.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable pz-web-manager.service
systemctl restart pz-web-manager.service

echo -e "${GREEN}✓ Systemd service created and started.${NC}"

# 6. Fetch Public IP
echo -e "${BLUE}[6/6] Finalizing installation...${NC}"
PUBLIC_IP=$(curl -s --max-time 3 https://api.ipify.org || curl -s --max-time 3 https://ifconfig.me/ip || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  🎉 ${GREEN}PZ Server Manager Web Panel is successfully installed!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "  🌐 Web Dashboard:    ${YELLOW}http://${PUBLIC_IP}:8080${NC}"
echo -e "  🔑 Admin Password:    ${YELLOW}${ADMIN_PW}${NC}"
echo ""
echo -e "  📋 Useful commands:"
echo -e "     • Check service status:   ${BLUE}systemctl status pz-web-manager${NC}"
echo -e "     • View live web logs:     ${BLUE}journalctl -u pz-web-manager -f${NC}"
echo -e "     • Restart panel service:  ${BLUE}systemctl restart pz-web-manager${NC}"
echo -e "     • Stop panel service:     ${BLUE}systemctl stop pz-web-manager${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
