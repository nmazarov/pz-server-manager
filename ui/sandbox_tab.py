#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sandbox Tab Mixin for PZ Server Manager.
Handles all sandbox variables (ZombieLore, ZombieConfig, Climate, Loot, Vehicles, Mod Options, etc.)
in servertest_SandboxVars.lua with responsive, widescreen-optimized two-column layouts.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox,
    QFormLayout, QScrollArea, QTabWidget, QLineEdit, QMessageBox,
    QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt

from core.translations import tr, get_language

logger = logging.getLogger(__name__)

# ── Sandbox value mappings (UI index → PZ numeric value) ────────────
_ZOMBIE_SPEED        = [('sprinters', 1), ('fast_shamblers', 2), ('shamblers', 3), ('random', 4)]
_ZOMBIE_STRENGTH     = [('superhuman', 1), ('normal', 2), ('weak', 3), ('random', 4)]
_ZOMBIE_TOUGHNESS    = [('tough', 1), ('normal', 2), ('fragile', 3), ('random', 4)]
_ZOMBIE_TRANSMISSION = [('blood_saliva', 1), ('saliva_only', 2), ('everyone_infected', 3), ('none', 4)]
_ZOMBIE_COGNITION    = [('navigate_doors', 1), ('navigate', 2), ('basic_navigation', 3), ('random', 4)]
_ZOMBIE_MEMORY       = [('long', 1), ('normal', 2), ('short', 3), ('none', 4)]
_ZOMBIE_DECOMP       = [('slow', 1), ('normal', 2), ('fast', 3), ('disabled', 4)]
_ZOMBIE_HEARING      = [('very_high', 1), ('normal', 2), ('low', 3)]
_ZOMBIE_SIGHT        = [('eagle', 1), ('normal', 2), ('poor', 3)]
_ZOMBIE_SMELL        = [('normal', 1), ('poor', 2), ('none', 3)]
_ZOMBIE_ACTIVE       = [('both', 1), ('night', 2), ('day', 3)]

_POP_MULTIPLIERS = [
    ('none', 0.0), ('very_low', 0.35), ('low', 0.5),
    ('normal', 1.0), ('high', 1.5), ('very_high', 2.0), ('insane', 4.0),
]

_ZOMBIE_DISTRIBUTION = [('urban_focused', 1), ('uniform', 2)]
_LOOT_RARITY  = [('extremely_rare', 1), ('rare', 2), ('normal', 3), ('common', 4), ('abundant', 5)]
_LOOT_RESPAWN = [('never', 0), ('every_day', 12), ('every_week', 168),
                 ('every_month', 720), ('every_2_months', 1440)]

_DAY_LENGTH   = [
    ('15 min', 1), ('30 min', 2), ('1 h', 3), ('2 h', 4), ('3 h', 5),
    ('4 h', 6), ('5 h', 7), ('6 h', 8), ('12 h', 9), ('Real-time', 10),
]
_START_TIMES  = [('7:00 AM', 1), ('9:00 AM', 2), ('12:00 PM', 3), ('2:00 PM', 4), ('5:00 PM', 5), ('9:00 PM', 6), ('12:00 AM', 7), ('2:00 AM', 8), ('5:00 AM', 9)]
_NIGHT_DARK   = [('pitch_black', 1), ('dark', 2), ('normal', 3), ('bright', 4)]
_NATURE_ABU   = [('very_abundant', 1), ('abundant', 2), ('normal', 3), ('scarce', 4), ('very_scarce', 5)]
_TIME_APO     = [('months_0_3', 1), ('months_3_6', 2), ('months_6_12', 3),
                 ('several_years', 4), ('many_years', 5)]

_CAR_SPAWN    = [('none', 1), ('very_low', 2), ('low', 3), ('normal', 4), ('high', 5)]
_CAR_LEVEL    = [('very_low', 1), ('low', 2), ('normal', 3), ('high', 4), ('very_high', 5)]
_EVENT_FREQ   = [('never', 1), ('once', 2), ('sometimes', 3), ('often', 4)]
_META_FREQ    = [('never', 1), ('sometimes', 2), ('often', 3)]
_FARMING_SPD  = [('very_fast', 1), ('fast', 2), ('normal', 3), ('slow', 4), ('very_slow', 5)]
_GENERATOR_SP = [('extremely_rare', 1), ('rare', 2), ('normal', 3), ('common', 4), ('abundant', 5)]
_EROSION_SPD  = [('very_fast', 1), ('fast', 2), ('normal', 3), ('slow', 4), ('very_slow', 5)]

_INFECTION    = [
    ('instant', 1), ('0_30_sec', 2), ('0_1_min', 3), ('0_12_hours', 4),
    ('1_2_days', 5), ('2_3_days', 6), ('1_week', 7), ('never', 8),
]
_PLAYER_DMG   = [('very_low', 1), ('low', 2), ('normal', 3), ('high', 4), ('very_high', 5)]


def _combo_items(mapping):
    return [tr(k) for k, _ in mapping]


def _safe_int(val, default: int = 0) -> int:
    try:
        if val is None or val == '':
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None or val == '':
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _combo_index(mapping, pz_value, default=0):
    for i, (_, val) in enumerate(mapping):
        if val == pz_value:
            return i
    return default


def _combo_value(mapping, idx: int, default=1):
    if 0 <= idx < len(mapping):
        return mapping[idx][1]
    return default


def _style_form(form: QFormLayout):
    """Apply consistent responsive styling to form layouts."""
    form.setContentsMargins(12, 14, 12, 14)
    form.setSpacing(8)
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)


def _set_ctl_limits(ctl, max_w: int = 280):
    """Limit control width so it doesn't stretch across ultrawide monitors."""
    ctl.setMaximumWidth(max_w)
    ctl.setMinimumWidth(180)


