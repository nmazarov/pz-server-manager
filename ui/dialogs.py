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
    QFileDialog, QListWidget, QAbstractSpinBox
)
from PyQt5.QtCore import Qt, QEvent, QObject, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QBrush, QPen, QColor

from translations import tr, get_language
from network_helper import NetworkHelper

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
        try:
            local_ip = NetworkHelper.get_local_ip()
        except Exception:
            local_ip = "127.0.0.1"
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
            ext_ip_str = public_ip if public_ip else "Не определен (используйте локальный / Radmin VPN)"
            share_text = (
                f"🎮 Данные для подключения к серверу Project Zomboid:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 Название: {srv_name}\n"
                f"🌐 Внешний IP (Интернет): {ext_ip_str}\n"
                f"🏠 Локальный IP (LAN / Hamachi / Radmin): {local_ip}\n"
                f"🔌 Порт: {port}\n"
                f"🔑 Пароль сервера: {pwd_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 Как подключиться в игре:\n"
                f"1. Главное меню -> 'Сетевая игра' (Join)\n"
                f"2. Заполните IP ({public_ip or local_ip}), Порт ({port}) и пароль (если задан)\n"
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
            ext_ip_str = public_ip if public_ip else "Not detected (use Local IP / VPN)"
            share_text = (
                f"🎮 Project Zomboid Server Connection Details:\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📛 Server Name: {srv_name}\n"
                f"🌐 Public IP: {ext_ip_str}\n"
                f"🏠 Local IP (LAN / VPN): {local_ip}\n"
                f"🔌 Порт: {port}\n"
                f"🔑 Password: {pwd_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 How to connect in-game:\n"
                f"1. Main Menu -> 'Join'\n"
                f"2. Fill in IP ({public_ip or local_ip}), Port ({port}) and Password\n"
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

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.reject)
        btn_row.addWidget(close_btn)
        vlayout.addLayout(btn_row)

        def do_restore():
            sel = list_widget.currentItem()
            if not sel:
                return
            chosen_name = sel.text()
            chosen_path = next((b for b in backups if b.name == chosen_name), None)
            if not chosen_path:
                return
            res = QMessageBox.question(
                dialog, tr('confirm'),
                f"Восстановить конфигурацию из архива:\n{chosen_name}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                ok = self.config_manager.restore_backup(chosen_path)
                if ok:
                    QMessageBox.information(dialog, tr('success'), "Конфигурация успешно восстановлена!")
                    self.load_settings()
                    self.load_sandbox_settings()
                    dialog.accept()
                else:
                    QMessageBox.critical(dialog, tr('error'), "Не удалось восстановить бэкап.")

        restore_btn.clicked.connect(do_restore)
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
        QMessageBox.information(self, tr('menu_validate'), 'Go to the Install tab and click Install / Update Server.')

    def update_server(self):
        self.show_install_tab()

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
