import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5.QtWidgets import QApplication, QListWidgetItem, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
from main import get_default_paths, load_theme_stylesheet

def capture_screenshots():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Apply dark tactical theme
    stylesheet = load_theme_stylesheet()
    app.setStyleSheet(stylesheet)

    os.makedirs("assets/screenshots", exist_ok=True)
    paths = get_default_paths()
    w = MainWindow(paths, True)
    w.resize(1366, 768)
    w.show()

    for _ in range(15):
        app.processEvents()
        time.sleep(0.04)

    # ─────────────────────────────────────────────────────────────
    # 1. Tab 0: Dashboard (Управление сервером и терминал)
    # ─────────────────────────────────────────────────────────────
    w.tabs.setCurrentIndex(0)
    sample_logs = (
        "[13:30:12] [INFO] Project Zomboid Dedicated Server v41.78.16 initialized.\n"
        "[13:30:13] [INFO] Loading world save: Saves/Multiplayer/servertest\n"
        "[13:30:15] [NETWORK] Steam Game Server initialized on ports 16261 (UDP), 8766 (Steam)\n"
        "[13:30:16] [CONFIG] Loaded 146 server configuration rules from servertest.ini\n"
        "[13:30:18] [MAP] Vehicle & Zombie spawn maps pre-cached successfully.\n"
        "[13:30:20] [SECURITY] Server is open for connections. VAC secured: ACTIVE.\n"
        "[13:31:05] [USER] Player 'RickGrimes' connected (SteamID: 76561198012345678, Ping: 14ms)\n"
        "[13:31:40] [USER] Player 'DarylDixon' connected (SteamID: 76561198087654321, Ping: 22ms)\n"
        "[13:32:10] [CHAT] RickGrimes: 'Heading towards West Point hardware store!'\n"
        "[13:33:00] [WORLD] Auto-saving world map state... OK.\n"
    )
    if hasattr(w, "console_output"):
        w.console_output.setPlainText(sample_logs)

    if hasattr(w, "players_list"):
        w.players_list.clear()
        w.players_list.addItem(QListWidgetItem("🟢 RickGrimes (14 ms)"))
        w.players_list.addItem(QListWidgetItem("🟢 DarylDixon (22 ms)"))
        w.players_list.addItem(QListWidgetItem("⚪ GlennRhee (Оффлайн)"))
    if hasattr(w, "lbl_players_count"):
        w.lbl_players_count.setText("👥 Игроки онлайн (2)")

    for _ in range(10):
        app.processEvents()
        time.sleep(0.04)
    w.grab().save("assets/screenshots/01_dashboard.png", "PNG")
    print("Saved 01_dashboard.png")

    # ─────────────────────────────────────────────────────────────
    # 2. Tab 1: Server Settings (Настройки сервера INI)
    # ─────────────────────────────────────────────────────────────
    w.tabs.setCurrentIndex(1)
    for _ in range(10):
        app.processEvents()
        time.sleep(0.04)
    w.grab().save("assets/screenshots/02_server_settings.png", "PNG")
    print("Saved 02_server_settings.png")

    # ─────────────────────────────────────────────────────────────
    # 3. Tab 2: Sandbox Config (Настройки Sandbox / Транспорт и пресеты)
    # ─────────────────────────────────────────────────────────────
    w.tabs.setCurrentIndex(2)
    if hasattr(w, "sandbox_subtabs"):
        w.sandbox_subtabs.setCurrentIndex(3)  # Вкладка "Транспорт"
    if hasattr(w, "preset_combo"):
        w.preset_combo.setCurrentText("Survivor (По умолчанию)")
    for _ in range(10):
        app.processEvents()
        time.sleep(0.04)
    w.grab().save("assets/screenshots/03_sandbox_vars.png", "PNG")
    print("Saved 03_sandbox_vars.png")

    # ─────────────────────────────────────────────────────────────
    # 4. Tab 3: Mods Manager (Мастер модов Steam Workshop)
    # ─────────────────────────────────────────────────────────────
    w.tabs.setCurrentIndex(3)
    if hasattr(w, "mods_list"):
        w.mods_list.clear()
        mods = [
            "🟢 Brita's Weapon Pack [2200145667] (ID: BritaWeaponPack) — Build 41 / 42 Verified",
            "🟢 Filibuster Rhymes' Used Cars! [1510950729] (ID: FRUsedCars) — Build 41 / 42 Verified",
            "🟢 Common Sense [2875848298] (ID: CommonSense) — Universal QoL",
            "🟢 True Actions (Act 1 & 2) [2487024875] (ID: TrueActionsCode) — Build 41 / 42 Verified",
            "🟡 Tsar's Common Library 2.0 [2392709985] (ID: tsarslib) — Core Framework",
            "🟢 Autotsar Tuning Atelier - Jaap Wrungel [2636100523] (ID: ata_jeep) — Build 41 / 42 Verified"
        ]
        for m in mods:
            w.mods_list.addItem(QListWidgetItem(m))
    for _ in range(10):
        app.processEvents()
        time.sleep(0.04)
    w.grab().save("assets/screenshots/04_mods_manager.png", "PNG")
    print("Saved 04_mods_manager.png")

    # ─────────────────────────────────────────────────────────────
    # 5. Tab 5: Interactive World Map (Интерактивная карта и радар)
    # ─────────────────────────────────────────────────────────────
    w.tabs.setCurrentIndex(5)
    if hasattr(w, "pz_map_canvas"):
        w.pz_map_canvas.fly_to(11900, 6850, target_scale=0.55)
        w.pz_map_canvas.set_players([
            {"username": "RickGrimes", "character": "Sheriff Rick", "x": 11950, "y": 6820, "online": True, "dead": False},
            {"username": "DarylDixon", "character": "Daryl", "x": 11840, "y": 6910, "online": True, "dead": False},
            {"username": "GlennRhee", "character": "Runner", "x": 12100, "y": 6750, "online": False, "dead": False}
        ])
    if hasattr(w, "tbl_map_players"):
        w.tbl_map_players.setRowCount(3)
        w.tbl_map_players.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        w.tbl_map_players.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        w.tbl_map_players.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        players = [
            ("🟢 RickGrimes", "Онлайн", "11950, 6820"),
            ("🟢 DarylDixon", "Онлайн", "11840, 6910"),
            ("🔵 GlennRhee", "Оффлайн", "12100, 6750"),
        ]
        for row, (nick, status, coords) in enumerate(players):
            w.tbl_map_players.setItem(row, 0, QTableWidgetItem(nick))
            w.tbl_map_players.setItem(row, 1, QTableWidgetItem(status))
            w.tbl_map_players.setItem(row, 2, QTableWidgetItem(coords))

    for _ in range(25):
        app.processEvents()
        time.sleep(0.06)
    w.grab().save("assets/screenshots/05_interactive_map.png", "PNG")
    print("Saved 05_interactive_map.png")

    w.cleanup_map_tab()
    w.close()
    print("Finished regenerating all 5 polished screenshots!")

if __name__ == "__main__":
    capture_screenshots()