class SandboxTabMixin:
    """Mixin for the Sandbox settings tab with tabbed UI and mod support."""

    def create_sandbox_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Top Bar: Presets & Action Buttons ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        lbl_p = QLabel(f"<b>{tr('lbl_preset')}</b>")
        lbl_p.setStyleSheet("font-size: 13px; color: #e0e0e0;")
        top_bar.addWidget(lbl_p)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(['Custom', 'Apocalypse', 'Survivor', 'Builder'])
        self.preset_combo.setMinimumWidth(160)
        self.preset_combo.setMaximumWidth(220)
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        top_bar.addWidget(self.preset_combo)

        top_bar.addSpacing(10)

        b_save = QPushButton(tr('btn_save_sandbox'))
        b_save.setStyleSheet("background-color: #1e6b3b; color: #ffffff; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        b_save.clicked.connect(self.save_sandbox_settings)
        top_bar.addWidget(b_save)

        b_reload = QPushButton(tr('btn_reload'))
        b_reload.setStyleSheet("padding: 6px 14px;")
        b_reload.clicked.connect(self.load_sandbox_settings)
        top_bar.addWidget(b_reload)

        top_bar.addStretch()

        self.sandbox_search = QLineEdit()
        self.sandbox_search.setPlaceholderText("🔍 " + tr('search_sandbox_ph'))
        self.sandbox_search.setClearButtonEnabled(True)
        self.sandbox_search.setMinimumWidth(240)
        self.sandbox_search.setMaximumWidth(340)
        self.sandbox_search.textChanged.connect(self.filter_sandbox_settings)
        top_bar.addWidget(self.sandbox_search)

        layout.addLayout(top_bar)

        # ── Central Subtabs ──
        self.sandbox_subtabs = QTabWidget()
        self.sandbox_subtabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3c3c3c; background-color: #1a1a1a; border-radius: 4px; }
            QTabBar::tab { background: #252525; color: #bbb; padding: 8px 16px; margin-right: 3px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #333333; color: #40ff40; font-weight: bold; border-bottom: 2px solid #40ff40; }
            QTabBar::tab:hover { background: #2c2c2c; color: #fff; }
        """)

        self._sandbox_subtab_names = [
            tr('subtab_zombies'), tr('subtab_loot'), tr('subtab_world'),
            tr('subtab_vehicles'), tr('subtab_character'), tr('subtab_mods')
        ]

        # Tab 1: Zombies & Population (2 Columns)
        self.sandbox_subtabs.addTab(self._create_zombies_subtab(), self._sandbox_subtab_names[0])
        # Tab 2: Loot & Resources (2 Columns)
        self.sandbox_subtabs.addTab(self._create_loot_subtab(), self._sandbox_subtab_names[1])
        # Tab 3: World & Time (2 Columns)
        self.sandbox_subtabs.addTab(self._create_world_subtab(), self._sandbox_subtab_names[2])
        # Tab 4: Vehicles (2 Columns)
        self.sandbox_subtabs.addTab(self._create_vehicles_subtab(), self._sandbox_subtab_names[3])
        # Tab 5: Character & Skills (2 Columns)
        self.sandbox_subtabs.addTab(self._create_character_subtab(), self._sandbox_subtab_names[4])
        # Tab 6: Mod Sandbox Options (Clean Informative Card Table)
        self.sandbox_subtabs.addTab(self._create_mods_subtab(), self._sandbox_subtab_names[5])

        layout.addWidget(self.sandbox_subtabs)
        self.tabs.addTab(tab, tr('tab_sandbox'))

    def filter_sandbox_settings(self, query: str):
        """Filter visible settings rows across all sandbox subtabs dynamically."""
        q = (query or "").lower().strip()
        subtab_names = getattr(self, '_sandbox_subtab_names', None)
        if not subtab_names:
            subtab_names = [
                tr('subtab_zombies'), tr('subtab_loot'), tr('subtab_world'),
                tr('subtab_vehicles'), tr('subtab_character'), tr('subtab_mods')
            ]
            self._sandbox_subtab_names = subtab_names

        if not q:
            for idx in range(self.sandbox_subtabs.count()):
                if idx < len(subtab_names):
                    self.sandbox_subtabs.setTabText(idx, subtab_names[idx])
                w = self.sandbox_subtabs.widget(idx)
                if w:
                    for gb in w.findChildren(QGroupBox):
                        gb.setVisible(True)
                        for form in gb.findChildren(QFormLayout):
                            for r in range(form.rowCount()):
                                item_lbl = form.itemAt(r, QFormLayout.LabelRole)
                                item_fld = form.itemAt(r, QFormLayout.FieldRole)
                                if item_lbl and item_lbl.widget():
                                    item_lbl.widget().setVisible(True)
                                if item_fld and item_fld.widget():
                                    item_fld.widget().setVisible(True)
                        for cb in gb.findChildren(QCheckBox):
                            cb.setVisible(True)
            return

        first_match_idx = -1
        for idx in range(self.sandbox_subtabs.count()):
            subtab_w = self.sandbox_subtabs.widget(idx)
            orig_name = subtab_names[idx] if idx < len(subtab_names) else self.sandbox_subtabs.tabText(idx)
            tab_matches = 0

            if subtab_w:
                for gb in subtab_w.findChildren(QGroupBox):
                    gb_title_match = q in gb.title().lower()
                    gb_has_visible_child = False

                    for form in gb.findChildren(QFormLayout):
                        for r in range(form.rowCount()):
                            item_lbl = form.itemAt(r, QFormLayout.LabelRole)
                            item_fld = form.itemAt(r, QFormLayout.FieldRole)
                            row_lbl = item_lbl.widget() if item_lbl else None
                            row_fld = item_fld.widget() if item_fld else None

                            lbl_text = (row_lbl.text() if row_lbl and hasattr(row_lbl, 'text') else "")
                            tip_text = (row_lbl.toolTip() if row_lbl else "") or (row_fld.toolTip() if row_fld else "")
                            fld_match = False
                            if row_fld and hasattr(row_fld, 'currentText'):
                                fld_match = q in row_fld.currentText().lower()

                            row_match = gb_title_match or (q in lbl_text.lower()) or (q in tip_text.lower()) or fld_match

                            if row_lbl:
                                row_lbl.setVisible(row_match)
                            if row_fld:
                                row_fld.setVisible(row_match)

                            if row_match:
                                tab_matches += 1
                                gb_has_visible_child = True

                    for cb in gb.findChildren(QCheckBox):
                        cb_text = cb.text() or ""
                        cb_tip = cb.toolTip() or ""
                        cb_match = gb_title_match or (q in cb_text.lower()) or (q in cb_tip.lower())
                        cb.setVisible(cb_match)
                        if cb_match:
                            tab_matches += 1
                            gb_has_visible_child = True

                    gb.setVisible(gb_has_visible_child)

            if tab_matches > 0:
                self.sandbox_subtabs.setTabText(idx, f"{orig_name} ({tab_matches})")
                if first_match_idx == -1:
                    first_match_idx = idx
            else:
                self.sandbox_subtabs.setTabText(idx, f"{orig_name} (0)")

        current_idx = self.sandbox_subtabs.currentIndex()
        if first_match_idx != -1 and self.sandbox_subtabs.tabText(current_idx).endswith("(0)"):
            self.sandbox_subtabs.setCurrentIndex(first_match_idx)

    # ── Subtab 1: Zombies & Population (2 Columns) ────────────────────
    def _create_zombies_subtab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 10, 10, 10)

        cols = QHBoxLayout()
        cols.setSpacing(14)

        # Left Column: Basic Zombie Lore
        g_lore = QGroupBox(tr('group_zombie_lore'))
        f_lore = QFormLayout(g_lore)
        _style_form(f_lore)

        self.sandbox_zombie_speed = QComboBox()
        self.sandbox_zombie_speed.addItems(_combo_items(_ZOMBIE_SPEED))
        _set_ctl_limits(self.sandbox_zombie_speed)
        f_lore.addRow(tr('lbl_speed'), self.sandbox_zombie_speed)

        self.sandbox_zombie_strength = QComboBox()
        self.sandbox_zombie_strength.addItems(_combo_items(_ZOMBIE_STRENGTH))
        _set_ctl_limits(self.sandbox_zombie_strength)
        f_lore.addRow(tr('lbl_strength'), self.sandbox_zombie_strength)

        self.sandbox_zombie_toughness = QComboBox()
        self.sandbox_zombie_toughness.addItems(_combo_items(_ZOMBIE_TOUGHNESS))
        _set_ctl_limits(self.sandbox_zombie_toughness)
        f_lore.addRow(tr('lbl_toughness'), self.sandbox_zombie_toughness)

        self.sandbox_zombie_transmission = QComboBox()
        self.sandbox_zombie_transmission.addItems(_combo_items(_ZOMBIE_TRANSMISSION))
        _set_ctl_limits(self.sandbox_zombie_transmission)
        f_lore.addRow(tr('lbl_transmission'), self.sandbox_zombie_transmission)

        self.sandbox_infection_mortality = QComboBox()
        self.sandbox_infection_mortality.addItems(_combo_items(_INFECTION))
        _set_ctl_limits(self.sandbox_infection_mortality)
        f_lore.addRow(tr('lbl_infection_mortality'), self.sandbox_infection_mortality)

        self.sandbox_zombie_cognition = QComboBox()
        self.sandbox_zombie_cognition.addItems(_combo_items(_ZOMBIE_COGNITION))
        _set_ctl_limits(self.sandbox_zombie_cognition)
        f_lore.addRow(tr('lbl_cognition'), self.sandbox_zombie_cognition)

        self.sandbox_memory = QComboBox()
        self.sandbox_memory.addItems(_combo_items(_ZOMBIE_MEMORY))
        _set_ctl_limits(self.sandbox_memory)
        f_lore.addRow(tr('lbl_memory'), self.sandbox_memory)

        self.sandbox_decomp = QComboBox()
        self.sandbox_decomp.addItems(_combo_items(_ZOMBIE_DECOMP))
        _set_ctl_limits(self.sandbox_decomp)
        f_lore.addRow(tr('lbl_decomp'), self.sandbox_decomp)

        self.sandbox_sight = QComboBox()
        self.sandbox_sight.addItems(_combo_items(_ZOMBIE_SIGHT))
        _set_ctl_limits(self.sandbox_sight)
        f_lore.addRow(tr('lbl_sight'), self.sandbox_sight)

        self.sandbox_hearing = QComboBox()
        self.sandbox_hearing.addItems(_combo_items(_ZOMBIE_HEARING))
        _set_ctl_limits(self.sandbox_hearing)
        f_lore.addRow(tr('lbl_hearing'), self.sandbox_hearing)

        self.sandbox_smell = QComboBox()
        self.sandbox_smell.addItems(_combo_items(_ZOMBIE_SMELL))
        _set_ctl_limits(self.sandbox_smell)
        f_lore.addRow(tr('lbl_smell'), self.sandbox_smell)

        self.sandbox_zombie_active = QComboBox()
        self.sandbox_zombie_active.addItems([tr(k) for k, _ in _ZOMBIE_ACTIVE])
        _set_ctl_limits(self.sandbox_zombie_active)
        f_lore.addRow("Активность зомби:" if get_language() == 'ru' else "Active Time:", self.sandbox_zombie_active)

        self.sandbox_zombie_distribution = QComboBox()
        self.sandbox_zombie_distribution.addItems(_combo_items(_ZOMBIE_DISTRIBUTION))
        _set_ctl_limits(self.sandbox_zombie_distribution)
        f_lore.addRow(tr('lbl_distribution'), self.sandbox_zombie_distribution)

        self.sandbox_thump_no_chasing = QCheckBox("Атаковать двери/стены без преследования" if get_language() == 'ru' else "Thump doors/walls without chasing")
        f_lore.addRow(self.sandbox_thump_no_chasing)

        self.sandbox_thump_on_construction = QCheckBox("Атаковать постройки игроков" if get_language() == 'ru' else "Damage player constructions")
        self.sandbox_thump_on_construction.setChecked(True)
        f_lore.addRow(self.sandbox_thump_on_construction)

        self.sandbox_trigger_alarm = QCheckBox("Зомби вызывают сигнализацию в домах" if get_language() == 'ru' else "Zombies trigger house alarms")
        f_lore.addRow(self.sandbox_trigger_alarm)

        cols.addWidget(g_lore, 1)

        # Right Column: Advanced Zombie Config
        g_adv = QGroupBox(tr('group_zombie_advanced'))
        f_adv = QFormLayout(g_adv)
        _style_form(f_adv)

        self.sandbox_pop_mult = QDoubleSpinBox()
        self.sandbox_pop_mult.setRange(0.0, 10.0)
        self.sandbox_pop_mult.setSingleStep(0.1)
        self.sandbox_pop_mult.setValue(1.0)
        _set_ctl_limits(self.sandbox_pop_mult, 140)
        f_adv.addRow(tr('lbl_pop_multiplier'), self.sandbox_pop_mult)

        self.sandbox_pop_start_mult = QDoubleSpinBox()
        self.sandbox_pop_start_mult.setRange(0.0, 10.0)
        self.sandbox_pop_start_mult.setSingleStep(0.1)
        self.sandbox_pop_start_mult.setValue(1.0)
        _set_ctl_limits(self.sandbox_pop_start_mult, 140)
        f_adv.addRow(tr('lbl_pop_start_mult'), self.sandbox_pop_start_mult)

        self.sandbox_pop_peak_mult = QDoubleSpinBox()
        self.sandbox_pop_peak_mult.setRange(0.0, 10.0)
        self.sandbox_pop_peak_mult.setSingleStep(0.1)
        self.sandbox_pop_peak_mult.setValue(1.5)
        _set_ctl_limits(self.sandbox_pop_peak_mult, 140)
        f_adv.addRow(tr('lbl_pop_peak_mult'), self.sandbox_pop_peak_mult)

        self.sandbox_pop_peak_day = QSpinBox()
        self.sandbox_pop_peak_day.setRange(1, 365)
        self.sandbox_pop_peak_day.setValue(28)
        self.sandbox_pop_peak_day.setSuffix(f" {tr('days')}")
        _set_ctl_limits(self.sandbox_pop_peak_day, 140)
        f_adv.addRow(tr('lbl_pop_peak_day'), self.sandbox_pop_peak_day)

        self.sandbox_respawn_hours = QSpinBox()
        self.sandbox_respawn_hours.setRange(0, 8760)
        self.sandbox_respawn_hours.setValue(72)
        self.sandbox_respawn_hours.setSuffix(" ч.")
        _set_ctl_limits(self.sandbox_respawn_hours, 140)
        f_adv.addRow(tr('lbl_respawn_hours'), self.sandbox_respawn_hours)

        self.sandbox_respawn_unseen_hours = QSpinBox()
        self.sandbox_respawn_unseen_hours.setRange(0, 8760)
        self.sandbox_respawn_unseen_hours.setValue(16)
        self.sandbox_respawn_unseen_hours.setSuffix(" ч.")
        _set_ctl_limits(self.sandbox_respawn_unseen_hours, 140)
        f_adv.addRow(tr('lbl_respawn_unseen_hours'), self.sandbox_respawn_unseen_hours)

        self.sandbox_respawn_mult = QDoubleSpinBox()
        self.sandbox_respawn_mult.setRange(0.0, 1.0)
        self.sandbox_respawn_mult.setSingleStep(0.05)
        self.sandbox_respawn_mult.setValue(0.1)
        _set_ctl_limits(self.sandbox_respawn_mult, 140)
        f_adv.addRow(tr('lbl_respawn_fraction'), self.sandbox_respawn_mult)

        self.sandbox_redistribute_hours = QSpinBox()
        self.sandbox_redistribute_hours.setRange(0, 8760)
        self.sandbox_redistribute_hours.setValue(12)
        self.sandbox_redistribute_hours.setSuffix(" ч.")
        _set_ctl_limits(self.sandbox_redistribute_hours, 140)
        f_adv.addRow(tr('lbl_redistribute_hours'), self.sandbox_redistribute_hours)

        self.sandbox_rally_size = QSpinBox()
        self.sandbox_rally_size.setRange(0, 500)
        self.sandbox_rally_size.setValue(20)
        _set_ctl_limits(self.sandbox_rally_size, 140)
        f_adv.addRow(tr('lbl_rally_group_size'), self.sandbox_rally_size)

        self.sandbox_rally_radius = QSpinBox()
        self.sandbox_rally_radius.setRange(1, 50)
        self.sandbox_rally_radius.setValue(3)
        _set_ctl_limits(self.sandbox_rally_radius, 140)
        f_adv.addRow(tr('lbl_rally_group_radius'), self.sandbox_rally_radius)

        cols.addWidget(g_adv, 1)

        sl.addLayout(cols)
        sl.addStretch()
        scroll.setWidget(sw)
        return scroll

    # ── Subtab 2: Loot & Resources (2 Columns) ─────────────────────────
    def _create_loot_subtab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 10, 10, 10)

        cols = QHBoxLayout()
        cols.setSpacing(14)

        # Left Column: 10 In-game Loot Categories
        g_cats = QGroupBox(tr('group_loot_categories'))
        f_cats = QFormLayout(g_cats)
        _style_form(f_cats)

        self.loot_combos = {}
        loot_keys = [
            ('WeaponLoot', 'lbl_loot_weapons', 2),
            ('RangedWeaponLoot', 'lbl_loot_ranged_weapons', 2),
            ('AmmoLoot', 'lbl_loot_ammo', 2),
            ('FoodLoot', 'lbl_loot_food', 3),
            ('CannedFoodLoot', 'lbl_loot_canned_food', 2),
            ('MedicalLoot', 'lbl_loot_medical', 2),
            ('LiteratureLoot', 'lbl_loot_literature', 2),
            ('SurvivalGearsLoot', 'lbl_loot_survival', 2),
            ('MechanicsLoot', 'lbl_loot_mechanics', 2),
            ('OtherLoot', 'lbl_loot_other', 3),
        ]
        for key, tr_key, def_idx in loot_keys:
            cb = QComboBox()
            cb.addItems(_combo_items(_LOOT_RARITY))
            cb.setCurrentIndex(def_idx)
            _set_ctl_limits(cb, 260)
            f_cats.addRow(tr(tr_key), cb)
            self.loot_combos[key] = cb

        cols.addWidget(g_cats, 1)

        # Right Column: Loot Respawn & Utilities
        g_respawn = QGroupBox(tr('group_loot_respawn'))
        f_respawn = QFormLayout(g_respawn)
        _style_form(f_respawn)

        self.sandbox_loot_respawn = QComboBox()
        self.sandbox_loot_respawn.addItems(_combo_items(_LOOT_RESPAWN))
        _set_ctl_limits(self.sandbox_loot_respawn, 260)
        f_respawn.addRow(tr('lbl_loot_respawn'), self.sandbox_loot_respawn)

        self.sandbox_max_items_respawn = QSpinBox()
        self.sandbox_max_items_respawn.setRange(1, 100)
        self.sandbox_max_items_respawn.setValue(4)
        _set_ctl_limits(self.sandbox_max_items_respawn, 140)
        f_respawn.addRow(tr('lbl_max_items_respawn'), self.sandbox_max_items_respawn)

        self.sandbox_construction_respawn = QCheckBox(
            "Постройки игроков блокируют респаун лута" if get_language() == 'ru'
            else "Player construction prevents loot respawn"
        )
        self.sandbox_construction_respawn.setChecked(True)
        f_respawn.addRow(self.sandbox_construction_respawn)

        self.sandbox_water_shutoff = QSpinBox()
        self.sandbox_water_shutoff.setRange(0, 365)
        self.sandbox_water_shutoff.setValue(14)
        self.sandbox_water_shutoff.setSpecialValueText(tr('never'))
        self.sandbox_water_shutoff.setSuffix(f" {tr('days')}")
        _set_ctl_limits(self.sandbox_water_shutoff, 140)
        f_respawn.addRow(tr('lbl_water_shutoff'), self.sandbox_water_shutoff)

        self.sandbox_electricity_shutoff = QSpinBox()
        self.sandbox_electricity_shutoff.setRange(0, 365)
        self.sandbox_electricity_shutoff.setValue(14)
        self.sandbox_electricity_shutoff.setSpecialValueText(tr('never'))
        self.sandbox_electricity_shutoff.setSuffix(f" {tr('days')}")
        _set_ctl_limits(self.sandbox_electricity_shutoff, 140)
        f_respawn.addRow(tr('lbl_electricity_shutoff'), self.sandbox_electricity_shutoff)

        cols.addWidget(g_respawn, 1)

        sl.addLayout(cols)
        sl.addStretch()
        scroll.setWidget(sw)
        return scroll

    # ── Subtab 3: World & Time (2 Columns) ─────────────────────────────
    def _create_world_subtab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 10, 10, 10)

        cols = QHBoxLayout()
        cols.setSpacing(14)

        # Left Column: Time & Calendar
        g_time = QGroupBox(tr('group_time'))
        f_time = QFormLayout(g_time)
        _style_form(f_time)

        self.sandbox_day_length = QComboBox()
        self.sandbox_day_length.addItems([k for k, _ in _DAY_LENGTH])
        self.sandbox_day_length.setCurrentIndex(2)  # 1h default
        _set_ctl_limits(self.sandbox_day_length, 260)
        f_time.addRow(tr('lbl_day_length'), self.sandbox_day_length)

        self.sandbox_start_year = QSpinBox()
        self.sandbox_start_year.setRange(1, 100)
        self.sandbox_start_year.setValue(1)
        _set_ctl_limits(self.sandbox_start_year, 140)
        f_time.addRow("Начальный год:" if get_language() == 'ru' else "Start Year:", self.sandbox_start_year)

        self.sandbox_start_month = QComboBox()
        months = ['january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december']
        self.sandbox_start_month.addItems([tr(m) for m in months])
        self.sandbox_start_month.setCurrentIndex(6)  # July
        _set_ctl_limits(self.sandbox_start_month, 260)
        f_time.addRow(tr('lbl_start_month'), self.sandbox_start_month)

        self.sandbox_start_day = QSpinBox()
        self.sandbox_start_day.setRange(1, 31)
        self.sandbox_start_day.setValue(9)
        _set_ctl_limits(self.sandbox_start_day, 140)
        f_time.addRow(tr('lbl_start_day'), self.sandbox_start_day)

        self.sandbox_start_time = QComboBox()
        self.sandbox_start_time.addItems([k for k, _ in _START_TIMES])
        self.sandbox_start_time.setCurrentIndex(1)  # 9:00 AM
        _set_ctl_limits(self.sandbox_start_time, 260)
        f_time.addRow("Время старта:" if get_language() == 'ru' else "Start Time:", self.sandbox_start_time)

        self.sandbox_night_darkness = QComboBox()
        self.sandbox_night_darkness.addItems(_combo_items(_NIGHT_DARK))
        self.sandbox_night_darkness.setCurrentIndex(2)  # normal
        _set_ctl_limits(self.sandbox_night_darkness, 260)
        f_time.addRow(tr('lbl_night_darkness'), self.sandbox_night_darkness)

        self.sandbox_time_since_apo = QComboBox()
        self.sandbox_time_since_apo.addItems(_combo_items(_TIME_APO))
        _set_ctl_limits(self.sandbox_time_since_apo, 260)
        f_time.addRow(tr('lbl_time_since_apo'), self.sandbox_time_since_apo)

        cols.addWidget(g_time, 1)

        # Right Column: Environment & Events
        g_env = QGroupBox(tr('group_world'))
        f_env = QFormLayout(g_env)
        _style_form(f_env)

        self.sandbox_fire_spread = QCheckBox("Распространение огня по постройкам и деревьям" if get_language() == 'ru' else "Fire spreads to buildings/trees")
        self.sandbox_fire_spread.setChecked(True)
        f_env.addRow(self.sandbox_fire_spread)

        self.sandbox_nature_abundance = QComboBox()
        self.sandbox_nature_abundance.addItems(_combo_items(_NATURE_ABU))
        self.sandbox_nature_abundance.setCurrentIndex(2)
        _set_ctl_limits(self.sandbox_nature_abundance, 260)
        f_env.addRow(tr('lbl_nature_abundance'), self.sandbox_nature_abundance)

        self.sandbox_helicopter = QComboBox()
        self.sandbox_helicopter.addItems(_combo_items(_EVENT_FREQ))
        self.sandbox_helicopter.setCurrentIndex(1)  # once
        _set_ctl_limits(self.sandbox_helicopter, 260)
        f_env.addRow(tr('lbl_helicopter'), self.sandbox_helicopter)

        self.sandbox_meta_event = QComboBox()
        self.sandbox_meta_event.addItems(_combo_items(_META_FREQ))
        self.sandbox_meta_event.setCurrentIndex(1)  # sometimes
        _set_ctl_limits(self.sandbox_meta_event, 260)
        f_env.addRow(tr('lbl_meta_event'), self.sandbox_meta_event)

        self.sandbox_sleeping_event = QComboBox()
        self.sandbox_sleeping_event.addItems(_combo_items(_META_FREQ))
        self.sandbox_sleeping_event.setCurrentIndex(1)  # sometimes
        _set_ctl_limits(self.sandbox_sleeping_event, 260)
        f_env.addRow(tr('lbl_sleeping_event'), self.sandbox_sleeping_event)

        self.sandbox_erosion_speed = QComboBox()
        self.sandbox_erosion_speed.addItems(_combo_items(_EROSION_SPD))
        self.sandbox_erosion_speed.setCurrentIndex(2)  # normal
        _set_ctl_limits(self.sandbox_erosion_speed, 260)
        f_env.addRow(tr('lbl_erosion_speed'), self.sandbox_erosion_speed)

        self.sandbox_erosion_days = QSpinBox()
        self.sandbox_erosion_days.setRange(0, 3650)
        self.sandbox_erosion_days.setValue(100)
        self.sandbox_erosion_days.setSuffix(f" {tr('days')}")
        _set_ctl_limits(self.sandbox_erosion_days, 140)
        f_env.addRow(tr('lbl_erosion_days'), self.sandbox_erosion_days)

        cols.addWidget(g_env, 1)

        sl.addLayout(cols)
        sl.addStretch()
        scroll.setWidget(sw)
        return scroll

    # ── Subtab 4: Vehicles (2 Columns) ─────────────────────────────────
    def _create_vehicles_subtab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 10, 10, 10)

        cols = QHBoxLayout()
        cols.setSpacing(14)

        # Left Column: Spawns & State
        g_veh = QGroupBox("Появление и состояние транспорта" if get_language() == 'ru' else "Vehicle Spawn & Condition")
        f_veh = QFormLayout(g_veh)
        _style_form(f_veh)

        self.sandbox_car_spawn = QComboBox()
        self.sandbox_car_spawn.addItems(_combo_items(_CAR_SPAWN))
        self.sandbox_car_spawn.setCurrentIndex(3)  # normal
        _set_ctl_limits(self.sandbox_car_spawn, 260)
        f_veh.addRow(tr('lbl_car_spawn'), self.sandbox_car_spawn)

        self.sandbox_vehicle_easy_use = QCheckBox("Легкое управление (без ключа зажигания и взлома)" if get_language() == 'ru' else "Easy use (no keys/hotwiring needed)")
        self.sandbox_vehicle_easy_use.setChecked(False)
        f_veh.addRow(self.sandbox_vehicle_easy_use)

        self.sandbox_car_condition = QComboBox()
        self.sandbox_car_condition.addItems(_combo_items(_CAR_LEVEL))
        self.sandbox_car_condition.setCurrentIndex(2)  # normal
        _set_ctl_limits(self.sandbox_car_condition, 260)
        f_veh.addRow(tr('lbl_car_condition'), self.sandbox_car_condition)

        self.sandbox_traffic_jam = QCheckBox("Заторы и пробки из разбитых машин на дорогах" if get_language() == 'ru' else "Traffic jams on roads")
        self.sandbox_traffic_jam.setChecked(True)
        f_veh.addRow(self.sandbox_traffic_jam)

        cols.addWidget(g_veh, 1)

        # Right Column: Fuel & Mechanics
        g_fuel = QGroupBox("Топливо и механика" if get_language() == 'ru' else "Fuel & Mechanics")
        f_fuel = QFormLayout(g_fuel)
        _style_form(f_fuel)

        self.sandbox_chance_gas = QComboBox()
        self.sandbox_chance_gas.addItems(_combo_items(_CAR_LEVEL))
        self.sandbox_chance_gas.setCurrentIndex(2)  # normal
        _set_ctl_limits(self.sandbox_chance_gas, 260)
        f_fuel.addRow(tr('lbl_gas_chance'), self.sandbox_chance_gas)

        self.sandbox_initial_gas = QComboBox()
        self.sandbox_initial_gas.addItems(_combo_items(_CAR_LEVEL))
        self.sandbox_initial_gas.setCurrentIndex(1)  # low
        _set_ctl_limits(self.sandbox_initial_gas, 260)
        f_fuel.addRow(tr('lbl_initial_gas'), self.sandbox_initial_gas)

        self.sandbox_gas_consumption = QDoubleSpinBox()
        self.sandbox_gas_consumption.setRange(0.0, 10.0)
        self.sandbox_gas_consumption.setSingleStep(0.1)
        self.sandbox_gas_consumption.setValue(1.0)
        _set_ctl_limits(self.sandbox_gas_consumption, 140)
        f_fuel.addRow(tr('lbl_gas_consumption'), self.sandbox_gas_consumption)

        self.sandbox_car_alarm = QComboBox()
        self.sandbox_car_alarm.addItems(_combo_items(_EVENT_FREQ))
        self.sandbox_car_alarm.setCurrentIndex(2)  # sometimes
        _set_ctl_limits(self.sandbox_car_alarm, 260)
        f_fuel.addRow(tr('lbl_car_alarm'), self.sandbox_car_alarm)

        self.sandbox_crash_damage = QCheckBox("Урон игроку при столкновении на машине" if get_language() == 'ru' else "Player damaged in vehicle crashes")
        self.sandbox_crash_damage.setChecked(True)
        f_fuel.addRow(self.sandbox_crash_damage)

        cols.addWidget(g_fuel, 1)

        sl.addLayout(cols)
        sl.addStretch()
        scroll.setWidget(sw)
        return scroll

    # ── Subtab 5: Character & Skills (2 Columns) ───────────────────────
    def _create_character_subtab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(10, 10, 10, 10)

        cols = QHBoxLayout()
        cols.setSpacing(14)

        # Left Column: XP & Points
        g_char = QGroupBox(tr('group_character'))
        f_char = QFormLayout(g_char)
        _style_form(f_char)

        xp_row = QHBoxLayout()
        xp_row.setSpacing(6)
        self.sandbox_xp_mult = QDoubleSpinBox()
        self.sandbox_xp_mult.setRange(0.1, 100.0)
        self.sandbox_xp_mult.setSingleStep(0.5)
        self.sandbox_xp_mult.setValue(1.0)
        self.sandbox_xp_mult.setFixedWidth(80)
        xp_row.addWidget(self.sandbox_xp_mult)

        for mult_val in [1.0, 1.5, 2.0, 3.0, 5.0]:
            btn = QPushButton(f"{mult_val:g}x")
            btn.setStyleSheet("padding: 3px 6px; font-size: 11px;")
            btn.clicked.connect(lambda _, v=mult_val: self.sandbox_xp_mult.setValue(v))
            xp_row.addWidget(btn)
        xp_row.addStretch()
        f_char.addRow(tr('lbl_xp_multiplier'), xp_row)

        self.sandbox_char_free_points = QSpinBox()
        self.sandbox_char_free_points.setRange(0, 100)
        self.sandbox_char_free_points.setValue(0)
        _set_ctl_limits(self.sandbox_char_free_points, 140)
        f_char.addRow(tr('lbl_char_free_points'), self.sandbox_char_free_points)

        self.sandbox_player_damage = QComboBox()
        self.sandbox_player_damage.addItems(_combo_items(_PLAYER_DMG))
        self.sandbox_player_damage.setCurrentIndex(2)
        _set_ctl_limits(self.sandbox_player_damage, 260)
        f_char.addRow(tr('lbl_player_damage'), self.sandbox_player_damage)

        cols.addWidget(g_char, 1)

        # Right Column: Farming & Generators
        g_farm = QGroupBox("Фермерство и генераторы" if get_language() == 'ru' else "Farming & Generators")
        f_farm = QFormLayout(g_farm)
        _style_form(f_farm)

        self.sandbox_farming_speed = QComboBox()
        self.sandbox_farming_speed.addItems(_combo_items(_FARMING_SPD))
        self.sandbox_farming_speed.setCurrentIndex(2)
        _set_ctl_limits(self.sandbox_farming_speed, 260)
        f_farm.addRow(tr('lbl_farming_speed'), self.sandbox_farming_speed)

        self.sandbox_plant_resilience = QComboBox()
        self.sandbox_plant_resilience.addItems(_combo_items(_CAR_LEVEL))
        self.sandbox_plant_resilience.setCurrentIndex(2)
        _set_ctl_limits(self.sandbox_plant_resilience, 260)
        f_farm.addRow(tr('lbl_plant_resilience'), self.sandbox_plant_resilience)

        self.sandbox_plant_abundance = QComboBox()
        self.sandbox_plant_abundance.addItems(_combo_items(_CAR_LEVEL))
        self.sandbox_plant_abundance.setCurrentIndex(2)
        _set_ctl_limits(self.sandbox_plant_abundance, 260)
        f_farm.addRow(tr('lbl_plant_abundance'), self.sandbox_plant_abundance)

        self.sandbox_generator_spawn = QComboBox()
        self.sandbox_generator_spawn.addItems(_combo_items(_GENERATOR_SP))
        self.sandbox_generator_spawn.setCurrentIndex(2)
        _set_ctl_limits(self.sandbox_generator_spawn, 260)
        f_farm.addRow(tr('lbl_generator_spawn'), self.sandbox_generator_spawn)

        self.sandbox_generator_fuel = QDoubleSpinBox()
        self.sandbox_generator_fuel.setRange(0.0, 10.0)
        self.sandbox_generator_fuel.setSingleStep(0.1)
        self.sandbox_generator_fuel.setValue(1.0)
        _set_ctl_limits(self.sandbox_generator_fuel, 140)
        f_farm.addRow(tr('lbl_generator_fuel'), self.sandbox_generator_fuel)

        cols.addWidget(g_farm, 1)

        sl.addLayout(cols)
        sl.addStretch()
        scroll.setWidget(sw)
        return scroll

    # ── Subtab 6: Mod Sandbox Options (Clean 3-Column Table) ───────────
    def _create_mods_subtab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel(f"<b>{tr('lbl_mod_search')}</b>"))
        self.mod_search_input = QLineEdit()
        self.mod_search_input.setPlaceholderText(tr('ph_mod_search'))
        self.mod_search_input.setMaximumWidth(400)
        self.mod_search_input.textChanged.connect(self._filter_mod_options)
        search_row.addWidget(self.mod_search_input)
        search_row.addStretch()
        layout.addLayout(search_row)

        self.mod_options_scroll = QScrollArea()
        self.mod_options_scroll.setWidgetResizable(True)
        self.mod_options_widget = QWidget()
        self.mod_options_layout = QVBoxLayout(self.mod_options_widget)
        self.mod_options_layout.setAlignment(Qt.AlignTop)
        self.mod_options_layout.setSpacing(12)

        self.mod_empty_label = QLabel(tr('no_mod_options_found'))
        self.mod_empty_label.setAlignment(Qt.AlignCenter)
        self.mod_empty_label.setStyleSheet("color: #888; font-size: 13px; padding: 40px;")
        self.mod_options_layout.addWidget(self.mod_empty_label)

        self.mod_options_scroll.setWidget(self.mod_options_widget)
        layout.addWidget(self.mod_options_scroll)

        self.mod_widgets = {}  # (mod_table, key): widget
        self.mod_group_boxes = []
        return container

    def _filter_mod_options(self, text: str):
        t = text.strip().lower()
        for gb, items in self.mod_group_boxes:
            gb_visible = False
            for row_w, key_str, comment_str in items:
                match = (t in key_str.lower()) or (t in comment_str.lower())
                row_w.setVisible(match or not t)
                if match:
                    gb_visible = True
            gb.setVisible(gb_visible or not t)

    def load_sandbox_settings(self):
        """Load all sandbox settings and populate both vanilla tabs and dynamic mod options."""
        try:
            name = self.server_name_input.text().strip() or 'servertest'
            self.config_manager.set_server_name(name)
            sb, meta = self.config_manager.load_sandbox_vars_full()

            def _get_val(key, subcat=None, default=None):
                if key in sb:
                    return sb[key]
                if subcat and subcat in sb and isinstance(sb[subcat], dict):
                    return sb[subcat].get(key, default)
                return default

            zl = sb.get('ZombieLore') if isinstance(sb.get('ZombieLore'), dict) else {}
            zc = sb.get('ZombieConfig') if isinstance(sb.get('ZombieConfig'), dict) else {}

            # 1. Zombies
            self.sandbox_zombie_speed.setCurrentIndex(_combo_index(_ZOMBIE_SPEED, zl.get('Speed', 3)))
            self.sandbox_zombie_strength.setCurrentIndex(_combo_index(_ZOMBIE_STRENGTH, zl.get('Strength', 2)))
            self.sandbox_zombie_toughness.setCurrentIndex(_combo_index(_ZOMBIE_TOUGHNESS, zl.get('Toughness', 2)))
            self.sandbox_zombie_transmission.setCurrentIndex(_combo_index(_ZOMBIE_TRANSMISSION, zl.get('Transmission', 1)))
            self.sandbox_infection_mortality.setCurrentIndex(_combo_index(_INFECTION, zl.get('Mortality', 6)))
            self.sandbox_zombie_cognition.setCurrentIndex(_combo_index(_ZOMBIE_COGNITION, zl.get('Cognition', 3)))
            self.sandbox_memory.setCurrentIndex(_combo_index(_ZOMBIE_MEMORY, zl.get('Memory', 2)))
            self.sandbox_decomp.setCurrentIndex(_combo_index(_ZOMBIE_DECOMP, zl.get('Decomp', 1)))
            self.sandbox_sight.setCurrentIndex(_combo_index(_ZOMBIE_SIGHT, zl.get('Sight', 2)))
            self.sandbox_hearing.setCurrentIndex(_combo_index(_ZOMBIE_HEARING, zl.get('Hearing', 2)))
            self.sandbox_smell.setCurrentIndex(_combo_index(_ZOMBIE_SMELL, zl.get('Smell', 2)))
            self.sandbox_zombie_active.setCurrentIndex(_combo_index(_ZOMBIE_ACTIVE, zl.get('Active', 1)))
            self.sandbox_zombie_distribution.setCurrentIndex(_combo_index(_ZOMBIE_DISTRIBUTION, zl.get('Distribution', 1)))
            self.sandbox_thump_no_chasing.setChecked(bool(zl.get('ThumpNoChasing', False)))
            self.sandbox_thump_on_construction.setChecked(bool(zl.get('ThumpOnConstruction', True)))
            self.sandbox_trigger_alarm.setChecked(bool(zl.get('TriggerHouseAlarm', False)))

            # Advanced ZombieConfig
            self.sandbox_pop_mult.setValue(_safe_float(zc.get('PopulationMultiplier', 1.0), 1.0))
            self.sandbox_pop_start_mult.setValue(_safe_float(zc.get('PopulationStartMultiplier', 1.0), 1.0))
            self.sandbox_pop_peak_mult.setValue(_safe_float(zc.get('PopulationPeakMultiplier', 1.5), 1.5))
            self.sandbox_pop_peak_day.setValue(_safe_int(zc.get('PopulationPeakDay', 28), 28))
            self.sandbox_respawn_hours.setValue(_safe_int(zc.get('RespawnHours', 72), 72))
            self.sandbox_respawn_unseen_hours.setValue(_safe_int(zc.get('RespawnUnseenHours', 16), 16))
            self.sandbox_respawn_mult.setValue(_safe_float(zc.get('RespawnMultiplier', 0.1), 0.1))
            self.sandbox_redistribute_hours.setValue(_safe_int(zc.get('RedistributeHours', 12), 12))
            self.sandbox_rally_size.setValue(_safe_int(zc.get('RallyGroupSize', 20), 20))
            self.sandbox_rally_radius.setValue(_safe_int(zc.get('RallyGroupRadius', 3), 3))

            # 2. Loot
            for k, cb in self.loot_combos.items():
                val = _get_val(k, 'Loot', 2)
                cb.setCurrentIndex(_combo_index(_LOOT_RARITY, val, default=1))

            self.sandbox_loot_respawn.setCurrentIndex(
                _combo_index(_LOOT_RESPAWN, _get_val('HoursForLootRespawn', 'Loot', 0))
            )
            self.sandbox_max_items_respawn.setValue(
                _safe_int(_get_val('MaxItemsForLootRespawn', 'Loot', 4), 4)
            )
            self.sandbox_construction_respawn.setChecked(
                bool(_get_val('ConstructionPreventsLootRespawn', 'Loot', True))
            )
            self.sandbox_water_shutoff.setValue(
                _safe_int(_get_val('WaterShutModifier', 'Loot', _get_val('WaterShut', None, 14)), 14)
            )
            self.sandbox_electricity_shutoff.setValue(
                _safe_int(_get_val('ElecShutModifier', 'Loot', _get_val('ElecShut', None, 14)), 14)
            )

            # 3. World & Time
            self.sandbox_day_length.setCurrentIndex(
                _combo_index(_DAY_LENGTH, _get_val('DayLength', 'GameTime', 3), default=2)
            )
            self.sandbox_start_year.setValue(_safe_int(_get_val('StartYear', 'GameTime', 1), 1))
            self.sandbox_start_month.setCurrentIndex(
                max(0, _safe_int(_get_val('StartMonth', 'GameTime', 7), 7) - 1)
            )
            self.sandbox_start_day.setValue(_safe_int(_get_val('StartDay', 'GameTime', 9), 9))
            self.sandbox_start_time.setCurrentIndex(
                _combo_index(_START_TIMES, _get_val('StartTime', 'GameTime', 2), default=1)
            )
            self.sandbox_night_darkness.setCurrentIndex(
                _combo_index(_NIGHT_DARK, _get_val('NightDarkness', 'GameTime', 3), default=2)
            )
            self.sandbox_time_since_apo.setCurrentIndex(
                _combo_index(_TIME_APO, _get_val('TimeSinceApo', 'GameTime', 1), default=0)
            )

            self.sandbox_fire_spread.setChecked(bool(_get_val('FireSpread', 'Climate', True)))
            self.sandbox_nature_abundance.setCurrentIndex(
                _combo_index(_NATURE_ABU, _get_val('NatureAbundance', 'Climate', 3), default=2)
            )
            self.sandbox_helicopter.setCurrentIndex(
                _combo_index(_EVENT_FREQ, _get_val('Helicopter', None, 2), default=1)
            )
            self.sandbox_meta_event.setCurrentIndex(
                _combo_index(_META_FREQ, _get_val('MetaEvent', None, 2), default=1)
            )
            self.sandbox_sleeping_event.setCurrentIndex(
                _combo_index(_META_FREQ, _get_val('SleepingEvent', None, 2), default=1)
            )
            self.sandbox_erosion_speed.setCurrentIndex(
                _combo_index(_EROSION_SPD, _get_val('ErosionSpeed', None, 3), default=2)
            )
            self.sandbox_erosion_days.setValue(_safe_int(_get_val('ErosionDays', None, 100), 100))

            # 4. Vehicles
            self.sandbox_car_spawn.setCurrentIndex(
                _combo_index(_CAR_SPAWN, _get_val('CarSpawnRate', 'Cars', 4), default=3)
            )
            self.sandbox_vehicle_easy_use.setChecked(
                bool(_get_val('VehicleEasyUse', 'Cars', False))
            )
            self.sandbox_chance_gas.setCurrentIndex(
                _combo_index(_CAR_LEVEL, _get_val('ChanceHasGas', 'Cars', 3), default=2)
            )
            self.sandbox_initial_gas.setCurrentIndex(
                _combo_index(_CAR_LEVEL, _get_val('InitialGas', 'Cars', 2), default=1)
            )
            self.sandbox_gas_consumption.setValue(
                _safe_float(_get_val('CarGasConsumption', 'Cars', 1.0), 1.0)
            )
            self.sandbox_car_condition.setCurrentIndex(
                _combo_index(_CAR_LEVEL, _get_val('CarGeneralCondition', 'Cars', 3), default=2)
            )
            self.sandbox_traffic_jam.setChecked(bool(_get_val('TrafficJam', 'Cars', True)))
            self.sandbox_car_alarm.setCurrentIndex(
                _combo_index(_EVENT_FREQ, _get_val('CarAlarm', 'Cars', 3), default=2)
            )
            self.sandbox_crash_damage.setChecked(
                bool(_get_val('PlayerDamagedFromCarCrash', 'Cars', True))
            )

            # 5. Character
            self.sandbox_xp_mult.setValue(
                _safe_float(_get_val('XPMultiplier', 'Character', 1.0), 1.0)
            )
            self.sandbox_char_free_points.setValue(
                _safe_int(_get_val('FreePoints', 'Character', 0), 0)
            )
            self.sandbox_player_damage.setCurrentIndex(
                _combo_index(_PLAYER_DMG, _get_val('DamageToPlayer', 'Character', 3), default=2)
            )
            self.sandbox_farming_speed.setCurrentIndex(
                _combo_index(_FARMING_SPD, _get_val('FarmingSpeed', 'Farming', _get_val('Farming', None, 3)), default=2)
            )
            self.sandbox_plant_resilience.setCurrentIndex(
                _combo_index(_CAR_LEVEL, _get_val('PlantResilience', 'Farming', 3), default=2)
            )
            self.sandbox_plant_abundance.setCurrentIndex(
                _combo_index(_CAR_LEVEL, _get_val('PlantAbundance', 'Farming', 3), default=2)
            )
            self.sandbox_generator_spawn.setCurrentIndex(
                _combo_index(_GENERATOR_SP, _get_val('GeneratorSpawning', 'Meta', 3), default=2)
            )
            self.sandbox_generator_fuel.setValue(
                _safe_float(_get_val('GeneratorFuelConsumption', 'Meta', 1.0), 1.0)
            )

            # 6. Populate Dynamic Mod Options
            self._populate_mod_options(sb, meta)

            self.statusBar.showMessage(tr('settings_loaded'), 3000)

        except FileNotFoundError:
            pass
        except Exception as e:
            logger.exception('Failed to load sandbox settings')

    def _populate_mod_options(self, sb: dict, meta: dict):
        """Dynamically render informative 3-column rows for all mod tables in SandboxVars."""
        # Clear existing mod widgets
        for i in reversed(range(self.mod_options_layout.count())):
            item = self.mod_options_layout.itemAt(i)
            w = item.widget()
            if w and w != self.mod_empty_label:
                w.deleteLater()

        self.mod_widgets.clear()
        self.mod_group_boxes.clear()

        # Vanilla tables to skip (they have dedicated tabs)
        vanilla_tables = {'ZombieLore', 'ZombieConfig', 'MultiplierConfig', 'Map', 'Basement', 'SandboxVars'}

        mod_tables = {k: v for k, v in sb.items() if isinstance(v, dict) and k not in vanilla_tables}

        if not mod_tables:
            self.mod_empty_label.setVisible(True)
            return

        self.mod_empty_label.setVisible(False)

        for mod_name in sorted(mod_tables.keys()):
            mod_data = mod_tables[mod_name]
            gb = QGroupBox(f"🧩 {mod_name}")
            gb.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid #3d3d3d;
                    border-radius: 6px;
                    margin-top: 10px;
                    padding-top: 16px;
                    background-color: #212121;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 6px;
                    color: #5294e2;
                }
            """)
            gb_vbox = QVBoxLayout(gb)
            gb_vbox.setContentsMargins(12, 10, 12, 10)
            gb_vbox.setSpacing(6)
            gb_items = []

            for key, val in mod_data.items():
                comment = meta.get((mod_name, key), '')

                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(4, 2, 4, 2)
                row_layout.setSpacing(12)

                lbl_k = QLabel(f"<b>{key}</b>:")
                lbl_k.setFixedWidth(230)
                lbl_k.setStyleSheet("color: #e0e0e0; font-size: 12px;")

                if isinstance(val, bool):
                    w = QCheckBox("Включено" if val and get_language() == 'ru' else ("Вкл" if get_language() == 'ru' else "Enabled"))
                    w.setChecked(val)
                    w.stateChanged.connect(lambda state, cb=w: cb.setText("Включено" if state and get_language() == 'ru' else ("Отключено" if get_language() == 'ru' else ("Enabled" if state else "Disabled"))))
                    _set_ctl_limits(w, 240)
                elif isinstance(val, int):
                    w = QSpinBox()
                    w.setRange(-999999, 999999)
                    w.setValue(val)
                    _set_ctl_limits(w, 140)
                elif isinstance(val, float):
                    w = QDoubleSpinBox()
                    w.setRange(-999999.0, 999999.0)
                    w.setSingleStep(0.1)
                    w.setValue(val)
                    _set_ctl_limits(w, 140)
                else:
                    w = QLineEdit(str(val))
                    _set_ctl_limits(w, 240)

                desc_lbl = QLabel(comment)
                desc_lbl.setStyleSheet("color: #9e9e9e; font-size: 11px;")
                desc_lbl.setWordWrap(True)

                row_layout.addWidget(lbl_k)
                row_layout.addWidget(w)
                row_layout.addWidget(desc_lbl, 1)

                gb_vbox.addWidget(row_widget)
                self.mod_widgets[(mod_name, key)] = w
                gb_items.append((row_widget, key, comment))

            self.mod_group_boxes.append((gb, gb_items))
            self.mod_options_layout.addWidget(gb)

    def save_sandbox_settings(self):
        """Save all sandbox settings non-destructively to SandboxVars.lua."""
        try:
            vars_dict = {
                # ── Root variables ──
                # 10 Loot Categories
                'WeaponLoot':        _combo_value(_LOOT_RARITY, self.loot_combos['WeaponLoot'].currentIndex(), 2),
                'RangedWeaponLoot':  _combo_value(_LOOT_RARITY, self.loot_combos['RangedWeaponLoot'].currentIndex(), 2),
                'AmmoLoot':          _combo_value(_LOOT_RARITY, self.loot_combos['AmmoLoot'].currentIndex(), 2),
                'FoodLoot':          _combo_value(_LOOT_RARITY, self.loot_combos['FoodLoot'].currentIndex(), 3),
                'CannedFoodLoot':    _combo_value(_LOOT_RARITY, self.loot_combos['CannedFoodLoot'].currentIndex(), 2),
                'MedicalLoot':       _combo_value(_LOOT_RARITY, self.loot_combos['MedicalLoot'].currentIndex(), 2),
                'LiteratureLoot':    _combo_value(_LOOT_RARITY, self.loot_combos['LiteratureLoot'].currentIndex(), 2),
                'SurvivalGearsLoot': _combo_value(_LOOT_RARITY, self.loot_combos['SurvivalGearsLoot'].currentIndex(), 2),
                'MechanicsLoot':     _combo_value(_LOOT_RARITY, self.loot_combos['MechanicsLoot'].currentIndex(), 2),
                'OtherLoot':         _combo_value(_LOOT_RARITY, self.loot_combos['OtherLoot'].currentIndex(), 3),

                # Loot Respawn & Utilities
                'HoursForLootRespawn':              _combo_value(_LOOT_RESPAWN, self.sandbox_loot_respawn.currentIndex(), 0),
                'MaxItemsForLootRespawn':            self.sandbox_max_items_respawn.value(),
                'ConstructionPreventsLootRespawn':   self.sandbox_construction_respawn.isChecked(),
                'WaterShutModifier':                self.sandbox_water_shutoff.value(),
                'ElecShutModifier':                 self.sandbox_electricity_shutoff.value(),
                'WaterShut':                        self.sandbox_water_shutoff.value(),
                'ElecShut':                         self.sandbox_electricity_shutoff.value(),

                # World & Time
                'DayLength':     _combo_value(_DAY_LENGTH, self.sandbox_day_length.currentIndex(), 3),
                'StartYear':     self.sandbox_start_year.value(),
                'StartMonth':    self.sandbox_start_month.currentIndex() + 1,
                'StartDay':      self.sandbox_start_day.value(),
                'StartTime':     _combo_value(_START_TIMES, self.sandbox_start_time.currentIndex(), 2),
                'NightDarkness': _combo_value(_NIGHT_DARK, self.sandbox_night_darkness.currentIndex(), 3),
                'TimeSinceApo':  _combo_value(_TIME_APO, self.sandbox_time_since_apo.currentIndex(), 1),

                'FireSpread':       self.sandbox_fire_spread.isChecked(),
                'NatureAbundance':  _combo_value(_NATURE_ABU, self.sandbox_nature_abundance.currentIndex(), 3),
                'Helicopter':       _combo_value(_EVENT_FREQ, self.sandbox_helicopter.currentIndex(), 2),
                'MetaEvent':        _combo_value(_META_FREQ, self.sandbox_meta_event.currentIndex(), 2),
                'SleepingEvent':    _combo_value(_META_FREQ, self.sandbox_sleeping_event.currentIndex(), 2),
                'ErosionSpeed':     _combo_value(_EROSION_SPD, self.sandbox_erosion_speed.currentIndex(), 3),
                'ErosionDays':      self.sandbox_erosion_days.value(),

                # Vehicles
                'CarSpawnRate':              _combo_value(_CAR_SPAWN, self.sandbox_car_spawn.currentIndex(), 4),
                'VehicleEasyUse':            self.sandbox_vehicle_easy_use.isChecked(),
                'ChanceHasGas':              _combo_value(_CAR_LEVEL, self.sandbox_chance_gas.currentIndex(), 3),
                'InitialGas':                _combo_value(_CAR_LEVEL, self.sandbox_initial_gas.currentIndex(), 2),
                'CarGasConsumption':         round(self.sandbox_gas_consumption.value(), 2),
                'CarGeneralCondition':       _combo_value(_CAR_LEVEL, self.sandbox_car_condition.currentIndex(), 3),
                'TrafficJam':                self.sandbox_traffic_jam.isChecked(),
                'CarAlarm':                  _combo_value(_EVENT_FREQ, self.sandbox_car_alarm.currentIndex(), 3),
                'PlayerDamagedFromCarCrash': self.sandbox_crash_damage.isChecked(),

                # Character & Farming
                'XPMultiplier':             round(self.sandbox_xp_mult.value(), 2),
                'FreePoints':               self.sandbox_char_free_points.value(),
                'DamageToPlayer':           _combo_value(_PLAYER_DMG, self.sandbox_player_damage.currentIndex(), 3),
                'FarmingSpeed':             _combo_value(_FARMING_SPD, self.sandbox_farming_speed.currentIndex(), 3),
                'Farming':                  _combo_value(_FARMING_SPD, self.sandbox_farming_speed.currentIndex(), 3),
                'PlantResilience':          _combo_value(_CAR_LEVEL, self.sandbox_plant_resilience.currentIndex(), 3),
                'PlantAbundance':           _combo_value(_CAR_LEVEL, self.sandbox_plant_abundance.currentIndex(), 3),
                'GeneratorSpawning':        _combo_value(_GENERATOR_SP, self.sandbox_generator_spawn.currentIndex(), 3),
                'GeneratorFuelConsumption': round(self.sandbox_generator_fuel.value(), 2),

                # ── Nested Vanilla Tables ──
                'ZombieLore': {
                    'Speed':               _combo_value(_ZOMBIE_SPEED, self.sandbox_zombie_speed.currentIndex(), 3),
                    'Strength':            _combo_value(_ZOMBIE_STRENGTH, self.sandbox_zombie_strength.currentIndex(), 2),
                    'Toughness':           _combo_value(_ZOMBIE_TOUGHNESS, self.sandbox_zombie_toughness.currentIndex(), 2),
                    'Transmission':        _combo_value(_ZOMBIE_TRANSMISSION, self.sandbox_zombie_transmission.currentIndex(), 1),
                    'Mortality':           _combo_value(_INFECTION, self.sandbox_infection_mortality.currentIndex(), 6),
                    'Cognition':           _combo_value(_ZOMBIE_COGNITION, self.sandbox_zombie_cognition.currentIndex(), 3),
                    'Memory':              _combo_value(_ZOMBIE_MEMORY, self.sandbox_memory.currentIndex(), 2),
                    'Decomp':              _combo_value(_ZOMBIE_DECOMP, self.sandbox_decomp.currentIndex(), 1),
                    'Sight':               _combo_value(_ZOMBIE_SIGHT, self.sandbox_sight.currentIndex(), 2),
                    'Hearing':             _combo_value(_ZOMBIE_HEARING, self.sandbox_hearing.currentIndex(), 2),
                    'Smell':               _combo_value(_ZOMBIE_SMELL, self.sandbox_smell.currentIndex(), 2),
                    'Active':              _combo_value(_ZOMBIE_ACTIVE, self.sandbox_zombie_active.currentIndex(), 1),
                    'Distribution':        _combo_value(_ZOMBIE_DISTRIBUTION, self.sandbox_zombie_distribution.currentIndex(), 1),
                    'ThumpNoChasing':      self.sandbox_thump_no_chasing.isChecked(),
                    'ThumpOnConstruction': self.sandbox_thump_on_construction.isChecked(),
                    'TriggerHouseAlarm':   self.sandbox_trigger_alarm.isChecked(),
                },
                'ZombieConfig': {
                    'PopulationMultiplier':      round(self.sandbox_pop_mult.value(), 2),
                    'PopulationStartMultiplier': round(self.sandbox_pop_start_mult.value(), 2),
                    'PopulationPeakMultiplier':  round(self.sandbox_pop_peak_mult.value(), 2),
                    'PopulationPeakDay':         self.sandbox_pop_peak_day.value(),
                    'RespawnHours':              self.sandbox_respawn_hours.value(),
                    'RespawnUnseenHours':        self.sandbox_respawn_unseen_hours.value(),
                    'RespawnMultiplier':         round(self.sandbox_respawn_mult.value(), 2),
                    'RedistributeHours':         self.sandbox_redistribute_hours.value(),
                    'RallyGroupSize':            self.sandbox_rally_size.value(),
                    'RallyGroupRadius':          self.sandbox_rally_radius.value(),
                },
            }

            # Collect Mod options
            for (mod_name, key), widget in self.mod_widgets.items():
                if mod_name not in vars_dict:
                    vars_dict[mod_name] = {}
                if isinstance(widget, QCheckBox):
                    vars_dict[mod_name][key] = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    vars_dict[mod_name][key] = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    vars_dict[mod_name][key] = round(widget.value(), 3)
                elif isinstance(widget, QLineEdit):
                    vars_dict[mod_name][key] = widget.text().strip()

            name = self.server_name_input.text().strip() or 'servertest'
            self.config_manager.set_server_name(name)
            self.config_manager.save_sandbox_vars(vars_dict)

            if hasattr(self, 'preset_combo'):
                try:
                    preset_file = self.paths['server_config_dir'] / "sandbox_preset.cfg"
                    preset_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(preset_file, 'w', encoding='utf-8') as pf:
                        pf.write(self.preset_combo.currentText())
                except Exception:
                    pass

            self.statusBar.showMessage(tr('sandbox_saved'), 5000)
            QMessageBox.information(self, tr('success'), tr('sandbox_saved'))

        except Exception as e:
            logger.exception('Failed to save sandbox settings')
            QMessageBox.critical(self, tr('error'), f"Failed to save sandbox settings: {e}")

    def on_preset_changed(self, preset: str):
        """Apply preset values to sandbox widgets."""
        p = preset.lower()
        if p == 'apocalypse':
            self.sandbox_pop_mult.setValue(1.5)
            self.sandbox_zombie_speed.setCurrentIndex(1)  # fast shamblers
            self.sandbox_zombie_strength.setCurrentIndex(1)  # normal
            self.sandbox_zombie_toughness.setCurrentIndex(1)
            for cb in self.loot_combos.values():
                cb.setCurrentIndex(0)  # extremely rare
            self.sandbox_xp_mult.setValue(1.0)
            self.sandbox_player_damage.setCurrentIndex(3)  # high
        elif p == 'survivor':
            self.sandbox_pop_mult.setValue(1.0)
            self.sandbox_zombie_speed.setCurrentIndex(1)  # fast shamblers
            self.sandbox_zombie_strength.setCurrentIndex(1)  # normal
            for cb in self.loot_combos.values():
                cb.setCurrentIndex(1)  # rare
            self.sandbox_xp_mult.setValue(1.0)
            self.sandbox_player_damage.setCurrentIndex(2)  # normal
        elif p == 'builder':
            self.sandbox_pop_mult.setValue(0.35)
            self.sandbox_zombie_speed.setCurrentIndex(2)  # shamblers
            self.sandbox_zombie_strength.setCurrentIndex(2)  # weak
            for cb in self.loot_combos.values():
                cb.setCurrentIndex(3)  # common
            self.sandbox_xp_mult.setValue(1.5)
            self.sandbox_player_damage.setCurrentIndex(0)  # very low
