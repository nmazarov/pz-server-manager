<p align="center">
  <img src="assets/logo.png" alt="Project Zomboid Server Manager" width="750"/>
</p>

# 🧟 Project Zomboid Dedicated Server Manager

<p align="center">
  <a href="#-project-zomboid-dedicated-server-manager-русский"><b>🇷🇺 Русский</b></a> |
  <a href="#-project-zomboid-dedicated-server-manager-english"><b>🇬🇧 English</b></a>
</p>

<p align="center">
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.8+-3776AB.svg?logo=python&logoColor=white" alt="Python 3.8+"/></a>
  <a href="https://pypi.org/project/PyQt5/"><img src="https://img.shields.io/badge/GUI-PyQt5-41CD52.svg?logo=qt&logoColor=white" alt="PyQt5"/></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Web-FastAPI-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI"/></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11%20%7C%20Linux%20(Desktop%20%26%20VPS)-lightgrey.svg" alt="Platform"/>
  <img src="https://img.shields.io/badge/PZ%20Build-41.78%20%7C%2042.21+-red.svg" alt="PZ Build"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"/></a>
</p>

---

# 🇷🇺 Project Zomboid Dedicated Server Manager (Русский)

Универсальный менеджер с графическим интерфейсом (Desktop GUI) и удаленной веб-панелью (Headless Web Dashboard) для автоматической установки, настройки, обновления, проверки модов и администрирования выделенного сервера игры **Project Zomboid** (полная поддержка **Build 41** и **Build 42+**).

Поддерживает работу на **Windows (10/11)**, **Linux Desktop** (Ubuntu, Debian, Fedora, Arch) и **Linux VPS / VDS** (Headless серверный режим без монитора).

---

## 🌟 Ключевые возможности

### 👥 1. Панель онлайн-игроков (Live Player Dashboard)
* **Список игроков в реальном времени**: автоматическое отслеживание подключений и отключений игроков из серверной консоли.
* **Быстрые действия администратора в один клик**:
  * 👢 **Кик** с указанием причины (`kickuser`).
  * 🚫 **Бан** по SteamID / имени (`banuser`).
  * 🌀 **Телепорт** игрока к другому игроку (`teleport`).
  * 👑 **Выдача прав Администратора** (`setaccesslevel admin`).
  * 📜 **Добавление в Whitelist** в SQLite базу сервера.
* **Контекстное меню**: правый клик по игроку в списке для мгновенного доступа к действиям.

### 🛡️ 2. Сторожевой таймер и авто-перезапуск (Watchdog)
* **Защита от сбоев**: автоматическое определение непредвиденного падения игрового сервера.
* **Авто-перезапуск**: запуск таймера обратного отсчета (10 секунд) и автоматический рестарт сервера при краше.
* **Ограничение попыток**: защита от циклических сбоев при поврежденных модах.
* **Discord Webhook уведомления**: отправка цветных карточек в Discord о запуске, остановке и падениях сервера.

### 🔍 3. Живой поиск по SandboxVars и модам
* **Глобальный поиск настроек песочницы**: строка `[ 🔍 Поиск по всем категориям... ]` мгновенно фильтрует сотни параметров по ключевым словам и подсказкам, подсвечивая количество совпадений на вкладках.
* **Поиск по модам**: быстрый фильтр установленных модов по названию и Workshop ID.

### 📦 4. Графический менеджер бэкапов (Backup GUI)
* **Полное резервное копирование**: архивация сохранений мира (`Saves/Multiplayer/`), конфигураций (`Server/`) и SQLite базы данных (`db/`) в `.zip`.
* **Автоматические бэкапы перед каждым стартом** с метками времени.
* **Удобное диалоговое окно**:
  * Таблица всех доступных бэкапов (имя архива, размер в МБ, точная дата создания).
  * ➕ **Создать бэкап сейчас** с возможностью ввода пользовательской метки/комментария.
  * 🔄 **Восстановить выбранный бэкап** в один клик с защитой от случайного нажатия.
  * 🗑️ **Удалить старые архивы**.
  * 📂 **Открыть папку бэкапов** в проводнике.

