<p align="center">
  <img src="assets/logo.png" alt="Project Zomboid Server Manager" width="750"/>
</p>

# 🧟 Project Zomboid Dedicated Server Manager

<p align="center">
  <a href="README.md"><b>🇬🇧 English</b></a> |
  <a href="README_RU.md"><b>🇷🇺 Русский</b></a>
</p>

<p align="center">
  <a href="https://github.com/nmazarov/pz-server-manager/releases"><img src="https://img.shields.io/badge/Release-v1.5.0-success.svg?style=flat-square" alt="Version v1.5.0"/></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.8+-3776AB.svg?logo=python&logoColor=white&style=flat-square" alt="Python 3.8+"/></a>
  <a href="https://pypi.org/project/PyQt5/"><img src="https://img.shields.io/badge/GUI-PyQt5-41CD52.svg?logo=qt&logoColor=white&style=flat-square" alt="PyQt5"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Web-FastAPI-009688.svg?logo=fastapi&logoColor=white&style=flat-square" alt="FastAPI"/></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20(Desktop%20%26%20VPS)-blue.svg?style=flat-square" alt="Platform"/>
  <img src="https://img.shields.io/badge/PZ%20Build-41.78%20%7C%2042+-red.svg?style=flat-square" alt="PZ Build"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"/></a>
</p>

---

A modern, high-performance dedicated server manager and administration suite for **Project Zomboid** (fully supporting **Build 41** and the next-generation **Build 42+**). 

Featuring both a tactical **Desktop GUI** (Windows & Linux) and an ultra-fast **Headless Web Dashboard** (FastAPI & WebSockets) optimized for dedicated Linux VPS hosting.

---

## 🌟 Key Features

### 🌐 1. Dual Interface: Desktop GUI & Headless VPS Web Panel
* **Tactical Desktop GUI**: Built with PyQt5, modern dark glassmorphic UI, custom typography (`Inter` & `JetBrains Mono`), and reactive controls.
* **Modern Web Dashboard**: Powered by FastAPI, WebSockets, and a responsive tactical SPA. Control your server remotely from any browser, tablet, or smartphone without needing an X11/desktop environment.
* **Live Bilingual Switcher**: Seamless 1-click toggle between **English** and **Russian** across both the Desktop app and the Web Panel.

### 🎮 2. Interactive Console & Live Player Management
* **Real-time Terminal Output**: Stream live game logs with automatic auto-scroll, color-coded severity levels, and instant command dispatch.
* **Live Player Roster**: Automatic player detection on connect/disconnect directly from the server log.
* **Admin Actions in 1 Click**:
  * 👢 **Kick Player** with optional customized message.
  * 🚫 **Ban Player** by Username / SteamID64.
  * 👑 **Grant Admin Rank** (`setaccesslevel admin`).
  * 📜 **Whitelist Player** directly into the server's SQLite database.
* **Quick Actions Bar**: Save world, toggle rain, spawn helicopter meta-events, or broadcast announcements with a single click.

### 🧟 3. 1:1 In-Game Sandbox Configurator (`SandboxVars.lua`)
Organized into 6 clean sub-tabs matching the in-game Project Zomboid menu:
1. **🧟 Zombies & Population**: Speed (Sprinters, Fast Shamblers, Shamblers), Strength, Toughness, Infection Transmission, Mortality, Reanimation, Cognition, Memory, Sight, Hearing, Smell, Decomposition, plus advanced `ZombieConfig` (Population Multiplier, Peak Day, Respawn, Drag Down, Fence Lunge, Rally Groups).
2. **📦 Loot & Resources**: 10 granular loot rarity categories, loot respawn timers, container limits, water and electricity shutoff.
3. **🌍 World & Time**: Day length (up to 24h real-time), starting calendar date/time, temperature, rainfall, world erosion speed and days, helicopter frequency, meta-events, night darkness, and time since apocalypse.
4. **🚗 Vehicles**: Spawn rates, initial mechanical condition, easy hotwiring mode, highway traffic jams, collision damage, fuel availability, and car alarms.
5. **👤 Character & Skills**: XP multiplier quick-presets (`1x`, `1.5x`, `2x`, `3x`, `5x`), starting free trait points, nutritional system, farming speeds, and generator fuel consumption.
6. **🧩 Mod Options**: Dynamic Lua table editor with real-time live search. Automatically detects and renders custom tables for mods like Brita, KI5, TrueActions, etc.

