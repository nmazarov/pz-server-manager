#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Install Tab Mixin for PZ Server Manager.
Handles dedicated server installation, Steam beta branch selection,
live installation progress logging, and automatic background update checking.
"""

import logging
import platform
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QProgressBar, QPlainTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QSizePolicy, QButtonGroup, QRadioButton, QFrame,
    QScrollArea
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from translations import tr, get_language
from server_installer import (
    InstallWorker, ServerUpdateCheckerWorker, fetch_available_server_branches
)

logger = logging.getLogger(__name__)


class InstallTabMixin:
    """Mixin for Server installation, Steam updates, and version branch selection."""

    def create_install_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ── Group 1: Installation Directory ──
        g = QGroupBox(tr('group_install_path'))
        pl = QHBoxLayout(g)
        self.install_path_edit = QLineEdit(str(self.paths['server_dir']))
        pl.addWidget(self.install_path_edit)
        b = QPushButton(tr('btn_browse'))
        b.clicked.connect(self.browse_install_path)
        pl.addWidget(b)
        layout.addWidget(g)

        # ── Group 2: Steam Betas & Versions (Compact Steam Table) ──
        g_ver = QGroupBox(tr('group_server_version'))
        vl_ver = QVBoxLayout(g_ver)
        vl_ver.setContentsMargins(8, 8, 8, 8)
        vl_ver.setSpacing(6)

        # Steam table frame
        self.steam_table_frame = QFrame()
        self.steam_table_frame.setObjectName("SteamTableFrame")
        self.steam_table_frame.setMinimumHeight(180)
        self.steam_table_frame.setStyleSheet("""
            QFrame#SteamTableFrame {
                background-color: #171d25;
                border: 1px solid #2a475e;
                border-radius: 5px;
            }
        """)
        table_vbox = QVBoxLayout(self.steam_table_frame)
        table_vbox.setContentsMargins(0, 0, 0, 0)
        table_vbox.setSpacing(0)

        # Table Column Headers
        hdr_frame = QFrame()
        hdr_frame.setFixedHeight(28)
        hdr_frame.setStyleSheet(
            "background-color: #1f2b3b; border-bottom: 1px solid #2a475e; "
            "border-top-left-radius: 4px; border-top-right-radius: 4px;"
        )
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(14, 0, 14, 0)

        lbl_hdr_name = QLabel(tr('col_branch_name_desc'))
        lbl_hdr_name.setStyleSheet("color: #8f98a0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        hdr_layout.addWidget(lbl_hdr_name, 1)

        lbl_hdr_date = QLabel(tr('col_branch_last_update'))
        lbl_hdr_date.setStyleSheet("color: #8f98a0; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        lbl_hdr_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hdr_layout.addWidget(lbl_hdr_date)

        table_vbox.addWidget(hdr_frame)

        # Dynamic rows container
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(1)
        table_vbox.addWidget(self.rows_container)

        vl_ver.addWidget(self.steam_table_frame)

        # Button group and radio registry for exclusive branch selection
        self.branch_button_group = QButtonGroup(tab)
        self.branch_radio_map = {}
        self.current_beta_password = ""

        # Hidden synchronized combo box so existing code still works seamlessly
        self.combo_server_version = QComboBox()
        self.combo_server_version.setVisible(False)
        vl_ver.addWidget(self.combo_server_version)

        # Section: Скрытые версии (Compact single-line bar)
        hidden_box = QFrame()
        hidden_box.setObjectName("HiddenBox")
        hidden_box.setFixedHeight(40)
        hidden_box.setStyleSheet("""
            QFrame#HiddenBox {
                background-color: #1b2838;
                border: 1px solid #2a475e;
                border-radius: 4px;
            }
        """)
        hidden_layout = QHBoxLayout(hidden_box)
        hidden_layout.setContentsMargins(10, 4, 10, 4)
        hidden_layout.setSpacing(8)

        lbl_hidden_icon = QLabel("🔑 " + tr('lbl_hidden_betas') + ":")
        lbl_hidden_icon.setStyleSheet("color: #8f98a0; font-size: 11px; font-weight: bold;")
        hidden_layout.addWidget(lbl_hidden_icon)

        self.edit_hidden_branch = QLineEdit()
        self.edit_hidden_branch.setPlaceholderText(tr('placeholder_hidden_branch'))
        self.edit_hidden_branch.setMaximumWidth(170)
        self.edit_hidden_branch.setFixedHeight(26)
        hidden_layout.addWidget(self.edit_hidden_branch)

        self.edit_beta_code = QLineEdit()
        self.edit_beta_code.setPlaceholderText(tr('placeholder_beta_code'))
        self.edit_beta_code.setFixedHeight(26)
        hidden_layout.addWidget(self.edit_beta_code)

        self.btn_check_beta_code = QPushButton(tr('btn_check_beta_code'))
        self.btn_check_beta_code.setStyleSheet(
            "background-color: #214b6b; color: #ffffff; font-weight: bold; "
            "padding: 2px 12px; border-radius: 3px;"
        )
        self.btn_check_beta_code.setFixedHeight(26)
        self.btn_check_beta_code.clicked.connect(self.on_check_beta_code)
        hidden_layout.addWidget(self.btn_check_beta_code)

        self.btn_refresh_ver = QPushButton("🔄 " + tr('btn_reload'))
        self.btn_refresh_ver.setFixedHeight(26)
        self.btn_refresh_ver.clicked.connect(self.refresh_server_versions)
        hidden_layout.addWidget(self.btn_refresh_ver)

        vl_ver.addWidget(hidden_box)

        self.lbl_beta_code_status = QLabel("")
        self.lbl_beta_code_status.setStyleSheet("font-size: 11px; color: #8bc34a; font-weight: bold; padding-left: 4px;")
        self.lbl_beta_code_status.setVisible(False)
        vl_ver.addWidget(self.lbl_beta_code_status)

        layout.addWidget(g_ver)

        self.refresh_server_versions()

        # ── Group 3: Installation Status & Console Log ──
        g2 = QGroupBox(tr('group_install_status'))
        sl = QVBoxLayout(g2)
        sl.setSpacing(6)
        self.install_status_label = QLabel(tr('lbl_ready_install'))
        self.install_status_label.setStyleSheet('font-size:13px; font-weight:bold;')
        sl.addWidget(self.install_status_label)
        self.install_progress = QProgressBar()
        self.install_progress.setRange(0, 100)
        self.install_progress.setFixedHeight(20)
        sl.addWidget(self.install_progress)
        self.install_log = QPlainTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMinimumHeight(110)
        self.install_log.setMaximumHeight(160)
        self.install_log.setMaximumBlockCount(1000)
        self.install_log.setFont(QFont(self._mono_font(), 9))
        sl.addWidget(self.install_log)
        layout.addWidget(g2)

        self.install_btn = QPushButton(tr('btn_install_server'))
        self.install_btn.setMinimumHeight(44)
        self.install_btn.setStyleSheet('font-size:14px;font-weight:bold;')
        self.install_btn.clicked.connect(self.start_installation)
        layout.addWidget(self.install_btn)

        warn = QLabel(
            '⚠️ '
            + ('Для установки требуется ~3 ГБ свободного места. '
               'Откройте порты 16261 (UDP) и 27015 (TCP) в брандмауэре.'
               if get_language() == 'ru' else
               'Installation requires ~3 GB disk space. '
               'Open ports 16261 (UDP) and 27015 (TCP) in your firewall.')
        )
        warn.setStyleSheet('color:#ffaa00;padding:4px;')
        layout.addWidget(warn)

        scroll.setWidget(tab)
        self.tabs.addTab(scroll, tr('tab_install'))

    def show_install_tab(self):
        self.tabs.setCurrentIndex(4)

    def browse_install_path(self):
        path = QFileDialog.getExistingDirectory(
            self, 'Select Installation Directory', str(self.paths['server_dir']))
        if path:
            self.install_path_edit.setText(path)
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'

    def refresh_server_versions(self):
        """Fetch and populate current available server beta branches from Steam."""
        try:
            # Clear existing rows
            while self.rows_layout.count() > 0:
                child = self.rows_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Clear button group
            for btn in self.branch_button_group.buttons():
                self.branch_button_group.removeButton(btn)
            self.branch_radio_map.clear()

            self.combo_server_version.blockSignals(True)
            current_choice = self.combo_server_version.currentData()
            self.combo_server_version.clear()

            is_ru = get_language() == 'ru'
            branches = fetch_available_server_branches(lang='ru' if is_ru else 'en')

            for b in branches:
                self.combo_server_version.addItem(b['label'], b['branch'])
                row = self._create_steam_branch_row(b, is_ru)
                self.rows_layout.addWidget(row)

            # Auto-select public branch or current choice
            target_key = current_choice if current_choice is not None else ""
            if target_key in self.branch_radio_map:
                self.branch_radio_map[target_key].setChecked(True)
            elif "" in self.branch_radio_map:
                self.branch_radio_map[""].setChecked(True)

            self.combo_server_version.blockSignals(False)

            self.statusBar.showMessage(
                "Версии сервера из Steam обновлены" if is_ru else "Server branches refreshed from Steam",
                3000
            )
        except Exception as e:
            logger.error(f"Failed to refresh server versions: {e}")

    def _create_steam_branch_row(self, b: dict, is_ru: bool) -> QWidget:
        row = QFrame()
        row.setObjectName("SteamBranchRow")
        row.setFixedHeight(38)
        row.setCursor(Qt.PointingHandCursor)
        row.setStyleSheet("""
            QFrame#SteamBranchRow {
                background-color: #161c24;
                border: 1px solid #212b38;
                border-radius: 4px;
            }
            QFrame#SteamBranchRow:hover {
                background-color: #1f2b38;
                border-color: #2f455d;
            }
        """)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        radio = QRadioButton()
        radio.setCursor(Qt.PointingHandCursor)
        radio.setFixedSize(20, 20)
        radio.setStyleSheet("""
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid #528cb8;
                background-color: #161c24;
            }
            QRadioButton::indicator:checked {
                background-color: #67c1f5;
                border: 2px solid #ffffff;
            }
            QRadioButton::indicator:hover {
                border-color: #ffffff;
            }
        """)
        self.branch_button_group.addButton(radio)
        branch_key = b['branch']
        self.branch_radio_map[branch_key] = radio

        info_box = QHBoxLayout()
        info_box.setSpacing(8)
        info_box.setContentsMargins(0, 0, 0, 0)

        name_text = b.get('name_ru') if is_ru else b.get('name_en')
        desc_text = b.get('desc_ru') if is_ru else b.get('desc_en')
        date_text = b.get('date_ru') if is_ru else b.get('date_en')

        lbl_name = QLabel(name_text or b.get('name', ''))
        lbl_name.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold;")
        lbl_desc = QLabel(f"— {desc_text}" if desc_text else "")
        lbl_desc.setStyleSheet("color: #8f98a0; font-size: 11px;")

        info_box.addWidget(lbl_name)
        info_box.addWidget(lbl_desc)
        info_box.addStretch()

        layout.addWidget(radio)
        layout.addLayout(info_box, 1)

        lbl_date = QLabel(date_text or b.get('date_str', ''))
        lbl_date.setStyleSheet("color: #8f98a0; font-size: 11px; font-weight: normal;")
        lbl_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(lbl_date)

        def _on_toggle(checked):
            if checked:
                idx = self.combo_server_version.findData(branch_key)
                if idx >= 0:
                    self.combo_server_version.setCurrentIndex(idx)
                row.setStyleSheet("""
                    QFrame#SteamBranchRow {
                        background-color: #1a334d;
                        border: 1px solid #3d79b2;
                        border-radius: 4px;
                    }
                    QFrame#SteamBranchRow:hover {
                        background-color: #213f5f;
                    }
                """)
            else:
                row.setStyleSheet("""
                    QFrame#SteamBranchRow {
                        background-color: #161c24;
                        border: 1px solid #212b38;
                        border-radius: 4px;
                    }
                    QFrame#SteamBranchRow:hover {
                        background-color: #1f2b38;
                        border-color: #2f455d;
                    }
                """)

        radio.toggled.connect(_on_toggle)

        def _mouse_press(event):
            radio.setChecked(True)
        row.mousePressEvent = _mouse_press

        return row

    def on_check_beta_code(self):
        code = self.edit_beta_code.text().strip()
        custom_branch = self.edit_hidden_branch.text().strip()
        if not code:
            QMessageBox.warning(self, tr('confirm'), tr('beta_code_empty'))
            return

        self.current_beta_password = code
        branch_name = custom_branch if custom_branch else "private_beta"

        # Add to combo box if not present
        idx = self.combo_server_version.findData(branch_name)
        if idx < 0:
            label = f"{branch_name} — [Скрытая ветка / Private]"
            self.combo_server_version.addItem(label, branch_name)
            idx = self.combo_server_version.findData(branch_name)

        self.combo_server_version.setCurrentIndex(idx)
        self.lbl_beta_code_status.setText(f"{tr('beta_code_success')} ({branch_name})")
        self.lbl_beta_code_status.setVisible(True)

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

        ver_data = self.combo_server_version.currentData()
        beta_branch = ver_data if ver_data is not None else ""
        beta_password = getattr(self, 'current_beta_password', "")

        self.install_worker = InstallWorker(
            self.installer, self.paths,
            beta_branch=beta_branch,
            beta_password=beta_password
        )
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

    def check_server_update_on_startup(self):
        """Silently check for server updates in the background on app startup."""
        if not self.server_installed:
            return
        server_dir = self.paths.get('server_dir')
        if not server_dir or not Path(server_dir).exists():
            return

        ver_data = getattr(self, 'combo_server_version', None)
        beta_branch = ver_data.currentData() if ver_data else ""
        if beta_branch == "custom":
            beta_branch = getattr(self, 'edit_custom_branch', None)
            beta_branch = beta_branch.text().strip() if beta_branch else ""

        self.update_checker = ServerUpdateCheckerWorker(Path(server_dir), beta_branch=beta_branch or "")
        self.update_checker.update_found.connect(self.on_server_update_detected)
        self.update_checker.start()

    def on_server_update_detected(self, update_info: dict):
        """Prompt user with a confirmation dialog when an update is available on Steam."""
        branch = update_info.get('branch', 'public')
        desc = update_info.get('description', '')
        inst_ver = update_info.get('installed_version', '41.78')
        new_ver = update_info.get('latest_version', '42.21')

        is_ru = get_language() == 'ru'
        title = "Обновление сервера Project Zomboid" if is_ru else "Project Zomboid Server Update"
        msg = (
            f"🚀 В Steam вышла новая версия сервера Project Zomboid!\n\n"
            f"Установлена версия: {inst_ver}\n"
            f"Доступна новая версия: {new_ver}\n"
            f"Канал обновления: {desc or branch}\n\n"
            f"Обновить сервер прямо сейчас?"
            if is_ru else
            f"🚀 A new version of Project Zomboid Dedicated Server is available on Steam!\n\n"
            f"Installed version: {inst_ver}\n"
            f"Available version: {new_ver}\n"
            f"Branch: {desc or branch}\n\n"
            f"Would you like to update the server now?"
        )

        reply = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.show_install_tab()
            self.start_installation()

    @staticmethod
    def _mono_font() -> str:
        from PyQt5.QtGui import QFontDatabase
        if 'JetBrains Mono' in QFontDatabase().families():
            return 'JetBrains Mono'
        system = platform.system()
        if system == 'Windows':
            return 'Consolas'
        elif system == 'Darwin':
            return 'Menlo'
        return 'DejaVu Sans Mono'