### 🌐 5. Веб-панель для VPS и удаленного доступа (FastAPI Web Panel)
* **Запуск в один клик из GUI**: кнопка `🌐 Веб-панель` запускает локальный веб-сервер на порту 8080 и открывает его в браузере.
* **Автономный запуск на Linux VPS**: управление сервером через браузер или со смартфона без X11/монитора.
* **Живая веб-консоль** через WebSockets с поддержкой команд в реальном времени.

### 🧩 6. Менеджер модов и проверка Build 41 / Build 42
* **Цветовая индикация совместимости**:
  * 🟢 **Зеленый**: проверен и совместим с выбранной версией игры.
  * 🔴 **Красный**: несовместим или устарел.
  * 🟡 **Желтый**: универсальный мод.
* **Импорт коллекций Steam Workshop** по ссылке в 1 клик.
* **Кураторские паки модов**: Автопарк (KI5), Арсенал (Brita), QoL и Хардкор.
* **Порядок загрузки карт (Map Load Order)**: удобное перемещение модовых карт выше vanilla карты *Muldraugh, KY*.

---

## 🚀 Установка и запуск (Инструкции)

### 🪟 Вариант 1: Windows (Готовый EXE)
1. Скачайте релиз или запустите файл [`PZ Server Manager.exe`](PZ%20Server%20Manager.exe) из папки проекта.
2. Никаких дополнительных установок не требуется — все библиотеки и зависимости уже упакованы.

#### Запуск из исходников (Windows):
```cmd
setup.bat
run.bat
```

#### Запуск только Веб-панели (Windows):
```cmd
run-web.bat
```

---

### 🐧 Вариант 2: Linux Desktop (С графической оболочкой)

1. **Установите системные зависимости:**
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

2. **Запустите автоматическую настройку:**
   ```bash
   chmod +x setup.sh run.sh run-web.sh build.sh
   ./setup.sh
   ```

3. **Запустите приложение:**
   ```bash
   ./run.sh
   ```

---

### 🖥️ Вариант 3: Выделенный Linux VPS / VDS Сервер (Headless)

Для серверов без графического интерфейса (Ubuntu Server, Debian, etc.) предусмотрен серверный режим с полноценной веб-панелью.

#### 🚀 Автоматическая установка через скрипт `setup_vps.sh`:
```bash
git clone https://github.com/nmazarov/pz-server-manager.git
cd pz-server-manager
chmod +x setup_vps.sh
sudo ./setup_vps.sh
```

**Скрипт автоматически:**
1. Установит необходимые пакеты, библиотеки SteamCMD (`lib32gcc-s1`) и **OpenJDK 17 JRE**.
2. Развернет виртуальное окружение и установит веб-зависимости FastAPI & Uvicorn.
3. Настроит пароль администратора.
4. Откроет необходимые порты в фаерволе `ufw`.
5. Создаст и запустит фоновую службу **systemd** (`pz-web-manager.service`) с автозапуском при перезагрузке сервера.
6. Выведет URL для входа: `http://<IP-вашего-VPS>:8080`.

#### 🛠️ Управление веб-службой на VPS:
* Проверить статус: `sudo systemctl status pz-web-manager`
* Просмотр логов: `sudo journalctl -u pz-web-manager -f`
* Перезапуск службы: `sudo systemctl restart pz-web-manager`
* Остановка службы: `sudo systemctl stop pz-web-manager`

#### Ручной запуск веб-панели (без systemd):
```bash
./run-web.sh
```

---

## 🌐 Настройка сетевых портов (Port Forwarding)

Для подключения игроков откройте следующие порты на вашем роутере или VPS фаерволе:

| Порт | Протокол | Назначение |
| :--- | :--- | :--- |
| **16261** | **UDP** | Основной порт игры Project Zomboid |
| **16261** | **TCP** | Handshake авторизация |
| **16262** | **UDP** | Прямое подключение игроков |
| **8766** | **UDP** | Steam Master Server |
| **8767** | **UDP** | Steam P2P |
| **8080** | **TCP** | Веб-панель управления (VPS Web Dashboard) |

