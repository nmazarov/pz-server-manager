#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mods Tab Mixin for PZ Server Manager.
Handles mod list management, Steam Workshop imports, collections, curated presets,
dependency analysis, and Build 41 / Build 42 compatibility color-coded verification.
"""

import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QGroupBox, QMessageBox, QInputDialog,
    QFileDialog, QApplication, QDialog, QRadioButton, QButtonGroup, QCheckBox,
    QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from core.translations import tr, get_language

logger = logging.getLogger(__name__)


class ModsTabMixin:
    """Mixin for Mod management, Steam Workshop collections, compatibility checks, and presets."""

    def create_mods_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Server readiness & target build status banner
        self.mods_server_status_banner = QFrame()
        self.mods_server_status_banner.setObjectName("ModsServerStatusBanner")
        banner_layout = QHBoxLayout(self.mods_server_status_banner)
        banner_layout.setContentsMargins(14, 10, 14, 10)
        banner_layout.setSpacing(12)

        self.lbl_mods_banner_icon = QLabel("🟢")
        self.lbl_mods_banner_icon.setStyleSheet("font-size: 20px; background: transparent;")
        banner_layout.addWidget(self.lbl_mods_banner_icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        self.lbl_mods_banner_title = QLabel("")
        self.lbl_mods_banner_title.setWordWrap(True)
        text_layout.addWidget(self.lbl_mods_banner_title)

        self.lbl_mods_banner_desc = QLabel("")
        self.lbl_mods_banner_desc.setWordWrap(True)
        text_layout.addWidget(self.lbl_mods_banner_desc)
        banner_layout.addLayout(text_layout, 1)

        self.btn_mods_banner_action = QPushButton("")
        self.btn_mods_banner_action.setCursor(Qt.PointingHandCursor)
        self.btn_mods_banner_action.clicked.connect(self.show_install_tab)
        banner_layout.addWidget(self.btn_mods_banner_action)

        layout.addWidget(self.mods_server_status_banner)

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

        compat_legend = QLabel(
            "🟢 <b>Зеленый</b>: Совместим с версией сервера | "
            "🔴 <b>Красный</b>: Несовместим или устарел | "
            "🟡 <b>Желтый</b>: Универсальный / требует проверки"
            if get_language() == 'ru' else
            "🟢 <b>Green</b>: Compatible with server | "
            "🔴 <b>Red</b>: Incompatible or outdated | "
            "🟡 <b>Yellow</b>: Universal / untested"
        )
        compat_legend.setStyleSheet("padding: 5px 8px; background-color: #262626; border: 1px solid #3d3d3d; border-radius: 4px; font-size: 11px; margin-bottom: 2px;")
        gl.addWidget(compat_legend)

        self.mods_list = QListWidget()
        self.mods_list.setAlternatingRowColors(True)
        self.mods_list.setStyleSheet("""
            QListWidget {
                background-color: #212121;
                alternate-background-color: #282828;
                color: #e0e0e0;
                border: 1px solid #383838;
                border-radius: 5px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 10px;
                margin: 1px 0;
                border-radius: 3px;
                border-left: 3px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #2e3339;
            }
            QListWidget::item:selected {
                background-color: #283747;
                color: #ffffff;
                border-left: 3px solid #5294e2;
            }
        """)
        gl.addWidget(self.mods_list)

        row = QHBoxLayout()
        for key, slot in [('btn_add_mod', self.add_mod),
                          ('btn_import_collection', self.import_collection),
                          ('btn_remove_mod', self.remove_mod),
                          ('btn_clear_mods', self.clear_mods)]:
            b = QPushButton(tr(key))
            b.setMinimumHeight(30)
            b.setMaximumWidth(240)
            b.clicked.connect(slot)
        row.addStretch()
        self.mod_search_input = QLineEdit()
        self.mod_search_input.setPlaceholderText("🔍 " + tr('search_mods_ph'))
        self.mod_search_input.setClearButtonEnabled(True)
        self.mod_search_input.setMinimumWidth(220)
        self.mod_search_input.setMaximumWidth(300)
        self.mod_search_input.textChanged.connect(self._filter_mods_list)
        row.addWidget(self.mod_search_input)
        gl.addLayout(row)
        layout.addWidget(g, 1)

        # ── Middle Row: Map Load Order (Left) + Import/Export/Presets (Right) ──
        mid_row = QHBoxLayout()
        mid_row.setSpacing(14)

        # Left Column: Map Load Order
        g_maps = QGroupBox(tr('group_map_order'))
        gl_maps = QVBoxLayout(g_maps)
        gl_maps.setContentsMargins(10, 10, 10, 10)
        gl_maps.setSpacing(8)

        lbl_map_hint = QLabel(
            "💡 Модовые карты должны быть выше стандартной карты <b>Muldraugh, KY</b> для корректной генерации мира."
            if get_language() == 'ru' else
            "💡 Custom mod maps must be loaded BEFORE vanilla <b>Muldraugh, KY</b>."
        )
        lbl_map_hint.setStyleSheet("font-size: 11px; color: #a0a0a0;")
        lbl_map_hint.setWordWrap(True)
        gl_maps.addWidget(lbl_map_hint)

        maps_row = QHBoxLayout()
        self.maps_order_list = QListWidget()
        self.maps_order_list.setMinimumHeight(120)
        self.maps_order_list.setMaximumHeight(160)
        self.maps_order_list.setStyleSheet("""
            QListWidget {
                background-color: #212121;
                color: #e0e0e0;
                border: 1px solid #383838;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #283747;
                color: #ffffff;
            }
        """)
        maps_row.addWidget(self.maps_order_list, 1)

        map_btns = QVBoxLayout()
        b_up = QPushButton(tr('btn_move_map_up'))
        b_up.setMinimumHeight(28)
        b_up.setMinimumWidth(90)
        b_up.clicked.connect(self.move_map_up)
        map_btns.addWidget(b_up)

        b_down = QPushButton(tr('btn_move_map_down'))
        b_down.setMinimumHeight(28)
        b_down.setMinimumWidth(90)
        b_down.clicked.connect(self.move_map_down)
        map_btns.addWidget(b_down)

        b_opt = QPushButton(tr('btn_optimize_map_order'))
        b_opt.setMinimumHeight(30)
        b_opt.setMinimumWidth(110)
        b_opt.setStyleSheet("background-color: #264e36; color: #fff; font-size: 11px; font-weight: bold;")
        b_opt.clicked.connect(self.optimize_map_order)
        map_btns.addWidget(b_opt)
        map_btns.addStretch()

        maps_row.addLayout(map_btns)
        gl_maps.addLayout(maps_row)
        mid_row.addWidget(g_maps, 1)

        # Right Column: Import/Export & Presets
        g2 = QGroupBox(tr('group_import_export'))
        iol = QVBoxLayout(g2)
        iol.setContentsMargins(10, 10, 10, 10)
        iol.setSpacing(10)

        io_btns_row = QHBoxLayout()
        bi = QPushButton(tr('btn_import_mods'))
        bi.setMinimumHeight(32)
        bi.clicked.connect(self.import_mods)
        io_btns_row.addWidget(bi)

        be = QPushButton(tr('btn_export_mods'))
        be.setMinimumHeight(32)
        be.clicked.connect(self.export_mods)
        io_btns_row.addWidget(be)
        iol.addLayout(io_btns_row)

        btn_preset_mods = QPushButton("🎁 " + ("Готовые наборы модов" if get_language() == 'ru' else "Mod Presets"))
        btn_preset_mods.setMinimumHeight(36)
        btn_preset_mods.setStyleSheet("background-color: #2b5b7b; color: #ffffff; font-weight: bold; font-size: 13px;")
        btn_preset_mods.setToolTip("Установить популярный готовый набор модов (Машины, Оружие, Интерфейс)" if get_language() == 'ru' else "Load curated mod packs")
        btn_preset_mods.clicked.connect(self.apply_mod_preset_action)
        iol.addWidget(btn_preset_mods)
        iol.addStretch()

        mid_row.addWidget(g2, 1)
        layout.addLayout(mid_row)

        # ── Bottom Action Row ──
        row_save = QHBoxLayout()
        row_save.setSpacing(10)

        btn_mod_sandbox = QPushButton(tr('btn_mod_options_quick'))
        btn_mod_sandbox.setMinimumHeight(34)
        btn_mod_sandbox.setMaximumWidth(280)
        btn_mod_sandbox.setStyleSheet("background-color: #5b3a8c; color: #ffffff; font-weight: bold; padding: 6px 14px;")
        btn_mod_sandbox.setToolTip("Перейти к детальным настройкам установленных модов в песочнице" if get_language() == 'ru' else "Open Mod Sandbox Options in Sandbox tab")
        btn_mod_sandbox.clicked.connect(self.open_mod_sandbox_tab)
        row_save.addWidget(btn_mod_sandbox)

        btn_check_compat = QPushButton("🔍 " + ("Проверить актуальность" if get_language() == 'ru' else "Check Compatibility"))
        btn_check_compat.setMinimumHeight(34)
        btn_check_compat.setMaximumWidth(240)
        btn_check_compat.setStyleSheet("background-color: #2e663e; color: #ffffff; font-weight: bold; padding: 6px 12px;")
        btn_check_compat.setToolTip("Проверить актуальность и совместимость всех модов в Steam Workshop" if get_language() == 'ru' else "Check all mods compatibility in Steam Workshop")
        btn_check_compat.clicked.connect(self.check_mods_compatibility_action)
        row_save.addWidget(btn_check_compat)

        ba = QPushButton(tr('btn_analyze_mods'))
        ba.setMinimumHeight(34)
        ba.setMaximumWidth(220)
        ba.clicked.connect(self.analyze_mods)
        row_save.addWidget(ba)

        row_save.addStretch()

        bs = QPushButton(tr('btn_save_mods'))
        bs.setMinimumHeight(34)
        bs.setMaximumWidth(240)
        bs.setStyleSheet("background-color: #1e6b3b; color: #ffffff; font-weight: bold; padding: 6px 18px;")
        bs.clicked.connect(self.save_mods)
        row_save.addWidget(bs)

        layout.addLayout(row_save)

        self.tabs.addTab(tab, tr('tab_mods'))
        self.update_mods_server_status_banner()

    def _filter_mods_list(self, query: str):
        """Filter mod list by workshop title, name, or workshop ID."""
        q = (query or "").lower().strip()
        if not hasattr(self, 'mods_list'):
            return
        for idx in range(self.mods_list.count()):
            item = self.mods_list.item(idx)
            if not item:
                continue
            item_text = (item.text() or "").lower()
            item_data = str(item.data(Qt.UserRole) or "").lower()
            item.setHidden(bool(q and (q not in item_text and q not in item_data)))

    def update_mods_server_status_banner(self):
        """Update the server readiness banner at the top of the Mods tab."""
        if not hasattr(self, 'mods_server_status_banner') or not hasattr(self, 'lbl_mods_banner_title'):
            return

        try:
            from core.server_installer import get_installed_server_buildid, buildid_to_game_version
            from main import check_server_installed

            is_installed = check_server_installed(self.paths)
            target_build = self.get_current_server_target_version()
            installed_id = get_installed_server_buildid(self.paths['server_dir'])
            installed_ver = buildid_to_game_version(installed_id) if installed_id else None

            lang = get_language()
            is_ru = (lang == 'ru')

            # Case 1: Server NOT installed
            if not is_installed:
                self.mods_server_status_banner.setStyleSheet("""
                    QFrame#ModsServerStatusBanner {
                        background-color: #2b2214;
                        border: 1px solid #734e16;
                        border-radius: 6px;
                    }
                    QFrame#ModsServerStatusBanner QLabel { background: transparent; border: none; }
                """)
                self.lbl_mods_banner_icon.setText("⚠️")
                self.lbl_mods_banner_title.setText(
                    f"Сервер ещё не установлен (целевая версия для модов: Build {target_build})"
                    if is_ru else
                    f"Server is not installed yet (target build for mods: Build {target_build})"
                )
                self.lbl_mods_banner_title.setStyleSheet("color: #ffb74d; font-size: 13px; font-weight: bold; background: transparent;")
                self.lbl_mods_banner_desc.setText(
                    "Сначала скачайте и установите актуальную версию сервера на вкладке «Установка». "
                    "После установки сервер сможет автоматически загружать моды из Steam Workshop."
                    if is_ru else
                    "Please download and install the server first on the 'Install' tab. "
                    "After installation, the server will download mods from Steam Workshop automatically."
                )
                self.lbl_mods_banner_desc.setStyleSheet("color: #e0d0b8; font-size: 11px; background: transparent;")
                self.btn_mods_banner_action.setText("📥 " + ("Установить сервер" if is_ru else "Install Server"))
                self.btn_mods_banner_action.setStyleSheet("background-color: #c67d12; color: #ffffff; font-weight: bold; padding: 6px 14px; border-radius: 4px; font-size: 12px;")
                self.btn_mods_banner_action.setVisible(True)

            # Case 2: Server installed, but version mismatch (e.g. installed B41, target B42)
            elif installed_ver and installed_ver.startswith('41') and target_build == 42:
                self.mods_server_status_banner.setStyleSheet("""
                    QFrame#ModsServerStatusBanner {
                        background-color: #2d1818;
                        border: 1px solid #7a2828;
                        border-radius: 6px;
                    }
                    QFrame#ModsServerStatusBanner QLabel { background: transparent; border: none; }
                """)
                self.lbl_mods_banner_icon.setText("🔴")
                self.lbl_mods_banner_title.setText(
                    f"Несоответствие версий: На диске установлен {installed_ver} (Build 41), а выбрана ветка Build 42"
                    if is_ru else
                    f"Version Mismatch: Installed is {installed_ver} (Build 41), but target is Build 42"
                )
                self.lbl_mods_banner_title.setStyleSheet("color: #ff6b6b; font-size: 13px; font-weight: bold; background: transparent;")
                self.lbl_mods_banner_desc.setText(
                    "Моды Build 42 не запустятся на сервере Build 41! Обновите сервер на вкладке «Установка»."
                    if is_ru else
                    "Build 42 mods will not run on a Build 41 server! Update the server on the Install tab."
                )
                self.lbl_mods_banner_desc.setStyleSheet("color: #e0b8b8; font-size: 11px; background: transparent;")
                self.btn_mods_banner_action.setText("⚡ " + ("Обновить до Build 42" if is_ru else "Update to Build 42"))
                self.btn_mods_banner_action.setStyleSheet("background-color: #b71c1c; color: #ffffff; font-weight: bold; padding: 6px 14px; border-radius: 4px; font-size: 12px;")
                self.btn_mods_banner_action.setVisible(True)

            # Case 3: Server installed and ready
            else:
                ver_text = f"Build {installed_ver}" if installed_ver else f"Build {target_build}"
                self.mods_server_status_banner.setStyleSheet("""
                    QFrame#ModsServerStatusBanner {
                        background-color: #1a251e;
                        border: 1px solid #285433;
                        border-radius: 6px;
                    }
                    QFrame#ModsServerStatusBanner QLabel { background: transparent; border: none; }
                """)
                self.lbl_mods_banner_icon.setText("🟢")
                self.lbl_mods_banner_title.setText(
                    f"Сервер готов: {ver_text} | Проверка совместимости модов: Build {target_build}"
                    if is_ru else
                    f"Server Ready: {ver_text} | Mod Compatibility Target: Build {target_build}"
                )
                self.lbl_mods_banner_title.setStyleSheet("color: #69f0ae; font-size: 13px; font-weight: bold; background: transparent;")
                self.lbl_mods_banner_desc.setText(
                    f"Папка сервера: {self.paths.get('server_dir')}"
                    if is_ru else
                    f"Server directory: {self.paths.get('server_dir')}"
                )
                self.lbl_mods_banner_desc.setStyleSheet("color: #9e9e9e; font-size: 11px; background: transparent;")
                self.btn_mods_banner_action.setVisible(False)
        except Exception as e:
            logger.debug(f"Banner update skipped: {e}")

    def open_mod_sandbox_tab(self):
        """Switch to Sandbox tab and select Mod Options subtab."""
        if hasattr(self, 'tabs'):
            self.tabs.setCurrentIndex(2)
        if hasattr(self, 'sandbox_subtabs'):
            self.sandbox_subtabs.setCurrentIndex(5)

    def load_maps_list(self):
        """Load maps from server configuration into the map order list."""
        if not hasattr(self, 'maps_order_list'):
            return
        self.maps_order_list.clear()
        try:
            name = self.server_name_input.text().strip() or 'servertest'
            self.config_manager.set_server_name(name)
            cfg = self.config_manager.load_server_ini()
            map_str = cfg.get('Map', 'Muldraugh, KY')
            maps = [m.strip() for m in map_str.split(';') if m.strip()]
            if not maps:
                maps = ['Muldraugh, KY']
            for m in maps:
                self.maps_order_list.addItem(m)
        except Exception as e:
            logger.warning(f"Failed to load map order: {e}")

    def move_map_up(self):
        row = self.maps_order_list.currentRow()
        if row > 0:
            item = self.maps_order_list.takeItem(row)
            self.maps_order_list.insertItem(row - 1, item)
            self.maps_order_list.setCurrentRow(row - 1)

    def move_map_down(self):
        row = self.maps_order_list.currentRow()
        if 0 <= row < self.maps_order_list.count() - 1:
            item = self.maps_order_list.takeItem(row)
            self.maps_order_list.insertItem(row + 1, item)
            self.maps_order_list.setCurrentRow(row + 1)

    def optimize_map_order(self):
        """Ensure all custom mod maps precede vanilla Muldraugh, KY."""
        if not hasattr(self, 'maps_order_list'):
            return
        all_maps = [self.maps_order_list.item(i).text() for i in range(self.maps_order_list.count())]
        vanilla = [m for m in all_maps if m in ('Muldraugh, KY', 'Riverside, KY', 'West Point, KY', 'Rosewood, KY')]
        mods = [m for m in all_maps if m not in ('Muldraugh, KY', 'Riverside, KY', 'West Point, KY', 'Rosewood, KY')]
        if not vanilla:
            vanilla = ['Muldraugh, KY']
        new_order = mods + vanilla
        self.maps_order_list.clear()
        for m in new_order:
            self.maps_order_list.addItem(m)
        self.statusBar.showMessage(
            "Порядок карт оптимизирован: кастомные карты загружаются первыми!" if get_language() == 'ru'
            else "Map order optimized: custom maps load first!", 4000
        )

    def get_current_server_target_version(self) -> int:
        """Determine whether the target server is Build 42 or Build 41."""
        if hasattr(self, 'target_server_build') and self.target_server_build in (41, 42):
            return self.target_server_build

        branch = getattr(self, 'selected_branch_key', '')
        if branch:
            return 41 if '41' in str(branch).lower() else 42

        try:
            from core.server_installer import get_installed_server_buildid, buildid_to_game_version
            installed_id = get_installed_server_buildid(self.paths['server_dir'])
            if installed_id:
                v_str = buildid_to_game_version(installed_id)
                if v_str.startswith('41'):
                    return 41
                elif v_str.startswith('42'):
                    return 42
        except Exception:
            pass

        return 42

    def load_mods_list(self):
        if hasattr(self, 'update_mods_server_status_banner'):
            self.update_mods_server_status_banner()
        if hasattr(self, 'load_maps_list'):
            self.load_maps_list()
        self.mods_list.clear()
        target_version = self.get_current_server_target_version()
        try:
            for mod in self.mod_manager.get_mods():
                m_ids = mod.get('mod_ids') or ([mod.get('mod_id')] if mod.get('mod_id') else [])
                m_str = f" [IDs: {', '.join(m_ids)}]" if m_ids else ""

                status, reason = self.mod_manager.check_compatibility(mod, target_build=target_version)
                wid = mod.get('workshop_id', '')
                name = mod.get('name', 'Unknown')

                if status == 'compatible':
                    prefix = "🟢 "
                    badge = f"  —  [✓ B{target_version} Совместим]" if get_language() == 'ru' else f"  —  [✓ B{target_version} Compatible]"
                    color = QColor('#70ff70')
                elif status == 'incompatible':
                    prefix = "🔴 "
                    badge = f"  —  [✗ {reason}]"
                    color = QColor('#ff6b6b')
                else:
                    prefix = "🟡 "
                    badge = f"  —  [{reason}]"
                    color = QColor('#ffd54f')

                item = QListWidgetItem(f"{prefix}[{wid}] {name}{m_str}{badge}")
                item.setForeground(color)

                tags = mod.get('tags', [])
                tags_str = f"\nТеги Steam: {', '.join(tags)}" if tags else ""
                item.setToolTip(
                    f"Название: {name}\n"
                    f"Workshop ID: {wid}\n"
                    f"Статус проверки: {reason}{tags_str}\n"
                    f"Целевая версия сервера: Build {target_version}"
                )
                item.setData(Qt.UserRole, mod)
                self.mods_list.addItem(item)
        except Exception as e:
            logger.exception('Failed to load mods list')

    def add_mod(self):
        wid, ok = QInputDialog.getText(
            self, tr('btn_add_mod'), 'Steam Workshop ID or URL:', QLineEdit.Normal)
        if ok and wid:
            wid = wid.strip()
            cid = self.mod_manager.parse_collection_id(wid)
            if not cid:
                QMessageBox.warning(self, tr('warning'), 'Не удалось распознать Workshop ID или URL.')
                return

            from main import check_server_installed
            if not check_server_installed(self.paths):
                target_build = self.get_current_server_target_version()
                is_ru = (get_language() == 'ru')
                proceed = QMessageBox.question(
                    self,
                    "Сервер не установлен" if is_ru else "Server Not Installed",
                    f"Сервер ещё не установлен в папке:\n{self.paths['server_dir']}\n\n"
                    f"Мод будет добавлен в список под целевую версию Build {target_build}.\n"
                    f"Однако чтобы сервер скачал файлы мода из Steam Workshop и они заработали, "
                    f"сначала необходимо скачать сам сервер на вкладке «Установка».\n\n"
                    f"Продолжить добавление?"
                    if is_ru else
                    f"The server is not yet installed in:\n{self.paths['server_dir']}\n\n"
                    f"The mod will be added for target Build {target_build}.\n"
                    f"However, for the server to download Workshop files and run them, "
                    f"you need to download the server first on the 'Install' tab.\n\n"
                    f"Continue adding?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if proceed != QMessageBox.Yes:
                    return

            # Check if this ID is a collection
            col_mods = self.mod_manager.get_collection_mods(cid)
            if len(col_mods) > 1:
                reply = QMessageBox.question(
                    self,
                    "Импорт коллекции" if get_language() == 'ru' else "Import Collection",
                    f"Обнаружена коллекция ({len(col_mods)} модов)!\nИмпортировать все моды этой коллекции?"
                    if get_language() == 'ru' else
                    f"Detected a Steam Workshop Collection ({len(col_mods)} mods)!\nImport all mods from this collection?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self._do_import_collection(cid)
                    return

            try:
                info = self.mod_manager.add_mod(cid)
                target_version = self.get_current_server_target_version()
                status, reason = self.mod_manager.check_compatibility(info, target_build=target_version)
                self.load_mods_list()

                if status == 'incompatible':
                    QMessageBox.warning(
                        self,
                        "⚠️ Предупреждение о несовместимости!" if get_language() == 'ru' else "⚠️ Compatibility Warning!",
                        f"Внимание!\n\nМод '{info.get('name')}' (ID: {cid}) определен как НЕСОВМЕСТИМЫЙ с текущей версией сервера (Build {target_version})!\n\n"
                        f"• Причина: {reason}\n\n"
                        f"Мод добавлен в список и выделен 🔴 красным цветом.\n"
                        f"Рекомендуется проверить описание мода или удалить его перед запуском сервера во избежание сбоев."
                        if get_language() == 'ru' else
                        f"Warning!\n\nMod '{info.get('name')}' (ID: {cid}) appears to be INCOMPATIBLE with your server version (Build {target_version})!\n\n"
                        f"• Reason: {reason}\n\n"
                        f"The mod was added and highlighted in 🔴 red.\n"
                        f"Please check the mod's workshop page or remove it to prevent server errors."
                    )
                elif status == 'compatible':
                    self.statusBar.showMessage(
                        f"Добавлен мод: {cid} ({info.get('name')}) — 🟢 Совместим с Build {target_version}!"
                        if get_language() == 'ru' else
                        f"Added mod: {cid} ({info.get('name')}) — 🟢 Compatible with Build {target_version}!",
                        4000
                    )
                else:
                    self.statusBar.showMessage(f"Добавлен мод: {cid} ({info.get('name')})", 3000)
            except Exception as e:
                QMessageBox.warning(self, tr('error'), f"Failed to add mod: {e}")

    def check_mods_compatibility_action(self):
        """Batch verify all configured mods for compatibility with the current server version."""
        if not self.mod_manager.mods:
            QMessageBox.information(
                self,
                tr('info'),
                "Список модов пуст. Добавьте моды для проверки." if get_language() == 'ru'
                else "Mod list is empty. Add mods first."
            )
            return

        target_version = self.get_current_server_target_version()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar.showMessage(
            f"Проверка актуальности {len(self.mod_manager.mods)} модов в Steam Workshop..."
            if get_language() == 'ru' else
            f"Checking compatibility of {len(self.mod_manager.mods)} mods with Steam Workshop...",
            10000
        )
        QApplication.processEvents()

        try:
            report = self.mod_manager.check_all_mods_compatibility(target_build=target_version)
            QApplication.processEvents()
            self.load_mods_list()
        finally:
            QApplication.restoreOverrideCursor()

        n_comp = len(report['compatible'])
        n_incomp = len(report['incompatible'])
        n_warn = len(report['warning'])

        msg = (
            f"<b>Результаты проверки совместимости для Build {target_version}:</b><br><br>"
            f"• Всего модов в списке: <b>{report['total']}</b><br>"
            f"• 🟢 Полностью совместимы: <b>{n_comp}</b><br>"
            f"• 🔴 <b>Несовместимы / Устарели: {n_incomp}</b><br>"
            f"• 🟡 Универсальные / Требуют проверки: <b>{n_warn}</b><br><br>"
        )

        if n_incomp > 0:
            msg += "<b>⚠️ Обнаружены потенциально проблемные моды:</b><br>"
            for item in report['incompatible'][:10]:
                m = item['mod']
                msg += f"• 🔴 <b>{m.name}</b> (ID: {m.workshop_id}): {item['reason']}<br>"
            if n_incomp > 10:
                msg += f"<i>...и еще {n_incomp - 10} несовместимых модов (выделены красным в списке).</i><br>"
            msg += "<br><i>Рекомендуется удалить или заменить устаревшие моды во избежание крашей сервера.</i>"
        else:
            msg += "🎉 <b>Отлично! Все моды актуальны и совместимы с версией сервера.</b>"

        QMessageBox.information(
            self,
            "Проверка актуальности модов" if get_language() == 'ru' else "Mod Compatibility Report",
            msg
        )

    def import_collection(self):
        """Prompt user for a Steam Workshop Collection URL or ID and import all mods."""
        url_or_id, ok = QInputDialog.getText(
            self,
            tr('btn_import_collection'),
            tr('msg_collection_prompt'),
            QLineEdit.Normal,
            "https://steamcommunity.com/sharedfiles/filedetails/?id="
        )
        if ok and url_or_id.strip():
            cid = self.mod_manager.parse_collection_id(url_or_id.strip())
            if not cid:
                QMessageBox.warning(self, tr('warning'), 'Некорректная ссылка или ID коллекции.')
                return
            self._do_import_collection(cid)

    def _do_import_collection(self, cid: str):
        self.statusBar.showMessage("Импорт коллекции из Steam Workshop..." if get_language() == 'ru' else "Importing Steam Workshop collection...", 8000)
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            res = self.mod_manager.import_collection(cid)
            self.load_mods_list()
            QApplication.restoreOverrideCursor()

            msg = (
                f"Коллекция {res['collection_id']} успешно загружена!\n\n"
                f"• Всего модов в коллекции: {res['total_items']}\n"
                f"• Добавлено новых: {res['added_count']}\n"
                f"• Обновлено существующих: {res['updated_count']}\n\n"
                f"Все зависимости и порядок загрузки (Load Order) автоматически проверены."
                if get_language() == 'ru' else
                f"Collection {res['collection_id']} successfully imported!\n\n"
                f"• Total mods in collection: {res['total_items']}\n"
                f"• New mods added: {res['added_count']}\n"
                f"• Existing updated: {res['updated_count']}\n\n"
                f"Dependencies and Load Order automatically resolved."
            )
            QMessageBox.information(self, tr('success'), msg)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            logger.exception("Failed to import collection")
            QMessageBox.critical(self, tr('error'), f"Не удалось импортировать коллекцию: {e}")

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

    def analyze_mods(self):
        """Run deep analyzer on all mods and present dependency & load-order report."""
        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.statusBar.showMessage("Анализ модов и зависимостей..." if get_language() == 'ru' else "Analyzing mod dependencies...", 5000)
            QApplication.processEvents()
            name = self.server_name_input.text().strip() or 'servertest'
            self.mod_manager.set_server_name(name)
            report = self.mod_manager.analyze_and_order_mods()
            QApplication.processEvents()
            self.load_mods_list()

            msg_parts = []
            if report.get('missing_workshop_ids'):
                wids_str = "\n".join(f"• ID {item['workshop_id']} (требуется для: {item['needed_by']})" for item in report['missing_workshop_ids'])
                msg_parts.append(
                    f"⚠️ Недостающие моды в Steam Workshop:\n{wids_str}"
                    if get_language() == 'ru' else
                    f"⚠️ Missing Steam Workshop dependencies:\n{wids_str}"
                )

            if report.get('missing_mod_ids'):
                mids_str = "\n".join(f"• ID '{item['mod_id']}' (требуется для: {item['needed_by']})" for item in report['missing_mod_ids'])
                msg_parts.append(
                    f"⚠️ Недостающие внутренние ID зависимостей:\n{mids_str}"
                    if get_language() == 'ru' else
                    f"⚠️ Missing internal Mod IDs:\n{mids_str}"
                )

            if report.get('map_folders'):
                maps_str = ", ".join(report['map_folders'])
                msg_parts.append(
                    f"🗺️ Обнаружены карты модов: {maps_str}"
                    if get_language() == 'ru' else
                    f"🗺️ Detected custom mod maps: {maps_str}"
                )

            if not msg_parts:
                msg_parts.append(tr('msg_mod_analysis_ok'))
            else:
                msg_parts.append(tr('msg_mod_analysis_ok'))

            QMessageBox.information(self, tr('msg_mod_analysis_title'), "\n\n".join(msg_parts))
        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"Ошибка анализа модов: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def save_mods(self):
        try:
            name = self.server_name_input.text().strip() or 'servertest'
            self.mod_manager.set_server_name(name)
            report = self.mod_manager.save_to_config()

            # Save manual map order to servertest.ini if specified
            if hasattr(self, 'maps_order_list') and self.maps_order_list.count() > 0:
                maps_order = [self.maps_order_list.item(i).text() for i in range(self.maps_order_list.count())]
                maps_str = ';'.join(maps_order)
                ini_path = self.config_manager.get_ini_path()
                if ini_path.exists():
                    try:
                        with open(ini_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        map_found = False
                        new_lines = []
                        for line in lines:
                            if line.strip().startswith('Map='):
                                new_lines.append(f"Map={maps_str}\n")
                                map_found = True
                            else:
                                new_lines.append(line)
                        if not map_found:
                            new_lines.append(f"Map={maps_str}\n")
                        with open(ini_path, 'w', encoding='utf-8') as f:
                            f.writelines(new_lines)
                        if hasattr(self, 'setting_map'):
                            self.setting_map.setText(maps_str)
                    except Exception as ex:
                        logger.warning(f"Failed to persist custom map order: {ex}")

            self.load_mods_list()

            from main import check_server_installed
            if not check_server_installed(self.paths):
                QMessageBox.information(
                    self,
                    tr('success'),
                    "Конфигурация модов и карт сохранена!\n\n"
                    "⚠️ Напоминание: сервер ещё не установлен в папке сервера. "
                    "Чтобы игра скачала эти моды из Steam Workshop, перейдите на вкладку «Установка» и установите сервер."
                    if get_language() == 'ru' else
                    "Mod & map configuration saved!\n\n"
                    "⚠️ Reminder: Server is not yet installed in the server directory. "
                    "Please switch to the 'Install' tab and install the server so Steam Workshop mods are downloaded."
                )
            else:
                QMessageBox.information(self, tr('success'), tr('mods_saved'))
        except Exception as e:
            QMessageBox.critical(self, tr('error'), f"Failed to save mods: {e}")

    def apply_mod_preset_action(self):
        """Show curated mod presets dialog and batch import popular mod packs."""
        presets = [
            {
                "id": "vehicles",
                "name": "🚗 Автопарк и тюнинг (KI5 & Autotsar Vehicles)" if get_language() == 'ru' else "🚗 Vehicles & Tuning (KI5 & Autotsar)",
                "desc": "Реалистичные машины, военные внедорожники Humvee, грузовики Oshkosh и мастерская тюнинга." if get_language() == 'ru' else "Realistic cars, military Humvees, Oshkosh trucks, and tuning workshops.",
                "mods": [
                    "1510950729",  # Filibuster Rhymes' Used Cars
                    "2642246942",  # '92 AM General M998 HMMWV
                    "2618213077",  # '82 Oshkosh M911
                    "2386577907",  # Autotsar Tuning Atelier - Jaap Wrath
                    "2788520752",  # Vehicle Scenes
                ]
            },
            {
                "id": "weapons",
                "name": "⚔️ Арсенал и экипировка (Brita Weapon & Armor)" if get_language() == 'ru' else "⚔️ Weapons & Gear (Brita Weapon & Armor)",
                "desc": "Огромный арсенал реалистичного огнестрельного оружия, патронов, обвесов и военной экипировки." if get_language() == 'ru' else "Huge arsenal of firearms, attachments, tactical gear, and body armor.",
                "mods": [
                    "2169435992",  # Mod Options
                    "2297098490",  # Arsenal[26] GunFighter
                    "2200145665",  # Brita's Weapon Pack
                    "2460154811",  # Brita's Armor Pack
                ]
            },
            {
                "id": "qol",
                "name": "🖥️ Удобство и интерфейс (Must-Have QoL & UI)" if get_language() == 'ru' else "🖥️ Must-Have QoL & UI Essentials",
                "desc": "Индикаторы потребностей, взлом замков ломом, метки прочитанных книг, мытье под дождем." if get_language() == 'ru' else "Status bars, crowbar door prying, has-been-read markers, rain wash, and UI improvements.",
                "mods": [
                    "2169435992",  # Mod Options
                    "2875848298",  # Common Sense
                    "2004998206",  # Minimal Display Bars
                    "2544353492",  # Has Been Read
                    "2657661246",  # Rain Wash
                    "2847184718",  # Proximity Inventory
                ]
            },
            {
                "id": "hardcore",
                "name": "🧟 Хардкорный выживач (True Hardcore Survival)" if get_language() == 'ru' else "🧟 True Hardcore Survival Pack",
                "desc": "Расширенные события с вертолетами (сброс припасов), урон зомби о баррикады, аутентичные зомби." if get_language() == 'ru' else "Expanded helicopter events with supply drops, zombies damaged by barricades, authentic zombies.",
                "mods": [
                    "2557792704",  # Expanded Helicopter Events
                    "2913137586",  # Barricades Hurt Zombies
                    "2335368829",  # Authentic Z
                    "2818577583",  # Worse Vehicle Condition
                ]
            }
        ]

        dialog = QDialog(self)
        dialog.setWindowTitle("🎁 Готовые наборы модов" if get_language() == 'ru' else "🎁 Curated Mod Packs")
        dialog.resize(620, 480)
        vlayout = QVBoxLayout(dialog)

        header_lbl = QLabel(
            "<b>Выберите готовый сбалансированный набор модов для добавления на ваш сервер:</b>"
            if get_language() == 'ru' else
            "<b>Choose a curated and balanced mod pack to install on your server:</b>"
        )
        header_lbl.setStyleSheet("font-size: 13px; color: #a0d0ff; margin-bottom: 6px;")
        vlayout.addWidget(header_lbl)

        radio_group = QButtonGroup(dialog)
        radios = []

        for i, p in enumerate(presets):
            box = QGroupBox()
            box.setStyleSheet("QGroupBox { background-color: #2b2b2b; border: 1px solid #444; border-radius: 6px; padding: 8px; margin-bottom: 4px; }")
            blayout = QVBoxLayout(box)

            rb = QRadioButton(p["name"])
            rb.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
            if i == 0:
                rb.setChecked(True)
            radio_group.addButton(rb, i)
            radios.append(rb)
            blayout.addWidget(rb)

            desc = QLabel(f"{p['desc']}\n<i>Workshop IDs: {', '.join(p['mods'])}</i>")
            desc.setStyleSheet("color: #cccccc; font-size: 11px; margin-left: 20px;")
            desc.setWordWrap(True)
            blayout.addWidget(desc)

            vlayout.addWidget(box)

        clear_cb = QCheckBox("Очистить существующий список модов перед установкой" if get_language() == 'ru' else "Clear existing mods before installing preset")
        clear_cb.setStyleSheet("margin-top: 6px; font-weight: bold;")
        vlayout.addWidget(clear_cb)

        btn_box = QHBoxLayout()
        btn_apply = QPushButton("🚀 " + ("Установить выбранный набор" if get_language() == 'ru' else "Install Selected Pack"))
        btn_apply.setStyleSheet("background-color: #1e6b3b; color: #ffffff; font-weight: bold; padding: 8px 16px;")
        btn_apply.clicked.connect(dialog.accept)

        btn_cancel = QPushButton("Отмена" if get_language() == 'ru' else "Cancel")
        btn_cancel.clicked.connect(dialog.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_apply)
        vlayout.addLayout(btn_box)

        if dialog.exec_() != QDialog.Accepted:
            return

        selected_idx = radio_group.checkedId()
        if selected_idx < 0 or selected_idx >= len(presets):
            return

        selected_preset = presets[selected_idx]

        if clear_cb.isChecked():
            self.clear_mods()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar.showMessage(
            f"Установка набора '{selected_preset['name']}'..." if get_language() == 'ru'
            else f"Installing preset '{selected_preset['name']}'...",
            10000
        )

        added_count = 0
        try:
            for wid in selected_preset["mods"]:
                try:
                    self.mod_manager.add_mod(wid)
                    added_count += 1
                except Exception as ex:
                    logger.warning(f"Error adding preset mod {wid}: {ex}")

            self.load_mods_list()
        finally:
            QApplication.restoreOverrideCursor()

        QMessageBox.information(
            self,
            "Набор модов добавлен!" if get_language() == 'ru' else "Mod Preset Installed!",
            f"Набор '{selected_preset['name']}' успешно загружен!\n"
            f"• Добавлено модов: {added_count}\n\n"
            f"Не забудьте нажать 'Сохранить список модов' во вкладке Моды."
            if get_language() == 'ru' else
            f"Preset '{selected_preset['name']}' installed!\n"
            f"• Mods processed: {added_count}\n\n"
            f"Remember to click 'Save Mods' in the Mods tab."
        )
