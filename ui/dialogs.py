#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialogs, Icons, and Helper Actions Mixin for PZ Server Manager.
"""

import os
import sys
import logging
import platform
import subprocess
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QCheckBox, QComboBox, QMessageBox, QDialog, QApplication,
    QFileDialog, QListWidget, QAbstractSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, QEvent, QObject, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QPen, QColor

from core.translations import tr, get_language
from core.network_helper import NetworkHelper

logger = logging.getLogger(__name__)


def create_zombie_app_icon() -> QIcon:
    """Load high-res Project Zomboid icon from assets or programmatically generate if missing."""
    app_root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    candidates = [
        app_root / "assets" / "icon.ico",
        app_root / "assets" / "icon.png",
        app_root / "icon.ico",
        app_root / "icon.png",
    ]
    for c in candidates:
        if c.exists():
            icon = QIcon(str(c))
            if not icon.isNull():
                return icon

    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QBrush(QColor("#152215")))
    painter.setPen(QPen(QColor("#2e7d32"), 2))
    painter.drawRoundedRect(2, 2, 60, 60, 14, 14)

    painter.setBrush(QBrush(QColor("#0a330a")))
    painter.drawEllipse(8, 8, 48, 48)

    font = QFont("Segoe UI Emoji", 28, QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#33cc33"))
    painter.drawText(QRect(0, 0, 64, 64), Qt.AlignCenter, "🧟")

    painter.end()
    return QIcon(pixmap)


def ensure_firewall_rules(ports_udp=[16261, 8766], ports_tcp=[27015]) -> tuple:
    """Automatically add inbound firewall rules for Project Zomboid server ports."""
    if os.name != 'nt':
        return True, "Firewall configuration is Windows-only."

    udp_str = ",".join(map(str, ports_udp))
    tcp_str = ",".join(map(str, ports_tcp))

    try:
        cmd_udp = (
            f'netsh advfirewall firewall add rule name="Project Zomboid Server (UDP)" '
            f'dir=in action=allow protocol=UDP localport={udp_str} enable=yes'
        )
        cmd_tcp = (
            f'netsh advfirewall firewall add rule name="Project Zomboid Server (TCP)" '
            f'dir=in action=allow protocol=TCP localport={tcp_str} enable=yes'
        )
        r1 = subprocess.run(cmd_udp, shell=True, capture_output=True, text=True)
        r2 = subprocess.run(cmd_tcp, shell=True, capture_output=True, text=True)

        if r1.returncode == 0 and r2.returncode == 0:
            return True, "Firewall rules added successfully."
        else:
            ps_cmd = (
                f'New-NetFirewallRule -DisplayName "Project Zomboid Server UDP ({udp_str})" -Direction Inbound -Protocol UDP -LocalPort {udp_str} -Action Allow -ErrorAction SilentlyContinue; '
                f'New-NetFirewallRule -DisplayName "Project Zomboid Server TCP ({tcp_str})" -Direction Inbound -Protocol TCP -LocalPort {tcp_str} -Action Allow -ErrorAction SilentlyContinue'
            )
            subprocess.run(["powershell", "-Command", f"Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -Command {ps_cmd}'"], capture_output=True)
            return True, "Requested Firewall rules with Administrator elevation."
    except Exception as e:
        logger.error(f"Failed to set firewall rules: {e}")
        return False, str(e)


class NoScrollEventFilter(QObject):
    """Filter out mouse wheel events on QSpinBox and QComboBox to prevent accidental value changes."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if isinstance(obj, (QAbstractSpinBox, QComboBox)):
                event.ignore()
                return True
        return super().eventFilter(obj, event)


def _b(checkbox: QCheckBox) -> str:
    """Convert checkbox state to 'true'/'false' string."""
    return 'true' if checkbox.isChecked() else 'false'


