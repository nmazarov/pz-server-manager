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

from core.translations import tr, get_language
from core.server_installer import (
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

        # ── Group 2: Steam Betas & Versions (Dark Gray Theme) ──
        g_ver = QGroupBox(tr('group_server_version'))
        vl_ver = QVBoxLayout(g_ver)
        vl_ver.setContentsMargins(10, 10, 10, 10)
        vl_ver.setSpacing(8)

        # Steam explanation subtitle
        lbl_sub_title = QLabel(tr('lbl_selected_version_title'))
        lbl_sub_title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold; background: transparent;")
        vl_ver.addWidget(lbl_sub_title)

        lbl_sub_note = QLabel(tr('lbl_selected_version_note'))
        lbl_sub_note.setStyleSheet("color: #aaaaaa; font-size: 12px; background: transparent; line-height: 1.4;")
        lbl_sub_note.setWordWrap(True)
        vl_ver.addWidget(lbl_sub_note)

        # Steam table frame (Dark gray theme matching the application)
        self.steam_table_frame = QFrame()
        self.steam_table_frame.setObjectName("SteamTableFrame")
        self.steam_table_frame.setMinimumHeight(240)
        self.steam_table_frame.setStyleSheet("""
            QFrame#SteamTableFrame {
                background-color: #212121;
                border: 1px solid #383838;
                border-radius: 6px;
            }
            QFrame#SteamTableFrame QLabel {
                background: transparent;
                border: none;
            }
        """)
        table_vbox = QVBoxLayout(self.steam_table_frame)
        table_vbox.setContentsMargins(0, 0, 0, 0)
        table_vbox.setSpacing(0)

        # Table Column Headers
        hdr_frame = QFrame()
        hdr_frame.setFixedHeight(32)
        hdr_frame.setStyleSheet(
            "background-color: #2b2b2b; border-bottom: 1px solid #383838; "
            "border-top-left-radius: 5px; border-top-right-radius: 5px;"
        )
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(16, 0, 16, 0)

        lbl_hdr_name = QLabel(tr('col_branch_name_desc'))
        lbl_hdr_name.setStyleSheet("color: #999999; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent;")
        hdr_layout.addWidget(lbl_hdr_name, 1)

        lbl_hdr_date = QLabel(tr('col_branch_last_update'))
        lbl_hdr_date.setStyleSheet("color: #999999; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent;")
        lbl_hdr_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hdr_layout.addWidget(lbl_hdr_date)

        table_vbox.addWidget(hdr_frame)

        # Dynamic rows container
        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("background: transparent;")
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(2)
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

        # Section: Скрытые версии (Private Betas in dark gray theme)
        hidden_box = QFrame()
        hidden_box.setObjectName("HiddenBox")
        hidden_box.setStyleSheet("""
            QFrame#HiddenBox {
                background-color: #242424;
                border: 1px solid #383838;
                border-radius: 6px;
            }
            QFrame#HiddenBox QLabel {
                background: transparent;
            }
        """)
        hl_vbox = QVBoxLayout(hidden_box)
        hl_vbox.setContentsMargins(14, 10, 14, 10)
        hl_vbox.setSpacing(6)

        lbl_hidden_title = QLabel("🔑 " + tr('lbl_hidden_betas'))
        lbl_hidden_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; background: transparent;")
        hl_vbox.addWidget(lbl_hidden_title)

        lbl_hidden_desc = QLabel(tr('lbl_hidden_betas_desc'))
        lbl_hidden_desc.setStyleSheet("color: #aaaaaa; font-size: 12px; background: transparent;")
        hl_vbox.addWidget(lbl_hidden_desc)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.edit_hidden_branch = QLineEdit()
        self.edit_hidden_branch.setPlaceholderText(tr('placeholder_hidden_branch'))
        self.edit_hidden_branch.setMaximumWidth(170)
        self.edit_hidden_branch.setFixedHeight(32)
        self.edit_hidden_branch.setStyleSheet(
            "background-color: #1c1c1c; border: 1px solid #3d3d3d; "
            "border-radius: 4px; padding: 0 10px; color: #ffffff; font-size: 12px;"
        )
        input_row.addWidget(self.edit_hidden_branch)

        self.edit_beta_code = QLineEdit()
        self.edit_beta_code.setPlaceholderText(tr('placeholder_beta_code'))
        self.edit_beta_code.setFixedHeight(32)
        self.edit_beta_code.setStyleSheet(
            "background-color: #1c1c1c; border: 1px solid #3d3d3d; "
            "border-radius: 4px; padding: 0 10px; color: #ffffff; font-size: 12px;"
        )
        input_row.addWidget(self.edit_beta_code)

        self.btn_check_beta_code = QPushButton(tr('btn_check_beta_code'))
        self.btn_check_beta_code.setFixedHeight(32)
        self.btn_check_beta_code.setStyleSheet(
            "background-color: #384858; color: #ffffff; font-weight: bold; "
            "padding: 0 16px; border-radius: 4px; border: 1px solid #4a5c6d; font-size: 12px;"
        )
        self.btn_check_beta_code.clicked.connect(self.on_check_beta_code)
        input_row.addWidget(self.btn_check_beta_code)

        self.btn_refresh_ver = QPushButton(tr('btn_reload'))
        self.btn_refresh_ver.setFixedHeight(32)
        self.btn_refresh_ver.setStyleSheet(
            "background-color: #333333; color: #e0e0e0; "
            "padding: 0 14px; border-radius: 4px; border: 1px solid #444444; font-size: 12px;"
        )
        self.btn_refresh_ver.clicked.connect(self.refresh_server_versions)
        input_row.addWidget(self.btn_refresh_ver)

        hl_vbox.addLayout(input_row)

        vl_ver.addWidget(hidden_box)

        self.lbl_beta_code_status = QLabel("")
        self.lbl_beta_code_status.setStyleSheet("font-size: 12px; color: #8bc34a; font-weight: bold; padding-left: 4px; background: transparent;")
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

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)
        btn_row.addStretch()

        self.install_btn = QPushButton(tr('btn_install_server'))
        self.install_btn.setMinimumHeight(44)
        self.install_btn.setMinimumWidth(240)
        self.install_btn.setMaximumWidth(320)
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e663e;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #387c4c; }
            QPushButton:disabled { background-color: #383838; color: #777777; }
        """)
        self.install_btn.setToolTip("Выполнить чистую/первичную установку выделенного сервера" if get_language() == 'ru' else "Perform a clean/initial installation of the dedicated server")
        self.install_btn.clicked.connect(self.start_installation)
        btn_row.addWidget(self.install_btn)

        self.update_btn = QPushButton(tr('btn_update_server'))
        self.update_btn.setMinimumHeight(44)
        self.update_btn.setMinimumWidth(240)
        self.update_btn.setMaximumWidth(320)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b5b7b;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #35729a; }
            QPushButton:disabled { background-color: #383838; color: #777777; }
        """)
        self.update_btn.setToolTip("Обновить и проверить целостность файлов уже установленного сервера" if get_language() == 'ru' else "Update and verify files of the installed server")
        self.update_btn.clicked.connect(self.start_update)
        btn_row.addWidget(self.update_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

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
        for i in range(self.tabs.count()):
            text = self.tabs.tabText(i).lower()
            if 'install' in text or 'установ' in text:
                self.tabs.setCurrentIndex(i)
                return
        self.tabs.setCurrentIndex(self.tabs.count() - 1)

    def browse_install_path(self):
        path = QFileDialog.getExistingDirectory(
            self, 'Select Installation Directory', str(self.paths['server_dir']))
        if path:
            self.install_path_edit.setText(path)
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'
            from main import check_server_installed
            self.server_installed = check_server_installed(self.paths)
            if hasattr(self, 'update_status'):
                self.update_status()
            if hasattr(self, 'update_target_server_build'):
                self.update_target_server_build()

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
        row.setFixedHeight(52)
        row.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(14)

        radio = QRadioButton()
        radio.setCursor(Qt.PointingHandCursor)
        radio.setFixedSize(20, 20)
        radio.setStyleSheet("""
            QRadioButton {
                background: transparent;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 8px;
                border: 2px solid #777777;
                background-color: #242424;
            }
            QRadioButton::indicator:checked {
                background-color: #5294e2;
                border: 2px solid #ffffff;
            }
            QRadioButton::indicator:hover {
                border-color: #ffffff;
            }
        """)
        self.branch_button_group.addButton(radio)
        branch_key = b['branch']
        self.branch_radio_map[branch_key] = radio

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        info_box.setContentsMargins(0, 0, 0, 0)

        name_text = b.get('name_ru') if is_ru else b.get('name_en')
        desc_text = b.get('desc_ru') if is_ru else b.get('desc_en')
        date_text = b.get('date_ru') if is_ru else b.get('date_en')

        lbl_name = QLabel(name_text or b.get('name', ''))
        lbl_name.setAttribute(Qt.WA_TranslucentBackground, True)
        lbl_name.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; background: transparent; border: none;")

        lbl_desc = QLabel(desc_text or "")
        lbl_desc.setAttribute(Qt.WA_TranslucentBackground, True)
        lbl_desc.setStyleSheet("color: #9e9e9e; font-size: 12px; background: transparent; border: none;")

        info_box.addWidget(lbl_name)
        info_box.addWidget(lbl_desc)

        layout.addWidget(radio)
        layout.addLayout(info_box, 1)

        lbl_date = QLabel(date_text or b.get('date_str', ''))
        lbl_date.setAttribute(Qt.WA_TranslucentBackground, True)
        lbl_date.setStyleSheet("color: #9e9e9e; font-size: 12px; font-weight: normal; background: transparent; border: none;")
        lbl_date.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(lbl_date)

        def set_row_style(selected: bool):
            if selected:
                row.setStyleSheet("""
                    QFrame#SteamBranchRow {
                        background-color: #34383d;
                        border: 1px solid #48525c;
                        border-left: 4px solid #5294e2;
                        border-radius: 4px;
                    }
                    QFrame#SteamBranchRow:hover {
                        background-color: #3b4046;
                    }
                    QFrame#SteamBranchRow QLabel {
                        background: transparent;
                        border: none;
                    }
                """)
                lbl_name.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; background: transparent; border: none;")
                lbl_desc.setStyleSheet("color: #dddddd; font-size: 12px; background: transparent; border: none;")
                lbl_date.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: bold; background: transparent; border: none;")
            else:
                row.setStyleSheet("""
                    QFrame#SteamBranchRow {
                        background-color: #252525;
                        border: 1px solid #2e2e2e;
                        border-left: 4px solid transparent;
                        border-radius: 4px;
                    }
                    QFrame#SteamBranchRow:hover {
                        background-color: #2d2d2d;
                        border-color: #3c3c3c;
                    }
                    QFrame#SteamBranchRow QLabel {
                        background: transparent;
                        border: none;
                    }
                """)
                lbl_name.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: bold; background: transparent; border: none;")
                lbl_desc.setStyleSheet("color: #9e9e9e; font-size: 12px; background: transparent; border: none;")
                lbl_date.setStyleSheet("color: #9e9e9e; font-size: 12px; background: transparent; border: none;")

        set_row_style(False)

        def _on_toggle(checked):
            set_row_style(checked)
            if checked:
                idx = self.combo_server_version.findData(branch_key)
                if idx >= 0:
                    self.combo_server_version.setCurrentIndex(idx)
                self.selected_branch_key = b.get('key') or branch_key or 'public'
                if hasattr(self, 'update_target_server_build'):
                    self.update_target_server_build()

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
        self.selected_branch_key = branch_name
        if hasattr(self, 'update_target_server_build'):
            self.update_target_server_build()
        self.lbl_beta_code_status.setText(f"{tr('beta_code_success')} ({branch_name})")
        self.lbl_beta_code_status.setVisible(True)

    def _run_install_worker(self, install_path: Path, is_update: bool = False):
        self.paths['server_dir'] = install_path
        self.paths['steamcmd_dir'] = install_path / 'steamcmd'
        self.install_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self._is_updating = is_update

        ver_data = self.combo_server_version.currentData()
        beta_branch = ver_data if ver_data is not None else ""
        beta_password = getattr(self, 'current_beta_password', "")

        action_text = (
            "Обновление и проверка файлов сервера..." if (get_language() == 'ru' and is_update)
            else ("Updating server files..." if is_update
                  else ("Установка сервера..." if get_language() == 'ru' else "Installing server..."))
        )
        self.install_status_label.setText(action_text)
        self.install_progress.setValue(0)

        self.install_worker = InstallWorker(
            self.installer, self.paths,
            beta_branch=beta_branch,
            beta_password=beta_password
        )
        self.install_worker.progress.connect(self.on_install_progress)
        self.install_worker.log.connect(self.on_install_log)
        self.install_worker.finished.connect(self.on_install_finished)
        self.install_worker.finished.connect(self.install_worker.deleteLater)
        self.install_worker.error.connect(self.on_install_error)
        self.install_worker.start()

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

        self._run_install_worker(install_path, is_update=False)

    def start_update(self):
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

        from main import check_server_installed
        if not check_server_installed({'server_dir': install_path}):
            reply = QMessageBox.question(
                self,
                tr('confirm'),
                "В указанной папке сервер ещё не обнаружен.\n\n"
                "Выполнить первичную установку сервера?"
                if get_language() == 'ru' else
                "No installed server was found in this directory.\n\n"
                "Perform a clean server installation?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        ver_label = self.combo_server_version.currentText()
        if QMessageBox.question(
            self, tr('confirm'),
            tr('confirm_update', path=install_path, branch=ver_label),
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        self._run_install_worker(install_path, is_update=True)

    def on_install_progress(self, value, message):
        self.install_progress.setValue(value)
        self.install_status_label.setText(message)

    def on_install_log(self, message):
        self.install_log.appendPlainText(message)

    def on_install_finished(self):
        self.install_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.install_progress.setValue(100)
        is_update = getattr(self, '_is_updating', False)
        if is_update:
            msg_title = tr('update_complete')
            msg_desc = tr('update_complete_msg')
            self.install_status_label.setText('Update complete!' if get_language() == 'en' else 'Обновление завершено!')
        else:
            msg_title = tr('install_complete')
            msg_desc = tr('install_complete_msg')
            self.install_status_label.setText('Installation complete!' if get_language() == 'en' else 'Установка завершена!')
        self.server_installed = True
        if hasattr(self, 'update_status'):
            self.update_status()
        if hasattr(self, 'update_target_server_build'):
            self.update_target_server_build()
        QMessageBox.information(self, msg_title, msg_desc)

    def on_install_error(self, error):
        self.install_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        is_update = getattr(self, '_is_updating', False)
        self.install_status_label.setText('Update failed!' if is_update else 'Installation failed!')
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
        self.update_checker.finished.connect(self.update_checker.deleteLater)
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
            self.start_update()

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
