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
    QMessageBox, QFileDialog, QSizePolicy
)
from PyQt5.QtGui import QFont

from translations import tr, get_language
from server_installer import (
    InstallWorker, ServerUpdateCheckerWorker, fetch_available_server_branches
)

logger = logging.getLogger(__name__)


class InstallTabMixin:
    """Mixin for Server installation, Steam updates, and version branch selection."""

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

        g_ver = QGroupBox(tr('group_server_version'))
        vl = QFormLayout(g_ver)

        row_ver = QHBoxLayout()
        self.combo_server_version = QComboBox()
        self.combo_server_version.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_ver.addWidget(self.combo_server_version)

        self.btn_refresh_ver = QPushButton(tr('btn_refresh_versions'))
        self.btn_refresh_ver.clicked.connect(self.refresh_server_versions)
        row_ver.addWidget(self.btn_refresh_ver)
        vl.addRow(tr('lbl_server_version'), row_ver)

        self.edit_custom_branch = QLineEdit()
        self.edit_custom_branch.setPlaceholderText("e.g. legacy41 or 42.19")
        self.edit_custom_branch.setVisible(False)
        vl.addRow(tr('lbl_custom_branch'), self.edit_custom_branch)

        def _on_ver_changed(index):
            data = self.combo_server_version.currentData()
            self.edit_custom_branch.setVisible(data == "custom")

        self.combo_server_version.currentIndexChanged.connect(_on_ver_changed)
        layout.addWidget(g_ver)

        self.refresh_server_versions()

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
            self.combo_server_version.blockSignals(True)
            current_choice = self.combo_server_version.currentData()
            self.combo_server_version.clear()

            branches = fetch_available_server_branches()
            for b in branches:
                self.combo_server_version.addItem(b['label'], b['branch'])

            if current_choice is not None:
                idx = self.combo_server_version.findData(current_choice)
                if idx >= 0:
                    self.combo_server_version.setCurrentIndex(idx)
            self.combo_server_version.blockSignals(False)

            data = self.combo_server_version.currentData()
            self.edit_custom_branch.setVisible(data == "custom")
            self.statusBar.showMessage(
                "Версии сервера из Steam обновлены" if get_language() == 'ru' else "Server branches refreshed from Steam",
                3000
            )
        except Exception as e:
            logger.error(f"Failed to refresh server versions: {e}")

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
        if ver_data == "custom":
            beta_branch = self.edit_custom_branch.text().strip()
        else:
            beta_branch = ver_data or ""

        self.install_worker = InstallWorker(self.installer, self.paths, beta_branch=beta_branch)
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
        system = platform.system()
        if system == 'Windows':
            return 'Consolas'
        elif system == 'Darwin':
            return 'Menlo'
        return 'DejaVu Sans Mono'