class DialogsMixin:
    """Mixin containing utility actions, folder openers, and common dialogs."""

    def show_about(self):
        QMessageBox.about(self, tr('menu_about'), tr('about_text'))

    def show_firewall_info(self):
        self.open_firewall_ports_action()

    def open_firewall_ports_action(self):
        ok, msg = ensure_firewall_rules()
        if ok:
            QMessageBox.information(
                self,
                tr('firewall_info'),
                '🔓 Порты 16261 (UDP), 8766 (UDP) и 27015 (TCP) успешно открыты в брандмауэре Windows!\n\n'
                'Inbound Firewall Rules configured successfully.'
            )
        else:
            QMessageBox.warning(self, tr('error'), f"Failed to set firewall rules: {msg}")

    def share_server_info_action(self):
        """Fetch server IP and connection info and copy it to clipboard for sharing with friends."""
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            public_ip = NetworkHelper.get_public_ip(timeout=2.5)
        except Exception:
            public_ip = None
        QApplication.restoreOverrideCursor()

        port = self.setting_port.value() if hasattr(self, 'setting_port') else 16261
        srv_name = ""
        if hasattr(self, 'setting_public_name') and self.setting_public_name.text().strip():
            srv_name = self.setting_public_name.text().strip()
        elif hasattr(self, 'server_name_input') and self.server_name_input.text().strip():
            srv_name = self.server_name_input.text().strip()
        else:
            srv_name = "Project Zomboid Server"

        pwd = self.setting_password.text().strip() if hasattr(self, 'setting_password') else ""

        is_ru = (get_language() == 'ru')
        if is_ru:
            pwd_str = pwd if pwd else "(без пароля)"
            ext_ip_str = public_ip if public_ip else "Не определен"
            connect_ip = public_ip if public_ip else "IP вашего сервера"
            share_text = (
                f"🎮 Данные для подключения к серверу Project Zomboid:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 Название: {srv_name}\n"
                f"🌐 IP сервера: {ext_ip_str}\n"
                f"🔌 Порт: {port}\n"
                f"🔑 Пароль сервера: {pwd_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 Как подключиться в игре:\n"
                f"1. Главное меню -> 'Сетевая игра' (Join)\n"
                f"2. Заполните IP ({connect_ip}), Порт ({port}) и пароль (если задан)\n"
                f"3. Нажмите 'Добавить' и 'Подключиться'!"
            )
            title = "Данные скопированы в буфер обмена!"
            info_msg = (
                "Информация о сервере скопирована в буфер обмена!\n"
                "Вы можете просто нажать Ctrl+V в Discord, Telegram или Steam:\n\n"
                f"{share_text}"
            )
        else:
            pwd_str = pwd if pwd else "(no password)"
            ext_ip_str = public_ip if public_ip else "Not detected"
            connect_ip = public_ip if public_ip else "Server IP"
            share_text = (
                f"🎮 Project Zomboid Server Connection Details:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 Server Name: {srv_name}\n"
                f"🌐 Server IP: {ext_ip_str}\n"
                f"🔌 Port: {port}\n"
                f"🔑 Password: {pwd_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 How to connect in-game:\n"
                f"1. Main Menu -> 'Join'\n"
                f"2. Fill in IP ({connect_ip}), Port ({port}) and Password\n"
                f"3. Click 'Add' and 'Connect'!"
            )
            title = "Connection Info Copied!"
            info_msg = (
                "Server details copied to clipboard!\n"
                "Paste (Ctrl+V) directly into Discord, Telegram or Steam chat:\n\n"
                f"{share_text}"
            )

        clipboard = QApplication.clipboard()
        clipboard.setText(share_text)
        QMessageBox.information(self, title, info_msg)

    def open_backup_manager(self):
        """Show graphical backup manager dialog to create, inspect, restore, and delete world backups."""
        if not hasattr(self, 'backup_manager'):
            from core.backup_manager import BackupManager
            name = self.server_name_input.text().strip() or 'servertest' if hasattr(self, 'server_name_input') else 'servertest'
            self.backup_manager = BackupManager(self.paths, name)

        dialog = QDialog(self)
        dialog.setWindowTitle("📦 " + tr('backup_mgr_title'))
        dialog.resize(750, 480)
        vlayout = QVBoxLayout(dialog)
        vlayout.setContentsMargins(14, 14, 14, 14)
        vlayout.setSpacing(10)

        # Header info
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #252526; border: 1px solid #3c3c3c; border-radius: 6px; padding: 6px;")
        hl = QHBoxLayout(header_frame)
        hl.setContentsMargins(8, 4, 8, 4)
        info_lbl = QLabel(f"📂 <b>{tr('col_filename')}:</b> {self.backup_manager.backup_dir}")
        info_lbl.setStyleSheet("color: #a0ffa0; font-size: 11px;")
        hl.addWidget(info_lbl)
        hl.addStretch()
        open_folder_btn = QPushButton("📂 " + tr('btn_open_backup_folder'))
        open_folder_btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        open_folder_btn.clicked.connect(lambda: self._open_folder(self.backup_manager.backup_dir))
        hl.addWidget(open_folder_btn)
        vlayout.addWidget(header_frame)

        # Table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([tr('col_filename'), tr('col_size'), tr('col_date')])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                color: #e0e0e0;
                gridline-color: #333333;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #3c3c3c;
            }
            QTableWidget::item:selected {
                background-color: #264f78;
                color: #ffffff;
            }
        """)
        vlayout.addWidget(table, 1)

        def refresh_table():
            backups = self.backup_manager.list_backups()
            table.setRowCount(len(backups))
            for row_idx, b in enumerate(backups):
                item_name = QTableWidgetItem("📦 " + b['filename'])
                item_name.setData(Qt.UserRole, b['filepath'])
                item_size = QTableWidgetItem(f"{b['size_mb']} MB")
                item_size.setTextAlignment(Qt.AlignCenter)
                item_date = QTableWidgetItem(b['modified'])
                item_date.setTextAlignment(Qt.AlignCenter)

                table.setItem(row_idx, 0, item_name)
                table.setItem(row_idx, 1, item_size)
                table.setItem(row_idx, 2, item_date)

        refresh_table()

        # Action Buttons Row
        btn_row = QHBoxLayout()
        create_btn = QPushButton("➕ " + tr('btn_create_backup'))
        create_btn.setStyleSheet("background-color: #1e6b3b; color: #ffffff; font-weight: bold; padding: 6px 14px;")
        btn_row.addWidget(create_btn)

        restore_btn = QPushButton("🔄 " + tr('btn_restore_backup'))
        restore_btn.setStyleSheet("background-color: #1e4b7a; color: #ffffff; font-weight: bold; padding: 6px 14px;")
        btn_row.addWidget(restore_btn)

        del_btn = QPushButton("🗑️ " + tr('btn_delete_backup'))
        del_btn.setStyleSheet("background-color: #6b2020; color: #ffffff; padding: 6px 14px;")
        btn_row.addWidget(del_btn)

        btn_row.addStretch()

        close_btn = QPushButton(tr('btn_close'))
        close_btn.setStyleSheet("padding: 6px 14px;")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        vlayout.addLayout(btn_row)

        def do_create():
            tag, ok = QInputDialog.getText(dialog, tr('btn_create_backup'), tr('prompt_backup_tag'))
            if ok:
                tag = tag.strip() or 'manual'
                try:
                    p = self.backup_manager.create_backup(tag=tag)
                    QMessageBox.information(dialog, tr('success'), tr('backup_created_success', path=p))
                    refresh_table()
                except Exception as e:
                    QMessageBox.critical(dialog, tr('error'), f"Failed to create backup: {e}")

        def do_restore():
            row = table.currentRow()
            if row < 0:
                QMessageBox.warning(dialog, tr('warning'), "Please select a backup from the list to restore.")
                return
            item = table.item(row, 0)
            if not item:
                return
            filepath = item.data(Qt.UserRole)
            filename = item.text().replace("📦 ", "")
            res = QMessageBox.warning(
                dialog,
                tr('confirm'),
                tr('backup_restore_confirm', name=filename),
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                ok = self.backup_manager.restore_backup(filepath)
                if ok:
                    QMessageBox.information(dialog, tr('success'), tr('backup_restore_success'))
                    if hasattr(self, 'load_settings'):
                        self.load_settings()
                    if hasattr(self, 'load_sandbox_settings'):
                        self.load_sandbox_settings()
                    dialog.accept()
                else:
                    QMessageBox.critical(dialog, tr('error'), "Failed to restore backup.")

        def do_delete():
            row = table.currentRow()
            if row < 0:
                QMessageBox.warning(dialog, tr('warning'), "Please select a backup from the list to delete.")
                return
            item = table.item(row, 0)
            if not item:
                return
            filepath = item.data(Qt.UserRole)
            filename = item.text().replace("📦 ", "")
            res = QMessageBox.question(
                dialog,
                tr('confirm'),
                tr('backup_delete_confirm', name=filename),
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                try:
                    Path(filepath).unlink(missing_ok=True)
                    QMessageBox.information(dialog, tr('success'), tr('backup_delete_success'))
                    refresh_table()
                except Exception as e:
                    QMessageBox.critical(dialog, tr('error'), f"Failed to delete backup: {e}")

        create_btn.clicked.connect(do_create)
        restore_btn.clicked.connect(do_restore)
        del_btn.clicked.connect(do_delete)

        dialog.exec_()

    def delete_save_world_action(self):
        name = self.server_name_input.text().strip() or 'servertest'
        save_dir = self.paths['zomboid_dir'] / 'Saves' / 'Multiplayer' / name
        if save_dir.exists():
            res = QMessageBox.question(
                self,
                tr('confirm'),
                f"Вы действительно хотите сбросить/удалить сохранение мира '{name}'?\n"
                f"Это решит проблему несовместимости версий карт (Build 41 / Build 42).\n\n"
                f"Путь: {save_dir}",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                import shutil
                try:
                    shutil.rmtree(save_dir, ignore_errors=True)
                    QMessageBox.information(
                        self,
                        tr('success'),
                        f"Сохранение мира '{name}' успешно удалено!\nПри следующем запуске сервера создастся чистая карта."
                    )
                except Exception as e:
                    QMessageBox.critical(self, tr('error'), f"Не удалось удалить папку мира: {e}")
        else:
            QMessageBox.information(
                self,
                tr('info'),
                f"Сохранение мира '{name}' еще не создавалось (папка не найдена)."
            )

    def _show_version_mismatch_dialog(self):
        name = self.server_name_input.text().strip() or 'servertest'
        save_dir = self.paths['zomboid_dir'] / 'Saves' / 'Multiplayer' / name
        res = QMessageBox.warning(
            self,
            "⚠️ Несовместимость версий мира!",
            f"Сервер не смог загрузить карту '{name}', так как файлы мира сохранены в более новой версии (Build 42), а вы запускаете Build 41.\n\n"
            f"• Желаете удалить старое сохранение мира '{name}', чтобы запустить чистую карту?\n"
            f"• Или перейдите во вкладку 'Установка' и докачайте Build 42 (unstable).",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes and save_dir.exists():
            import shutil
            try:
                shutil.rmtree(save_dir, ignore_errors=True)
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Сохранение мира '{name}' успешно удалено!\nТеперь сервер запустит чистую карту."
                )
            except Exception as e:
                QMessageBox.critical(self, tr('error'), f"Не удалось удалить папку мира: {e}")

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
            QMessageBox.warning(self, tr('folder_not_found'), f"Config folder not found:\n{d}")

    def open_server_folder(self):
        d = self.paths['server_dir']
        if d.exists():
            self._open_folder(d)
        else:
            QMessageBox.warning(self, tr('folder_not_found'), f"Server folder not found:\n{d}")

    def change_server_directory(self):
        path = QFileDialog.getExistingDirectory(self, 'Select Server Directory', str(self.paths['server_dir']))
        if path:
            self.paths['server_dir'] = Path(path)
            self.paths['steamcmd_dir'] = Path(path) / 'steamcmd'
            if hasattr(self, 'install_path_edit'):
                self.install_path_edit.setText(path)
            p = Path(path)
            self.server_installed = any(
                (p / n).exists() for n in [
                    'ProjectZomboid64.exe', 'StartServer64.bat',
                    'start-server.sh', 'ProjectZomboid64',
                ])
            self.statusBar.showMessage(f"Server directory: {path}", 5000)

    def validate_server(self):
        self.show_install_tab()
        if hasattr(self, 'start_update'):
            self.start_update()

    def update_server(self):
        self.show_install_tab()
        if hasattr(self, 'start_update'):
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


class WebSecurityDialog(QDialog):
    """Dialog to configure custom port, password, and firewall rules for the Web Dashboard."""

    def __init__(self, parent=None, current_port: int = 8080, current_password: str = "admin"):
        super().__init__(parent)
        self.setWindowTitle(tr('web_security_title'))
        self.setFixedSize(520, 370)
        self.result_port = current_port
        self.result_password = current_password
        self.result_open_firewall = True

        self.setStyleSheet("""
            QDialog {
                background-color: #252526;
                color: #ffffff;
            }
            QLabel {
                color: #e0e0e0;
            }
            QSpinBox, QLineEdit {
                background-color: #1e1e1e;
                color: #40ff40;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QSpinBox:focus, QLineEdit:focus {
                border: 1px solid #2eb84d;
            }
            QPushButton {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QCheckBox {
                color: #cccccc;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header with icon and description
        header_layout = QHBoxLayout()
        icon_lbl = QLabel("🛡️")
        icon_lbl.setStyleSheet("font-size: 30px;")
        desc_lbl = QLabel(tr('web_security_desc'))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #a0a0a0; font-size: 12px; line-height: 1.4;")
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(desc_lbl, 1)
        layout.addLayout(header_layout)

        # Port selection
        port_box = QGroupBox(tr('web_port_label'))
        port_box.setStyleSheet("QGroupBox { font-weight: bold; color: #40ff40; border: 1px solid #3c3c3c; border-radius: 6px; margin-top: 6px; padding-top: 14px; }")
        port_layout = QHBoxLayout(port_box)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(current_port)
        port_layout.addWidget(self.port_spin, 1)

        rand_port_btn = QPushButton(tr('btn_random_port'))
        rand_port_btn.clicked.connect(self._generate_random_port)
        port_layout.addWidget(rand_port_btn)
        layout.addWidget(port_box)

        # Password selection
        pw_box = QGroupBox(tr('web_pw_label'))
        pw_box.setStyleSheet("QGroupBox { font-weight: bold; color: #40ff40; border: 1px solid #3c3c3c; border-radius: 6px; margin-top: 6px; padding-top: 14px; }")
        pw_layout = QHBoxLayout(pw_box)

        self.pw_edit = QLineEdit()
        self.pw_edit.setText(current_password)
        pw_layout.addWidget(self.pw_edit, 1)

        rand_pw_btn = QPushButton(tr('btn_gen_pw'))
        rand_pw_btn.clicked.connect(self._generate_random_password)
        pw_layout.addWidget(rand_pw_btn)
        layout.addWidget(pw_box)

        # Firewall checkbox
        self.fw_check = QCheckBox(tr('web_firewall_label'))
        self.fw_check.setChecked(os.name == 'nt')
        self.fw_check.setEnabled(os.name == 'nt')
        layout.addWidget(self.fw_check)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(tr('btn_cancel') or "Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("🚀 " + tr('btn_save_start_web'))
        save_btn.setStyleSheet("background-color: #208336; color: #ffffff; padding: 7px 16px; border: 1px solid #1c6d2d;")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _generate_random_port(self):
        import random
        excluded = {16261, 16262, 8766, 8767, 27015, 8080}
        while True:
            port = random.randint(8100, 48000)
            if port not in excluded:
                self.port_spin.setValue(port)
                break

    def _generate_random_password(self):
        import secrets
        self.pw_edit.setText(secrets.token_urlsafe(10))

    def _on_save(self):
        self.result_port = self.port_spin.value()
        self.result_password = self.pw_edit.text().strip() or "admin"
        self.result_open_firewall = self.fw_check.isChecked()
        self.accept()