> [!TIP]
> В Windows нажмите кнопку **«🔓 Открыть порты»** в шапке программы для автоматической настройки брандмауэра Windows.

---
---

# 🇬🇧 Project Zomboid Dedicated Server Manager (English)

A comprehensive, cross-platform server manager featuring both a modern **Desktop GUI** and a lightweight **Remote Web Dashboard** for automatic installation, configuration, mod management, crash protection, and administration of **Project Zomboid Dedicated Server** (supporting both **Build 41** and **Build 42+**).

Runs seamlessly on **Windows (10/11)**, **Linux Desktop** (Ubuntu, Debian, Fedora, Arch), and **Linux VPS / Headless Dedicated Servers**.

---

## 🌟 Key Features

### 👥 1. Live Player Dashboard
* **Real-time online player tracking**: auto-detects player connect and disconnect events directly from console output.
* **One-click Admin actions**:
  * 👢 **Kick** player with optional custom reason (`kickuser`).
  * 🚫 **Ban** player by username / SteamID (`banuser`).
  * 🌀 **Teleport** player to another connected player (`teleport`).
  * 👑 **Grant Administrator rank** (`setaccesslevel admin`).
  * 📜 **Add to Whitelist** in the server's SQLite database.
* **Context Menu**: right-click any player in the list for quick access to actions.

### 🛡️ 2. Watchdog & Auto-Restart on Crash
* **Crash Supervision**: automatically detects unexpected server shutdowns.
* **Auto-recovery**: starts a 10-second countdown and restarts the server automatically.
* **Loop Protection**: limits maximum consecutive crash attempts to prevent boot loops with broken mods.
* **Discord Notifications**: embeds status cards to Discord webhooks on startup, shutdown, and crashes.

### 🔍 3. Global SandboxVars & Mod Search
* **Instant Sandbox Search**: search field `[ 🔍 Search settings across all categories... ]` filters hundreds of settings dynamically across tabs. Displays match count badges on category tabs.
* **Mod Search**: filter installed mods list instantly by title or Steam Workshop ID.

### 📦 4. Graphical Backup Manager (Backup GUI)
* **Complete World Archiving**: backs up save files (`Saves/Multiplayer/`), configs (`Server/`), and database (`db/`) into compressed `.zip` archives.
* **Pre-launch Backups**: automatically creates safety snapshots before every server start.
* **Interactive Dialog**:
  * Full table showing archive name, size in MB, and exact timestamp.
  * ➕ **Create Backup Now** with custom note / tag.
  * 🔄 **Restore Selected Backup** in one click with overwrite protection.
  * 🗑️ **Delete Old Backups**.
  * 📂 **Open Backups Folder** in file explorer.

### 🌐 5. Web Dashboard for VPS Remote Control (FastAPI)
* **One-Click Launch**: `🌐 Web Dashboard` header button launches a local FastAPI server on port 8080 and opens it in your default browser.
* **Headless Linux VPS Mode**: manage your dedicated server remotely from any PC, tablet, or smartphone without needing a desktop environment.
* **Live WebSocket Console** with real-time command input and color-coded output.

### 🧩 6. Mod Manager & Build 41 / Build 42 Verification
* **Color-Coded Compatibility**:
  * 🟢 **Green**: verified compatible with current game build.
  * 🔴 **Red**: outdated or incompatible.
  * 🟡 **Yellow**: universal mod.
* **Steam Workshop Collection Import** via URL.
* **Curated Mod Packs**: Vehicles (KI5), Weapons & Armor (Brita), Quality of Life (QoL), and Hardcore Survival.
* **Map Load Order**: arrange mod maps above vanilla *Muldraugh, KY* easily.

---

## 🚀 Installation & Launch Guide

### 🪟 Option 1: Windows (Standalone .exe)
1. Download the release and launch [`PZ Server Manager.exe`](PZ%20Server%20Manager.exe).
2. No Python installation required — all runtime components and dependencies are included.

#### Run from source (Windows):
```cmd
setup.bat
run.bat
```

#### Launch Web Dashboard directly (Windows):
```cmd
run-web.bat
```

---

### 🐧 Option 2: Linux Desktop (GUI)

1. **Install dependencies:**
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

