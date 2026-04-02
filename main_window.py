#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window for PZ Server Manager
Contains the main GUI with tabs for server control, settings, sandbox and mods.
"""

import os
import sys
import logging
import platform
import subprocess
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QTextEdit, QPlainTextEdit, QListWidget, QListWidgetItem, QProgressBar,
    QGroupBox, QFormLayout, QGridLayout, QFileDialog, QMessageBox,
    QInputDialog, QScrollArea, QFrame, QSplitter, QStatusBar, QMenuBar,
    QMenu, QAction,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QIcon

from server_installer import ServerInstaller, InstallWorker
from server_process import ServerProcess
from config_manager import ConfigManager
from mod_manager import ModManager
from translations import tr, set_language, get_language

logger = logging.getLogger(__name__)

# ── Sandbox value mappings (UI index → PZ numeric value) ────────────

_ZOMBIE_SPEED        = [('sprinters',1),('fast_shamblers',2),('shamblers',3),('random',4)]
_ZOMBIE_STRENGTH     = [('superhuman',1),('normal',2),('weak',3),('random',4)]
_ZOMBIE_TOUGHNESS    = [('tough',1),('normal',2),('fragile',3),('random',4)]
_ZOMBIE_TRANSMISSION = [('blood_saliva',1),('saliva_only',2),('everyone_infected',3),('none',4)]
_ZOMBIE_COGNITION    = [('navigate_doors',1),('navigate',2),('basic_navigation',3),('random',4)]
_ZOMBIE_MEMORY       = [('long',1),('normal',2),('short',3),('none',4)]
_ZOMBIE_DECOMP       = [('slow',1),('normal',2),('fast',3),('disabled',4)]
_ZOMBIE_HEARING      = [('very_high',1),('normal',2),('low',3)]
_ZOMBIE_SIGHT        = [('eagle',1),('normal',2),('poor',3)]
_ZOMBIE_SMELL        = [('normal',1),('poor',2),('none',3)]

# PopulationMultiplier: index 0..6 maps to these floats
_POP_MULTIPLIERS = [
    ('none', 0.0), ('very_low', 0.35), ('low', 0.5),
    ('normal', 1.0), ('high', 1.5), ('very_high', 2.0), ('insane', 4.0),
]

_ZOMBIE_DISTRIBUTION = [('urban_focused',1),('uniform',2),('random',3)]

_LOOT_RARITY  = [('extremely_rare',1),('rare',2),('normal',3),('common',4),('abundant',5)]
_LOOT_RESPAWN = [('never',0),('every_day',12),('every_week',168),
                 ('every_month',720),('every_2_months',1440)]

_DAY_LENGTH   = [
    ('15 min',1),('30 min',2),('1 h',3),('2 h',4),('3 h',5),
    ('4 h',6),('5 h',7),('6 h',8),('12 h',9),('Real-time',10),
]
_NIGHT_DARK   = [('pitch_black',1),('dark',2),('normal',3),('bright',4)]
_NATURE_ABU   = [('very_abundant',1),('abundant',2),('normal',3),('scarce',4),('very_scarce',5)]
_TIME_APO     = [('months_0_3',1),('months_3_6',2),('months_6_12',3),
                 ('several_years',4),('many_years',5)]

_CAR_SPAWN    = [('very_low',1),('low',2),('normal',3),('high',4),('very_high',5)]
_FARMING_SPD  = [('very_fast',1),('fast',2),('normal',3),('slow',4),('very_slow',5)]
_GENERATOR_SP = [('very_low',1),('low',2),('normal',3),('high',4),('very_high',5)]
_GENERATOR_FU = [('very_low',1),('low',2),('normal',3),('high',4),('very_high',5)]

_INFECTION    = [
    ('instant',1),('0_30_sec',2),('0_1_min',3),('0_12_hours',4),
    ('1_2_days',5),('2_3_days',6),('1_week',7),('never',8),
]
_XP_MULT      = [
    ('0.5x',0.5),('0.75x',0.75),('1x',1.0),('1.5x',1.5),
    ('2x',2.0),('3x',3.0),('5x',5.0),('10x',10.0),
]
_PLAYER_DMG   = [('very_low',1),('low',2),('normal',3),('high',4),('very_high',5)]
_DROP_DEATH   = [('drop_nothing',0),('drop_all',1),('drop_equipped',2),('drop_backpack',3)]


def _combo_items(mapping):
    """Return list of tr()-translated display strings from a mapping list."""
    return [tr(k) for k, _ in mapping]


def _combo_index(mapping, pz_value, default=0):
    """Return the combo index matching pz_value (2nd element of each tuple)."""
    for i, (_, v) in enumerate(mapping):
        if v == pz_value:
            return i
    return default


def _combo_value(mapping, index, default=None):
    """Return the pz_value at given combo index."""
    if 0 <= index < len(mapping):
        return mapping[index][1]
    return default


# ════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, paths: dict, server_installed: bool):
        super().__init__()
        self.paths = paths
        self.server_installed = server_installed

        self.config_manager = ConfigManager(paths)
        self.server_process = ServerProcess(paths)
        self.mod_manager    = ModManager(paths)
        self.installer      = ServerInstaller(paths)

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

    # ── UI init ─────────────────────────────────────────────────────

    def init_ui(self):
        self.setWindowTitle(tr('app_title'))
        self.setMinimumSize(950, 720)
        self.resize(1050, 780)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.create_server_tab()
        self.create_settings_tab()
        self.create_sandbox_tab()
        self.create_mods_tab()
        self.create_install_tab()

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.update_status()

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
            ('menu_validate',    self.validate_server),
            ('menu_update',      self.update_server),
            (None,               None),
            ('menu_open_config', self.open_config_folder),
            ('menu_open_server', self.open_server_folder),
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

    # ── Tab: Server Control ─────────────────────────────────────────

    def create_server_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        status_group = QGroupBox(tr('server_status'))
        sl = QHBoxLayout(status_group)
        self.status_indicator = QLabel('●')
        self.status_indicator.setStyleSheet('color:#ff4444;font-size:24px;')
        sl.addWidget(self.status_indicator)
        self.status_label = QLabel(tr('server_stopped'))
        self.status_label.setStyleSheet('font-size:16px;font-weight:bold;')
        sl.addWidget(self.status_label)
        sl.addStretch()
        sl.addWidget(QLabel(tr('server_name')))
        self.server_name_input = QLineEdit('servertest')
        self.server_name_input.setMaximumWidth(150)
        self.server_name_input.setToolTip(tr('server_name_tooltip'))
        sl.addWidget(self.server_name_input)
        layout.addWidget(status_group)

        controls_group = QGroupBox(tr('controls'))
        cl = QHBoxLayout(controls_group)
        self.start_btn = QPushButton(tr('btn_start'))
        self.start_btn.setObjectName('startBtn')
        self.start_btn.setMinimumHeight(50)
        self.start_btn.clicked.connect(self.start_server)
        cl.addWidget(self.start_btn)
        self.stop_btn = QPushButton(tr('btn_stop'))
        self.stop_btn.setObjectName('stopBtn')
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_server)
        cl.addWidget(self.stop_btn)
        self.restart_btn = QPushButton(tr('btn_restart'))
        self.restart_btn.setMinimumHeight(50)
        self.restart_btn.setEnabled(False)
        self.restart_btn.clicked.connect(self.restart_server)
        cl.addWidget(self.restart_btn)
        layout.addWidget(controls_group)

        console_group = QGroupBox(tr('server_console'))
        conl = QVBoxLayout(console_group)
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumBlockCount(5000)
        self.console_output.setFont(QFont(self._mono_font(), 9))
        conl.addWidget(self.console_output)
        row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText(tr('command_placeholder'))
        self.command_input.returnPressed.connect(self.send_command)
        row.addWidget(self.command_input)
        btn = QPushButton(tr('btn_send'))
        btn.clicked.connect(self.send_command)
        row.addWidget(btn)
        btn2 = QPushButton(tr('btn_clear'))
        btn2.clicked.connect(self.console_output.clear)
        row.addWidget(btn2)
        conl.addLayout(row)
        layout.addWidget(console_group)

        self.tabs.addTab(tab, tr('tab_server'))

    # ── Tab: Server Settings ────────────────────────────────────────

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)

        # ── Basic ──
        g = QGroupBox(tr('group_basic'))
        f = QFormLayout(g)

        self.setting_public_name = QLineEdit()
        self.setting_public_name.setPlaceholderText('My Zomboid Server')
        f.addRow(tr('lbl_server_name'), self.setting_public_name)

        self.setting_public_desc = QLineEdit()
        self.setting_public_desc.setPlaceholderText('A Project Zomboid server')
        f.addRow(tr('lbl_description'), self.setting_public_desc)

        self.setting_password = QLineEdit()
        self.setting_password.setEchoMode(QLineEdit.Password)
        self.setting_password.setPlaceholderText(tr('ph_empty_no_password'))
        f.addRow(tr('lbl_password'), self.setting_password)

        self.setting_max_players = QSpinBox()
        self.setting_max_players.setRange(1, 100)
        self.setting_max_players.setValue(16)
        f.addRow(tr('lbl_max_players'), self.setting_max_players)

        self.setting_map = QLineEdit('Muldraugh, KY')
        self.setting_map.setPlaceholderText(tr('ph_map'))
        f.addRow(tr('lbl_map'), self.setting_map)

        self.setting_welcome_msg = QLineEdit()
        self.setting_welcome_msg.setPlaceholderText(tr('ph_welcome_msg'))
        f.addRow(tr('lbl_welcome_msg'), self.setting_welcome_msg)

        sl.addWidget(g)

        # ── Network ──
        g = QGroupBox(tr('group_network'))
        f = QFormLayout(g)

        self.setting_port = QSpinBox()
        self.setting_port.setRange(1024, 65535)
        self.setting_port.setValue(16261)
        f.addRow(tr('lbl_game_port'), self.setting_port)

        self.setting_udp_port = QSpinBox()
        self.setting_udp_port.setRange(1024, 65535)
        self.setting_udp_port.setValue(16262)
        f.addRow(tr('lbl_direct_port'), self.setting_udp_port)

        self.setting_steam_port = QSpinBox()
        self.setting_steam_port.setRange(1024, 65535)
        self.setting_steam_port.setValue(8766)
        f.addRow(tr('lbl_steam_port1'), self.setting_steam_port)

        self.setting_steam_port2 = QSpinBox()
        self.setting_steam_port2.setRange(1024, 65535)
        self.setting_steam_port2.setValue(8767)
        f.addRow(tr('lbl_steam_port2'), self.setting_steam_port2)

        self.setting_rcon_port = QSpinBox()
        self.setting_rcon_port.setRange(1024, 65535)
        self.setting_rcon_port.setValue(27015)
        f.addRow(tr('lbl_rcon_port'), self.setting_rcon_port)

        self.setting_rcon_password = QLineEdit()
        self.setting_rcon_password.setPlaceholderText('RCON password')
        f.addRow(tr('lbl_rcon_password'), self.setting_rcon_password)

        self.setting_public = QCheckBox(tr('chk_public'))
        self.setting_public.setChecked(True)
        f.addRow('', self.setting_public)

        sl.addWidget(g)

        # ── Gameplay ──
        g = QGroupBox(tr('group_gameplay'))
        f = QFormLayout(g)

        self.setting_pvp = QCheckBox(tr('chk_pvp'))
        self.setting_pvp.setChecked(True)
        f.addRow('', self.setting_pvp)

        self.setting_pause_empty = QCheckBox(tr('chk_pause_empty'))
        self.setting_pause_empty.setChecked(True)
        f.addRow('', self.setting_pause_empty)

        self.setting_allow_coop = QCheckBox(tr('chk_allow_coop'))
        self.setting_allow_coop.setChecked(True)
        f.addRow('', self.setting_allow_coop)

        self.setting_sleep_allowed = QCheckBox(tr('chk_sleep_allowed'))
        self.setting_sleep_allowed.setChecked(False)
        f.addRow('', self.setting_sleep_allowed)

        self.setting_sleep_needed = QCheckBox(tr('chk_sleep_needed'))
        self.setting_sleep_needed.setChecked(False)
        f.addRow('', self.setting_sleep_needed)

        self.setting_announce_death = QCheckBox(tr('chk_announce_death'))
        self.setting_announce_death.setChecked(False)
        f.addRow('', self.setting_announce_death)

        self.setting_no_fire = QCheckBox(tr('chk_no_fire'))
        self.setting_no_fire.setChecked(False)
        f.addRow('', self.setting_no_fire)

        self.setting_allow_destruction = QCheckBox(tr('chk_allow_destruction'))
        self.setting_allow_destruction.setChecked(True)
        f.addRow('', self.setting_allow_destruction)

        self.setting_drop_on_death = QComboBox()
        self.setting_drop_on_death.addItems(_combo_items(_DROP_DEATH))
        self.setting_drop_on_death.setCurrentIndex(1)  # drop_all
        f.addRow(tr('lbl_drop_on_death'), self.setting_drop_on_death)

        self.setting_spawn_point = QLineEdit()
        self.setting_spawn_point.setPlaceholderText('0,0,0')
        f.addRow(tr('lbl_spawn_point'), self.setting_spawn_point)

        sl.addWidget(g)

        # ── Safehouses ──
        g = QGroupBox(tr('group_safehouse'))
        f = QFormLayout(g)

        self.setting_player_safehouse = QCheckBox(tr('chk_player_safehouse'))
        f.addRow('', self.setting_player_safehouse)
        self.setting_admin_safehouse = QCheckBox(tr('chk_admin_safehouse'))
        f.addRow('', self.setting_admin_safehouse)
        self.setting_safehouse_trespassing = QCheckBox(tr('chk_safehouse_trespassing'))
        f.addRow('', self.setting_safehouse_trespassing)
        self.setting_safehouse_fire = QCheckBox(tr('chk_safehouse_fire'))
        f.addRow('', self.setting_safehouse_fire)
        self.setting_safehouse_loot = QCheckBox(tr('chk_safehouse_loot'))
        f.addRow('', self.setting_safehouse_loot)
        self.setting_safehouse_respawn = QCheckBox(tr('chk_safehouse_respawn'))
        f.addRow('', self.setting_safehouse_respawn)

        sl.addWidget(g)

        # ── Chat & Voice ──
        g = QGroupBox(tr('group_chat_voice'))
        f = QFormLayout(g)

        self.setting_global_chat = QCheckBox(tr('chk_global_chat'))
        self.setting_global_chat.setChecked(True)
        f.addRow('', self.setting_global_chat)

        self.setting_safety_system = QCheckBox(tr('chk_safety_system'))
        self.setting_safety_system.setChecked(True)
        f.addRow('', self.setting_safety_system)

        self.setting_show_safety = QCheckBox(tr('chk_show_safety'))
        self.setting_show_safety.setChecked(True)
        f.addRow('', self.setting_show_safety)

        self.setting_display_username = QCheckBox(tr('chk_display_username'))
        self.setting_display_username.setChecked(True)
        f.addRow('', self.setting_display_username)

        self.setting_voice_enable = QCheckBox(tr('chk_voice_enable'))
        self.setting_voice_enable.setChecked(True)
        f.addRow('', self.setting_voice_enable)

        self.setting_voice_3d = QCheckBox(tr('chk_voice_3d'))
        self.setting_voice_3d.setChecked(True)
        f.addRow('', self.setting_voice_3d)

        self.setting_voice_min = QSpinBox()
        self.setting_voice_min.setRange(1, 500)
        self.setting_voice_min.setValue(10)
        f.addRow(tr('lbl_voice_min'), self.setting_voice_min)

        self.setting_voice_max = QSpinBox()
        self.setting_voice_max.setRange(10, 10000)
        self.setting_voice_max.setValue(100)
        f.addRow(tr('lbl_voice_max'), self.setting_voice_max)

        sl.addWidget(g)

        # ── Security ──
        g = QGroupBox(tr('group_security'))
        f = QFormLayout(g)

        self.setting_secure_join = QCheckBox(tr('chk_secure_join'))
        f.addRow('', self.setting_secure_join)

        self.setting_non_ascii = QCheckBox(tr('chk_non_ascii'))
        f.addRow('', self.setting_non_ascii)

        self.setting_auto_whitelist = QCheckBox(tr('chk_auto_whitelist'))
        f.addRow('', self.setting_auto_whitelist)

        self.setting_max_accounts = QSpinBox()
        self.setting_max_accounts.setRange(0, 100)
        self.setting_max_accounts.setValue(0)
        self.setting_max_accounts.setSpecialValueText(tr('unlimited'))
        f.addRow(tr('lbl_max_accounts'), self.setting_max_accounts)

        self.setting_speed_limit = QSpinBox()
        self.setting_speed_limit.setRange(0, 250)
        self.setting_speed_limit.setValue(70)
        self.setting_speed_limit.setSuffix(' km/h')
        f.addRow(tr('lbl_speed_limit'), self.setting_speed_limit)

        sl.addWidget(g)

        # ── Admin ──
        g = QGroupBox(tr('group_admin'))
        f = QFormLayout(g)

        self.setting_admin_password = QLineEdit()
        self.setting_admin_password.setEchoMode(QLineEdit.Password)
        f.addRow(tr('lbl_admin_password'), self.setting_admin_password)

        self.setting_auto_save = QSpinBox()
        self.setting_auto_save.setRange(1, 60)
        self.setting_auto_save.setValue(15)
        self.setting_auto_save.setSuffix(' min')
        f.addRow(tr('lbl_auto_save'), self.setting_auto_save)

        self.setting_backups_count = QSpinBox()
        self.setting_backups_count.setRange(0, 50)
        self.setting_backups_count.setValue(5)
        f.addRow(tr('lbl_backups_count'), self.setting_backups_count)

        self.setting_backups_period = QSpinBox()
        self.setting_backups_period.setRange(0, 720)
        self.setting_backups_period.setValue(0)
        self.setting_backups_period.setSpecialValueText('On start')
        self.setting_backups_period.setSuffix(' h')
        f.addRow(tr('lbl_backups_period'), self.setting_backups_period)

        sl.addWidget(g)

        sl.addStretch()
        scroll.setWidget(sw)
        layout.addWidget(scroll)

        row = QHBoxLayout()
        b = QPushButton(tr('btn_save_settings'))
        b.clicked.connect(self.save_settings)
        row.addWidget(b)
        b2 = QPushButton(tr('btn_reload_settings'))
        b2.clicked.connect(self.load_settings)
        row.addWidget(b2)
        layout.addLayout(row)

        self.tabs.addTab(tab, tr('tab_settings'))

    # ── Tab: Sandbox ────────────────────────────────────────────────

    def create_sandbox_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel(tr('lbl_preset')))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['Custom', 'Apocalypse', 'Survivor', 'Builder', 'Sandbox'])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_row.addWidget(self.preset_combo)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)

        # ── Zombies ──
        g = QGroupBox(tr('group_zombie'))
        f = QFormLayout(g)

        self.sandbox_zombie_count = QComboBox()
        self.sandbox_zombie_count.addItems(_combo_items(_POP_MULTIPLIERS))
        self.sandbox_zombie_count.setCurrentIndex(3)  # normal
        f.addRow(tr('lbl_zombie_count'), self.sandbox_zombie_count)

        self.sandbox_zombie_distribution = QComboBox()
        self.sandbox_zombie_distribution.addItems(_combo_items(_ZOMBIE_DISTRIBUTION))
        f.addRow(tr('lbl_distribution'), self.sandbox_zombie_distribution)

        self.sandbox_zombie_speed = QComboBox()
        self.sandbox_zombie_speed.addItems(_combo_items(_ZOMBIE_SPEED))
        self.sandbox_zombie_speed.setCurrentIndex(2)  # shamblers
        f.addRow(tr('lbl_speed'), self.sandbox_zombie_speed)

        self.sandbox_zombie_strength = QComboBox()
        self.sandbox_zombie_strength.addItems(_combo_items(_ZOMBIE_STRENGTH))
        self.sandbox_zombie_strength.setCurrentIndex(1)  # normal
        f.addRow(tr('lbl_strength'), self.sandbox_zombie_strength)

        self.sandbox_zombie_toughness = QComboBox()
        self.sandbox_zombie_toughness.addItems(_combo_items(_ZOMBIE_TOUGHNESS))
        self.sandbox_zombie_toughness.setCurrentIndex(1)
        f.addRow(tr('lbl_toughness'), self.sandbox_zombie_toughness)

        self.sandbox_zombie_transmission = QComboBox()
        self.sandbox_zombie_transmission.addItems(_combo_items(_ZOMBIE_TRANSMISSION))
        f.addRow(tr('lbl_transmission'), self.sandbox_zombie_transmission)

        self.sandbox_zombie_cognition = QComboBox()
        self.sandbox_zombie_cognition.addItems(_combo_items(_ZOMBIE_COGNITION))
        self.sandbox_zombie_cognition.setCurrentIndex(2)  # basic
        f.addRow(tr('lbl_cognition'), self.sandbox_zombie_cognition)

        sl.addWidget(g)

        # ── Zombie Lore ──
        g = QGroupBox(tr('group_zombie_lore'))
        f = QFormLayout(g)

        self.sandbox_memory = QComboBox()
        self.sandbox_memory.addItems(_combo_items(_ZOMBIE_MEMORY))
        self.sandbox_memory.setCurrentIndex(1)
        f.addRow(tr('lbl_memory'), self.sandbox_memory)

        self.sandbox_decomp = QComboBox()
        self.sandbox_decomp.addItems(_combo_items(_ZOMBIE_DECOMP))
        f.addRow(tr('lbl_decomp'), self.sandbox_decomp)

        self.sandbox_hearing = QComboBox()
        self.sandbox_hearing.addItems(_combo_items(_ZOMBIE_HEARING))
        self.sandbox_hearing.setCurrentIndex(1)
        f.addRow(tr('lbl_hearing'), self.sandbox_hearing)

        self.sandbox_sight = QComboBox()
        self.sandbox_sight.addItems(_combo_items(_ZOMBIE_SIGHT))
        self.sandbox_sight.setCurrentIndex(1)
        f.addRow(tr('lbl_sight'), self.sandbox_sight)

        self.sandbox_smell = QComboBox()
        self.sandbox_smell.addItems(_combo_items(_ZOMBIE_SMELL))
        f.addRow(tr('lbl_smell'), self.sandbox_smell)

        self.sandbox_infection_mortality = QComboBox()
        self.sandbox_infection_mortality.addItems(_combo_items(_INFECTION))
        self.sandbox_infection_mortality.setCurrentIndex(5)  # 2-3 days
        f.addRow(tr('lbl_infection_mortality'), self.sandbox_infection_mortality)

        sl.addWidget(g)

        # ── Loot & Resources ──
        g = QGroupBox(tr('group_loot'))
        f = QFormLayout(g)

        self.sandbox_loot_rarity = QComboBox()
        self.sandbox_loot_rarity.addItems(_combo_items(_LOOT_RARITY))
        self.sandbox_loot_rarity.setCurrentIndex(1)  # rare
        f.addRow(tr('lbl_loot_rarity'), self.sandbox_loot_rarity)

        self.sandbox_loot_respawn = QComboBox()
        self.sandbox_loot_respawn.addItems(_combo_items(_LOOT_RESPAWN))
        f.addRow(tr('lbl_loot_respawn'), self.sandbox_loot_respawn)

        self.sandbox_water_shutoff = QSpinBox()
        self.sandbox_water_shutoff.setRange(0, 365)
        self.sandbox_water_shutoff.setValue(14)
        self.sandbox_water_shutoff.setSpecialValueText(tr('never'))
        self.sandbox_water_shutoff.setSuffix(f" {tr('days')}")
        f.addRow(tr('lbl_water_shutoff'), self.sandbox_water_shutoff)

        self.sandbox_electricity_shutoff = QSpinBox()
        self.sandbox_electricity_shutoff.setRange(0, 365)
        self.sandbox_electricity_shutoff.setValue(14)
        self.sandbox_electricity_shutoff.setSpecialValueText(tr('never'))
        self.sandbox_electricity_shutoff.setSuffix(f" {tr('days')}")
        f.addRow(tr('lbl_electricity_shutoff'), self.sandbox_electricity_shutoff)

        sl.addWidget(g)

        # ── Time & Environment ──
        g = QGroupBox(tr('group_time'))
        f = QFormLayout(g)

        self.sandbox_start_month = QComboBox()
        months = ['january','february','march','april','may','june',
                  'july','august','september','october','november','december']
        self.sandbox_start_month.addItems([tr(m) for m in months])
        self.sandbox_start_month.setCurrentIndex(6)  # July
        f.addRow(tr('lbl_start_month'), self.sandbox_start_month)

        self.sandbox_start_day = QSpinBox()
        self.sandbox_start_day.setRange(1, 31)
        self.sandbox_start_day.setValue(9)
        f.addRow(tr('lbl_start_day'), self.sandbox_start_day)

        self.sandbox_day_length = QComboBox()
        self.sandbox_day_length.addItems([k for k,_ in _DAY_LENGTH])
        self.sandbox_day_length.setCurrentIndex(3)  # 2 h
        f.addRow(tr('lbl_day_length'), self.sandbox_day_length)

        self.sandbox_night_darkness = QComboBox()
        self.sandbox_night_darkness.addItems(_combo_items(_NIGHT_DARK))
        self.sandbox_night_darkness.setCurrentIndex(1)  # dark
        f.addRow(tr('lbl_night_darkness'), self.sandbox_night_darkness)

        self.sandbox_fire_spread = QCheckBox()
        self.sandbox_fire_spread.setChecked(True)
        f.addRow(tr('lbl_fire_spread'), self.sandbox_fire_spread)

        self.sandbox_nature_abundance = QComboBox()
        self.sandbox_nature_abundance.addItems(_combo_items(_NATURE_ABU))
        self.sandbox_nature_abundance.setCurrentIndex(2)  # normal
        f.addRow(tr('lbl_nature_abundance'), self.sandbox_nature_abundance)

        sl.addWidget(g)

        # ── World State ──
        g = QGroupBox(tr('group_world'))
        f = QFormLayout(g)

        self.sandbox_time_since_apo = QComboBox()
        self.sandbox_time_since_apo.addItems(_combo_items(_TIME_APO))
        f.addRow(tr('lbl_time_since_apo'), self.sandbox_time_since_apo)

        self.sandbox_zombie_pop_multiplier = QComboBox()
        self.sandbox_zombie_pop_multiplier.addItems(_combo_items(_POP_MULTIPLIERS))
        self.sandbox_zombie_pop_multiplier.setCurrentIndex(3)
        f.addRow(tr('lbl_pop_multiplier'), self.sandbox_zombie_pop_multiplier)

        sl.addWidget(g)

        # ── Vehicles ──
        g = QGroupBox(tr('group_vehicles'))
        f = QFormLayout(g)

        self.sandbox_car_spawn = QComboBox()
        self.sandbox_car_spawn.addItems(_combo_items(_CAR_SPAWN))
        self.sandbox_car_spawn.setCurrentIndex(2)  # normal
        f.addRow(tr('lbl_car_spawn'), self.sandbox_car_spawn)

        self.sandbox_vehicle_easy_use = QCheckBox()
        self.sandbox_vehicle_easy_use.setChecked(False)
        f.addRow(tr('lbl_vehicle_easy_use'), self.sandbox_vehicle_easy_use)

        sl.addWidget(g)

        # ── Character & XP ──
        g = QGroupBox(tr('group_character'))
        f = QFormLayout(g)

        self.sandbox_xp_multiplier = QComboBox()
        self.sandbox_xp_multiplier.addItems([k for k, _ in _XP_MULT])
        self.sandbox_xp_multiplier.setCurrentIndex(2)  # 1x
        f.addRow(tr('lbl_xp_multiplier'), self.sandbox_xp_multiplier)

        self.sandbox_player_damage = QComboBox()
        self.sandbox_player_damage.addItems(_combo_items(_PLAYER_DMG))
        self.sandbox_player_damage.setCurrentIndex(2)  # normal
        f.addRow(tr('lbl_player_damage'), self.sandbox_player_damage)

        self.sandbox_char_free_points = QSpinBox()
        self.sandbox_char_free_points.setRange(0, 100)
        self.sandbox_char_free_points.setValue(0)
        f.addRow(tr('lbl_char_free_points'), self.sandbox_char_free_points)

        self.sandbox_farming_speed = QComboBox()
        self.sandbox_farming_speed.addItems(_combo_items(_FARMING_SPD))
        self.sandbox_farming_speed.setCurrentIndex(2)  # normal
        f.addRow(tr('lbl_farming_speed'), self.sandbox_farming_speed)

        self.sandbox_generator_spawn = QComboBox()
        self.sandbox_generator_spawn.addItems(_combo_items(_GENERATOR_SP))
        self.sandbox_generator_spawn.setCurrentIndex(2)
        f.addRow(tr('lbl_generator_spawn'), self.sandbox_generator_spawn)

        self.sandbox_generator_fuel = QComboBox()
        self.sandbox_generator_fuel.addItems(_combo_items(_GENERATOR_FU))
        self.sandbox_generator_fuel.setCurrentIndex(2)
        f.addRow(tr('lbl_generator_fuel'), self.sandbox_generator_fuel)

        sl.addWidget(g)

        sl.addStretch()
        scroll.setWidget(sw)
        layout.addWidget(scroll)

        row = QHBoxLayout()
        b = QPushButton(tr('btn_save_sandbox'))
        b.clicked.connect(self.save_sandbox_settings)
        row.addWidget(b)
        b2 = QPushButton(tr('btn_reload'))
        b2.clicked.connect(self.load_sandbox_settings)
        row.addWidget(b2)
        layout.addLayout(row)

        self.tabs.addTab(tab, tr('tab_sandbox'))

    # ── Tab: Mods ───────────────────────────────────────────────────

    def create_mods_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info = QLabel(
            '💡 '
            + ('Добавляйте моды по Steam Workshop ID. '
               'ID находится в URL мода: …filedetails/?id=<b>123456789</b>'
               if get_language() == 'ru' else
               'Add mods using their Steam Workshop ID found in the workshop URL: '
               '…filedetails/?id=<b>123456789</b>')
        )
        info.setWordWrap(True)
        info.setStyleSheet('padding:10px;background-color:#3d3d3d;border-radius:4px;')
        layout.addWidget(info)

        g = QGroupBox(tr('group_mods'))
        gl = QVBoxLayout(g)
        self.mods_list = QListWidget()
        self.mods_list.setAlternatingRowColors(True)
        gl.addWidget(self.mods_list)

        row = QHBoxLayout()
        for key, slot in [('btn_add_mod', self.add_mod),
                          ('btn_remove_mod', self.remove_mod),
                          ('btn_clear_mods', self.clear_mods)]:
            b = QPushButton(tr(key))
            b.clicked.connect(slot)
            row.addWidget(b)
        gl.addLayout(row)
        layout.addWidget(g)

        g2 = QGroupBox(tr('group_import_export'))
        iol = QHBoxLayout(g2)
        bi = QPushButton(tr('btn_import_mods'))
        bi.clicked.connect(self.import_mods)
        iol.addWidget(bi)
        be = QPushButton(tr('btn_export_mods'))
        be.clicked.connect(self.export_mods)
        iol.addWidget(be)
        layout.addWidget(g2)

        bs = QPushButton(tr('btn_save_mods'))
        bs.clicked.connect(self.save_mods)
        layout.addWidget(bs)

        self.tabs.addTab(tab, tr('tab_mods'))

    # ── Tab: Install ─────────────────────────────────────────────────

    def create_install_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        g = QGroupBox(tr('group_install_path'))
        pl = QHBoxLayout(g)
        self.install_path_edit = QLineEdit(str(self.paths['server_dir']))
        pl.addWidget(self.install_path_edit)
        b = QPushButton(tr('btn_browse'))
        b.clicked.connect(self.browse_install_path)
        pl.addWidget(b)
        layout.addWidget(g)

        g2 = QGroupBox(tr('group_install_status'))
        sl = QVBoxLayout(g2)
        self.install_status_label = QLabel(tr('lbl_ready_install'))
        self.install_status_label.setStyleSheet('font-size:14px;')
        sl.addWidget(self.install_status_label)
        self.install_progress = QProgressBar()
        self.install_progress.setRange(0, 100)
        sl.addWidget(self.install_progress)
        self.install_log = QPlainTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMaximumBlockCount(1000)
        self.install_log.setFont(QFont(self._mono_font(), 9))
        sl.addWidget(self.install_log)
        layout.addWidget(g2)

        self.install_btn = QPushButton(tr('btn_install_server'))
        self.install_btn.setMinimumHeight(50)
        self.install_btn.setStyleSheet('font-size:14px;font-weight:bold;')
        self.install_btn.clicked.connect(self.start_installation)
        layout.addWidget(self.install_btn)

        warn = QLabel(
            '⚠️ '
            + ('Для установки требуется ~3 ГБ свободного места.\n'
               'Откройте порты 16261 (UDP) и 27015 (TCP) в брандмауэре.'
               if get_language() == 'ru' else
               'Installation requires ~3 GB of disk space.\n'
               'Open ports 16261 (UDP) and 27015 (TCP) in your firewall.')
        )
        warn.setStyleSheet('color:#ffaa00;padding:10px;')
        layout.addWidget(warn)

        self.tabs.addTab(tab, tr('tab_install'))

    def show_install_tab(self):
        self.tabs.setCurrentIndex(4)

    # ── Server Control ───────────────────────────────────────────────

    def start_server(self):
        if not self.server_installed:
            QMessageBox.warning(self, tr('server_not_installed'), tr('server_not_installed_msg'))
            return
        name = self.server_name_input.text().strip() or 'servertest'
        self.append_console_output(f"{tr('starting_server')} '{name}'…")
        try:
            self.server_process.start(name)
        except Exception as e:
            self.append_console_error(f"Failed to start: {e}")

    def stop_server(self):
        self.append_console_output(tr('stopping_server'))
        try:
            self.server_process.stop()
        except Exception as e:
            self.append_console_error(f"Failed to stop: {e}")

    def restart_server(self):
        self.append_console_output(tr('restarting_server'))
        self.stop_server()
        QTimer.singleShot(3000, self.start_server)

    def send_command(self):
        cmd = self.command_input.text().strip()
        if cmd:
            self.server_process.send_command(cmd)
            self.append_console_output(f'> {cmd}')
            self.command_input.clear()

    def on_server_started(self):
        self.status_indicator.setStyleSheet('color:#44ff44;font-size:24px;')
        self.status_label.setText(tr('server_running'))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)

    def on_server_stopped(self):
        self.status_indicator.setStyleSheet('color:#ff4444;font-size:24px;')
        self.status_label.setText(tr('server_stopped'))
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)

    def append_console_output(self, text: str):
        ts = datetime.now().strftime('%H:%M:%S')
        self.console_output.appendPlainText(f'[{ts}] {text}')

    def append_console_error(self, text: str):
        ts = datetime.now().strftime('%H:%M:%S')
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor('#ff6666'))
        cursor.insertText(f'[{ts}] ERROR: {text}\n', fmt)
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible()

    # ── Settings load / save ─────────────────────────────────────────

    def load_settings(self):
        try:
            c = self.config_manager.load_server_ini()

            self.setting_public_name.setText(c.get('PublicName', ''))
            self.setting_public_desc.setText(c.get('PublicDescription', ''))
            self.setting_password.setText(c.get('Password', ''))
            self.setting_max_players.setValue(int(c.get('MaxPlayers', 16)))
            self.setting_map.setText(c.get('Map', 'Muldraugh, KY'))
            self.setting_welcome_msg.setText(c.get('ServerWelcomeMessage', ''))

            self.setting_port.setValue(int(c.get('DefaultPort', 16261)))
            self.setting_udp_port.setValue(int(c.get('UDPPort', 16262)))
            self.setting_steam_port.setValue(int(c.get('SteamPort1', 8766)))
            self.setting_steam_port2.setValue(int(c.get('SteamPort2', 8767)))
            self.setting_rcon_port.setValue(int(c.get('RCONPort', 27015)))
            self.setting_rcon_password.setText(c.get('RCONPassword', ''))
            self.setting_public.setChecked(c.get('Open', 'true').lower() == 'true')

            self.setting_pvp.setChecked(c.get('PVP', 'true').lower() == 'true')
            self.setting_pause_empty.setChecked(c.get('PauseEmpty', 'true').lower() == 'true')
            self.setting_allow_coop.setChecked(c.get('AllowCoop', 'true').lower() == 'true')
            self.setting_sleep_allowed.setChecked(c.get('SleepAllowed', 'false').lower() == 'true')
            self.setting_sleep_needed.setChecked(c.get('SleepNeeded', 'false').lower() == 'true')
            self.setting_announce_death.setChecked(c.get('AnnounceDeath', 'false').lower() == 'true')
            self.setting_no_fire.setChecked(c.get('NoFire', 'false').lower() == 'true')
            self.setting_allow_destruction.setChecked(
                c.get('AllowDestructionBySledgehammer', 'true').lower() == 'true')
            self.setting_drop_on_death.setCurrentIndex(
                _combo_index(_DROP_DEATH, int(c.get('DropOnDeath', 1))))
            self.setting_spawn_point.setText(c.get('SpawnPoint', '0,0,0'))

            self.setting_player_safehouse.setChecked(c.get('PlayerSafehouse', 'false').lower() == 'true')
            self.setting_admin_safehouse.setChecked(c.get('AdminSafehouse', 'false').lower() == 'true')
            self.setting_safehouse_trespassing.setChecked(
                c.get('SafehouseAllowTreassing', 'false').lower() == 'true')
            self.setting_safehouse_fire.setChecked(c.get('SafehouseAllowFire', 'false').lower() == 'true')
            self.setting_safehouse_loot.setChecked(c.get('SafehouseAllowLoot', 'false').lower() == 'true')
            self.setting_safehouse_respawn.setChecked(
                c.get('SafehouseAllowRespawn', 'false').lower() == 'true')

            self.setting_global_chat.setChecked(c.get('GlobalChat', 'true').lower() == 'true')
            self.setting_safety_system.setChecked(c.get('SafetySystem', 'true').lower() == 'true')
            self.setting_show_safety.setChecked(c.get('ShowSafety', 'true').lower() == 'true')
            self.setting_display_username.setChecked(c.get('DisplayUserName', 'true').lower() == 'true')
            self.setting_voice_enable.setChecked(c.get('VoiceEnable', 'true').lower() == 'true')
            self.setting_voice_3d.setChecked(c.get('Voice3D', 'true').lower() == 'true')
            self.setting_voice_min.setValue(int(c.get('VoiceMinDistance', 10)))
            self.setting_voice_max.setValue(int(c.get('VoiceMaxDistance', 100)))

            self.setting_secure_join.setChecked(c.get('UseSecureJoin', 'false').lower() == 'true')
            self.setting_non_ascii.setChecked(c.get('AllowNonAsciiUsername', 'false').lower() == 'true')
            self.setting_auto_whitelist.setChecked(
                c.get('AutoCreateUserInWhiteList', 'false').lower() == 'true')
            self.setting_max_accounts.setValue(int(c.get('MaxAccountsPerUser', 0)))
            self.setting_speed_limit.setValue(int(c.get('SpeedLimit', 70)))

            self.setting_admin_password.setText(c.get('AdminPassword', ''))
            self.setting_auto_save.setValue(int(c.get('SaveWorldEveryMinutes', 15)))
            self.setting_backups_count.setValue(int(c.get('BackupsCount', 5)))
            self.setting_backups_period.setValue(int(c.get('BackupsPeriod', 0)))

            self.load_mods_list()
            self.load_sandbox_settings()

            self.statusBar.showMessage(tr('settings_loaded'), 3000)

        except FileNotFoundError:
            self.statusBar.showMessage(tr('no_config_found'), 3000)
        except Exception as e:
            logger.exception('Failed to load settings')
            QMessageBox.warning(self, tr('error'), f"Failed to load settings: {e}")

    def save_settings(self):
        try:
            config = {
                'PublicName':                    self.setting_public_name.text(),
                'PublicDescription':             self.setting_public_desc.text(),
                'Password':                      self.setting_password.text(),
                'MaxPlayers':                    str(self.setting_max_players.value()),
                'Map':                           self.setting_map.text(),
                'ServerWelcomeMessage':          self.setting_welcome_msg.text(),
                'DefaultPort':                   str(self.setting_port.value()),
                'UDPPort':                       str(self.setting_udp_port.value()),
                'SteamPort1':                    str(self.setting_steam_port.value()),
                'SteamPort2':                    str(self.setting_steam_port2.value()),
                'RCONPort':                      str(self.setting_rcon_port.value()),
                'RCONPassword':                  self.setting_rcon_password.text(),
                'Open':                          _b(self.setting_public),
                'PVP':                           _b(self.setting_pvp),
                'PauseEmpty':                    _b(self.setting_pause_empty),
                'AllowCoop':                     _b(self.setting_allow_coop),
                'SleepAllowed':                  _b(self.setting_sleep_allowed),
                'SleepNeeded':                   _b(self.setting_sleep_needed),
                'AnnounceDeath':                 _b(self.setting_announce_death),
                'NoFire':                        _b(self.setting_no_fire),
                'AllowDestructionBySledgehammer':_b(self.setting_allow_destruction),
                'DropOnDeath':                   str(_combo_value(_DROP_DEATH,
                                                     self.setting_drop_on_death.currentIndex(), 1)),
                'SpawnPoint':                    self.setting_spawn_point.text(),
                'PlayerSafehouse':               _b(self.setting_player_safehouse),
                'AdminSafehouse':                _b(self.setting_admin_safehouse),
                'SafehouseAllowTreassing':       _b(self.setting_safehouse_trespassing),
                'SafehouseAllowFire':            _b(self.setting_safehouse_fire),
                'SafehouseAllowLoot':            _b(self.setting_safehouse_loot),
                'SafehouseAllowRespawn':         _b(self.setting_safehouse_respawn),
                'GlobalChat':                    _b(self.setting_global_chat),
                'SafetySystem':                  _b(self.setting_safety_system),
                'ShowSafety':                    _b(self.setting_show_safety),
                'DisplayUserName':               _b(self.setting_display_username),
                'VoiceEnable':                   _b(self.setting_voice_enable),
                'Voice3D':                       _b(self.setting_voice_3d),
                'VoiceMinDistance':              str(self.setting_voice_min.value()),
                'VoiceMaxDistance':              str(self.setting_voice_max.value()),
                'UseSecureJoin':                 _b(self.setting_secure_join),
                'AllowNonAsciiUsername':         _b(self.setting_non_ascii),
                'AutoCreateUserInWhiteList':     _b(self.setting_auto_whitelist),
                'MaxAccountsPerUser':            str(self.setting_max_accounts.value()),
                'SpeedLimit':                    str(self.setting_speed_limit.value()),
                'AdminPassword':                 self.setting_admin_password.text(),
                'SaveWorldEveryMinutes':         str(self.setting_auto_save.value()),
                'BackupsCount':                  str(self.setting_backups_count.value()),
                'BackupsPeriod':                 str(self.setting_backups_period.value()),
            }
            self.config_manager.save_server_ini(config)
            self.statusBar.showMessage(tr('settings_loaded'), 3000)
            QMessageBox.information(self, tr('success'), tr('settings_saved'))

        except Exception as e:
            logger.exception('Failed to save settings')
            QMessageBox.critical(self, tr('error'), f"Failed to save settings: {e}")

    # ── Sandbox load / save ──────────────────────────────────────────

    def load_sandbox_settings(self):
        try:
            sb = self.config_manager.load_sandbox_vars()

            zl = sb.get('ZombieLore', {})
            zc = sb.get('ZombieConfig', {})
            gt = sb.get('GameTime', {})
            lo = sb.get('Loot', {})
            cl = sb.get('Climate', {})
            ca = sb.get('Cars', {})
            ch = sb.get('Character', {})
            fa = sb.get('Farming', {})

            def _si(mapping, val, default=0):
                return _combo_index(mapping, val, default)

            # Zombies
            pm = float(zc.get('PopulationMultiplier', 1.0))
            best = min(range(len(_POP_MULTIPLIERS)), key=lambda i: abs(_POP_MULTIPLIERS[i][1]-pm))
            self.sandbox_zombie_count.setCurrentIndex(best)
            self.sandbox_zombie_pop_multiplier.setCurrentIndex(best)

            self.sandbox_zombie_distribution.setCurrentIndex(_si(_ZOMBIE_DISTRIBUTION, zl.get('Distribution', 1)))
            self.sandbox_zombie_speed.setCurrentIndex(_si(_ZOMBIE_SPEED, zl.get('Speed', 3)))
            self.sandbox_zombie_strength.setCurrentIndex(_si(_ZOMBIE_STRENGTH, zl.get('Strength', 2)))
            self.sandbox_zombie_toughness.setCurrentIndex(_si(_ZOMBIE_TOUGHNESS, zl.get('Toughness', 2)))
            self.sandbox_zombie_transmission.setCurrentIndex(_si(_ZOMBIE_TRANSMISSION, zl.get('Transmission', 1)))
            self.sandbox_zombie_cognition.setCurrentIndex(_si(_ZOMBIE_COGNITION, zl.get('Cognition', 3)))

            # Zombie Lore
            self.sandbox_memory.setCurrentIndex(_si(_ZOMBIE_MEMORY, zl.get('Memory', 2)))
            self.sandbox_decomp.setCurrentIndex(_si(_ZOMBIE_DECOMP, zl.get('Decomp', 1)))
            self.sandbox_hearing.setCurrentIndex(_si(_ZOMBIE_HEARING, zl.get('Hearing', 2)))
            self.sandbox_sight.setCurrentIndex(_si(_ZOMBIE_SIGHT, zl.get('Sight', 2)))
            self.sandbox_smell.setCurrentIndex(_si(_ZOMBIE_SMELL, zl.get('Smell', 2)))
            self.sandbox_infection_mortality.setCurrentIndex(_si(_INFECTION, zl.get('Mortality', 6)))

            # Loot
            self.sandbox_loot_rarity.setCurrentIndex(_si(_LOOT_RARITY, lo.get('Weapons', 2)))
            hrs = lo.get('HoursForLootRespawn', 0)
            self.sandbox_loot_respawn.setCurrentIndex(_si(_LOOT_RESPAWN, hrs))
            self.sandbox_water_shutoff.setValue(int(lo.get('WaterShutModifier', 14)))
            self.sandbox_electricity_shutoff.setValue(int(lo.get('ElecShutModifier', 14)))

            # Time
            self.sandbox_start_month.setCurrentIndex(max(0, int(gt.get('StartMonth', 7)) - 1))
            self.sandbox_start_day.setValue(int(gt.get('StartDay', 9)))
            self.sandbox_day_length.setCurrentIndex(_si(_DAY_LENGTH, gt.get('DayLength', 4)))
            self.sandbox_night_darkness.setCurrentIndex(_si(_NIGHT_DARK, gt.get('NightDarkness', 2)))
            self.sandbox_time_since_apo.setCurrentIndex(_si(_TIME_APO, gt.get('TimeSinceApo', 1)))

            # Climate / environment
            self.sandbox_fire_spread.setChecked(bool(cl.get('FireSpread', True)))
            self.sandbox_nature_abundance.setCurrentIndex(_si(_NATURE_ABU, cl.get('NatureAbundance', 3)))

            # Vehicles
            self.sandbox_car_spawn.setCurrentIndex(_si(_CAR_SPAWN, ca.get('CarSpawnRate', 3)))
            self.sandbox_vehicle_easy_use.setChecked(bool(ca.get('EasyUse', False)))

            # Character
            xp = float(ch.get('XPMultiplier', 1.0))
            best_xp = min(range(len(_XP_MULT)), key=lambda i: abs(_XP_MULT[i][1]-xp))
            self.sandbox_xp_multiplier.setCurrentIndex(best_xp)
            self.sandbox_player_damage.setCurrentIndex(_si(_PLAYER_DMG, ch.get('DamageToPlayer', 3)))
            self.sandbox_char_free_points.setValue(int(ch.get('FreePoints', 0)))

            # Farming / generators
            self.sandbox_farming_speed.setCurrentIndex(_si(_FARMING_SPD, fa.get('FarmingSpeed', 3)))
            self.sandbox_generator_spawn.setCurrentIndex(
                _si(_GENERATOR_SP, sb.get('Meta', {}).get('GeneratorSpawning', 3)))
            self.sandbox_generator_fuel.setCurrentIndex(
                _si(_GENERATOR_FU, sb.get('Meta', {}).get('GeneratorFuelConsumption', 3)))

            self.statusBar.showMessage(tr('settings_loaded'), 3000)

        except FileNotFoundError:
            pass  # No sandbox file yet – silently use UI defaults
        except Exception as e:
            logger.exception('Failed to load sandbox settings')

    def save_sandbox_settings(self):
        try:
            pm = _combo_value(_POP_MULTIPLIERS, self.sandbox_zombie_count.currentIndex(), 1.0)
            pm2 = _combo_value(_POP_MULTIPLIERS, self.sandbox_zombie_pop_multiplier.currentIndex(), 1.0)

            vars_dict = {
                'ZombieLore': {
                    'Speed':        _combo_value(_ZOMBIE_SPEED,
                                        self.sandbox_zombie_speed.currentIndex(), 3),
                    'Strength':     _combo_value(_ZOMBIE_STRENGTH,
                                        self.sandbox_zombie_strength.currentIndex(), 2),
                    'Toughness':    _combo_value(_ZOMBIE_TOUGHNESS,
                                        self.sandbox_zombie_toughness.currentIndex(), 2),
                    'Transmission': _combo_value(_ZOMBIE_TRANSMISSION,
                                        self.sandbox_zombie_transmission.currentIndex(), 1),
                    'Mortality':    _combo_value(_INFECTION,
                                        self.sandbox_infection_mortality.currentIndex(), 6),
                    'Cognition':    _combo_value(_ZOMBIE_COGNITION,
                                        self.sandbox_zombie_cognition.currentIndex(), 3),
                    'Memory':       _combo_value(_ZOMBIE_MEMORY,
                                        self.sandbox_memory.currentIndex(), 2),
                    'Decomp':       _combo_value(_ZOMBIE_DECOMP,
                                        self.sandbox_decomp.currentIndex(), 1),
                    'Hearing':      _combo_value(_ZOMBIE_HEARING,
                                        self.sandbox_hearing.currentIndex(), 2),
                    'Sight':        _combo_value(_ZOMBIE_SIGHT,
                                        self.sandbox_sight.currentIndex(), 2),
                    'Smell':        _combo_value(_ZOMBIE_SMELL,
                                        self.sandbox_smell.currentIndex(), 1),
                    'ThumpNoChasing':     False,
                    'ThumpOnConstruction':True,
                    'Distribution': _combo_value(_ZOMBIE_DISTRIBUTION,
                                        self.sandbox_zombie_distribution.currentIndex(), 1),
                },
                'ZombieConfig': {
                    'PopulationMultiplier':      pm,
                    'PopulationStartMultiplier': pm,
                    'PopulationPeakMultiplier':  min(pm * 1.5, pm2 * 1.5),
                    'PopulationPeakDay':         28,
                    'RespawnHours':              72,
                    'RespawnUnseenHours':        16,
                    'RespawnMultiplier':         0.1,
                    'RedistributeHours':         12,
                },
                'GameTime': {
                    'StartYear':      1,
                    'StartMonth':     self.sandbox_start_month.currentIndex() + 1,
                    'StartDay':       self.sandbox_start_day.value(),
                    'DayLength':      _combo_value(_DAY_LENGTH,
                                          self.sandbox_day_length.currentIndex(), 4),
                    'NightDarkness':  _combo_value(_NIGHT_DARK,
                                          self.sandbox_night_darkness.currentIndex(), 2),
                    'TimeSinceApo':   _combo_value(_TIME_APO,
                                          self.sandbox_time_since_apo.currentIndex(), 1),
                },
                'Loot': {
                    'Weapons':             _combo_value(_LOOT_RARITY,
                                               self.sandbox_loot_rarity.currentIndex(), 2),
                    'HoursForLootRespawn': _combo_value(_LOOT_RESPAWN,
                                               self.sandbox_loot_respawn.currentIndex(), 0),
                    'WaterShutModifier':   self.sandbox_water_shutoff.value(),
                    'ElecShutModifier':    self.sandbox_electricity_shutoff.value(),
                },
                'Climate': {
                    'FireSpread':       self.sandbox_fire_spread.isChecked(),
                    'NatureAbundance':  _combo_value(_NATURE_ABU,
                                            self.sandbox_nature_abundance.currentIndex(), 3),
                },
                'Cars': {
                    'CarSpawnRate': _combo_value(_CAR_SPAWN,
                                        self.sandbox_car_spawn.currentIndex(), 3),
                    'EasyUse':      self.sandbox_vehicle_easy_use.isChecked(),
                },
                'Character': {
                    'XPMultiplier':    _combo_value(_XP_MULT,
                                           self.sandbox_xp_multiplier.currentIndex(), 1.0),
                    'DamageToPlayer':  _combo_value(_PLAYER_DMG,
                                           self.sandbox_player_damage.currentIndex(), 3),
                    'FreePoints':      self.sandbox_char_free_points.value(),
                },
                'Farming': {
                    'FarmingSpeed': _combo_value(_FARMING_SPD,
                                        self.sandbox_farming_speed.currentIndex(), 3),
                },
                'Meta': {
                    'GeneratorSpawning':       _combo_value(_GENERATOR_SP,
                                                   self.sandbox_generator_spawn.currentIndex(), 3),
                    'GeneratorFuelConsumption':_combo_value(_GENERATOR_FU,
                                                   self.sandbox_generator_fuel.currentIndex(), 3),
                },
            }

            self.config_manager.save_sandbox_vars(vars_dict)
            self.statusBar.showMessage(tr('sandbox_saved'), 5000)
            QMessageBox.information(self, tr('success'), tr('sandbox_saved'))

        except Exception as e:
            logger.exception('Failed to save sandbox settings')
            QMessageBox.critical(self, tr('error'), f"Failed to save sandbox settings: {e}")

    def on_preset_changed(self, preset: str):
        """Apply preset values to sandbox widgets."""
        p = preset.lower()
        if p == 'apocalypse':
            self.sandbox_zombie_count.setCurrentIndex(4)        # high
            self.sandbox_zombie_speed.setCurrentIndex(0)        # sprinters
            self.sandbox_zombie_strength.setCurrentIndex(0)     # superhuman
            self.sandbox_zombie_toughness.setCurrentIndex(0)    # tough
            self.sandbox_loot_rarity.setCurrentIndex(0)         # extremely rare
            self.sandbox_xp_multiplier.setCurrentIndex(0)       # 0.5x
            self.sandbox_player_damage.setCurrentIndex(4)       # very high
        elif p == 'survivor':
            self.sandbox_zombie_count.setCurrentIndex(3)        # normal
            self.sandbox_zombie_speed.setCurrentIndex(2)        # shamblers
            self.sandbox_zombie_strength.setCurrentIndex(1)     # normal
            self.sandbox_loot_rarity.setCurrentIndex(1)         # rare
            self.sandbox_xp_multiplier.setCurrentIndex(2)       # 1x
            self.sandbox_player_damage.setCurrentIndex(2)       # normal
        elif p == 'builder':
            self.sandbox_zombie_count.setCurrentIndex(1)        # very_low
            self.sandbox_zombie_speed.setCurrentIndex(2)        # shamblers
            self.sandbox_loot_rarity.setCurrentIndex(3)         # common
            self.sandbox_xp_multiplier.setCurrentIndex(4)       # 2x
            self.sandbox_player_damage.setCurrentIndex(0)       # very low
        # 'sandbox' / 'custom' – leave as-is

    # ── Mods ────────────────────────────────────────────────────────

    def load_mods_list(self):
        self.mods_list.clear()
        try:
            for mod in self.mod_manager.get_mods():
                item = QListWidgetItem(f"[{mod['workshop_id']}] {mod['name']}")
                item.setData(Qt.UserRole, mod)
                self.mods_list.addItem(item)
        except Exception as e:
            logger.exception('Failed to load mods list')

    def add_mod(self):
        wid, ok = QInputDialog.getText(
            self, tr('btn_add_mod'), 'Steam Workshop ID:', QLineEdit.Normal)
        if ok and wid:
            wid = wid.strip()
            if not wid.isdigit():
                QMessageBox.warning(self, tr('warning'), 'Workshop ID must be a number.')
                return
            try:
                info = self.mod_manager.add_mod(wid)
                item = QListWidgetItem(f"[{wid}] {info.get('name','Unknown Mod')}")
                item.setData(Qt.UserRole, info)
                self.mods_list.addItem(item)
                self.statusBar.showMessage(f"Added mod: {wid}", 3000)
            except Exception as e:
                QMessageBox.warning(self, tr('error'), f"Failed to add mod: {e}")

    def remove_mod(self):
        cur = self.mods_list.currentItem()
        if cur:
            self.mod_manager.remove_mod(cur.data(Qt.UserRole)['workshop_id'])
            self.mods_list.takeItem(self.mods_list.row(cur))
            self.statusBar.showMessage('Mod removed', 3000)

    def clear_mods(self):
        if QMessageBox.question(self, tr('confirm'), tr('confirm_clear_mods'),
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.mod_manager.clear_mods()
            self.mods_list.clear()

    def import_mods(self):
        fp, _ = QFileDialog.getOpenFileName(self, 'Import', '', 'Text (*.txt);;All (*)')
        if fp:
            try:
                self.mod_manager.import_from_file(fp)
                self.load_mods_list()
            except Exception as e:
                QMessageBox.warning(self, tr('error'), f"Import failed: {e}")

    def export_mods(self):
        fp, _ = QFileDialog.getSaveFileName(self, 'Export', 'pz_mods.txt', 'Text (*.txt);;All (*)')
        if fp:
            try:
                self.mod_manager.export_to_file(fp)
            except Exception as e:
                QMessageBox.warning(self, tr('error'), f"Export failed: {e}")

    def save_mods(self):
        try:
            self.mod_manager.save_to_config()
            QMessageBox.information(self, tr('success'), tr('mods_saved'))
        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"Failed to save mods: {e}")

    # ── Installation ─────────────────────────────────────────────────

    def browse_install_path(self):
        path = QFileDialog.getExistingDirectory(
            self, 'Select Installation Directory', str(self.paths['server_dir']))
        if path:
            self.install_path_edit.setText(path)
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'

    def start_installation(self):
        install_path = Path(self.install_path_edit.text())
        try:
            install_path.mkdir(parents=True, exist_ok=True)
            tf = install_path / '.write_test'
            tf.touch(); tf.unlink()
        except PermissionError:
            if QMessageBox.warning(
                self, 'Permission Denied',
                tr('admin_required_msg', path=install_path),
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes:
                self.browse_install_path()
            return

        if QMessageBox.question(
            self, tr('confirm'),
            tr('confirm_install', path=install_path),
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        self.paths['server_dir'] = install_path
        self.paths['steamcmd_dir'] = install_path / 'steamcmd'
        self.install_btn.setEnabled(False)
        self.install_log.clear()

        self.install_worker = InstallWorker(self.installer, self.paths)
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.log.connect(self.on_install_log)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.error.connect(self.on_install_error)
        self.install_worker.start()

    def on_install_progress(self, value, message):
        self.install_progress.setValue(value)
        self.install_status_label.setText(message)

    def on_install_log(self, message):
        self.install_log.appendPlainText(message)

    def on_install_finished(self):
        self.install_btn.setEnabled(True)
        self.install_progress.setValue(100)
        self.install_status_label.setText('Installation complete!')
        self.server_installed = True
        QMessageBox.information(self, tr('install_complete'), tr('install_complete_msg'))

    def on_install_error(self, error):
        self.install_btn.setEnabled(True)
        self.install_status_label.setText('Installation failed!')
        QMessageBox.critical(self, tr('install_failed'), error)

    # ── Utilities ────────────────────────────────────────────────────

    def update_status(self):
        if self.server_process.is_running():
            self.statusBar.showMessage(tr('status_running'))
        else:
            self.statusBar.showMessage(tr('status_stopped'))

    def change_server_directory(self):
        path = QFileDialog.getExistingDirectory(
            self, 'Select Server Directory', str(self.paths['server_dir']))
        if path:
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'
            self.install_path_edit.setText(path)
            p = Path(path)
            self.server_installed = any(
                (p / n).exists() for n in [
                    'ProjectZomboid64.exe', 'StartServer64.bat',
                    'start-server.sh', 'ProjectZomboid64',
                ])
            self.statusBar.showMessage(f"Server directory: {path}", 5000)

    def validate_server(self):
        QMessageBox.information(
            self, tr('menu_validate'),
            'Go to the Install tab and click Install / Update Server.')

    def update_server(self):
        self.show_install_tab()

    def _open_folder(self, path: Path):
        system = platform.system()
        if system == 'Windows':
            subprocess.run(['explorer', str(path)])
        elif system == 'Darwin':
            subprocess.run(['open', str(path)])
        else:
            subprocess.run(['xdg-open', str(path)])

    def open_config_folder(self):
        d = self.paths['server_config_dir']
        if d.exists():
            self._open_folder(d)
        else:
            QMessageBox.warning(self, tr('folder_not_found'),
                                f"Config folder not found:\n{d}")

    def open_server_folder(self):
        d = self.paths['server_dir']
        if d.exists():
            self._open_folder(d)
        else:
            QMessageBox.warning(self, tr('folder_not_found'),
                                f"Server folder not found:\n{d}")

    def show_about(self):
        QMessageBox.about(self, tr('menu_about'), tr('about_text'))

    def show_firewall_info(self):
        QMessageBox.information(self, tr('firewall_info'), tr('firewall_info_msg'))

    def change_language(self, language: str):
        set_language(language)
        try:
            with open('language.cfg', 'w') as f:
                f.write(language)
        except Exception:
            pass
        QMessageBox.information(
            self,
            'Language Changed' if language == 'en' else 'Язык изменён',
            'Please restart the application to apply the new language.\n\n'
            'Перезапустите приложение для применения нового языка.'
        )

    def closeEvent(self, event):
        if self.server_process.is_running():
            res = QMessageBox.question(
                self, tr('server_running_close'), tr('server_running_close_msg'),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if res == QMessageBox.Yes:
                self.stop_server()
                event.accept()
            elif res == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    @staticmethod
    def _mono_font() -> str:
        system = platform.system()
        if system == 'Windows':
            return 'Consolas'
        elif system == 'Darwin':
            return 'Menlo'
        return 'DejaVu Sans Mono'


# ── Helper ────────────────────────────────────────────────────────────

def _b(checkbox: QCheckBox) -> str:
    """Convert checkbox state to 'true'/'false' string."""
    return 'true' if checkbox.isChecked() else 'false'
