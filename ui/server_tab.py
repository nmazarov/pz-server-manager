#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Tab Mixin for PZ Server Manager.
Handles server lifecycle, live console output, quick admin commands, and resource monitoring.
"""

import os
import logging
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QCheckBox, QComboBox, QPlainTextEdit, QGroupBox, QGridLayout, QMessageBox,
    QInputDialog, QSizePolicy, QDialog, QListWidget, QSystemTrayIcon, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont

from translations import tr, get_language
from server_process import check_ports_in_use
from config_manager import AppPreferences

START_BTN_STYLE = """
QPushButton#start_btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2eb84d, stop:1 #208336);
    border: 1px solid #1c6d2d;
    border-radius: 6px;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    padding: 8px 20px;
}
QPushButton#start_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3be060, stop:1 #269e40);
    border: 1px solid #55ff88;
}
QPushButton#start_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #186329, stop:1 #11471d);
    border: 1px solid #0d3616;
    padding-top: 10px;
    padding-bottom: 6px;
}
QPushButton#start_btn:disabled {
    background: #243026;
    border: 1px solid #2d3d30;
    color: #556b59;
}
"""

STOP_BTN_STYLE = """
QPushButton#stop_btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d93838, stop:1 #a82222);
    border: 1px solid #8f1c1c;
    border-radius: 6px;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    padding: 8px 20px;
}
QPushButton#stop_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fa4d4d, stop:1 #c92828);
    border: 1px solid #ff7575;
}
QPushButton#stop_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7d1717, stop:1 #590f0f);
    border: 1px solid #450b0b;
    padding-top: 10px;
    padding-bottom: 6px;
}
QPushButton#stop_btn:disabled {
    background: #332424;
    border: 1px solid #3d2b2b;
    color: #6b5555;
}
"""

RESTART_BTN_STYLE = """
QPushButton#restart_btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b6cb0, stop:1 #1d4e82);
    border: 1px solid #163c63;
    border-radius: 6px;
    color: #ffffff;
    font-weight: bold;
    font-size: 13px;
    padding: 8px 20px;
}
QPushButton#restart_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b8be0, stop:1 #2463a6);
    border: 1px solid #63b3ff;
}
QPushButton#restart_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #143559, stop:1 #0e243d);
    border: 1px solid #091829;
    padding-top: 10px;
    padding-bottom: 6px;
}
QPushButton#restart_btn:disabled {
    background: #242930;
    border: 1px solid #2d3440;
    color: #555e6b;
}
"""


class ServerTabMixin:
    """Mixin for the Server control tab and live console."""

    def _animate_button_click(self, btn: QPushButton, base_style: str, glow_color: str):
        """Play a smooth physical glow pulse animation when button is clicked."""
        pulse_style = base_style + f"\nQPushButton {{ border: 2px solid {glow_color} !important; }}"
        btn.setStyleSheet(pulse_style)
        QTimer.singleShot(140, lambda: btn.setStyleSheet(base_style) if btn else None)

    def create_server_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # ── Status Banner Card ─────────────────────────────────────────
        status_card = QFrame()
        status_card.setStyleSheet("background-color: #252526; border: 1px solid #3c3c3c; border-radius: 6px;")
        sc_layout = QHBoxLayout(status_card)
        sc_layout.setContentsMargins(14, 8, 14, 8)

        self.status_indicator = QLabel("🔴")
        self.status_indicator.setStyleSheet("font-size: 22px;")
        sc_layout.addWidget(self.status_indicator)

        self.status_label = QLabel(tr('server_stopped'))
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6666;")
        sc_layout.addWidget(self.status_label)

        sc_layout.addStretch()

        self.status_detail_label = QLabel("127.0.0.1:16261")
        self.status_detail_label.setStyleSheet("font-size: 12px; color: #999999; font-family: monospace;")
        sc_layout.addWidget(self.status_detail_label)

        layout.addWidget(status_card)

        # ── Group: Server Controls ─────────────────────────────────────
        controls_group = QGroupBox(tr('group_server_control'))
        cl = QVBoxLayout(controls_group)

        # Load persistent user preferences
        prefs = AppPreferences.load(self.paths)
        saved_server_name = prefs.get('last_server_name', 'servertest')
        saved_ram = prefs.get('last_ram_gb', 6)
        saved_auto_backup = prefs.get('auto_backup', True)

        row_top = QHBoxLayout()
        name_lbl = QLabel(tr('lbl_server_name'))
        name_lbl.setStyleSheet("font-weight: bold;")
        row_top.addWidget(name_lbl)

        self.server_name_input = QLineEdit(saved_server_name)
        self.server_name_input.setPlaceholderText("e.g. servertest")
        self.server_name_input.textChanged.connect(self.on_server_name_changed)
        row_top.addWidget(self.server_name_input)

        ram_lbl = QLabel(" " + ("Выделение ОЗУ (RAM):" if get_language() == 'ru' else "Server RAM:"))
        ram_lbl.setStyleSheet("font-weight: bold; margin-left: 10px;")
        row_top.addWidget(ram_lbl)

        self.server_ram_combo = QComboBox()
        default_ram_idx = 1
        for idx, gb in enumerate([4, 6, 8, 10, 12, 16, 20, 24, 32]):
            self.server_ram_combo.addItem(f"{gb} GB", gb)
            if gb == saved_ram:
                default_ram_idx = idx
        self.server_ram_combo.setCurrentIndex(default_ram_idx)
        self.server_ram_combo.currentIndexChanged.connect(self._on_ram_changed)
        self.server_ram_combo.setToolTip("Выделение оперативной памяти для сервера (-Xms / -Xmx)" if get_language() == 'ru' else "Allocate RAM for dedicated server")
        row_top.addWidget(self.server_ram_combo)

        cl.addLayout(row_top)

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("▶ " + tr('btn_start_server'))
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setStyleSheet(START_BTN_STYLE)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(lambda: self._animate_button_click(self.start_btn, START_BTN_STYLE, "#77ffaa"))
        self.start_btn.clicked.connect(self.start_server)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ " + tr('btn_stop_server'))
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setStyleSheet(STOP_BTN_STYLE)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.clicked.connect(lambda: self._animate_button_click(self.stop_btn, STOP_BTN_STYLE, "#ff8888"))
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)

        self.restart_btn = QPushButton("🔄 " + tr('btn_restart_server'))
        self.restart_btn.setObjectName("restart_btn")
        self.restart_btn.setStyleSheet(RESTART_BTN_STYLE)
        self.restart_btn.setCursor(Qt.PointingHandCursor)
        self.restart_btn.clicked.connect(lambda: self._animate_button_click(self.restart_btn, RESTART_BTN_STYLE, "#77bbff"))
        self.restart_btn.clicked.connect(self.restart_server)
        self.restart_btn.setEnabled(False)
        btn_row.addWidget(self.restart_btn)

        cl.addLayout(btn_row)

        # Launch animation timer for pulsing status and dynamic dots
        self._launch_anim_timer = QTimer(self)
        self._launch_anim_frame = 0
        self._launch_anim_timer.timeout.connect(self._step_launch_animation)

        del_save_btn = QPushButton("🗑️ " + ("Сбросить/Удалить сохранение этого мира" if get_language() == 'ru' else "Reset / Delete this World Save"))
        del_save_btn.setStyleSheet("background-color: #553333; color: #ffcccc; font-size: 11px;")
        del_save_btn.setToolTip("Удаляет сохраненную карту этого мира, если возникла ошибка несовместимости версий карт (например, Build 42 в Build 41)" if get_language() == 'ru' else "Deletes the world save folder for this server if version mismatch occurs")
        del_save_btn.clicked.connect(self.delete_save_world_action)
        cl.addWidget(del_save_btn)

        self.auto_backup_checkbox = QCheckBox("📦 " + ("Авто-бэкап мира перед запуском" if get_language() == 'ru' else "Auto-backup world on launch"))
        self.auto_backup_checkbox.setChecked(saved_auto_backup)
        self.auto_backup_checkbox.toggled.connect(self._on_auto_backup_toggled)
        self.auto_backup_checkbox.setToolTip("Автоматически создавать резервную копию файлов сохранения мира перед каждым стартом" if get_language() == 'ru' else "Automatically backup world save before starting")
        cl.addWidget(self.auto_backup_checkbox)

        layout.addWidget(controls_group)

        # ── Group: Console Output ──────────────────────────────────────
        console_group = QGroupBox(tr('group_console'))
        conl = QVBoxLayout(console_group)

        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumBlockCount(3000)
        self.console_output.setFont(QFont(self._mono_font(), 9))
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        conl.addWidget(self.console_output)

        self._console_buffer = []
        self._console_timer = QTimer(self)
        self._console_timer.setInterval(100)
        self._console_timer.timeout.connect(self._flush_console_buffer)
        self._console_timer.start()

        cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText(tr('ph_command'))
        self.cmd_input.returnPressed.connect(self.send_console_command)
        cmd_row.addWidget(self.cmd_input)

        send_btn = QPushButton(tr('btn_send'))
        send_btn.clicked.connect(self.send_console_command)
        cmd_row.addWidget(send_btn)
        conl.addLayout(cmd_row)

        # ── Quick Actions Row ──────────────────────────────────────────
        quick_row = QHBoxLayout()
        quick_lbl = QLabel("⚡ " + ("Быстрые команды:" if get_language() == 'ru' else "Quick Actions:"))
        quick_lbl.setStyleSheet("font-weight: bold; color: #5294e2;")
        quick_row.addWidget(quick_lbl)

        btn_save_world = QPushButton("💾 " + ("Сохранить мир" if get_language() == 'ru' else "Save World"))
        btn_save_world.setToolTip("Отправить команду 'save' для немедленного сохранения мира" if get_language() == 'ru' else "Send 'save' command")
        btn_save_world.clicked.connect(lambda: self.send_quick_server_cmd("save"))
        quick_row.addWidget(btn_save_world)

        btn_rain = QPushButton("🌧️ " + ("Дождь Вкл/Выкл" if get_language() == 'ru' else "Toggle Rain"))
        btn_rain.setToolTip("Вызвать или остановить дождь на сервере" if get_language() == 'ru' else "Start or stop rain")
        btn_rain.clicked.connect(self.toggle_rain_action)
        quick_row.addWidget(btn_rain)

        btn_heli = QPushButton("🚁 " + ("Вызвать вертолет" if get_language() == 'ru' else "Trigger Heli"))
        btn_heli.setToolTip("Запустить вертолетное событие над случайным игроком" if get_language() == 'ru' else "Trigger helicopter event")
        btn_heli.clicked.connect(lambda: self.send_quick_server_cmd("chopper"))
        quick_row.addWidget(btn_heli)

        btn_broadcast = QPushButton("📢 " + ("Объявление в чат" if get_language() == 'ru' else "Broadcast Msg"))
        btn_broadcast.setToolTip("Отправить глобальное системное сообщение всем игрокам в чат" if get_language() == 'ru' else "Send global server message to all players")
        btn_broadcast.clicked.connect(self.broadcast_message_action)
        quick_row.addWidget(btn_broadcast)

        quick_row.addStretch()
        conl.addLayout(quick_row)

        layout.addWidget(console_group)
        self.tabs.addTab(tab, tr('tab_server'))

    def _on_ram_changed(self):
        if hasattr(self, 'server_ram_combo'):
            ram = self.server_ram_combo.currentData()
            if ram:
                AppPreferences.save(self.paths, {'last_ram_gb': int(ram)})

    def _on_auto_backup_toggled(self, checked: bool):
        AppPreferences.save(self.paths, {'auto_backup': bool(checked)})

    def on_server_name_changed(self, text: str):
        name = text.strip() or 'servertest'
        AppPreferences.save(self.paths, {'last_server_name': name})
        if hasattr(self, 'config_manager'):
            self.config_manager.set_server_name(name)
        if hasattr(self, 'mod_manager'):
            self.mod_manager.set_server_name(name)

    def _step_launch_animation(self):
        dots = [".  ", ".. ", "...", " ..", "  .", "   "][self._launch_anim_frame % 6]
        self._launch_anim_frame += 1
        if hasattr(self, 'start_btn') and not self.start_btn.isEnabled():
            self.start_btn.setText(f"⏳ {tr('btn_start_server')} {dots}")
        if hasattr(self, 'status_indicator'):
            icons = ["🟡", "🟠"]
            self.status_indicator.setText(icons[self._launch_anim_frame % len(icons)])

    def start_server(self):
        if not self.server_installed:
            QMessageBox.warning(self, tr('server_not_installed'), tr('server_not_installed_msg'))
            return

        try:
            game_port = getattr(self, 'setting_game_port', None)
            g_p = game_port.text().strip() if game_port else '16261'
            steam_port = getattr(self, 'setting_steam_port1', None)
            s_p = steam_port.text().strip() if steam_port else '8766'
            rcon_port = getattr(self, 'setting_rcon_port', None)
            r_p = rcon_port.text().strip() if rcon_port else '27015'

            in_use = check_ports_in_use([g_p, s_p, r_p])
            if in_use:
                running_pid = self.server_process.detect_and_attach_running_server()
                if running_pid:
                    res = QMessageBox.question(
                        self,
                        tr('app_title'),
                        ("Сервер Project Zomboid уже запущен (PID: %s)!\n\n"
                         "Вы хотите остановить старый процесс и перезапустить сервер заново?" % running_pid)
                        if get_language() == 'ru' else
                        ("Project Zomboid server is already running (PID: %s)!\n\n"
                         "Do you want to stop the existing process and restart fresh?" % running_pid),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    if res == QMessageBox.Yes:
                        self.append_console_output("⏹ " + ("Остановка предыдущего процесса сервера..." if get_language() == 'ru' else "Stopping previous server process..."))
                        self.server_process.stop()
                        self.on_server_stopped()
                        QTimer.singleShot(1500, self.start_server)
                        return
                    else:
                        self.on_server_ready()
                        return
                else:
                    res = QMessageBox.warning(
                        self,
                        tr('app_title'),
                        tr('warn_ports_in_use', ports=", ".join(map(str, in_use))),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if res != QMessageBox.Yes:
                        return
        except Exception as e:
            logger.debug(f"Port check failed: {e}")

        name = self.server_name_input.text().strip() or 'servertest'
        ram_data = self.server_ram_combo.currentData() if hasattr(self, 'server_ram_combo') else 6
        ram_gb = int(ram_data) if ram_data else 6
        auto_bkp = self.auto_backup_checkbox.isChecked() if hasattr(self, 'auto_backup_checkbox') else True

        # Save all settings to preferences permanently
        AppPreferences.save(self.paths, {
            'last_server_name': name,
            'last_ram_gb': ram_gb,
            'auto_backup': auto_bkp
        })

        # Auto-backup before start if enabled
        if auto_bkp:
            try:
                from backup_manager import BackupManager
                bm = BackupManager(self.paths, server_name=name)
                save_dir = self.paths['zomboid_dir'] / 'Saves' / 'Multiplayer' / name
                cfg_file = self.paths['zomboid_dir'] / 'Server' / f"{name}.ini"
                if save_dir.exists() or cfg_file.exists():
                    self.append_console_output("📦 " + ("Создание авто-бэкапа мира перед запуском..." if get_language() == 'ru' else "Creating pre-launch auto-backup..."))
                    b_path = bm.create_backup(tag="launch")
                    self.append_console_output(f"✅ " + (f"Бэкап сохранен: {Path(b_path).name}" if get_language() == 'ru' else f"Backup saved: {Path(b_path).name}"))
            except Exception as e:
                logger.error(f"Pre-launch backup error: {e}")
                self.append_console_error(f"⚠️ Pre-launch backup warning: {e}")

        self.on_server_launching()
        self.append_console_output(f"🟡 {tr('starting_server')} '{name}' (RAM: {ram_gb} GB)...")
        try:
            self.server_process.start(name, ram_gb=ram_gb)
        except Exception as e:
            self.append_console_error(f"Failed to start: {e}")
            self.on_server_stopped()

    def stop_server(self):
        self.append_console_output("⏹ " + tr('stopping_server'))
        try:
            self.server_process.stop()
        except Exception as e:
            self.append_console_error(f"Failed to stop: {e}")
        finally:
            self.on_server_stopped()

    def restart_server(self):
        name = self.server_name_input.text().strip() or 'servertest'
        ram_data = self.server_ram_combo.currentData() if hasattr(self, 'server_ram_combo') else 6
        ram_gb = int(ram_data) if ram_data else 6
        self.on_server_launching()
        self.append_console_output(f"🔄 {tr('restarting_server')} '{name}' (RAM: {ram_gb} GB)...")
        try:
            self.server_process.restart(name, ram_gb=ram_gb)
        except Exception as e:
            self.append_console_error(f"Failed to restart: {e}")
            self.on_server_stopped()

    def send_console_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self.append_console_output(f"> {cmd}")
        self.server_process.send_command(cmd)
        self.cmd_input.clear()

    def send_command(self):
        self.send_console_command()

    def on_server_launching(self):
        """Called when server process is initiated and loading mods/world."""
        if hasattr(self, 'status_indicator'):
            self.status_indicator.setText("🟡")
        if hasattr(self, 'status_label'):
            self.status_label.setText(tr('server_launching'))
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffcc00;")
        if hasattr(self, 'status_detail_label'):
            self.status_detail_label.setText("Загрузка модов и мира..." if get_language() == 'ru' else "Loading mods & world...")
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(False)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(True)
        if hasattr(self, 'restart_btn'):
            self.restart_btn.setEnabled(True)
        if hasattr(self, '_launch_anim_timer'):
            self._launch_anim_frame = 0
            self._launch_anim_timer.start(350)

    def on_server_started(self):
        """Called when server process is spawned."""
        if getattr(self.server_process, 'is_ready', False):
            self.on_server_ready()
        else:
            self.on_server_launching()

    def on_server_ready(self):
        """Called when server has finished loading and is ready for player connections."""
        if hasattr(self, '_launch_anim_timer'):
            self._launch_anim_timer.stop()
        if hasattr(self, 'start_btn'):
            self.start_btn.setText("▶ " + tr('btn_start_server'))
            self.start_btn.setEnabled(False)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(True)
        if hasattr(self, 'restart_btn'):
            self.restart_btn.setEnabled(True)
        if hasattr(self, 'status_indicator'):
            self.status_indicator.setText("🟢")
        if hasattr(self, 'status_label'):
            self.status_label.setText(tr('server_ready'))
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ff66;")
        if hasattr(self, 'status_detail_label'):
            detail_msg = "🟢 127.0.0.1:16261 • " + ("Готов к игре!" if get_language() == 'ru' else "Ready to join!")
            self.status_detail_label.setText(detail_msg)

        # Sound Alert (Windows chime or beep)
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            try:
                from PyQt5.QtWidgets import QApplication
                QApplication.beep()
            except Exception:
                pass

        # Tray alert balloon
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(tr('app_title'), tr('tray_server_ready'), QSystemTrayIcon.Information, 5000)

        # Prominent highlight banner in server console
        is_ru = get_language() == 'ru'
        title_banner = "🎉 СЕРВЕР УСПЕШНО ЗАПУЩЕН И ГОТОВ К ИГРЕ!" if is_ru else "🎉 SERVER IS ONLINE AND READY TO PLAY!"
        port_banner = "👉 Порт подключения: 127.0.0.1:16261 (для друзей: ваш внешний IP:16261)" if is_ru else "👉 Connect address: 127.0.0.1:16261 (friends: your external IP:16261)"
        ready_banner = (
            f"\n{'=' * 65}\n"
            f"{title_banner}\n"
            f"{port_banner}\n"
            f"{'=' * 65}"
        )
        self.append_console_output(ready_banner)

    def on_server_stopped(self):
        """Called when server process is terminated."""
        if hasattr(self, '_launch_anim_timer'):
            self._launch_anim_timer.stop()
        if hasattr(self, 'start_btn'):
            self.start_btn.setText("▶ " + tr('btn_start_server'))
            self.start_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)
        if hasattr(self, 'restart_btn'):
            self.restart_btn.setEnabled(False)
        if hasattr(self, 'status_indicator'):
            self.status_indicator.setText("🔴")
        if hasattr(self, 'status_label'):
            self.status_label.setText(tr('server_stopped'))
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6666;")
        if hasattr(self, 'status_detail_label'):
            self.status_detail_label.setText("127.0.0.1:16261")
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(tr('app_title'), tr('tray_server_stopped'), QSystemTrayIcon.Information, 3000)

    def append_console_output(self, text: str):
        ts = datetime.now().strftime('%H:%M:%S')
        if not hasattr(self, '_console_buffer'):
            self._console_buffer = []
        self._console_buffer.append(f'[{ts}] {text}')

    def append_console_error(self, text: str):
        ts = datetime.now().strftime('%H:%M:%S')
        if not hasattr(self, '_console_buffer'):
            self._console_buffer = []
        self._console_buffer.append(f'[{ts}] ERROR: {text}')

    def _flush_console_buffer(self):
        if not hasattr(self, '_console_buffer') or not self._console_buffer:
            return
        batch = self._console_buffer
        self._console_buffer = []
        combined = "\n".join(batch)
        self.console_output.appendPlainText(combined)

    def open_backup_manager(self):
        """Show backup manager dialog to list and restore config backups."""
        backups = self.config_manager.list_backups()
        if not backups:
            QMessageBox.information(self, tr('backup_title'), tr('no_backups_found'))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(tr('backup_title'))
        dialog.resize(500, 350)
        vlayout = QVBoxLayout(dialog)

        lbl = QLabel(tr('backup_title'))
        vlayout.addWidget(lbl)

        list_widget = QListWidget()
        for b_path in backups:
            list_widget.addItem(b_path.name)
        vlayout.addWidget(list_widget)

        btn_row = QHBoxLayout()
        restore_btn = QPushButton(tr('btn_restore'))
        btn_row.addWidget(restore_btn)

        close_btn = QPushButton(tr('btn_close'))
        close_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(close_btn)
        vlayout.addLayout(btn_row)

        def restore_action():
            selected = list_widget.currentItem()
            if not selected:
                return
            b_name = selected.text()
            b_path = self.paths['server_config_dir'] / b_name
            try:
                self.config_manager.restore_backup_file(b_path)
                QMessageBox.information(dialog, tr('backup_title'), tr('backup_restored'))
                self.load_settings()
                if hasattr(self, 'load_sandbox_settings'):
                    self.load_sandbox_settings()
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, tr('error'), f"Failed to restore: {e}")

        restore_btn.clicked.connect(restore_action)
        dialog.exec_()

    def send_quick_server_cmd(self, cmd: str):
        """Send a quick in-game admin console command."""
        if not self.server_process.is_running():
            QMessageBox.warning(
                self,
                tr('error'),
                "Сервер не запущен! Команды можно отправлять только на работающий сервер."
                if get_language() == 'ru' else
                "Server is not running! Commands can only be sent while the server is active."
            )
            return

        self.server_process.send_command(cmd)
        self.append_console_output(f"> [⚡ Quick Action]: {cmd}")

    def toggle_rain_action(self):
        """Toggle rain on or off on the server."""
        if not self.server_process.is_running():
            QMessageBox.warning(
                self,
                tr('error'),
                "Сервер не запущен!" if get_language() == 'ru' else "Server is not running!"
            )
            return

        self._is_raining = not getattr(self, '_is_raining', False)
        cmd = "startrain" if self._is_raining else "stoprain"
        self.server_process.send_command(cmd)
        status_text = ("Дождь включен (startrain)" if self._is_raining else "Дождь остановлен (stoprain)") if get_language() == 'ru' else ("Rain started (startrain)" if self._is_raining else "Rain stopped (stoprain)")
        self.append_console_output(f"> [🌧️ Weather]: {status_text}")

    def broadcast_message_action(self):
        """Send a global announcement message to all connected players."""
        if not self.server_process.is_running():
            QMessageBox.warning(
                self,
                tr('error'),
                "Сервер не запущен!" if get_language() == 'ru' else "Server is not running!"
            )
            return

        title = "Объявление на сервере" if get_language() == 'ru' else "Broadcast Server Message"
        label = "Введите сообщение для всех игроков (отобразится в чате):" if get_language() == 'ru' else "Enter announcement text for all players:"
        text, ok = QInputDialog.getText(self, title, label, QLineEdit.Normal)
        if ok and text.strip():
            clean_msg = text.strip().replace('"', "'")
            self.server_process.send_command(f'servermsg "{clean_msg}"')
            self.append_console_output(f'> [📢 Announcement]: servermsg "{clean_msg}"')

    def update_server_metrics(self):
        """Periodic status bar monitor for PC RAM and running PZ Server process RAM/CPU."""
        if not hasattr(self, 'server_metrics_lbl') or self.server_metrics_lbl is None:
            return

        sys_ram_text = ""
        if os.name == 'nt':
            try:
                import ctypes
                from ctypes import wintypes

                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', wintypes.DWORD),
                        ('dwMemoryLoad', wintypes.DWORD),
                        ('ullTotalPhys', ctypes.c_uint64),
                        ('ullAvailPhys', ctypes.c_uint64),
                        ('ullTotalPageFile', ctypes.c_uint64),
                        ('ullAvailPageFile', ctypes.c_uint64),
                        ('ullTotalVirtual', ctypes.c_uint64),
                        ('ullAvailVirtual', ctypes.c_uint64),
                        ('sullAvailExtendedVirtual', ctypes.c_uint64),
                    ]

                mem = MEMORYSTATUSEX()
                mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                    used_gb = (mem.ullTotalPhys - mem.ullAvailPhys) / (1024 ** 3)
                    total_gb = mem.ullTotalPhys / (1024 ** 3)
                    sys_ram_text = (
                        f"🖥️ ПК RAM: {used_gb:.1f}/{total_gb:.1f} ГБ ({mem.dwMemoryLoad}%)"
                        if get_language() == 'ru' else
                        f"🖥️ PC RAM: {used_gb:.1f}/{total_gb:.1f} GB ({mem.dwMemoryLoad}%)"
                    )
            except Exception:
                pass
        else:
            try:
                meminfo = {}
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        parts = line.split(':')
                        if len(parts) == 2:
                            meminfo[parts[0].strip()] = int(parts[1].split()[0])
                total_kb = meminfo.get('MemTotal', 0)
                avail_kb = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
                used_kb = total_kb - avail_kb
                if total_kb > 0:
                    pct = int(used_kb / total_kb * 100)
                    used_gb = used_kb / (1024 * 1024)
                    total_gb = total_kb / (1024 * 1024)
                    sys_ram_text = (
                        f"🖥️ ПК RAM: {used_gb:.1f}/{total_gb:.1f} ГБ ({pct}%)"
                        if get_language() == 'ru' else
                        f"🖥️ PC RAM: {used_gb:.1f}/{total_gb:.1f} GB ({pct}%)"
                    )
            except Exception:
                pass

        if self.server_process and self.server_process.is_running():
            srv_ram_mb = 0
            root_pid = self.server_process.get_pid()
            if root_pid and os.name == 'nt':
                try:
                    kernel32 = ctypes.windll.kernel32
                    psapi = ctypes.windll.psapi
                    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
                    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
                    kernel32.OpenProcess.restype = wintypes.HANDLE
                    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
                    kernel32.CloseHandle.restype = wintypes.BOOL
                    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

                    class PROCESSENTRY32(ctypes.Structure):
                        _fields_ = [
                            ('dwSize', wintypes.DWORD),
                            ('cntUsage', wintypes.DWORD),
                            ('th32ProcessID', wintypes.DWORD),
                            ('th32DefaultHeapID', ctypes.POINTER(wintypes.ULONG)),
                            ('th32ModuleID', wintypes.DWORD),
                            ('cntThreads', wintypes.DWORD),
                            ('th32ParentProcessID', wintypes.DWORD),
                            ('pcPriClassBase', wintypes.LONG),
                            ('dwFlags', wintypes.DWORD),
                            ('szExeFile', ctypes.c_char * 260)
                        ]

                    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
                        _fields_ = [
                            ('cb', wintypes.DWORD),
                            ('PageFaultCount', wintypes.DWORD),
                            ('PeakWorkingSetSize', ctypes.c_size_t),
                            ('WorkingSetSize', ctypes.c_size_t),
                            ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                            ('QuotaPagedPoolUsage', ctypes.c_size_t),
                            ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                            ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                            ('PagefileUsage', ctypes.c_size_t),
                            ('PeakPagefileUsage', ctypes.c_size_t),
                            ('PrivateUsage', ctypes.c_size_t),
                        ]

                    pids_to_check = {root_pid}
                    # Check cached java child pid if still alive to avoid repeated full snapshots
                    cached_child = getattr(self, '_cached_server_child_pid', None)
                    if cached_child:
                        test_handle = kernel32.OpenProcess(0x0400, False, cached_child)
                        if test_handle:
                            kernel32.CloseHandle(test_handle)
                            pids_to_check.add(cached_child)
                        else:
                            self._cached_server_child_pid = None

                    if len(pids_to_check) == 1:
                        hSnapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
                        if hSnapshot and hSnapshot != -1 and hSnapshot != wintypes.HANDLE(-1).value:
                            pe = PROCESSENTRY32()
                            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                            if kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
                                while True:
                                    if pe.th32ParentProcessID == root_pid:
                                        pids_to_check.add(pe.th32ProcessID)
                                        self._cached_server_child_pid = pe.th32ProcessID
                                    if not kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                                        break
                            kernel32.CloseHandle(hSnapshot)

                    for p in pids_to_check:
                        handle = kernel32.OpenProcess(0x0410, False, p)
                        if handle:
                            counters = PROCESS_MEMORY_COUNTERS_EX()
                            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
                            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                                srv_ram_mb += counters.WorkingSetSize // (1024 * 1024)
                            kernel32.CloseHandle(handle)
                except Exception as e:
                    logger.debug(f"Metrics collection exception: {e}")
            elif root_pid and os.name != 'nt':
                try:
                    with open(f'/proc/{root_pid}/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                srv_ram_mb = int(line.split()[1]) // 1024
                                break
                except Exception as e:
                    logger.debug(f"Linux process metrics exception: {e}")

            if srv_ram_mb > 1024:
                srv_ram_str = f"{srv_ram_mb / 1024:.2f} ГБ" if get_language() == 'ru' else f"{srv_ram_mb / 1024:.2f} GB"
            else:
                srv_ram_str = f"{srv_ram_mb} МБ" if get_language() == 'ru' else f"{srv_ram_mb} MB"

            server_lbl = f"🟢 Сервер: RAM {srv_ram_str}" if get_language() == 'ru' else f"🟢 Server: RAM {srv_ram_str}"
            full_status = f"{server_lbl}   |   {sys_ram_text}" if sys_ram_text else server_lbl
            self.server_metrics_lbl.setStyleSheet("color: #70ff70; font-weight: bold; padding-right: 12px;")
            self.server_metrics_lbl.setText(full_status)
        else:
            self.server_metrics_lbl.setStyleSheet("color: #b0b0b0; font-weight: normal; padding-right: 12px;")
            self.server_metrics_lbl.setText(sys_ram_text)

    @staticmethod
    def _mono_font() -> str:
        import platform
        from PyQt5.QtGui import QFontDatabase
        if 'JetBrains Mono' in QFontDatabase().families():
            return 'JetBrains Mono'
        system = platform.system()
        if system == 'Windows':
            return 'Consolas'
        elif system == 'Darwin':
            return 'Menlo'
        else:
            return 'DejaVu Sans Mono'
