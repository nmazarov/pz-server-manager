#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Tab Mixin for PZ Server Manager.
Handles server lifecycle, live console output, quick admin commands, and resource monitoring.
"""

import os
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QCheckBox, QComboBox, QPlainTextEdit, QGroupBox, QGridLayout, QMessageBox,
    QInputDialog, QSizePolicy, QDialog, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QFrame, QApplication, QToolTip, QMenu
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QCursor, QPainter, QRadialGradient, QBrush, QPen

from core.translations import tr, get_language
from core.server_process import check_ports_in_use
from core.config_manager import AppPreferences
from core.network_helper import NetworkHelper

START_BTN_STYLE = """
QPushButton#start_btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669);
    border: 1px solid #34d399;
    border-radius: 7px;
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 22px;
}
QPushButton#start_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34d399, stop:1 #10b981);
    border: 1px solid #6ee7b7;
}
QPushButton#start_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #047857, stop:1 #065f46);
    border: 1px solid #064e3b;
    padding-top: 11px;
    padding-bottom: 7px;
}
QPushButton#start_btn:disabled {
    background: #18231e;
    border: 1px solid #1f3227;
    color: #3e5246;
}
"""

STOP_BTN_STYLE = """
QPushButton#stop_btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #b91c1c);
    border: 1px solid #f87171;
    border-radius: 7px;
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 22px;
}
QPushButton#stop_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f87171, stop:1 #dc2626);
    border: 1px solid #fca5a5;
}
QPushButton#stop_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #991b1b, stop:1 #7f1d1d);
    border: 1px solid #450a0a;
    padding-top: 11px;
    padding-bottom: 7px;
}
QPushButton#stop_btn:disabled {
    background: #251b1b;
    border: 1px solid #332323;
    color: #553e3e;
}
"""

RESTART_BTN_STYLE = """
QPushButton#restart_btn {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #1d4ed8);
    border: 1px solid #60a5fa;
    border-radius: 7px;
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 22px;
}
QPushButton#restart_btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60a5fa, stop:1 #2563eb);
    border: 1px solid #93c5fd;
}
QPushButton#restart_btn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e40af, stop:1 #172554);
    border: 1px solid #0f172a;
    padding-top: 11px;
    padding-bottom: 7px;
}
QPushButton#restart_btn:disabled {
    background: #19202c;
    border: 1px solid #242c3c;
    color: #3f4c60;
}
"""



class PulseStatusIndicator(QWidget):
    """
    Tactical breathing glowing LED status indicator widget.
    States:
      - 'offline': deep crimson dot with calm subtle glow
      - 'launching': breathing warm amber glow pulsating 0.35s
      - 'running': breathing vibrant neon survival green aura
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self._state = "offline"
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def set_state(self, state: str):
        if state != self._state:
            self._state = state
            self._phase = 0.0
            self.update()

    def setText(self, text: str):
        # Compatibility with legacy setText calls
        if "🟢" in text:
            self.set_state("running")
        elif "🟡" in text or "🟠" in text or "⏳" in text:
            self.set_state("launching")
        else:
            self.set_state("offline")

    def _on_tick(self):
        import math
        self._phase += 0.09
        if self._phase > 2 * math.pi:
            self._phase -= 2 * math.pi
        self.update()

    def paintEvent(self, event):
        import math
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() / 2.0, self.height() / 2.0

        if self._state == "running":
            pulse = (math.sin(self._phase) + 1.0) / 2.0
            outer_radius = 8.5 + pulse * 3.0
            inner_radius = 5.5

            halo_grad = QRadialGradient(cx, cy, outer_radius)
            halo_grad.setColorAt(0.0, QColor(56, 239, 125, int(150 + pulse * 80)))
            halo_grad.setColorAt(0.65, QColor(16, 185, 129, int(50 + pulse * 40)))
            halo_grad.setColorAt(1.0, QColor(16, 185, 129, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(halo_grad))
            painter.drawEllipse(int(cx - outer_radius), int(cy - outer_radius), int(outer_radius * 2), int(outer_radius * 2))

            core_grad = QRadialGradient(cx - 1, cy - 1, inner_radius)
            core_grad.setColorAt(0.0, QColor(220, 255, 230))
            core_grad.setColorAt(0.6, QColor(64, 255, 64))
            core_grad.setColorAt(1.0, QColor(20, 150, 70))
            painter.setBrush(QBrush(core_grad))
            painter.drawEllipse(int(cx - inner_radius), int(cy - inner_radius), int(inner_radius * 2), int(inner_radius * 2))

        elif self._state == "launching":
            pulse = (math.sin(self._phase * 1.5) + 1.0) / 2.0
            outer_radius = 8.5 + pulse * 3.0
            inner_radius = 5.5

            halo_grad = QRadialGradient(cx, cy, outer_radius)
            halo_grad.setColorAt(0.0, QColor(245, 158, 11, int(160 + pulse * 80)))
            halo_grad.setColorAt(0.65, QColor(217, 119, 6, int(60 + pulse * 40)))
            halo_grad.setColorAt(1.0, QColor(217, 119, 6, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(halo_grad))
            painter.drawEllipse(int(cx - outer_radius), int(cy - outer_radius), int(outer_radius * 2), int(outer_radius * 2))

            core_grad = QRadialGradient(cx - 1, cy - 1, inner_radius)
            core_grad.setColorAt(0.0, QColor(254, 243, 199))
            core_grad.setColorAt(0.6, QColor(245, 158, 11))
            core_grad.setColorAt(1.0, QColor(180, 83, 9))
            painter.setBrush(QBrush(core_grad))
            painter.drawEllipse(int(cx - inner_radius), int(cy - inner_radius), int(inner_radius * 2), int(inner_radius * 2))

        else:
            inner_radius = 5.0
            # Subtle crimson halo
            halo_grad = QRadialGradient(cx, cy, 7.5)
            halo_grad.setColorAt(0.0, QColor(239, 68, 68, 80))
            halo_grad.setColorAt(1.0, QColor(239, 68, 68, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(halo_grad))
            painter.drawEllipse(int(cx - 7.5), int(cy - 7.5), 15, 15)

            # Core
            painter.setPen(QPen(QColor(130, 25, 25), 1))
            painter.setBrush(QBrush(QColor(220, 53, 69)))
            painter.drawEllipse(int(cx - inner_radius), int(cy - inner_radius), int(inner_radius * 2), int(inner_radius * 2))


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
        status_card.setObjectName("status_card")
        sc_layout = QHBoxLayout(status_card)
        sc_layout.setContentsMargins(14, 9, 14, 9)

        self.status_indicator = PulseStatusIndicator()
        sc_layout.addWidget(self.status_indicator)

        self.status_label = QLabel(tr('server_stopped'))
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6b6b;")
        sc_layout.addWidget(self.status_label)

        sc_layout.addStretch()

        self.status_detail_label = QLabel()
        self.status_detail_label.setStyleSheet(
            "font-size: 12px; color: #79c0ff; font-family: 'JetBrains Mono', monospace; "
            "padding: 5px 12px; background-color: #121822; border: 1px solid #23354b; "
            "border-radius: 6px; font-weight: 600;"
        )
        self.status_detail_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_detail_label.setCursor(Qt.PointingHandCursor)
        self.status_detail_label.mousePressEvent = self._on_ip_label_clicked
        sc_layout.addWidget(self.status_detail_label)

        self.update_connection_info('stopped')
        self._async_fetch_public_ip()

        layout.addWidget(status_card)

        # ── Group: Server Controls ─────────────────────────────────────
        controls_group = QGroupBox(tr('group_server_control'))
        cl = QVBoxLayout(controls_group)

        # Load persistent user preferences
        prefs = AppPreferences.load(self.paths)
        saved_server_name = prefs.get('last_server_name', 'servertest')
        try:
            saved_ram = int(prefs.get('last_ram_gb', 6))
        except Exception:
            saved_ram = 6
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
        ram_options = [4, 6, 8, 10, 12, 16, 20, 24, 32]
        if saved_ram not in ram_options:
            ram_options.append(saved_ram)
            ram_options.sort()
        default_ram_idx = 1
        for idx, gb in enumerate(ram_options):
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
        del_save_btn.setStyleSheet("background-color: #261616; border: 1px solid #4a2222; color: #f87171; border-radius: 5px; font-size: 11px; padding: 4px 10px;")
        del_save_btn.setCursor(Qt.PointingHandCursor)
        del_save_btn.setToolTip("Удаляет сохраненную карту этого мира, если возникла ошибка несовместимости версий карт (например, Build 42 в Build 41)" if get_language() == 'ru' else "Deletes the world save folder for this server if version mismatch occurs")
        del_save_btn.clicked.connect(self.delete_save_world_action)
        cl.addWidget(del_save_btn)

        chk_row = QHBoxLayout()
        self.auto_backup_checkbox = QCheckBox("📦 " + ("Авто-бэкап мира перед запуском" if get_language() == 'ru' else "Auto-backup world on launch"))
        self.auto_backup_checkbox.setChecked(saved_auto_backup)
        self.auto_backup_checkbox.toggled.connect(self._on_auto_backup_toggled)
        self.auto_backup_checkbox.setToolTip("Автоматически создавать резервную копию файлов сохранения мира перед каждым стартом" if get_language() == 'ru' else "Automatically backup world save before starting")
        chk_row.addWidget(self.auto_backup_checkbox)

        self.watchdog_checkbox = QCheckBox("🛡️ " + tr('chk_watchdog'))
        self.watchdog_checkbox.setChecked(prefs.get('watchdog_enabled', True))
        self.watchdog_checkbox.toggled.connect(self._on_watchdog_toggled)
        self.watchdog_checkbox.setToolTip(tr('watchdog_tooltip'))
        chk_row.addWidget(self.watchdog_checkbox)
        chk_row.addStretch()
        cl.addLayout(chk_row)

        layout.addWidget(controls_group)

        # ── Group: Console Output & Live Players Dashboard ─────────────
        console_group = QGroupBox(tr('group_console'))
        conl = QVBoxLayout(console_group)

        split_layout = QHBoxLayout()
        split_layout.setSpacing(12)

        left_vbox = QVBoxLayout()
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumBlockCount(3000)
        self.console_output.setFont(QFont(self._mono_font(), 9))
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        left_vbox.addWidget(self.console_output)

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
        left_vbox.addLayout(cmd_row)

        # ── Quick Actions Row ──────────────────────────────────────────
        quick_row = QHBoxLayout()
        quick_lbl = QLabel("⚡ " + ("Быстрые команды:" if get_language() == 'ru' else "Quick Actions:"))
        quick_lbl.setStyleSheet("font-weight: bold; color: #4ea8de; font-size: 12px;")
        quick_row.addWidget(quick_lbl)

        btn_save_world = QPushButton("💾 " + ("Сохранить" if get_language() == 'ru' else "Save"))
        btn_save_world.setObjectName("quick_btn")
        btn_save_world.setCursor(Qt.PointingHandCursor)
        btn_save_world.setToolTip("Отправить команду 'save' для немедленного сохранения мира" if get_language() == 'ru' else "Send 'save' command")
        btn_save_world.clicked.connect(lambda: self.send_quick_server_cmd("save"))
        quick_row.addWidget(btn_save_world)

        btn_rain = QPushButton("🌧️ " + ("Дождь" if get_language() == 'ru' else "Rain"))
        btn_rain.setObjectName("quick_btn")
        btn_rain.setCursor(Qt.PointingHandCursor)
        btn_rain.setToolTip("Вызвать или остановить дождь на сервере" if get_language() == 'ru' else "Start or stop rain")
        btn_rain.clicked.connect(self.toggle_rain_action)
        quick_row.addWidget(btn_rain)

        btn_heli = QPushButton("🚁 " + ("Вертолет" if get_language() == 'ru' else "Heli"))
        btn_heli.setObjectName("quick_btn")
        btn_heli.setCursor(Qt.PointingHandCursor)
        btn_heli.setToolTip("Запустить вертолетное событие над случайным игроком" if get_language() == 'ru' else "Trigger helicopter event")
        btn_heli.clicked.connect(lambda: self.send_quick_server_cmd("chopper"))
        quick_row.addWidget(btn_heli)

        btn_broadcast = QPushButton("📢 " + ("Объявление" if get_language() == 'ru' else "Broadcast"))
        btn_broadcast.setObjectName("quick_btn")
        btn_broadcast.setCursor(Qt.PointingHandCursor)
        btn_broadcast.setToolTip("Отправить глобальное системное сообщение всем игрокам в чат" if get_language() == 'ru' else "Send global server message to all players")
        btn_broadcast.clicked.connect(self.broadcast_message_action)
        quick_row.addWidget(btn_broadcast)

        quick_row.addStretch()
        left_vbox.addLayout(quick_row)
        split_layout.addLayout(left_vbox, 4)

        # ── Right Side: Live Player Dashboard Panel ────────────────────
        players_panel = QFrame()
        players_panel.setMinimumWidth(230)
        players_panel.setMaximumWidth(280)
        players_panel.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
            }
        """)
        pl_layout = QVBoxLayout(players_panel)
        pl_layout.setContentsMargins(10, 8, 10, 8)
        pl_layout.setSpacing(6)

        self.lbl_players_count = QLabel(tr('lbl_online_players', count=0))
        self.lbl_players_count.setStyleSheet("font-size: 13px; font-weight: bold; color: #40ff40; padding: 2px 0;")
        pl_layout.addWidget(self.lbl_players_count)

        self.players_list = QListWidget()
        self.players_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px 8px;
                border-radius: 3px;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: #2d2d30;
            }
            QListWidget::item:selected {
                background-color: #1e4b7a;
                color: #ffffff;
                font-weight: bold;
            }
        """)
        self.players_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.players_list.customContextMenuRequested.connect(self._show_player_context_menu)
        pl_layout.addWidget(self.players_list, 1)

        self._set_empty_players_placeholder()

        # Action palette buttons
        p_btns_row1 = QHBoxLayout()
        btn_kick = QPushButton(tr('btn_kick'))
        btn_kick.setStyleSheet("background-color: #6b3333; color: #ffcccc; font-size: 11px; padding: 4px;")
        btn_kick.clicked.connect(self.kick_selected_player)
        p_btns_row1.addWidget(btn_kick)

        btn_ban = QPushButton(tr('btn_ban'))
        btn_ban.setStyleSheet("background-color: #8b1111; color: #ffffff; font-size: 11px; font-weight: bold; padding: 4px;")
        btn_ban.clicked.connect(self.ban_selected_player)
        p_btns_row1.addWidget(btn_ban)
        pl_layout.addLayout(p_btns_row1)

        p_btns_row2 = QHBoxLayout()
        btn_tp = QPushButton(tr('btn_teleport'))
        btn_tp.setStyleSheet("background-color: #2b4b6f; color: #ffffff; font-size: 11px; padding: 4px;")
        btn_tp.clicked.connect(self.teleport_selected_player)
        p_btns_row2.addWidget(btn_tp)

        btn_admin = QPushButton(tr('btn_admin'))
        btn_admin.setStyleSheet("background-color: #5b4b1a; color: #ffeb99; font-size: 11px; padding: 4px;")
        btn_admin.clicked.connect(self.admin_selected_player)
        p_btns_row2.addWidget(btn_admin)
        pl_layout.addLayout(p_btns_row2)

        p_btns_row3 = QHBoxLayout()
        btn_wl = QPushButton(tr('btn_whitelist'))
        btn_wl.setStyleSheet("background-color: #1e5e3a; color: #ffffff; font-size: 11px; padding: 4px;")
        btn_wl.clicked.connect(self.whitelist_selected_player)
        p_btns_row3.addWidget(btn_wl)

        btn_ref = QPushButton(tr('btn_refresh_players'))
        btn_ref.setStyleSheet("background-color: #3a3a3c; color: #ffffff; font-size: 11px; padding: 4px;")
        btn_ref.clicked.connect(self.refresh_players_list)
        p_btns_row3.addWidget(btn_ref)
        pl_layout.addLayout(p_btns_row3)

        split_layout.addWidget(players_panel)
        conl.addLayout(split_layout)

        layout.addWidget(console_group)
        self.tabs.addTab(tab, tr('tab_server'))

    def _on_ram_changed(self, *args):
        if hasattr(self, 'server_ram_combo'):
            ram = self.server_ram_combo.currentData()
            if ram:
                AppPreferences.save(self.paths, {'last_ram_gb': int(ram)})

    def _on_auto_backup_toggled(self, checked: bool):
        AppPreferences.save(self.paths, {'auto_backup': bool(checked)})

    def _on_watchdog_toggled(self, checked: bool):
        if hasattr(self, 'watchdog'):
            self.watchdog.auto_restart_on_crash = bool(checked)
        AppPreferences.save(self.paths, {'watchdog_enabled': bool(checked)})

    def on_server_name_changed(self, text: str):
        name = text.strip() or 'servertest'
        AppPreferences.save(self.paths, {'last_server_name': name})
        if hasattr(self, 'config_manager'):
            self.config_manager.set_server_name(name)
        if hasattr(self, 'mod_manager'):
            self.mod_manager.set_server_name(name)
        if hasattr(self, 'backup_manager'):
            self.backup_manager.set_server_name(name)
        if hasattr(self, 'player_manager'):
            self.player_manager.set_server_name(name)

    def on_server_process_exited(self, exit_code: int):
        """Called when server process terminates; triggers watchdog auto-restart if unexpected."""
        name = self.server_name_input.text().strip() or 'servertest'
        if hasattr(self, 'watchdog') and hasattr(self, 'watchdog_checkbox') and self.watchdog_checkbox.isChecked():
            self.watchdog.on_server_process_ended(exit_code, name)

    # ── Live Player Dashboard Handlers ────────────────────────────

    def _set_empty_players_placeholder(self):
        if not hasattr(self, 'players_list'):
            return
        self.players_list.clear()
        it = QListWidgetItem("ℹ️ " + tr('no_players_online'))
        it.setFlags(it.flags() & ~Qt.ItemIsSelectable)
        it.setForeground(QColor("#777777"))
        self.players_list.addItem(it)

    def on_players_updated(self, players: list):
        """Update live players UI when player manager detects joins/leaves."""
        if hasattr(self, 'lbl_players_count'):
            self.lbl_players_count.setText(tr('lbl_online_players', count=len(players)))
        if not hasattr(self, 'players_list'):
            return

        self.players_list.clear()
        if not players:
            self._set_empty_players_placeholder()
            return

        for p in sorted(players):
            it = QListWidgetItem(f"👤 {p}")
            it.setData(Qt.UserRole, p)
            self.players_list.addItem(it)

    def _get_selected_player_name(self) -> Optional[str]:
        if not hasattr(self, 'players_list'):
            return None
        item = self.players_list.currentItem()
        if not item:
            return None
        data = item.data(Qt.UserRole)
        return str(data).strip() if data else None

    def _show_player_context_menu(self, pos):
        player = self._get_selected_player_name()
        if not player:
            return
        menu = QMenu(self)
        a_kick = menu.addAction(f"👢 {tr('btn_kick')} ({player})")
        a_kick.triggered.connect(self.kick_selected_player)

        a_ban = menu.addAction(f"🚫 {tr('btn_ban')} ({player})")
        a_ban.triggered.connect(self.ban_selected_player)

        a_tp = menu.addAction(f"🌀 {tr('btn_teleport')}...")
        a_tp.triggered.connect(self.teleport_selected_player)

        a_admin = menu.addAction(f"👑 {tr('btn_admin')}")
        a_admin.triggered.connect(self.admin_selected_player)

        a_wl = menu.addAction(f"📜 {tr('btn_whitelist')}")
        a_wl.triggered.connect(self.whitelist_selected_player)

        menu.exec_(self.players_list.mapToGlobal(pos))

    def kick_selected_player(self):
        player = self._get_selected_player_name()
        if not player:
            QMessageBox.information(self, tr('player_actions'), tr('no_players_online'))
            return
        reason, ok = QInputDialog.getText(self, tr('btn_kick'), f"{tr('kick_reason_prompt')} ({player}):", text="Kicked by Administrator")
        if ok:
            reason = reason.strip() or "Kicked by Administrator"
            cmd = self.player_manager.cmd_kick(player, reason) if hasattr(self, 'player_manager') else f'kickuser "{player}" -r "{reason}"'
            self.send_quick_server_cmd(cmd)
            self.append_console_output(f"👢 {tr('player_kicked_success', player=player)}")

    def ban_selected_player(self):
        player = self._get_selected_player_name()
        if not player:
            QMessageBox.information(self, tr('player_actions'), tr('no_players_online'))
            return
        res = QMessageBox.warning(
            self,
            tr('btn_ban'),
            f"Are you sure you want to ban player '{player}'?" if get_language() == 'en' else f"Вы уверены, что хотите забанить игрока '{player}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            reason, ok = QInputDialog.getText(self, tr('btn_ban'), f"{tr('ban_reason_prompt')} ({player}):", text="Banned by Administrator")
            if ok:
                reason = reason.strip() or "Banned by Administrator"
                cmd = self.player_manager.cmd_ban(player, reason) if hasattr(self, 'player_manager') else f'banuser "{player}" -r "{reason}"'
                self.send_quick_server_cmd(cmd)
                self.append_console_output(f"🚫 {tr('player_banned_success', player=player)}")

    def teleport_selected_player(self):
        player = self._get_selected_player_name()
        if not player:
            QMessageBox.information(self, tr('player_actions'), tr('no_players_online'))
            return
        all_players = self.player_manager.get_online_players() if hasattr(self, 'player_manager') else []
        candidates = [p for p in all_players if p != player]
        if not candidates:
            target, ok = QInputDialog.getText(self, tr('btn_teleport'), tr('teleport_target_prompt', player=player))
        else:
            target, ok = QInputDialog.getItem(self, tr('btn_teleport'), tr('teleport_target_prompt', player=player), candidates, 0, False)
        if ok and target.strip():
            cmd = self.player_manager.cmd_teleport(player, target.strip()) if hasattr(self, 'player_manager') else f'teleport "{player}" "{target.strip()}"'
            self.send_quick_server_cmd(cmd)
            self.append_console_output(f"🌀 Teleported {player} to {target.strip()}")

    def admin_selected_player(self):
        player = self._get_selected_player_name()
        if not player:
            QMessageBox.information(self, tr('player_actions'), tr('no_players_online'))
            return
        res = QMessageBox.question(
            self,
            tr('btn_admin'),
            f"Grant Administrator permissions to '{player}'?" if get_language() == 'en' else f"Предоставить права Администратора игроку '{player}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            cmd = self.player_manager.cmd_set_access(player, 'admin') if hasattr(self, 'player_manager') else f'setaccesslevel "{player}" "admin"'
            self.send_quick_server_cmd(cmd)
            self.append_console_output(f"👑 {tr('player_admin_success', player=player)}")

    def whitelist_selected_player(self):
        player = self._get_selected_player_name()
        if not player:
            QMessageBox.information(self, tr('player_actions'), tr('no_players_online'))
            return
        if hasattr(self, 'player_manager'):
            self.player_manager.add_to_whitelist(player)
        self.send_quick_server_cmd(f'addusertowhitelist "{player}"')
        QMessageBox.information(self, tr('btn_whitelist'), tr('player_whitelist_success', player=player))
        self.append_console_output(f"📜 {tr('player_whitelist_success', player=player)}")

    def refresh_players_list(self):
        self.send_quick_server_cmd("players")
        self.append_console_output("🔄 Sent 'players' query to server console...")

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
                from core.backup_manager import BackupManager
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

        if hasattr(self, 'watchdog'):
            self.watchdog.on_server_starting()

        self.on_server_launching()
        self.append_console_output(f"🟡 {tr('starting_server')} '{name}' (RAM: {ram_gb} GB)...")
        try:
            self.server_process.start(name, ram_gb=ram_gb)
        except Exception as e:
            self.append_console_error(f"Failed to start: {e}")
            self.on_server_stopped()

    def stop_server(self):
        name = self.server_name_input.text().strip() or 'servertest'
        if hasattr(self, 'watchdog'):
            self.watchdog.on_server_manual_stop(name)
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
            if hasattr(self.status_indicator, 'set_state'):
                self.status_indicator.set_state("launching")
            else:
                self.status_indicator.setText("🟡")
        if hasattr(self, 'status_label'):
            self.status_label.setText(tr('server_launching'))
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f59e0b;")
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
            if hasattr(self.status_indicator, 'set_state'):
                self.status_indicator.set_state("running")
            else:
                self.status_indicator.setText("🟢")
        if hasattr(self, 'status_label'):
            self.status_label.setText(tr('server_ready'))
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #38ef7d;")
        self._server_is_ready = True
        self.update_connection_info('ready')

        # Sound Alert (Windows chime or beep)
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            try:
                QApplication.beep()
            except Exception:
                pass

        # Tray alert balloon
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(tr('app_title'), tr('tray_server_ready'), QSystemTrayIcon.Information, 5000)

        # Prominent highlight banner in server console
        is_ru = get_language() == 'ru'
        title_banner = "🎉 СЕРВЕР УСПЕШНО ЗАПУЩЕН И ГОТОВ К ИГРЕ!" if is_ru else "🎉 SERVER IS ONLINE AND READY TO PLAY!"
        port = self.get_server_port()
        pub_ip = getattr(self, '_cached_public_ip', None) or NetworkHelper.get_public_ip(timeout=1.0) or ("ваш_внешний_IP" if is_ru else "your_external_IP")
        loc_ip = getattr(self, '_cached_local_ip', None) or NetworkHelper.get_local_ip()

        if is_ru:
            port_banner = (
                f"👉 Подключение для друзей (через интернет): {pub_ip}:{port}\n"
                f"👉 Подключение в локальной сети (LAN):       {loc_ip}:{port}"
            )
        else:
            port_banner = (
                f"👉 Connect address for friends (Internet): {pub_ip}:{port}\n"
                f"👉 Connect address in Local Network (LAN):  {loc_ip}:{port}"
            )
        ready_banner = (
            f"\n{'=' * 68}\n"
            f"{title_banner}\n"
            f"{port_banner}\n"
            f"{'=' * 68}"
        )
        self.append_console_output(ready_banner)
        name = self.server_name_input.text().strip() or 'servertest'
        if hasattr(self, 'watchdog'):
            self.watchdog.on_server_started_ok(name, str(pub_ip), str(port))

    def on_server_stopped(self):
        """Called when server process is terminated."""
        self._server_is_ready = False
        if hasattr(self, 'player_manager'):
            self.player_manager.clear_online_players()
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
            if hasattr(self.status_indicator, 'set_state'):
                self.status_indicator.set_state("offline")
            else:
                self.status_indicator.setText("🔴")
        if hasattr(self, 'status_label'):
            self.status_label.setText(tr('server_stopped'))
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff6b6b;")
        self.update_connection_info('stopped')
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(tr('app_title'), tr('tray_server_stopped'), QSystemTrayIcon.Information, 3000)

    def get_server_port(self) -> int:
        """Get the configured server UDP game port (default 16261)."""
        if hasattr(self, 'setting_port') and self.setting_port is not None:
            try:
                return self.setting_port.value()
            except Exception:
                pass
        return 16261

    def _on_ip_label_clicked(self, event):
        """Clicking the IP badge copies external join address to clipboard."""
        try:
            pub = getattr(self, '_cached_public_ip', None)
            port = self.get_server_port()
            if pub:
                conn_str = f"{pub}:{port}"
                QApplication.clipboard().setText(conn_str)
                is_ru = (get_language() == 'ru')
                msg = f"Скопировано: {conn_str}" if is_ru else f"Copied: {conn_str}"
                QToolTip.showText(QCursor.pos(), msg, self.status_detail_label, msecDisplayTime=2000)
        except Exception:
            pass

    def update_connection_info(self, status: str = 'stopped'):
        """Update connection info with External IP (for friends) and Local IP (non-127)."""
        if not hasattr(self, 'status_detail_label') or self.status_detail_label is None:
            return

        port = self.get_server_port()
        if not hasattr(self, '_cached_local_ip') or not self._cached_local_ip or self._cached_local_ip.startswith("127."):
            self._cached_local_ip = NetworkHelper.get_local_ip()

        pub_ip = getattr(self, '_cached_public_ip', None)
        loc_ip = self._cached_local_ip

        is_ru = (get_language() == 'ru')
        pub_str = f"{pub_ip}:{port}" if pub_ip else ("Определение..." if is_ru else "Resolving...")
        loc_str = f"{loc_ip}:{port}"

        if status == 'ready':
            if is_ru:
                text = f"🌐 Внешний IP: {pub_str}   |   🏠 Локальный IP: {loc_str}"
            else:
                text = f"🌐 Public IP: {pub_str}   |   🏠 Local IP: {loc_str}"
            self.status_detail_label.setStyleSheet(
                "font-size: 13px; color: #70f3a8; font-family: 'Segoe UI', monospace; "
                "padding: 4px 10px; background-color: #123020; border: 1px solid #1e6b3b; border-radius: 4px; font-weight: bold;"
            )
        else:
            if is_ru:
                text = f"🌐 Внешний IP: {pub_str}   |   🏠 Локальный IP: {loc_str}"
            else:
                text = f"🌐 Public IP: {pub_str}   |   🏠 Local IP: {loc_str}"
            self.status_detail_label.setStyleSheet(
                "font-size: 13px; color: #a8c7fa; font-family: 'Segoe UI', monospace; "
                "padding: 4px 10px; background-color: #1b2636; border: 1px solid #2d4263; border-radius: 4px; font-weight: 500;"
            )

        self.status_detail_label.setText(text)
        tip = (
            f"Внешний IP (для друзей через интернет): {pub_str}\n"
            f"Локальный IP (для домашней сети LAN): {loc_str}\n\n"
            f"Нажмите, чтобы скопировать внешний адрес подключения"
            if is_ru else
            f"Public IP (for friends over Internet): {pub_str}\n"
            f"Local IP (for LAN): {loc_str}\n\n"
            f"Click to copy external join address"
        )
        self.status_detail_label.setToolTip(tip)

    def _async_fetch_public_ip(self):
        """Fetch Public IP in background thread so startup remains instantaneous."""
        def worker():
            try:
                ip = NetworkHelper.get_public_ip(timeout=3.0)
                if ip:
                    self._cached_public_ip = ip
                    QTimer.singleShot(0, lambda: self.update_connection_info(
                        'ready' if getattr(self, '_server_is_ready', False) else 'stopped'
                    ))
            except Exception as e:
                logger.debug(f"Public IP background lookup error: {e}")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

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
