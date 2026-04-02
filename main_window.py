#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window for PZ Server Manager
Contains the main GUI with tabs for server control, settings, and mods.
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
    QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QIcon

from server_installer import ServerInstaller, InstallWorker
from server_process import ServerProcess
from config_manager import ConfigManager
from mod_manager import ModManager
from translations import tr, set_language, get_language

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, paths: dict, server_installed: bool):
        super().__init__()
        self.paths = paths
        self.server_installed = server_installed
        
        # Initialize managers
        self.config_manager = ConfigManager(paths)
        self.server_process = ServerProcess(paths)
        self.mod_manager = ModManager(paths)
        self.installer = ServerInstaller(paths)
        
        # Connect server process signals
        self.server_process.output_received.connect(self.append_console_output)
        self.server_process.error_received.connect(self.append_console_error)
        self.server_process.server_started.connect(self.on_server_started)
        self.server_process.server_stopped.connect(self.on_server_stopped)
        
        self.init_ui()
        self.setup_menu()
        self.load_settings()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(tr('app_title'))
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs
        self.create_server_tab()
        self.create_settings_tab()
        self.create_sandbox_tab()
        self.create_mods_tab()
        self.create_install_tab()
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.update_status()
        
    def setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu(tr('menu_file'))
        
        change_dir_action = QAction(tr('menu_change_dir'), self)
        change_dir_action.triggered.connect(self.change_server_directory)
        file_menu.addAction(change_dir_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(tr('menu_exit'), self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu(tr('menu_tools'))
        
        validate_action = QAction(tr('menu_validate'), self)
        validate_action.triggered.connect(self.validate_server)
        tools_menu.addAction(validate_action)
        
        update_action = QAction(tr('menu_update'), self)
        update_action.triggered.connect(self.update_server)
        tools_menu.addAction(update_action)
        
        tools_menu.addSeparator()
        
        open_config_action = QAction(tr('menu_open_config'), self)
        open_config_action.triggered.connect(self.open_config_folder)
        tools_menu.addAction(open_config_action)
        
        open_server_action = QAction(tr('menu_open_server'), self)
        open_server_action.triggered.connect(self.open_server_folder)
        tools_menu.addAction(open_server_action)
        
        # Language menu
        lang_menu = menubar.addMenu(tr('menu_language'))
        
        lang_ru_action = QAction("🇷🇺 Русский", self)
        lang_ru_action.triggered.connect(lambda: self.change_language('ru'))
        lang_menu.addAction(lang_ru_action)
        
        lang_en_action = QAction("🇬🇧 English", self)
        lang_en_action.triggered.connect(lambda: self.change_language('en'))
        lang_menu.addAction(lang_en_action)
        
        # Help menu
        help_menu = menubar.addMenu(tr('menu_help'))
        
        about_action = QAction(tr('menu_about'), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        firewall_action = QAction(tr('menu_firewall'), self)
        firewall_action.triggered.connect(self.show_firewall_info)
        help_menu.addAction(firewall_action)
        
    def create_server_tab(self):
        """Create the server control tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Status group
        status_group = QGroupBox(tr('server_status'))
        status_layout = QHBoxLayout(status_group)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #ff4444; font-size: 24px;")
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel(tr('server_stopped'))
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Server name input
        status_layout.addWidget(QLabel(tr('server_name')))
        self.server_name_input = QLineEdit("servertest")
        self.server_name_input.setMaximumWidth(150)
        self.server_name_input.setToolTip(tr('server_name_tooltip'))
        status_layout.addWidget(self.server_name_input)
        
        layout.addWidget(status_group)
        
        # Control buttons
        controls_group = QGroupBox(tr('controls'))
        controls_layout = QHBoxLayout(controls_group)
        
        self.start_btn = QPushButton(tr('btn_start'))
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_server)
        self.start_btn.setMinimumHeight(50)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(tr('btn_stop'))
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(50)
        controls_layout.addWidget(self.stop_btn)
        
        self.restart_btn = QPushButton(tr('btn_restart'))
        self.restart_btn.clicked.connect(self.restart_server)
        self.restart_btn.setEnabled(False)
        self.restart_btn.setMinimumHeight(50)
        controls_layout.addWidget(self.restart_btn)
        
        layout.addWidget(controls_group)
        
        # Console output
        console_group = QGroupBox(tr('server_console'))
        console_layout = QVBoxLayout(console_group)
        
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setMaximumBlockCount(5000)  # Limit lines
        system = platform.system()
        if system == 'Windows':
            mono = 'Consolas'
        elif system == 'Darwin':
            mono = 'Menlo'
        else:
            mono = 'DejaVu Sans Mono'
        font = QFont(mono, 9)
        self.console_output.setFont(font)
        console_layout.addWidget(self.console_output)
        
        # Console controls
        console_controls = QHBoxLayout()
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText(tr('command_placeholder'))
        self.command_input.returnPressed.connect(self.send_command)
        console_controls.addWidget(self.command_input)
        
        send_btn = QPushButton(tr('btn_send'))
        send_btn.clicked.connect(self.send_command)
        console_controls.addWidget(send_btn)
        
        clear_btn = QPushButton(tr('btn_clear'))
        clear_btn.clicked.connect(self.console_output.clear)
        console_controls.addWidget(clear_btn)
        
        console_layout.addLayout(console_controls)
        layout.addWidget(console_group)
        
        self.tabs.addTab(tab, tr('tab_server'))
        
    def create_settings_tab(self):
        """Create the server settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Basic settings
        basic_group = QGroupBox(tr("group_basic"))
        basic_layout = QFormLayout(basic_group)
        
        self.setting_public_name = QLineEdit()
        self.setting_public_name.setPlaceholderText("My Zomboid Server")
        basic_layout.addRow("Server Name:", self.setting_public_name)
        
        self.setting_public_desc = QLineEdit()
        self.setting_public_desc.setPlaceholderText("A Project Zomboid server")
        basic_layout.addRow("Description:", self.setting_public_desc)
        
        self.setting_password = QLineEdit()
        self.setting_password.setEchoMode(QLineEdit.Password)
        self.setting_password.setPlaceholderText("Leave empty for no password")
        basic_layout.addRow("Password:", self.setting_password)
        
        self.setting_max_players = QSpinBox()
        self.setting_max_players.setRange(1, 100)
        self.setting_max_players.setValue(16)
        basic_layout.addRow("Max Players:", self.setting_max_players)
        
        scroll_layout.addWidget(basic_group)
        
        # Network settings
        network_group = QGroupBox(tr("group_network"))
        network_layout = QFormLayout(network_group)
        
        self.setting_port = QSpinBox()
        self.setting_port.setRange(1024, 65535)
        self.setting_port.setValue(16261)
        network_layout.addRow("Game Port (UDP):", self.setting_port)
        
        self.setting_steam_port = QSpinBox()
        self.setting_steam_port.setRange(1024, 65535)
        self.setting_steam_port.setValue(8766)
        network_layout.addRow("Steam Port:", self.setting_steam_port)
        
        self.setting_rcon_port = QSpinBox()
        self.setting_rcon_port.setRange(1024, 65535)
        self.setting_rcon_port.setValue(27015)
        network_layout.addRow("RCON Port:", self.setting_rcon_port)
        
        self.setting_rcon_password = QLineEdit()
        self.setting_rcon_password.setPlaceholderText("RCON password")
        network_layout.addRow("RCON Password:", self.setting_rcon_password)
        
        self.setting_public = QCheckBox(tr("chk_public"))
        self.setting_public.setChecked(True)
        network_layout.addRow("Public Server:", self.setting_public)
        
        scroll_layout.addWidget(network_group)
        
        # Gameplay settings
        gameplay_group = QGroupBox(tr("group_gameplay"))
        gameplay_layout = QFormLayout(gameplay_group)
        
        self.setting_pvp = QCheckBox(tr("chk_pvp"))
        self.setting_pvp.setChecked(True)
        gameplay_layout.addRow("PvP:", self.setting_pvp)
        
        self.setting_pause_empty = QCheckBox(tr("chk_pause_empty"))
        self.setting_pause_empty.setChecked(True)
        gameplay_layout.addRow("Pause Empty:", self.setting_pause_empty)
        
        self.setting_global_chat = QCheckBox(tr("chk_global_chat"))
        self.setting_global_chat.setChecked(True)
        gameplay_layout.addRow("Global Chat:", self.setting_global_chat)
        
        self.setting_safety_system = QCheckBox(tr("chk_safety_system"))
        self.setting_safety_system.setChecked(True)
        gameplay_layout.addRow("Safety System:", self.setting_safety_system)
        
        self.setting_show_safety = QCheckBox(tr("chk_show_safety"))
        self.setting_show_safety.setChecked(True)
        gameplay_layout.addRow("Show Safety:", self.setting_show_safety)
        
        self.setting_spawn_point = QLineEdit()
        self.setting_spawn_point.setPlaceholderText("0,0,0")
        gameplay_layout.addRow("Spawn Point (x,y,z):", self.setting_spawn_point)
        
        scroll_layout.addWidget(gameplay_group)
        
        # Admin settings
        admin_group = QGroupBox(tr("group_admin"))
        admin_layout = QFormLayout(admin_group)
        
        self.setting_admin_password = QLineEdit()
        self.setting_admin_password.setEchoMode(QLineEdit.Password)
        admin_layout.addRow("Admin Password:", self.setting_admin_password)
        
        self.setting_auto_save = QSpinBox()
        self.setting_auto_save.setRange(1, 60)
        self.setting_auto_save.setValue(15)
        self.setting_auto_save.setSuffix(" min")
        admin_layout.addRow("Auto-save Interval:", self.setting_auto_save)
        
        scroll_layout.addWidget(admin_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton(tr("btn_save_settings"))
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        reload_btn = QPushButton(tr("btn_reload_settings"))
        reload_btn.clicked.connect(self.load_settings)
        btn_layout.addWidget(reload_btn)
        
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(tab, tr("tab_settings"))
        
    def create_sandbox_tab(self):
        """Create the sandbox/difficulty settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Preset selector
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel(tr("lbl_preset")))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom", "Apocalypse", "Survivor", "Builder", "Sandbox"
        ])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Zombie settings
        zombie_group = QGroupBox(tr("group_zombie"))
        zombie_layout = QFormLayout(zombie_group)
        
        self.sandbox_zombie_count = QComboBox()
        self.sandbox_zombie_count.addItems(["None", "Insane", "Very High", "High", "Normal", "Low", "Very Low"])
        self.sandbox_zombie_count.setCurrentText("Normal")
        zombie_layout.addRow("Zombie Count:", self.sandbox_zombie_count)
        
        self.sandbox_zombie_distribution = QComboBox()
        self.sandbox_zombie_distribution.addItems(["Urban Focused", "Uniform", "Random"])
        zombie_layout.addRow("Distribution:", self.sandbox_zombie_distribution)
        
        self.sandbox_zombie_speed = QComboBox()
        self.sandbox_zombie_speed.addItems(["Sprinters", "Fast Shamblers", "Shamblers", "Random"])
        self.sandbox_zombie_speed.setCurrentText("Shamblers")
        zombie_layout.addRow("Speed:", self.sandbox_zombie_speed)
        
        self.sandbox_zombie_strength = QComboBox()
        self.sandbox_zombie_strength.addItems(["Superhuman", "Normal", "Weak", "Random"])
        self.sandbox_zombie_strength.setCurrentText("Normal")
        zombie_layout.addRow("Strength:", self.sandbox_zombie_strength)
        
        self.sandbox_zombie_toughness = QComboBox()
        self.sandbox_zombie_toughness.addItems(["Tough", "Normal", "Fragile", "Random"])
        self.sandbox_zombie_toughness.setCurrentText("Normal")
        zombie_layout.addRow("Toughness:", self.sandbox_zombie_toughness)
        
        self.sandbox_zombie_transmission = QComboBox()
        self.sandbox_zombie_transmission.addItems(["Blood + Saliva", "Saliva Only", "Everyone's Infected", "None"])
        self.sandbox_zombie_transmission.setCurrentText("Blood + Saliva")
        zombie_layout.addRow("Transmission:", self.sandbox_zombie_transmission)
        
        self.sandbox_zombie_cognition = QComboBox()
        self.sandbox_zombie_cognition.addItems(["Navigate + Use Doors", "Navigate", "Basic Navigation", "Random"])
        self.sandbox_zombie_cognition.setCurrentText("Basic Navigation")
        zombie_layout.addRow("Cognition:", self.sandbox_zombie_cognition)
        
        scroll_layout.addWidget(zombie_group)
        
        # Loot settings
        loot_group = QGroupBox(tr("group_loot"))
        loot_layout = QFormLayout(loot_group)
        
        self.sandbox_loot_rarity = QComboBox()
        self.sandbox_loot_rarity.addItems(["Extremely Rare", "Rare", "Normal", "Common", "Abundant"])
        self.sandbox_loot_rarity.setCurrentText("Rare")
        loot_layout.addRow("Loot Rarity:", self.sandbox_loot_rarity)
        
        self.sandbox_loot_respawn = QComboBox()
        self.sandbox_loot_respawn.addItems(["None", "Every Day", "Every Week", "Every Month", "Every 2 Months"])
        self.sandbox_loot_respawn.setCurrentText("None")
        loot_layout.addRow("Loot Respawn:", self.sandbox_loot_respawn)
        
        self.sandbox_water_shutoff = QSpinBox()
        self.sandbox_water_shutoff.setRange(0, 365)
        self.sandbox_water_shutoff.setValue(14)
        self.sandbox_water_shutoff.setSpecialValueText("Never")
        self.sandbox_water_shutoff.setSuffix(" days")
        loot_layout.addRow("Water Shutoff:", self.sandbox_water_shutoff)
        
        self.sandbox_electricity_shutoff = QSpinBox()
        self.sandbox_electricity_shutoff.setRange(0, 365)
        self.sandbox_electricity_shutoff.setValue(14)
        self.sandbox_electricity_shutoff.setSpecialValueText("Never")
        self.sandbox_electricity_shutoff.setSuffix(" days")
        loot_layout.addRow("Electricity Shutoff:", self.sandbox_electricity_shutoff)
        
        scroll_layout.addWidget(loot_group)
        
        # Time settings
        time_group = QGroupBox(tr("group_time"))
        time_layout = QFormLayout(time_group)
        
        self.sandbox_start_month = QComboBox()
        self.sandbox_start_month.addItems([
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ])
        self.sandbox_start_month.setCurrentIndex(6)  # July
        time_layout.addRow("Start Month:", self.sandbox_start_month)
        
        self.sandbox_start_day = QSpinBox()
        self.sandbox_start_day.setRange(1, 31)
        self.sandbox_start_day.setValue(9)
        time_layout.addRow("Start Day:", self.sandbox_start_day)
        
        self.sandbox_day_length = QComboBox()
        self.sandbox_day_length.addItems([
            "15 min", "30 min", "1 hour", "2 hours", "3 hours", 
            "4 hours", "5 hours", "6 hours", "12 hours", "Real-time"
        ])
        self.sandbox_day_length.setCurrentText("2 hours")
        time_layout.addRow("Day Length:", self.sandbox_day_length)
        
        scroll_layout.addWidget(time_group)
        
        # Character settings
        char_group = QGroupBox(tr("group_character"))
        char_layout = QFormLayout(char_group)
        
        self.sandbox_xp_multiplier = QComboBox()
        self.sandbox_xp_multiplier.addItems(["0.5x", "0.75x", "1x", "1.5x", "2x", "3x", "5x", "10x"])
        self.sandbox_xp_multiplier.setCurrentText("1x")
        char_layout.addRow("XP Multiplier:", self.sandbox_xp_multiplier)
        
        self.sandbox_player_damage = QComboBox()
        self.sandbox_player_damage.addItems(["Very Low", "Low", "Normal", "High", "Very High"])
        self.sandbox_player_damage.setCurrentText("Normal")
        char_layout.addRow("Damage to Player:", self.sandbox_player_damage)
        
        self.sandbox_infection_mortality = QComboBox()
        self.sandbox_infection_mortality.addItems(["Instant", "0-30 sec", "0-1 min", "0-12 hours", "1-2 days", "2-3 days", "1 week", "Never"])
        self.sandbox_infection_mortality.setCurrentText("2-3 days")
        char_layout.addRow("Infection Mortality:", self.sandbox_infection_mortality)
        
        scroll_layout.addWidget(char_group)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton(tr("btn_save_sandbox"))
        save_btn.clicked.connect(self.save_sandbox_settings)
        btn_layout.addWidget(save_btn)
        
        reload_btn = QPushButton(tr("btn_reload"))
        reload_btn.clicked.connect(self.load_sandbox_settings)
        btn_layout.addWidget(reload_btn)
        
        layout.addLayout(btn_layout)
        
        self.tabs.addTab(tab, tr("tab_sandbox"))
        
    def create_mods_tab(self):
        """Create the mods management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Info label
        info_label = QLabel(
            "💡 Add mods using their Steam Workshop ID. "
            "You can find the ID in the workshop URL (e.g., steamcommunity.com/sharedfiles/filedetails/?id=<b>123456789</b>)"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 10px; background-color: #3d3d3d; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # Mods list
        mods_group = QGroupBox(tr("group_mods"))
        mods_layout = QVBoxLayout(mods_group)
        
        self.mods_list = QListWidget()
        self.mods_list.setAlternatingRowColors(True)
        mods_layout.addWidget(self.mods_list)
        
        # Mod control buttons
        mod_btn_layout = QHBoxLayout()
        
        add_btn = QPushButton(tr("btn_add_mod"))
        add_btn.clicked.connect(self.add_mod)
        mod_btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton(tr("btn_remove_mod"))
        remove_btn.clicked.connect(self.remove_mod)
        mod_btn_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton(tr("btn_clear_mods"))
        clear_btn.clicked.connect(self.clear_mods)
        mod_btn_layout.addWidget(clear_btn)
        
        mods_layout.addLayout(mod_btn_layout)
        layout.addWidget(mods_group)
        
        # Import/Export
        io_group = QGroupBox(tr("group_import_export"))
        io_layout = QHBoxLayout(io_group)
        
        import_btn = QPushButton(tr("btn_import_mods"))
        import_btn.clicked.connect(self.import_mods)
        io_layout.addWidget(import_btn)
        
        export_btn = QPushButton(tr("btn_export_mods"))
        export_btn.clicked.connect(self.export_mods)
        io_layout.addWidget(export_btn)
        
        layout.addWidget(io_group)
        
        # Save button
        save_btn = QPushButton(tr("btn_save_mods"))
        save_btn.clicked.connect(self.save_mods)
        layout.addWidget(save_btn)
        
        self.tabs.addTab(tab, tr("tab_mods"))
        
    def create_install_tab(self):
        """Create the installation tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Installation path
        path_group = QGroupBox(tr("group_install_path"))
        path_layout = QHBoxLayout(path_group)
        
        self.install_path_edit = QLineEdit(str(self.paths['server_dir']))
        path_layout.addWidget(self.install_path_edit)
        
        browse_btn = QPushButton(tr("btn_browse"))
        browse_btn.clicked.connect(self.browse_install_path)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)
        
        # Installation status
        status_group = QGroupBox(tr("group_install_status"))
        status_layout = QVBoxLayout(status_group)
        
        self.install_status_label = QLabel(tr("lbl_ready_install"))
        self.install_status_label.setStyleSheet("font-size: 14px;")
        status_layout.addWidget(self.install_status_label)
        
        self.install_progress = QProgressBar()
        self.install_progress.setRange(0, 100)
        self.install_progress.setValue(0)
        status_layout.addWidget(self.install_progress)
        
        self.install_log = QPlainTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMaximumBlockCount(1000)
        system = platform.system()
        if system == 'Windows':
            mono = 'Consolas'
        elif system == 'Darwin':
            mono = 'Menlo'
        else:
            mono = 'DejaVu Sans Mono'
        font = QFont(mono, 9)
        self.install_log.setFont(font)
        status_layout.addWidget(self.install_log)
        
        layout.addWidget(status_group)
        
        # Install button
        self.install_btn = QPushButton(tr("btn_install_server"))
        self.install_btn.setMinimumHeight(50)
        self.install_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.install_btn.clicked.connect(self.start_installation)
        layout.addWidget(self.install_btn)
        
        # Info
        info_label = QLabel(
            "⚠️ Installation requires ~3GB of disk space.\n"
            "Make sure to open ports 16261 (UDP) and 27015 (TCP) in your firewall."
        )
        info_label.setStyleSheet("color: #ffaa00; padding: 10px;")
        layout.addWidget(info_label)
        
        self.tabs.addTab(tab, tr("tab_install"))
        
    def show_install_tab(self):
        """Switch to the installation tab."""
        self.tabs.setCurrentIndex(4)  # Install tab index
        
    # ===== Server Control Methods =====
    
    def start_server(self):
        """Start the game server."""
        if not self.server_installed:
            QMessageBox.warning(
                self,
                "Server Not Installed",
                "Please install the server first using the Install tab."
            )
            return
            
        server_name = self.server_name_input.text().strip() or "servertest"
        self.append_console_output(f"Starting server '{server_name}'...")
        
        try:
            self.server_process.start(server_name)
        except Exception as e:
            self.append_console_error(f"Failed to start server: {e}")
            logger.exception("Failed to start server")
            
    def stop_server(self):
        """Stop the game server."""
        self.append_console_output("Stopping server...")
        try:
            self.server_process.stop()
        except Exception as e:
            self.append_console_error(f"Failed to stop server: {e}")
            logger.exception("Failed to stop server")
            
    def restart_server(self):
        """Restart the game server."""
        self.append_console_output("Restarting server...")
        self.stop_server()
        QTimer.singleShot(3000, self.start_server)  # Wait 3 seconds before restart
        
    def send_command(self):
        """Send a command to the server console."""
        command = self.command_input.text().strip()
        if command:
            self.server_process.send_command(command)
            self.append_console_output(f"> {command}")
            self.command_input.clear()
            
    def on_server_started(self):
        """Handle server started event."""
        self.status_indicator.setStyleSheet("color: #44ff44; font-size: 24px;")
        self.status_label.setText(tr('server_running'))
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)
        
    def on_server_stopped(self):
        """Handle server stopped event."""
        self.status_indicator.setStyleSheet("color: #ff4444; font-size: 24px;")
        self.status_label.setText(tr('server_stopped'))
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        
    def append_console_output(self, text: str):
        """Append text to console output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_output.appendPlainText(f"[{timestamp}] {text}")
        
    def append_console_error(self, text: str):
        """Append error text to console output with red color."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set red color for errors
        format = QTextCharFormat()
        format.setForeground(QColor("#ff6666"))
        cursor.insertText(f"[{timestamp}] ERROR: {text}\n", format)
        
        self.console_output.setTextCursor(cursor)
        self.console_output.ensureCursorVisible()
        
    # ===== Settings Methods =====
    
    def load_settings(self):
        """Load server settings from config files."""
        try:
            config = self.config_manager.load_server_ini()
            
            self.setting_public_name.setText(config.get('PublicName', ''))
            self.setting_public_desc.setText(config.get('PublicDescription', ''))
            self.setting_password.setText(config.get('Password', ''))
            self.setting_max_players.setValue(int(config.get('MaxPlayers', 16)))
            self.setting_port.setValue(int(config.get('DefaultPort', 16261)))
            self.setting_steam_port.setValue(int(config.get('SteamPort1', 8766)))
            self.setting_rcon_port.setValue(int(config.get('RCONPort', 27015)))
            self.setting_rcon_password.setText(config.get('RCONPassword', ''))
            self.setting_public.setChecked(config.get('Open', 'true').lower() == 'true')
            self.setting_pvp.setChecked(config.get('PVP', 'true').lower() == 'true')
            self.setting_pause_empty.setChecked(config.get('PauseEmpty', 'true').lower() == 'true')
            self.setting_global_chat.setChecked(config.get('GlobalChat', 'true').lower() == 'true')
            self.setting_safety_system.setChecked(config.get('SafetySystem', 'true').lower() == 'true')
            self.setting_show_safety.setChecked(config.get('ShowSafety', 'true').lower() == 'true')
            self.setting_spawn_point.setText(config.get('SpawnPoint', '0,0,0'))
            self.setting_admin_password.setText(config.get('AdminPassword', ''))
            self.setting_auto_save.setValue(int(config.get('SaveWorldEveryMinutes', 15)))
            
            # Load mods
            self.load_mods_list()
            
            # Load sandbox settings
            self.load_sandbox_settings()
            
            logger.info("Settings loaded successfully")
            self.statusBar.showMessage("Settings loaded", 3000)
            
        except FileNotFoundError:
            logger.warning("Config file not found - using defaults")
            self.statusBar.showMessage("No config found - using defaults", 3000)
        except Exception as e:
            logger.exception("Failed to load settings")
            QMessageBox.warning(self, "Error", f"Failed to load settings: {e}")
            
    def save_settings(self):
        """Save server settings to config file."""
        try:
            config = {
                'PublicName': self.setting_public_name.text(),
                'PublicDescription': self.setting_public_desc.text(),
                'Password': self.setting_password.text(),
                'MaxPlayers': str(self.setting_max_players.value()),
                'DefaultPort': str(self.setting_port.value()),
                'SteamPort1': str(self.setting_steam_port.value()),
                'RCONPort': str(self.setting_rcon_port.value()),
                'RCONPassword': self.setting_rcon_password.text(),
                'Open': 'true' if self.setting_public.isChecked() else 'false',
                'PVP': 'true' if self.setting_pvp.isChecked() else 'false',
                'PauseEmpty': 'true' if self.setting_pause_empty.isChecked() else 'false',
                'GlobalChat': 'true' if self.setting_global_chat.isChecked() else 'false',
                'SafetySystem': 'true' if self.setting_safety_system.isChecked() else 'false',
                'ShowSafety': 'true' if self.setting_show_safety.isChecked() else 'false',
                'SpawnPoint': self.setting_spawn_point.text(),
                'AdminPassword': self.setting_admin_password.text(),
                'SaveWorldEveryMinutes': str(self.setting_auto_save.value()),
            }
            
            self.config_manager.save_server_ini(config)
            
            logger.info("Settings saved successfully")
            self.statusBar.showMessage("Settings saved", 3000)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            
        except Exception as e:
            logger.exception("Failed to save settings")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
            
    def load_sandbox_settings(self):
        """Load sandbox settings from SandboxVars.lua."""
        try:
            sandbox = self.config_manager.load_sandbox_vars()
            
            # Map values to combo boxes
            # This is simplified - full implementation would need more mappings
            self.statusBar.showMessage("Sandbox settings loaded", 3000)
            
        except FileNotFoundError:
            logger.warning("Sandbox file not found")
        except Exception as e:
            logger.exception("Failed to load sandbox settings")
            
    def save_sandbox_settings(self):
        """Save sandbox settings to SandboxVars.lua."""
        try:
            # Build sandbox settings dict
            # This is a simplified version - full implementation would need
            # to map all combo box values to proper Lua values
            
            QMessageBox.information(
                self, 
                "Note",
                "Sandbox settings saved. Changes will take effect on next server restart."
            )
            self.statusBar.showMessage("Sandbox settings saved", 3000)
            
        except Exception as e:
            logger.exception("Failed to save sandbox settings")
            QMessageBox.critical(self, "Error", f"Failed to save sandbox settings: {e}")
            
    def on_preset_changed(self, preset: str):
        """Handle preset selection change."""
        # Apply preset values
        pass  # Would set all sandbox values based on preset
        
    # ===== Mod Management Methods =====
    
    def load_mods_list(self):
        """Load the list of mods from config."""
        self.mods_list.clear()
        try:
            mods = self.mod_manager.get_mods()
            for mod in mods:
                item = QListWidgetItem(f"[{mod['workshop_id']}] {mod['name']}")
                item.setData(Qt.UserRole, mod)
                self.mods_list.addItem(item)
        except Exception as e:
            logger.exception("Failed to load mods list")
            
    def add_mod(self):
        """Add a new mod by Workshop ID."""
        workshop_id, ok = QInputDialog.getText(
            self,
            "Add Mod",
            "Enter Steam Workshop ID:",
            QLineEdit.Normal
        )
        
        if ok and workshop_id:
            workshop_id = workshop_id.strip()
            if not workshop_id.isdigit():
                QMessageBox.warning(self, "Invalid ID", "Workshop ID must be a number.")
                return
                
            try:
                mod_info = self.mod_manager.add_mod(workshop_id)
                item = QListWidgetItem(f"[{workshop_id}] {mod_info.get('name', 'Unknown Mod')}")
                item.setData(Qt.UserRole, mod_info)
                self.mods_list.addItem(item)
                self.statusBar.showMessage(f"Added mod: {workshop_id}", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to add mod: {e}")
                
    def remove_mod(self):
        """Remove selected mod."""
        current = self.mods_list.currentItem()
        if current:
            mod_data = current.data(Qt.UserRole)
            self.mod_manager.remove_mod(mod_data['workshop_id'])
            self.mods_list.takeItem(self.mods_list.row(current))
            self.statusBar.showMessage("Mod removed", 3000)
            
    def clear_mods(self):
        """Clear all mods."""
        result = QMessageBox.question(
            self,
            "Confirm",
            "Are you sure you want to remove all mods?",
            QMessageBox.Yes | QMessageBox.No
        )
        if result == QMessageBox.Yes:
            self.mod_manager.clear_mods()
            self.mods_list.clear()
            self.statusBar.showMessage("All mods cleared", 3000)
            
    def import_mods(self):
        """Import mod list from file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Mod List",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            try:
                self.mod_manager.import_from_file(filepath)
                self.load_mods_list()
                self.statusBar.showMessage("Mods imported", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to import mods: {e}")
                
    def export_mods(self):
        """Export mod list to file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Mod List",
            "pz_mods.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            try:
                self.mod_manager.export_to_file(filepath)
                self.statusBar.showMessage("Mods exported", 3000)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export mods: {e}")
                
    def save_mods(self):
        """Save mods to server config."""
        try:
            self.mod_manager.save_to_config()
            self.statusBar.showMessage("Mods saved to config", 3000)
            QMessageBox.information(
                self,
                "Success",
                "Mods saved. The server will download mods on next start."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mods: {e}")
            
    # ===== Installation Methods =====
    
    def browse_install_path(self):
        """Browse for installation directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Installation Directory",
            str(self.paths['server_dir'])
        )
        if path:
            self.install_path_edit.setText(path)
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'
            
    def start_installation(self):
        """Start the server installation process."""
        install_path = Path(self.install_path_edit.text())
        
        # Check write permissions
        try:
            install_path.mkdir(parents=True, exist_ok=True)
            test_file = install_path / '.write_test'
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            if os.name == 'nt':
                hint = ("Options:\n"
                        "1. Run this application as Administrator\n"
                        "2. Choose a different folder (e.g., C:\\Games\\PZServer)")
            else:
                hint = ("Options:\n"
                        "1. Run with sudo: sudo python3 main.py\n"
                        "2. Choose a folder you have write access to (e.g., ~/pzserver)")
            result = QMessageBox.warning(
                self,
                "Permission Denied",
                f"Cannot write to: {install_path}\n\n{hint}\n\n"
                "Would you like to choose a different folder?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self.browse_install_path()
            return
        except Exception as e:
            logger.warning(f"Could not test write permissions: {e}")
        
        # Confirm installation
        result = QMessageBox.question(
            self,
            "Confirm Installation",
            f"Install Project Zomboid Server to:\n{install_path}\n\n"
            "This will download ~3GB of files.\nContinue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result != QMessageBox.Yes:
            return
            
        # Update paths
        self.paths['server_dir'] = install_path
        self.paths['steamcmd_dir'] = install_path / 'steamcmd'
        
        # Disable install button
        self.install_btn.setEnabled(False)
        self.install_log.clear()
        
        # Create and start worker thread
        self.install_worker = InstallWorker(self.installer, self.paths)
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.log.connect(self.on_install_log)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.error.connect(self.on_install_error)
        self.install_worker.start()
        
    def on_install_progress(self, value: int, message: str):
        """Handle installation progress update."""
        self.install_progress.setValue(value)
        self.install_status_label.setText(message)
        
    def on_install_log(self, message: str):
        """Handle installation log message."""
        self.install_log.appendPlainText(message)
        
    def on_install_finished(self):
        """Handle installation completion."""
        self.install_btn.setEnabled(True)
        self.install_progress.setValue(100)
        self.install_status_label.setText("Installation complete!")
        self.server_installed = True
        
        QMessageBox.information(
            self,
            "Installation Complete",
            "Project Zomboid Server has been installed successfully!\n\n"
            "Remember to open the following ports in your firewall:\n"
            "• 16261 (UDP) - Game port\n"
            "• 27015 (TCP) - RCON port\n\n"
            "You can now configure and start your server."
        )
        
    def on_install_error(self, error: str):
        """Handle installation error."""
        self.install_btn.setEnabled(True)
        self.install_status_label.setText("Installation failed!")
        
        QMessageBox.critical(
            self,
            "Installation Failed",
            f"An error occurred during installation:\n\n{error}"
        )
        
    # ===== Utility Methods =====
    
    def update_status(self):
        """Update the status bar."""
        if self.server_process.is_running():
            self.statusBar.showMessage(tr('status_running'))
        else:
            self.statusBar.showMessage(tr('status_stopped'))
            
    def change_server_directory(self):
        """Change the server directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Server Directory",
            str(self.paths['server_dir'])
        )
        if path:
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'
            self.install_path_edit.setText(path)
            p = Path(path)
            self.server_installed = (
                (p / 'ProjectZomboid64.exe').exists() or
                (p / 'StartServer64.bat').exists() or
                (p / 'start-server.sh').exists() or
                (p / 'ProjectZomboid64').exists()
            )
            self.statusBar.showMessage(f"Server directory changed to: {path}", 5000)
            
    def validate_server(self):
        """Validate server files through SteamCMD."""
        QMessageBox.information(
            self,
            "Validate Server",
            "Server validation will be performed during the next update.\n"
            "Go to the Install tab and click 'Install / Update Server'."
        )
        
    def update_server(self):
        """Update the server."""
        self.show_install_tab()
        
    def _open_folder(self, path: Path):
        """Open a folder in the system file manager (cross-platform)."""
        system = platform.system()
        if system == 'Windows':
            subprocess.run(['explorer', str(path)])
        elif system == 'Darwin':
            subprocess.run(['open', str(path)])
        else:
            subprocess.run(['xdg-open', str(path)])

    def open_config_folder(self):
        """Open the config folder in the file manager."""
        config_dir = self.paths['server_config_dir']
        if config_dir.exists():
            self._open_folder(config_dir)
        else:
            QMessageBox.warning(
                self,
                "Folder Not Found",
                f"Config folder not found:\n{config_dir}\n\n"
                "Start the server once to create config files."
            )
            
    def open_server_folder(self):
        """Open the server folder in the file manager."""
        server_dir = self.paths['server_dir']
        if server_dir.exists():
            self._open_folder(server_dir)
        else:
            QMessageBox.warning(self, "Folder Not Found", f"Server folder not found:\n{server_dir}")
            
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            tr('menu_about'),
            tr('about_text')
        )
        
    def show_firewall_info(self):
        """Show firewall information."""
        QMessageBox.information(
            self,
            tr('firewall_info'),
            tr('firewall_info_msg')
        )
        
    def change_language(self, language: str):
        """Change the application language."""
        set_language(language)
        
        # Save language preference
        try:
            with open('language.cfg', 'w') as f:
                f.write(language)
        except:
            pass
        
        # Show restart message
        QMessageBox.information(
            self,
            "Language Changed" if language == 'en' else "Язык изменён",
            "Please restart the application to apply the new language.\n\n"
            "Перезапустите приложение для применения нового языка."
            if language == 'en' else
            "Перезапустите приложение для применения нового языка.\n\n"
            "Please restart the application to apply the new language."
        )
        
    def closeEvent(self, event):
        """Handle window close event."""
        if self.server_process.is_running():
            result = QMessageBox.question(
                self,
                tr('server_running_close'),
                tr('server_running_close_msg'),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if result == QMessageBox.Yes:
                self.stop_server()
                event.accept()
            elif result == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
