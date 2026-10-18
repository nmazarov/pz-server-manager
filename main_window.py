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

from translations import tr, set_language, get_language
from config_manager import ConfigManager
from server_process import ServerProcess
from mod_manager import ModManager
from server_installer import ServerInstaller

from ui import (
    DialogsMixin, create_zombie_app_icon, ensure_firewall_rules,
    NoScrollEventFilter, _b,
    ServerTabMixin, SettingsTabMixin, SandboxTabMixin,
    ModsTabMixin, InstallTabMixin
)

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

        self.server_process.output_received.connect(self.append_console_output)
        self.server_process.error_received.connect(self.append_console_error)
        self.server_process.server_started.connect(self.on_server_started)
        self.server_process.server_stopped.connect(self.on_server_stopped)

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
        header.setStyleSheet("background-color: #252526; border-radius: 6px; border: 1px solid #3c3c3c;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 6, 12, 6)

        logo_lbl = QLabel()
        base_dirs = []
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dirs.append(Path(sys._MEIPASS))
            base_dirs.append(Path(sys.executable).parent)
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
        fw_btn.setStyleSheet("background-color: #2b5b2b; color: #ffffff; padding: 4px 10px;")
        fw_btn.clicked.connect(self.open_firewall_ports_action)
        header_layout.addWidget(fw_btn)

        share_btn = QPushButton("📋 " + ("Поделиться с друзьями" if get_language() == 'ru' else "Share with Friends"))
        share_btn.setStyleSheet("background-color: #1e4b7a; color: #ffffff; padding: 4px 10px; font-weight: bold;")
        share_btn.setToolTip(
            "Скопировать IP и порт сервера в буфер обмена для отправки друзьям"
            if get_language() == 'ru' else
            "Copy server IP and connection info to clipboard"
        )
        share_btn.clicked.connect(self.share_server_info_action)
        header_layout.addWidget(share_btn)

        main_layout.addWidget(header)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.server_metrics_lbl = QLabel("")
        self.server_metrics_lbl.setStyleSheet("color: #a0ffa0; font-weight: bold; padding-right: 12px;")
        self.statusBar.addPermanentWidget(self.server_metrics_lbl)

        # Timer to monitor server resource usage (CPU & RAM)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.update_server_metrics)
        self.metrics_timer.start(2000)

        self.tabs = QTabWidget()
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
        QTimer.singleShot(1500, self.check_server_update_on_startup)

    def update_target_server_build(self):
        """Update target build (42 or 41) based on user's selected branch and installed server."""
        branch = getattr(self, 'selected_branch_key', 'public') or 'public'
        if '41' in branch.lower():
            self.target_server_build = 41
        else:
            self.target_server_build = 42

        # Refresh mods tab banner and mod list
        if hasattr(self, 'update_mods_server_status_banner'):
            self.update_mods_server_status_banner()
        if hasattr(self, 'load_mods_list'):
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

    def quit_app(self):
        """Force application exit."""
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
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

    def update_status(self):
        if self.server_process.is_running():
            self.statusBar.showMessage(tr('status_running'))
        else:
            self.statusBar.showMessage(tr('status_stopped'))

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
