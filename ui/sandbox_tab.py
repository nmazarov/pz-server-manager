#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sandbox Tab Mixin for PZ Server Manager.
Handles all sandbox variables (ZombieLore, ZombieConfig, Climate, Loot, Vehicles, etc.) in servertest_SandboxVars.lua.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QFormLayout, QScrollArea,
    QMessageBox
)

from translations import tr

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


def _combo_items(mapping):
    return [tr(k) for k, _ in mapping]


def _safe_int(val, default: int = 0) -> int:
    try:
        if val is None or val == '':
            return default
        return int(float(val))
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


class SandboxTabMixin:
    """Mixin for the Sandbox settings tab."""

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
        self.sandbox_zombie_count.setCurrentIndex(3)
        f.addRow(tr('lbl_zombie_count'), self.sandbox_zombie_count)

        self.sandbox_zombie_distribution = QComboBox()
        self.sandbox_zombie_distribution.addItems(_combo_items(_ZOMBIE_DISTRIBUTION))
        f.addRow(tr('lbl_distribution'), self.sandbox_zombie_distribution)

        self.sandbox_zombie_speed = QComboBox()
        self.sandbox_zombie_speed.addItems(_combo_items(_ZOMBIE_SPEED))
        self.sandbox_zombie_speed.setCurrentIndex(2)
        f.addRow(tr('lbl_speed'), self.sandbox_zombie_speed)

        self.sandbox_zombie_strength = QComboBox()
        self.sandbox_zombie_strength.addItems(_combo_items(_ZOMBIE_STRENGTH))
        self.sandbox_zombie_strength.setCurrentIndex(1)
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
        self.sandbox_zombie_cognition.setCurrentIndex(2)
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
        self.sandbox_infection_mortality.setCurrentIndex(5)
        f.addRow(tr('lbl_infection_mortality'), self.sandbox_infection_mortality)

        sl.addWidget(g)

        # ── Loot & Resources ──
        g = QGroupBox(tr('group_loot'))
        f = QFormLayout(g)

        self.sandbox_loot_rarity = QComboBox()
        self.sandbox_loot_rarity.addItems(_combo_items(_LOOT_RARITY))
        self.sandbox_loot_rarity.setCurrentIndex(1)
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
        self.sandbox_start_month.setCurrentIndex(6)
        f.addRow(tr('lbl_start_month'), self.sandbox_start_month)

        self.sandbox_start_day = QSpinBox()
        self.sandbox_start_day.setRange(1, 31)
        self.sandbox_start_day.setValue(9)
        f.addRow(tr('lbl_start_day'), self.sandbox_start_day)

        self.sandbox_day_length = QComboBox()
        self.sandbox_day_length.addItems([k for k,_ in _DAY_LENGTH])
        self.sandbox_day_length.setCurrentIndex(3)
        f.addRow(tr('lbl_day_length'), self.sandbox_day_length)

        self.sandbox_night_darkness = QComboBox()
        self.sandbox_night_darkness.addItems(_combo_items(_NIGHT_DARK))
        self.sandbox_night_darkness.setCurrentIndex(1)
        f.addRow(tr('lbl_night_darkness'), self.sandbox_night_darkness)

        self.sandbox_fire_spread = QCheckBox()
        self.sandbox_fire_spread.setChecked(True)
        f.addRow(tr('lbl_fire_spread'), self.sandbox_fire_spread)

        self.sandbox_nature_abundance = QComboBox()
        self.sandbox_nature_abundance.addItems(_combo_items(_NATURE_ABU))
        self.sandbox_nature_abundance.setCurrentIndex(2)
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
        self.sandbox_car_spawn.setCurrentIndex(2)
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
        self.sandbox_xp_multiplier.setCurrentIndex(2)
        f.addRow(tr('lbl_xp_multiplier'), self.sandbox_xp_multiplier)

        self.sandbox_player_damage = QComboBox()
        self.sandbox_player_damage.addItems(_combo_items(_PLAYER_DMG))
        self.sandbox_player_damage.setCurrentIndex(2)
        f.addRow(tr('lbl_player_damage'), self.sandbox_player_damage)

        self.sandbox_char_free_points = QSpinBox()
        self.sandbox_char_free_points.setRange(0, 100)
        self.sandbox_char_free_points.setValue(0)
        f.addRow(tr('lbl_char_free_points'), self.sandbox_char_free_points)

        self.sandbox_farming_speed = QComboBox()
        self.sandbox_farming_speed.addItems(_combo_items(_FARMING_SPD))
        self.sandbox_farming_speed.setCurrentIndex(2)
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

    def load_sandbox_settings(self):
        try:
            name = self.server_name_input.text().strip() or 'servertest'
            self.config_manager.set_server_name(name)
            sb = self.config_manager.load_sandbox_vars()

            def _get_dict(cat_name):
                v = sb.get(cat_name)
                return v if isinstance(v, dict) else {}

            zl = _get_dict('ZombieLore')
            zc = _get_dict('ZombieConfig')
            gt = _get_dict('GameTime')
            lo = _get_dict('Loot')
            cl = _get_dict('Climate')
            ca = _get_dict('Cars')
            ch = _get_dict('Character')
            fa = _get_dict('Farming')

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
            self.sandbox_water_shutoff.setValue(_safe_int(lo.get('WaterShutModifier', 14)))
            self.sandbox_electricity_shutoff.setValue(_safe_int(lo.get('ElecShutModifier', 14)))

            # Time
            self.sandbox_start_month.setCurrentIndex(max(0, _safe_int(gt.get('StartMonth', 7)) - 1))
            self.sandbox_start_day.setValue(_safe_int(gt.get('StartDay', 9)))
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
            self.sandbox_char_free_points.setValue(_safe_int(ch.get('FreePoints', 0)))

            # Farming / generators
            self.sandbox_farming_speed.setCurrentIndex(_si(_FARMING_SPD, fa.get('FarmingSpeed', 3)))
            meta_dict = _get_dict('Meta')
            self.sandbox_generator_spawn.setCurrentIndex(
                _si(_GENERATOR_SP, meta_dict.get('GeneratorSpawning', 3)))
            self.sandbox_generator_fuel.setCurrentIndex(
                _si(_GENERATOR_FU, meta_dict.get('GeneratorFuelConsumption', 3)))

            # Restore saved preset name if available
            preset_file = self.paths['server_config_dir'] / "sandbox_preset.cfg"
            if preset_file.exists():
                try:
                    with open(preset_file, 'r', encoding='utf-8') as pf:
                        saved_p = pf.read().strip()
                        if saved_p and hasattr(self, 'preset_combo'):
                            idx = self.preset_combo.findText(saved_p)
                            if idx >= 0:
                                self.preset_combo.blockSignals(True)
                                self.preset_combo.setCurrentIndex(idx)
                                self.preset_combo.blockSignals(False)
                except Exception:
                    pass

            self.statusBar.showMessage(tr('settings_loaded'), 3000)

        except FileNotFoundError:
            pass
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
        if hasattr(self, 'preset_combo'):
            try:
                preset_file = self.paths['server_config_dir'] / "sandbox_preset.cfg"
                preset_file.parent.mkdir(parents=True, exist_ok=True)
                with open(preset_file, 'w', encoding='utf-8') as pf:
                    pf.write(preset)
            except Exception:
                pass

        p = preset.lower()
        if p == 'apocalypse':
            self.sandbox_zombie_count.setCurrentIndex(4)
            self.sandbox_zombie_speed.setCurrentIndex(0)
            self.sandbox_zombie_strength.setCurrentIndex(0)
            self.sandbox_zombie_toughness.setCurrentIndex(0)
            self.sandbox_loot_rarity.setCurrentIndex(0)
            self.sandbox_xp_multiplier.setCurrentIndex(0)
            self.sandbox_player_damage.setCurrentIndex(4)
        elif p == 'survivor':
            self.sandbox_zombie_count.setCurrentIndex(3)
            self.sandbox_zombie_speed.setCurrentIndex(2)
            self.sandbox_zombie_strength.setCurrentIndex(1)
            self.sandbox_loot_rarity.setCurrentIndex(1)
            self.sandbox_xp_multiplier.setCurrentIndex(2)
            self.sandbox_player_damage.setCurrentIndex(2)
        elif p == 'builder':
            self.sandbox_zombie_count.setCurrentIndex(1)
            self.sandbox_zombie_speed.setCurrentIndex(2)
            self.sandbox_loot_rarity.setCurrentIndex(3)
            self.sandbox_xp_multiplier.setCurrentIndex(4)
            self.sandbox_player_damage.setCurrentIndex(0)
