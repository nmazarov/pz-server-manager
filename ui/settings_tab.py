#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Tab Mixin for PZ Server Manager.
Handles server network, security, chat, voice, and gameplay settings in servertest.ini.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QFormLayout, QScrollArea,
    QMessageBox
)

from translations import tr
from ui.dialogs import _b

logger = logging.getLogger(__name__)

_DROP_DEATH = [('drop_everything', 1), ('drop_equipped', 2), ('drop_nothing', 3)]


def _safe_int(val, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _combo_items(mapping: list) -> list:
    return [tr(k) for k, _ in mapping]


def _combo_index(mapping: list, value) -> int:
    for i, (_, v) in enumerate(mapping):
        if v == value:
            return i
    return 0


def _combo_value(mapping: list, idx: int, default=None):
    if 0 <= idx < len(mapping):
        return mapping[idx][1]
    return default


class SettingsTabMixin:
    """Mixin for the Server Settings (INI) tab."""

    def create_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 10, 10, 10)

        cols = QHBoxLayout()
        cols.setSpacing(14)

        left_col = QVBoxLayout()
        left_col.setSpacing(12)

        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        LABEL_W = 220

        def _fmt_form(form):
            form.setContentsMargins(12, 12, 12, 12)
            form.setSpacing(8)
            form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)

        def _add_field(form, label_text, ctl, w=280):
            ctl.setMaximumWidth(w)
            lbl = QLabel(label_text)
            lbl.setFixedWidth(LABEL_W)
            form.addRow(lbl, ctl)

        def _add_chk(form, chk):
            form.addRow(chk)

        # ── 1. Basic (Left) ──
        g_basic = QGroupBox(tr('group_basic'))
        f = QFormLayout(g_basic)
        _fmt_form(f)

        self.setting_public_name = QLineEdit()
        self.setting_public_name.setPlaceholderText('My Zomboid Server')
        _add_field(f, tr('lbl_server_name'), self.setting_public_name, 280)

        self.setting_public_desc = QLineEdit()
        self.setting_public_desc.setPlaceholderText('A Project Zomboid server')
        _add_field(f, tr('lbl_description'), self.setting_public_desc, 280)

        self.setting_password = QLineEdit()
        self.setting_password.setEchoMode(QLineEdit.Password)
        self.setting_password.setPlaceholderText(tr('ph_empty_no_password'))
        _add_field(f, tr('lbl_password'), self.setting_password, 280)

        self.setting_max_players = QSpinBox()
        self.setting_max_players.setRange(1, 100)
        self.setting_max_players.setValue(16)
        _add_field(f, tr('lbl_max_players'), self.setting_max_players, 140)

        self.setting_map = QLineEdit('Muldraugh, KY')
        self.setting_map.setPlaceholderText(tr('ph_map'))
        _add_field(f, tr('lbl_map'), self.setting_map, 280)

        self.setting_welcome_msg = QLineEdit()
        self.setting_welcome_msg.setPlaceholderText(tr('ph_welcome_msg'))
        _add_field(f, tr('lbl_welcome_msg'), self.setting_welcome_msg, 280)

        left_col.addWidget(g_basic)

        # ── 2. Gameplay (Left) ──
        g_gameplay = QGroupBox(tr('group_gameplay'))
        f = QFormLayout(g_gameplay)
        _fmt_form(f)

        self.setting_pvp = QCheckBox(tr('chk_pvp'))
        self.setting_pvp.setChecked(True)
        _add_chk(f, self.setting_pvp)

        self.setting_pause_empty = QCheckBox(tr('chk_pause_empty'))
        self.setting_pause_empty.setChecked(True)
        _add_chk(f, self.setting_pause_empty)

        self.setting_allow_coop = QCheckBox(tr('chk_allow_coop'))
        self.setting_allow_coop.setChecked(True)
        _add_chk(f, self.setting_allow_coop)

        self.setting_sleep_allowed = QCheckBox(tr('chk_sleep_allowed'))
        self.setting_sleep_allowed.setChecked(False)
        _add_chk(f, self.setting_sleep_allowed)

        self.setting_sleep_needed = QCheckBox(tr('chk_sleep_needed'))
        self.setting_sleep_needed.setChecked(False)
        _add_chk(f, self.setting_sleep_needed)

        self.setting_announce_death = QCheckBox(tr('chk_announce_death'))
        self.setting_announce_death.setChecked(False)
        _add_chk(f, self.setting_announce_death)

        self.setting_no_fire = QCheckBox(tr('chk_no_fire'))
        self.setting_no_fire.setChecked(False)
        _add_chk(f, self.setting_no_fire)

        self.setting_allow_destruction = QCheckBox(tr('chk_allow_destruction'))
        self.setting_allow_destruction.setChecked(True)
        _add_chk(f, self.setting_allow_destruction)

        self.setting_drop_on_death = QComboBox()
        self.setting_drop_on_death.addItems(_combo_items(_DROP_DEATH))
        self.setting_drop_on_death.setCurrentIndex(1)
        _add_field(f, tr('lbl_drop_on_death'), self.setting_drop_on_death, 240)

        self.setting_spawn_point = QLineEdit()
        self.setting_spawn_point.setPlaceholderText('0,0,0')
        _add_field(f, tr('lbl_spawn_point'), self.setting_spawn_point, 240)

        left_col.addWidget(g_gameplay)

        # ── 3. Safehouses (Left) ──
        g_safehouse = QGroupBox(tr('group_safehouse'))
        f = QFormLayout(g_safehouse)
        _fmt_form(f)

        self.setting_player_safehouse = QCheckBox(tr('chk_player_safehouse'))
        _add_chk(f, self.setting_player_safehouse)

        self.setting_admin_safehouse = QCheckBox(tr('chk_admin_safehouse'))
        _add_chk(f, self.setting_admin_safehouse)

        self.setting_safehouse_trespassing = QCheckBox(tr('chk_safehouse_trespassing'))
        _add_chk(f, self.setting_safehouse_trespassing)

        self.setting_safehouse_fire = QCheckBox(tr('chk_safehouse_fire'))
        _add_chk(f, self.setting_safehouse_fire)

        self.setting_safehouse_loot = QCheckBox(tr('chk_safehouse_loot'))
        _add_chk(f, self.setting_safehouse_loot)

        self.setting_safehouse_respawn = QCheckBox(tr('chk_safehouse_respawn'))
        _add_chk(f, self.setting_safehouse_respawn)

        left_col.addWidget(g_safehouse)
        left_col.addStretch()

        # ── 4. Network (Right) ──
        g_network = QGroupBox(tr('group_network'))
        f = QFormLayout(g_network)
        _fmt_form(f)

        self.setting_port = QSpinBox()
        self.setting_port.setRange(1024, 65535)
        self.setting_port.setValue(16261)
        _add_field(f, tr('lbl_game_port'), self.setting_port, 140)

        self.setting_udp_port = QSpinBox()
        self.setting_udp_port.setRange(1024, 65535)
        self.setting_udp_port.setValue(16262)
        _add_field(f, tr('lbl_direct_port'), self.setting_udp_port, 140)

        self.setting_steam_port = QSpinBox()
        self.setting_steam_port.setRange(1024, 65535)
        self.setting_steam_port.setValue(8766)
        _add_field(f, tr('lbl_steam_port1'), self.setting_steam_port, 140)

        self.setting_steam_port2 = QSpinBox()
        self.setting_steam_port2.setRange(1024, 65535)
        self.setting_steam_port2.setValue(8767)
        _add_field(f, tr('lbl_steam_port2'), self.setting_steam_port2, 140)

        self.setting_rcon_port = QSpinBox()
        self.setting_rcon_port.setRange(1024, 65535)
        self.setting_rcon_port.setValue(27015)
        _add_field(f, tr('lbl_rcon_port'), self.setting_rcon_port, 140)

        self.setting_rcon_password = QLineEdit()
        self.setting_rcon_password.setPlaceholderText('RCON password')
        _add_field(f, tr('lbl_rcon_password'), self.setting_rcon_password, 280)

        self.setting_public = QCheckBox(tr('chk_public'))
        self.setting_public.setChecked(True)
        _add_chk(f, self.setting_public)

        right_col.addWidget(g_network)

        # ── 5. Security (Right) ──
        g_security = QGroupBox(tr('group_security'))
        f = QFormLayout(g_security)
        _fmt_form(f)

        self.setting_secure_join = QCheckBox(tr('chk_secure_join'))
        _add_chk(f, self.setting_secure_join)

        self.setting_non_ascii = QCheckBox(tr('chk_non_ascii'))
        _add_chk(f, self.setting_non_ascii)

        self.setting_auto_whitelist = QCheckBox(tr('chk_auto_whitelist'))
        _add_chk(f, self.setting_auto_whitelist)

        self.setting_max_accounts = QSpinBox()
        self.setting_max_accounts.setRange(0, 100)
        self.setting_max_accounts.setValue(0)
        self.setting_max_accounts.setSpecialValueText(tr('unlimited'))
        _add_field(f, tr('lbl_max_accounts'), self.setting_max_accounts, 140)

        self.setting_speed_limit = QSpinBox()
        self.setting_speed_limit.setRange(0, 250)
        self.setting_speed_limit.setValue(70)
        self.setting_speed_limit.setSuffix(' km/h')
        _add_field(f, tr('lbl_speed_limit'), self.setting_speed_limit, 140)

        right_col.addWidget(g_security)

        # ── 6. Admin (Right) ──
        g_admin = QGroupBox(tr('group_admin'))
        f = QFormLayout(g_admin)
        _fmt_form(f)

        self.setting_admin_password = QLineEdit()
        self.setting_admin_password.setEchoMode(QLineEdit.Password)
        _add_field(f, tr('lbl_admin_password'), self.setting_admin_password, 280)

        self.setting_auto_save = QSpinBox()
        self.setting_auto_save.setRange(1, 60)
        self.setting_auto_save.setValue(15)
        self.setting_auto_save.setSuffix(' min')
        _add_field(f, tr('lbl_auto_save'), self.setting_auto_save, 140)

        self.setting_backups_count = QSpinBox()
        self.setting_backups_count.setRange(0, 50)
        self.setting_backups_count.setValue(5)
        _add_field(f, tr('lbl_backups_count'), self.setting_backups_count, 140)

        self.setting_backups_period = QSpinBox()
        self.setting_backups_period.setRange(0, 720)
        self.setting_backups_period.setValue(0)
        self.setting_backups_period.setSpecialValueText('On start')
        self.setting_backups_period.setSuffix(' h')
        _add_field(f, tr('lbl_backups_period'), self.setting_backups_period, 140)

        right_col.addWidget(g_admin)

        # ── 7. Chat & Voice (Right) ──
        g_chat = QGroupBox(tr('group_chat_voice'))
        f = QFormLayout(g_chat)
        _fmt_form(f)

        self.setting_global_chat = QCheckBox(tr('chk_global_chat'))
        self.setting_global_chat.setChecked(True)
        _add_chk(f, self.setting_global_chat)

        self.setting_safety_system = QCheckBox(tr('chk_safety_system'))
        self.setting_safety_system.setChecked(True)
        _add_chk(f, self.setting_safety_system)

        self.setting_show_safety = QCheckBox(tr('chk_show_safety'))
        self.setting_show_safety.setChecked(True)
        _add_chk(f, self.setting_show_safety)

        self.setting_display_username = QCheckBox(tr('chk_display_username'))
        self.setting_display_username.setChecked(True)
        _add_chk(f, self.setting_display_username)

        self.setting_voice_enable = QCheckBox(tr('chk_voice_enable'))
        self.setting_voice_enable.setChecked(True)
        _add_chk(f, self.setting_voice_enable)

        self.setting_voice_3d = QCheckBox(tr('chk_voice_3d'))
        self.setting_voice_3d.setChecked(True)
        _add_chk(f, self.setting_voice_3d)

        self.setting_voice_min = QSpinBox()
        self.setting_voice_min.setRange(1, 500)
        self.setting_voice_min.setValue(10)
        _add_field(f, tr('lbl_voice_min'), self.setting_voice_min, 140)

        self.setting_voice_max = QSpinBox()
        self.setting_voice_max.setRange(10, 10000)
        self.setting_voice_max.setValue(100)
        _add_field(f, tr('lbl_voice_max'), self.setting_voice_max, 140)

        right_col.addWidget(g_chat)
        right_col.addStretch()

        cols.addLayout(left_col, 1)
        cols.addLayout(right_col, 1)
        sl.addLayout(cols)

        scroll.setWidget(sw)
        layout.addWidget(scroll)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addStretch()
        b = QPushButton(tr('btn_save_settings'))
        b.setMinimumHeight(34)
        b.setMinimumWidth(200)
        b.setStyleSheet("background-color: #1e6b3b; color: #ffffff; font-weight: bold; padding: 6px 18px;")
        b.clicked.connect(self.save_settings)
        row.addWidget(b)
        b2 = QPushButton(tr('btn_reload_settings'))
        b2.setMinimumHeight(34)
        b2.setMinimumWidth(180)
        b2.clicked.connect(self.load_settings)
        row.addWidget(b2)
        row.addStretch()
        layout.addLayout(row)

        self.tabs.addTab(tab, tr('tab_settings'))

    def load_settings(self):
        try:
            c = self.config_manager.load_server_ini()

            self.setting_public_name.setText(c.get('PublicName', ''))
            self.setting_public_desc.setText(c.get('PublicDescription', ''))
            self.setting_password.setText(c.get('Password', ''))
            self.setting_max_players.setValue(_safe_int(c.get('MaxPlayers', 16)))
            self.setting_map.setText(c.get('Map', 'Muldraugh, KY'))
            self.setting_welcome_msg.setText(c.get('ServerWelcomeMessage', ''))

            self.setting_port.setValue(_safe_int(c.get('DefaultPort', 16261)))
            self.setting_udp_port.setValue(_safe_int(c.get('UDPPort', 16262)))
            self.setting_steam_port.setValue(_safe_int(c.get('SteamPort1', 8766)))
            self.setting_steam_port2.setValue(_safe_int(c.get('SteamPort2', 8767)))
            self.setting_rcon_port.setValue(_safe_int(c.get('RCONPort', 27015)))
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
                _combo_index(_DROP_DEATH, _safe_int(c.get('DropOnDeath', 1))))
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
            self.setting_voice_min.setValue(_safe_int(c.get('VoiceMinDistance', 10)))
            self.setting_voice_max.setValue(_safe_int(c.get('VoiceMaxDistance', 100)))

            self.setting_secure_join.setChecked(c.get('UseSecureJoin', 'false').lower() == 'true')
            self.setting_non_ascii.setChecked(c.get('AllowNonAsciiUsername', 'false').lower() == 'true')
            self.setting_auto_whitelist.setChecked(
                c.get('AutoCreateUserInWhiteList', 'false').lower() == 'true')
            self.setting_max_accounts.setValue(_safe_int(c.get('MaxAccountsPerUser', 0)))
            self.setting_speed_limit.setValue(_safe_int(c.get('SpeedLimit', 70)))

            self.setting_admin_password.setText(c.get('AdminPassword', ''))
            self.setting_auto_save.setValue(_safe_int(c.get('SaveWorldEveryMinutes', 15)))
            self.setting_backups_count.setValue(_safe_int(c.get('BackupsCount', 5)))
            self.setting_backups_period.setValue(_safe_int(c.get('BackupsPeriod', 0)))

            if hasattr(self, 'load_mods_list'):
                self.load_mods_list()
            if hasattr(self, 'load_sandbox_settings'):
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
