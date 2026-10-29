#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window for PZ Server Manager.
Coordinates UI tabs via modular mixins, system tray, menus, and application lifecycle.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QStatusBar, QFrame, QMessageBox, QApplication,
    QSystemTrayIcon, QMenu, QAction, QAbstractSpinBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap

from core.translations import tr, set_language, get_language
from core.config_manager import ConfigManager, AppPreferences
from core.server_process import ServerProcess
from core.mod_manager import ModManager
from core.server_installer import ServerInstaller
from core.backup_manager import BackupManager
from core.player_manager import PlayerManager
from core.watchdog_manager import WatchdogManager

from ui.dialogs import (
    DialogsMixin, create_zombie_app_icon, ensure_firewall_rules,
    NoScrollEventFilter, _b
)
from ui.server_tab import ServerTabMixin
from ui.settings_tab import SettingsTabMixin
from ui.sandbox_tab import SandboxTabMixin
from ui.mods_tab import ModsTabMixin
from ui.install_tab import InstallTabMixin

logger = logging.getLogger(__name__)


class MainWindow(
    QMainWindow,
    ServerTabMixin,
    SettingsTabMixin,
    SandboxTabMixin,
    ModsTabMixin,
    InstallTabMixin,
    DialogsMixin
):
    """Main application window composed of modular tab mixins."""

    def __init__(self, paths: dict, server_installed: bool):
        super().__init__()
        self.paths = paths
        self.server_installed = server_installed

        self.config_manager = ConfigManager(paths)
        self.server_process = ServerProcess(paths)
        self.mod_manager    = ModManager(paths)
        self.installer      = ServerInstaller(paths)
        self.selected_branch_key = "public"
        self.target_server_build = 42

        # Restore saved server name from preferences
        prefs = AppPreferences.load(paths)
        saved_name = prefs.get('last_server_name', 'servertest')
        self.config_manager.set_server_name(saved_name)
        self.mod_manager.set_server_name(saved_name)

        self.backup_manager = BackupManager(paths, saved_name)
        self.player_manager = PlayerManager(paths, saved_name)
        self.watchdog       = WatchdogManager(self)
        self.web_process    = None
        self.web_server_thread = None

        self.server_process.output_received.connect(self.append_console_output)
        self.server_process.output_received.connect(self.player_manager.parse_console_line)
        self.server_process.error_received.connect(self.append_console_error)
        self.server_process.server_launching.connect(self.on_server_launching)
        self.server_process.server_started.connect(self.on_server_started)
        self.server_process.server_ready.connect(self.on_server_ready)
        self.server_process.server_stopped.connect(self.on_server_stopped)
        self.server_process.process_exited.connect(self.on_server_process_exited)

        self.player_manager.players_updated.connect(self.on_players_updated)
        self.watchdog.log_message.connect(self.append_console_output)
        self.watchdog.restart_requested.connect(self.restart_server)

        self.init_ui()
        self.setup_menu()
        self.load_settings()

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)

    # ── UI Initialization ──────────────────────────────────────────

    def init_ui(self):
        self.setWindowTitle(tr('app_title'))
        self.setMinimumSize(950, 720)
        self.resize(1050, 780)

        # Set Zombie Application Icon
        zombie_icon = create_zombie_app_icon()
        self.setWindowIcon(zombie_icon)
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.setWindowIcon(zombie_icon)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Top Header Banner with Zombie Logo
        header = QFrame()
        header.setObjectName("header_banner")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)

        logo_lbl = QLabel()
        base_dirs = []
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dirs.append(Path(sys._MEIPASS))
            base_dirs.append(Path(sys.executable).parent)
        base_dirs.append(Path(__file__).resolve().parent.parent)
        base_dirs.append(Path(__file__).resolve().parent)

        icon_path = None
        for b in base_dirs:
            p1 = b / "assets" / "icon.png"
            if p1.exists():
                icon_path = p1
                break
            p2 = b / "icon.png"
            if p2.exists():
                icon_path = p2
                break

        if icon_path and icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("border-radius: 6px;")
        else:
            logo_lbl.setText("🧟")
            logo_lbl.setStyleSheet("font-size: 24px;")

        title_lbl = QLabel("Project Zomboid Server Manager")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #40ff40; margin-left: 6px;")

        header_layout.addWidget(logo_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        fw_btn = QPushButton("🔓 " + ("Открыть порты" if get_language() == 'ru' else "Open Firewall Ports"))
        fw_btn.setObjectName("header_btn_ports")
        fw_btn.setCursor(Qt.PointingHandCursor)
        fw_btn.clicked.connect(self.open_firewall_ports_action)
        header_layout.addWidget(fw_btn)

        share_btn = QPushButton("📋 " + ("Поделиться с друзьями" if get_language() == 'ru' else "Share with Friends"))
        share_btn.setObjectName("header_btn_share")
        share_btn.setCursor(Qt.PointingHandCursor)
        share_btn.setToolTip(
            "Скопировать IP и порт сервера в буфер обмена для отправки друзьям"
            if get_language() == 'ru' else
            "Copy server IP and connection info to clipboard"
        )
        share_btn.clicked.connect(self.share_server_info_action)
        header_layout.addWidget(share_btn)

        self.backup_btn = QPushButton("📦 " + ("Бэкапы" if get_language() == 'ru' else "Backups"))
        self.backup_btn.setObjectName("header_btn_backups")
        self.backup_btn.setCursor(Qt.PointingHandCursor)
        self.backup_btn.setToolTip(tr('backup_mgr_title'))
        self.backup_btn.clicked.connect(self.open_backup_manager)
        header_layout.addWidget(self.backup_btn)

        self.web_btn = QPushButton("🌐 " + ("Веб-панель" if get_language() == 'ru' else "Web Dashboard"))
        self.web_btn.setObjectName("header_btn_web")
        self.web_btn.setCursor(Qt.PointingHandCursor)
        self.web_btn.setToolTip(tr('web_dashboard_tooltip'))
        self.web_btn.clicked.connect(self.toggle_web_dashboard)
        header_layout.addWidget(self.web_btn)

        main_layout.addWidget(header)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.server_metrics_lbl = QLabel("")
        self.server_metrics_lbl.setStyleSheet("color: #38ef7d; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: bold; padding-right: 12px;")
        self.statusBar.addPermanentWidget(self.server_metrics_lbl)

        # Timer to monitor server resource usage (CPU & RAM)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_server_metrics)
        self.metrics_timer.start(2000)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._animate_tab_transition)
        main_layout.addWidget(self.tabs)

        self.create_server_tab()
        self.create_settings_tab()
        self.create_sandbox_tab()
        self.create_mods_tab()
        self.create_install_tab()

        self.update_target_server_build()
        self.update_status()

        # Disable mouse wheel scrolling on controls & hide spinbox arrows
        self.no_scroll_filter = NoScrollEventFilter(self)
        if app_inst:
            app_inst.installEventFilter(self.no_scroll_filter)

        for spin in self.findChildren(QAbstractSpinBox):
            spin.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self._setup_tray_icon()
        QTimer.singleShot(300, self.check_existing_server_status)
        QTimer.singleShot(1000, self._auto_ensure_firewall)
        QTimer.singleShot(1500, self.check_server_update_on_startup)

    def _auto_ensure_firewall(self):
        """Silently check and configure Windows Firewall rules if missing."""
        if os.name == 'nt':
            try:
                from core.network_helper import NetworkHelper
                if not NetworkHelper.check_firewall_rules_exist():
                    NetworkHelper.add_windows_firewall_rules()
            except Exception as e:
                logger.debug(f"Auto firewall check: {e}")

    def _animate_tab_transition(self, index: int):
        """Play a smooth fade-in opacity animation when changing tabs."""
        widget = self.tabs.widget(index)
        if not widget:
            return
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(160)
        anim.setStartValue(0.2)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        widget._tab_anim = anim
        anim.start()

    def update_target_server_build(self):
        """Update target build (42 or 41) based on user's selected branch and installed server."""
        branch = getattr(self, 'selected_branch_key', 'public') or 'public'
        new_build = 41 if '41' in branch.lower() else 42
        build_changed = (getattr(self, 'target_server_build', None) != new_build)
        self.target_server_build = new_build

        # Refresh mods tab banner and mod list only when changed or initial
        if hasattr(self, 'update_mods_server_status_banner'):
            self.update_mods_server_status_banner()
        if build_changed and hasattr(self, 'load_mods_list'):
            self.load_mods_list()

    # ── Tray ────────────────────────────────────────────────────────

    def _setup_tray_icon(self):
        """Setup system tray icon and context menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        self.tray_icon = QSystemTrayIcon(self)
        icon = create_zombie_app_icon()
        self.tray_icon.setIcon(icon)

        tray_menu = QMenu(self)
        a_show = QAction(tr('tray_show'), self)
        a_show.triggered.connect(self.show_normal_and_raise)
        tray_menu.addAction(a_show)

        a_start = QAction(tr('tray_start'), self)
        a_start.triggered.connect(self.start_server)
        tray_menu.addAction(a_start)

        a_stop = QAction(tr('tray_stop'), self)
        a_stop.triggered.connect(self.stop_server)
        tray_menu.addAction(a_stop)

        tray_menu.addSeparator()
        a_exit = QAction(tr('tray_exit'), self)
        a_exit.triggered.connect(self.quit_app)
        tray_menu.addAction(a_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_icon_activated)
        self.tray_icon.show()

    def show_normal_and_raise(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_normal_and_raise()

    def open_web_security_dialog(self):
        """Open dialog to configure port, password, and firewall for the Web Dashboard."""
        return self.toggle_web_dashboard(force_configure=True)

    def toggle_web_dashboard(self, force_configure: bool = False):
        """Configure and toggle or open the FastAPI Web Dashboard."""
        import webbrowser
        import threading
        is_ru = get_language() == 'ru'

        from core.config_manager import AppPreferences
        from web.auth import AuthManager
        from core.network_helper import NetworkHelper

        prefs = AppPreferences.load(self.paths)
        web_port = int(prefs.get('web_port', 8080))

        # Check if already running
        is_running = hasattr(self, 'web_server_thread') and self.web_server_thread and getattr(self.web_server_thread, 'is_running', False)

        if is_running and not force_configure:
            info_text = (
                f"🌐 Веб-панель уже работает на порту {web_port}!\n\n"
                f"URL: http://localhost:{web_port}\n\n"
                f"Выберите действие:"
                if is_ru else
                f"🌐 Web Dashboard is already running on port {web_port}!\n\n"
                f"URL: http://localhost:{web_port}\n\n"
                f"Choose an action:"
            )
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(tr('web_dashboard_title') or "Веб-панель")
            msg_box.setText(info_text)

            btn_open = msg_box.addButton("🌐 " + ("Открыть в браузере" if is_ru else "Open in Browser"), QMessageBox.AcceptRole)
            btn_reconfig = msg_box.addButton("⚙️ " + ("Изменить порт/пароль" if is_ru else "Change Port/Password"), QMessageBox.ActionRole)
            btn_stop = msg_box.addButton("⏹ " + ("Остановить" if is_ru else "Stop Server"), QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton(tr('btn_cancel') or "Отмена", QMessageBox.RejectRole)

            msg_box.exec_()
            clicked = msg_box.clickedButton()

            if clicked == btn_open:
                webbrowser.open(f"http://localhost:{web_port}")
                return True
            elif clicked == btn_stop:
                try:
                    self.web_server_thread.stop()
                    self.web_server_thread = None
                    if hasattr(self, 'web_btn'):
                        self.web_btn.setStyleSheet("background-color: #4a287a; color: #ffffff; padding: 4px 10px; font-weight: bold;")
                        self.web_btn.setText("🌐 " + ("Веб-панель" if is_ru else "Web Dashboard"))
                    QMessageBox.information(self, tr('web_dashboard_title'), tr('web_dashboard_stopped'))
                except Exception as e:
                    logger.error(f"Failed to stop web server: {e}")
                return True
            elif clicked == btn_reconfig:
                force_configure = True
            else:
                return False

        # Prompt with WebSecurityDialog to confirm or customize port & password
        from ui.dialogs import WebSecurityDialog
        pw_file = Path('initial_password.txt')
        current_password = ""
        if pw_file.exists():
            try:
                current_password = pw_file.read_text(encoding='utf-8').strip()
            except Exception:
                pass
        if not current_password:
            import secrets
            current_password = secrets.token_urlsafe(10)

        dlg = WebSecurityDialog(self, current_port=web_port, current_password=current_password)
        if dlg.exec_() != 1:
            return False

        new_port = dlg.result_port
        new_pw = dlg.result_password

        prefs['web_port'] = new_port
        prefs['web_configured'] = True
        AppPreferences.save(self.paths, prefs)

        am = AuthManager()
        am.set_password(new_pw)

        try:
            pw_file.write_text(new_pw, encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not write initial_password.txt: {e}")

        if dlg.result_open_firewall and os.name == 'nt':
            NetworkHelper.ensure_web_firewall_rule(new_port)

        # If already running, stop old instance
        if hasattr(self, 'web_server_thread') and self.web_server_thread and getattr(self.web_server_thread, 'is_running', False):
            try:
                self.web_server_thread.stop()
            except Exception:
                pass
            self.web_server_thread = None

        # Start FastAPI Web Dashboard in background thread
        try:
            import uvicorn
            from web.server import create_app
        except ImportError as e:
            logger.error(f"Web Dashboard dependencies not found: {e}")
            QMessageBox.warning(
                self,
                tr('web_dashboard_title'),
                "Библиотеки для веб-панели (FastAPI, Uvicorn) не найдены.\n"
                "Установите: pip install -r requirements-web.txt"
                if is_ru else
                "Web Dashboard dependencies (FastAPI, Uvicorn) not found.\n"
                "Install: pip install -r requirements-web.txt"
            )
            return False

        try:
            app = create_app(
                paths=self.paths,
                auth_manager=am,
                server_process=self.server_process,
                config_manager=self.config_manager,
                mod_manager=self.mod_manager,
                installer=self.installer
            )

            class _WebDashboardThread(threading.Thread):
                def __init__(self, fastapi_app, host="0.0.0.0", port=8080):
                    super().__init__(daemon=True, name="WebDashboardServer")
                    config = uvicorn.Config(app=fastapi_app, host=host, port=port, log_config=None)
                    self.server = uvicorn.Server(config)
                    self.is_running = False

                def run(self):
                    self.is_running = True
                    try:
                        self.server.run()
                    finally:
                        self.is_running = False

                def stop(self):
                    self.server.should_exit = True

            self.web_server_thread = _WebDashboardThread(app, port=new_port)
            self.web_server_thread.start()

            if hasattr(self, 'web_btn'):
                self.web_btn.setStyleSheet("background-color: #1e6b3b; color: #ffffff; padding: 4px 10px; font-weight: bold;")
                self.web_btn.setText(f"🌐 Веб-панель ({new_port}: Онлайн)" if is_ru else f"🌐 Web Dashboard ({new_port}: Online)")

            QTimer.singleShot(800, lambda: webbrowser.open(f"http://localhost:{new_port}"))
            self.statusBar.showMessage(f"🌐 Веб-панель: http://localhost:{new_port}" if is_ru else f"🌐 Web Dashboard: http://localhost:{new_port}", 10000)

            QMessageBox.information(
                self,
                tr('web_security_title'),
                f"🚀 Веб-панель успешно запущена!\n\n"
                f"• Адрес: http://localhost:{new_port}\n"
                f"• Пароль: {new_pw}\n\n"
                f"(Пароль сохранён в файле initial_password.txt)"
                if is_ru else
                f"🚀 Web Dashboard launched successfully!\n\n"
                f"• URL: http://localhost:{new_port}\n"
                f"• Password: {new_pw}\n\n"
                f"(Password saved to initial_password.txt)"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to launch Web Dashboard: {e}")
            QMessageBox.critical(self, tr('error'), f"Failed to start Web Dashboard: {e}")
            return False

    def quit_app(self):
        """Force application exit."""
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        if hasattr(self, 'web_server_thread') and self.web_server_thread:
            try:
                self.web_server_thread.stop()
            except Exception:
                pass
        if hasattr(self, 'web_process') and self.web_process and self.web_process.poll() is None:
            try:
                self.web_process.terminate()
            except Exception:
                pass
        if self.server_process.is_running():
            self.server_process.stop()
        QApplication.quit()

    # ── Menu ────────────────────────────────────────────────────────

    def setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu(tr('menu_file'))
        a = QAction(tr('menu_change_dir'), self)
        a.triggered.connect(self.change_server_directory)
        file_menu.addAction(a)
        file_menu.addSeparator()
        a = QAction(tr('menu_exit'), self)
        a.triggered.connect(self.close)
        file_menu.addAction(a)

        tools_menu = menubar.addMenu(tr('menu_tools'))
        for key, slot in [
            ('menu_validate',      self.validate_server),
            ('menu_update',        self.update_server),
            ('btn_manage_backups', self.open_backup_manager),
            ('btn_web_dashboard',  self.toggle_web_dashboard),
            (None,                 None),
            ('menu_open_config',   self.open_config_folder),
            ('menu_open_server',   self.open_server_folder),
        ]:
            if key is None:
                tools_menu.addSeparator()
            else:
                a = QAction(tr(key), self)
                a.triggered.connect(slot)
                tools_menu.addAction(a)

        lang_menu = menubar.addMenu(tr('menu_language'))
        a = QAction('🇷🇺 Русский', self)
        a.triggered.connect(lambda: self.change_language('ru'))
        lang_menu.addAction(a)
        a = QAction('🇬🇧 English', self)
        a.triggered.connect(lambda: self.change_language('en'))
        lang_menu.addAction(a)

        help_menu = menubar.addMenu(tr('menu_help'))
        a = QAction(tr('menu_about'), self)
        a.triggered.connect(self.show_about)
        help_menu.addAction(a)
        a = QAction(tr('menu_firewall'), self)
        a.triggered.connect(self.show_firewall_info)
        help_menu.addAction(a)

    # ── Utilities & Lifecycle ───────────────────────────────────────

    def check_existing_server_status(self):
        """Check on startup if Project Zomboid dedicated server is already running."""
        pid = self.server_process.detect_and_attach_running_server()
        if pid:
            self.on_server_ready()
            is_ru = get_language() == 'ru'
            msg = (
                f"ℹ️ " + (f"Обнаружен работающий сервер Project Zomboid (PID: {pid}). Управление активно."
                          if is_ru else
                          f"Discovered active Project Zomboid server (PID: {pid}). Management attached.")
            )
            self.append_console_output(msg)

    def update_status(self):
        if self.server_process.is_running():
            if getattr(self.server_process, 'is_ready', False):
                self.statusBar.showMessage(tr('server_ready'))
            else:
                self.statusBar.showMessage(tr('server_launching'))
        else:
            self.statusBar.showMessage(tr('server_stopped'))

    def change_language(self, language: str):
        if get_language() == language:
            return

        set_language(language)
        try:
            with open('language.cfg', 'w') as f:
                f.write(language)
        except Exception as e:
            logger.error(f"Failed to save language.cfg: {e}")

        # Hide tray icon to prevent leftover icon in system tray
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()

        # Stop running server gracefully before restart
        if self.server_process.is_running():
            try:
                self.server_process.stop()
            except Exception:
                pass

        # Automatically relaunch application process
        try:
            args = [sys.executable] + sys.argv
            subprocess.Popen(args)
        except Exception as e:
            logger.error(f"Failed to relaunch application: {e}")

        QApplication.quit()

    def closeEvent(self, event):
        """Handle window close event: minimize to tray or confirm server stop."""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                tr('app_title'),
                tr('tray_minimized'),
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
            return

        if self.server_process.is_running():
            res = QMessageBox.question(
                self, tr('server_running_close'), tr('server_running_close_msg'),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if res == QMessageBox.Yes:
                self.stop_server()
                event.accept()
            elif res == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