2. **Run setup script:**
   ```bash
   chmod +x setup.sh run.sh run-web.sh build.sh
   ./setup.sh
   ```

3. **Launch the application:**
   ```bash
   ./run.sh
   ```

---

### 🖥️ Option 3: Headless Linux VPS / Dedicated Server

Designed for headless Linux servers without a display or desktop environment.

#### 🚀 1-Command Automated Installer (`setup_vps.sh`):
```bash
git clone https://github.com/nmazarov/pz-server-manager.git
cd pz-server-manager
chmod +x setup_vps.sh
sudo ./setup_vps.sh
```

**What the installer does automatically:**
1. Installs system packages, SteamCMD 32-bit libraries (`lib32gcc-s1`), and **OpenJDK 17 JRE**.
2. Creates virtual environment and installs FastAPI & Uvicorn dependencies.
3. Sets up your web administrator password.
4. Opens firewall ports via `ufw`.
5. Creates and enables the **systemd** service (`pz-web-manager.service`) with auto-restart on boot.
6. Prints your dashboard URL: `http://<YOUR-VPS-IP>:8080`.

#### 🛠️ Managing the VPS Web Service:
* Service status: `sudo systemctl status pz-web-manager`
* Live web logs: `sudo journalctl -u pz-web-manager -f`
* Restart service: `sudo systemctl restart pz-web-manager`
* Stop service: `sudo systemctl stop pz-web-manager`

#### Manual Launch (without systemd):
```bash
./run-web.sh
```

---

## 🌐 Network & Port Forwarding

Forward these ports on your router or cloud security group to allow incoming player connections:

| Port | Protocol | Purpose |
| :--- | :--- | :--- |
| **16261** | **UDP** | Primary Game Port |
| **16261** | **TCP** | Handshake authentication |
| **16262** | **UDP** | Direct player connection |
| **8766** | **UDP** | Steam Master Server |
| **8767** | **UDP** | Steam P2P Communication |
| **8080** | **TCP** | Web Management Dashboard |

> [!TIP]
> On Windows, click **«🔓 Open Firewall Ports»** in the application header to automatically configure Windows Defender Firewall.

---

## 📁 Project Architecture

```text
pz-server-manager/
├── main.py                     # Application entry point & crash handlers
├── main_window.py              # Main Window coordinator & header actions
├── web_main.py                 # FastAPI Web runner for headless VPS
│
├── ui/                         # Modular PyQt5 interface package
│   ├── server_tab.py           # Server control, console, live players panel, RAM
│   ├── mods_tab.py             # Mod manager, search, B41/B42 compatibility, presets
│   ├── settings_tab.py         # servertest.ini configuration
│   ├── sandbox_tab.py          # SandboxVars.lua settings & global search
│   ├── install_tab.py          # SteamCMD installation & branch selector
│   └── dialogs.py              # Graphical Backup GUI, Firewall rules, icons
│
├── config_manager.py           # INI and LUA parser & serializer
├── mod_manager.py              # Steam Workshop API parser & mod dependencies
├── server_installer.py         # SteamCMD downloader & version checker
├── server_process.py           # Server process lifecycle & port checker
├── backup_manager.py           # Full world ZIP backup, restore, and rotate engine
├── network_helper.py           # IP detection, Firewall & UPnP
├── translations.py             # Complete bilingual localization (RU / EN)
├── player_manager.py           # Live player tracking, RCON commands, Whitelist/Bans
├── watchdog_manager.py         # Crash watchdog & Discord webhook alerts
│
├── setup.bat / setup.sh        # Desktop setup scripts (Windows / Linux)
├── run.bat / run.sh            # Desktop run scripts (Windows / Linux)
├── run-web.bat / run-web.sh    # Web Dashboard runners (Windows / Linux)
├── setup_vps.sh                # Automated 1-command Linux VPS installer
├── build.bat / build.sh        # PyInstaller executable builders
├── pz_server_manager.spec      # PyInstaller build specification
└── README.md                   # Full bilingual documentation (RU & EN)
```

---

## 📄 License

This project is licensed under the open-source **MIT License**. See the [LICENSE](LICENSE) file for details.