### ⚙️ 4. Comprehensive Server Configuration (`servertest.ini`)
* Complete coverage of networking (`DefaultPort`, `UDPPort`, `SteamPort1`, `SteamPort2`, `RCONPort`).
* Safehouse permissions (player vs admin safehouses, trespassing, fire, loot, respawn).
* Security rules (Auto-whitelist on connect, Lua checksum verification, duplicate Steam ID block, safety spawn protection, max accounts per user).
* In-game VOIP audio and global chat toggles.

### 🧩 5. Steam Workshop Mod Master
* **Build 41 & Build 42 Compatibility Engine**: Color-coded badges (🟢 Verified, 🟡 Universal, 🔴 Outdated/Incompatible).
* **Steam Workshop Collection Import**: Paste any Steam Collection URL or Workshop ID to bulk-import mods automatically.
* **Curated Mod Packs**: Quick 1-click presets for KI5 Vehicle Fleet, Brita Weapon Pack, QoL Essentials, and Hardcore Survival.
* **Map Load Order**: Easy reordering to ensure modded maps load before vanilla *Muldraugh, KY*.

### 🛡️ 6. Watchdog & Crash Supervisor
* Continuous background heartbeat monitoring.
* Detects unexpected server crashes and initiates an automatic 10-second restart sequence.
* Infinite loop protection against broken or incompatible mods.
* Optional **Discord Webhook alerts** on startup, shutdown, and crashes.

### 💾 7. Automated Backups & One-Click Restore
* Full snapshot archives (`.zip`) containing world saves (`Saves/Multiplayer/`), configuration files (`Server/`), and player databases (`db/`).
* Pre-launch safety backups created automatically before every start.
* Backup manager dialog with creation date, size in MB, 1-click restore, and clean deletion.

---

## 🚀 Quick Start Guide

### 🪟 Windows (Recommended: Standalone Executable)
1. Download [`PZ Server Manager.exe`](PZ%20Server%20Manager.exe) or run the installer [`PZ_Server_Manager_Setup.exe`](PZ_Server_Manager_Setup.exe).
2. Launch the application. All dependencies and Python runtime are self-contained.

#### Running from source on Windows:
```cmd
setup.bat
run.bat
```

#### Launching only the Web Panel on Windows:
```cmd
run-web.bat
```

---

### 🐧 Linux Desktop (GUI)
1. **Install system packages:**
   * **Ubuntu / Debian**:
     ```bash
     sudo apt update && sudo apt install -y python3 python3-venv python3-pip libxcb-xinerama0
     ```
   * **Arch Linux / Manjaro**:
     ```bash
     sudo pacman -S python python-pip
     ```
   * **Fedora**:
     ```bash
     sudo dnf install -y python3 python3-pip
     ```
2. **Setup and launch:**
   ```bash
   chmod +x setup.sh run.sh run-web.sh
   ./setup.sh
   ./run.sh
   ```

---

### 🖥️ Headless Linux VPS / Dedicated Server (Web Panel)
Designed specifically for remote VPS hosting without graphical desktop environments.

#### 1-Command Automated Installer (`setup_vps.sh`):
```bash
git clone https://github.com/nmazarov/pz-server-manager.git
cd pz-server-manager
chmod +x setup_vps.sh
sudo ./setup_vps.sh
```

**What the installer does automatically:**
1. Installs Java 17 JRE, SteamCMD 32-bit dependencies (`lib32gcc-s1`), and Python 3.
2. Creates virtual environment and installs FastAPI & Uvicorn dependencies.
3. Sets up your administrator password for the Web Panel.
4. Automatically opens firewall ports via `ufw`.
5. Installs and starts a **systemd** service (`pz-web-manager.service`) running 24/7 with auto-restart on system reboot.
6. Displays your web login URL: `http://<YOUR-VPS-IP>:8080`.

#### Managing the Linux VPS Service:
```bash
sudo systemctl status pz-web-manager   # Check service status
sudo journalctl -u pz-web-manager -f    # View live web logs
sudo systemctl restart pz-web-manager  # Restart panel
sudo systemctl stop pz-web-manager     # Stop panel
```

---

## 🌐 Network Ports & Port Forwarding

Forward these ports on your router or cloud provider security group (AWS, Hetzner, DigitalOcean, OVH):

| Port | Protocol | Purpose |
| :--- | :--- | :--- |
| **16261** | **UDP** | Primary Game Port |
| **16261** | **TCP** | Handshake Authentication |
| **16262** | **UDP** | Direct Client Connection |
| **8766** | **UDP** | Steam Master Server |
| **8767** | **UDP** | Steam P2P Communication |
| **8080** | **TCP** | Web Management Dashboard |

> [!TIP]
> On Windows, click **«🔓 Open Firewall Ports»** in the application header to automatically configure Windows Defender Firewall rules with one click.

---

## 📁 Repository Structure

```text
pz-server-manager/
├── main.py                     # Desktop GUI application & CLI dispatcher
├── web_main.py                 # Standalone FastAPI Web runner for headless VPS
│
├── core/                       # Core backend managers & engines
│   ├── config_manager.py       # INI and Lua parser, serializer & preferences
│   ├── mod_manager.py          # Steam Workshop parser, dependencies & presets
│   ├── server_installer.py     # SteamCMD downloader & branch manager
│   ├── server_process.py       # Server lifecycle supervisor & port monitor
│   ├── backup_manager.py       # ZIP backup, restore, and rotation engine
│   ├── network_helper.py       # IP discovery, Windows firewall & UPnP
│   ├── translations.py         # Complete bilingual localization (RU / EN)
│   ├── player_manager.py       # Real-time player tracking & SQLite whitelist
│   ├── watchdog_manager.py     # Crash supervisor & Discord webhook engine
│   └── diagnostics_manager.py  # System diagnostic tools
│
├── ui/                         # Modular PyQt5 Desktop GUI package
│   ├── main_window.py          # Window coordinator & header action buttons
│   ├── server_tab.py           # Server control, console, live players panel, RAM
│   ├── settings_tab.py         # servertest.ini configuration
│   ├── sandbox_tab.py          # SandboxVars.lua settings & global search
│   ├── mods_tab.py             # Mod manager, B41/B42 compatibility & presets
│   ├── install_tab.py          # SteamCMD installation & branch selector
│   └── dialogs.py              # Backup GUI, Firewall rules & custom icons
│
├── web/                        # Headless Web Dashboard (FastAPI + SPA)
│   ├── server.py               # REST API & WebSockets server
│   ├── auth.py                 # Session tokens & password hashing
│   └── static/                 # Glassmorphic Single Page App (HTML, CSS, JS)
│
├── scripts/                    # Build, installer, and utility scripts
│   ├── setup_vps.sh            # Automated 1-command Linux VPS installer
│   ├── pz_server_manager.spec  # PyInstaller spec for single-file EXE
│   ├── installer.iss           # Inno Setup Windows installer script
│   └── run-web.sh / .bat       # Dedicated web dashboard launch scripts
│
├── assets/                     # Logos, dark theme QSS, checkmarks, fonts
├── requirements.txt            # Desktop dependencies (PyQt5, psutil, etc.)
├── requirements-web.txt        # VPS headless dependencies (FastAPI, uvicorn, psutil)
├── LICENSE                     # MIT License
├── README.md                   # English documentation
└── README_RU.md                # Russian documentation
```

---

## 📄 License

This project is open-source and released under the [MIT License](LICENSE).
Contributions, bug reports, and pull requests are welcome!
