#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager Module
Handles reading and writing server configuration files (.ini and .lua).
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from configparser import ConfigParser

logger = logging.getLogger(__name__)


def read_text_safely(path: Path) -> str:
    """Read file content with UTF-8, falling back to cp1251 and latin-1 if decode fails."""
    try:
        return path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, LookupError):
        try:
            return path.read_text(encoding='cp1251')
        except Exception:
            return path.read_text(encoding='utf-8', errors='replace')


def read_lines_safely(path: Path) -> List[str]:
    """Read lines from file safely handling various encodings."""
    text = read_text_safely(path)
    return text.splitlines(keepends=True)


class AppPreferences:
    """Persistent user preferences across launches (last server name, ram, backup, etc.)."""
    @staticmethod
    def _prefs_path(paths: dict) -> Path:
        zomboid_dir = paths.get('zomboid_dir', Path.home() / 'Zomboid')
        return zomboid_dir / 'pz_manager_prefs.json'

    @classmethod
    def load(cls, paths: dict) -> dict:
        p = cls._prefs_path(paths)
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load preferences: {e}")
        return {}

    @classmethod
    def save(cls, paths: dict, data: dict):
        p = cls._prefs_path(paths)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            current = cls.load(paths)
            current.update(data)
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save preferences: {e}")


class ConfigManager:
    """Manages server configuration files."""
    
    def __init__(self, paths: dict):
        self.paths = paths
        self.server_config_dir = paths.get('server_config_dir') or (Path(paths['zomboid_dir']) / 'Server')
        # Restore last saved server name if available
        prefs = AppPreferences.load(paths)
        self._server_name = prefs.get('last_server_name', 'servertest')
        self._ini_cache = None
        
    def set_server_name(self, name: str):
        """Set the server name (config folder name)."""
        if self._server_name != name:
            self._server_name = name
            self._ini_cache = None
            self._sandbox_cache = None
        
    def get_ini_path(self) -> Path:
        """Get path to the server .ini file."""
        return self.server_config_dir / f"{self._server_name}.ini"
        
    def get_sandbox_path(self) -> Path:
        """Get path to the SandboxVars.lua file."""
        return self.server_config_dir / f"{self._server_name}_SandboxVars.lua"
        
    def get_spawnpoints_path(self) -> Path:
        """Get path to the spawnpoints.lua file."""
        return self.server_config_dir / f"{self._server_name}_spawnpoints.lua"
        
    def get_spawnregions_path(self) -> Path:
        """Get path to the spawnregions.lua file."""
        return self.server_config_dir / f"{self._server_name}_spawnregions.lua"
        
    def get_default_server_ini(self) -> Dict[str, str]:
        """Return full standard default configuration for a PZ dedicated server."""
        return {
            'PublicName': 'My PZ Server',
            'PublicDescription': 'A Project Zomboid Dedicated Server',
            'Password': '',
            'MaxPlayers': '16',
            'DefaultPort': '16261',
            'UDPPort': '16262',
            'SteamPort1': '8766',
            'SteamPort2': '8767',
            'RCONPort': '27015',
            'RCONPassword': '',
            'Open': 'true',
            'PVP': 'true',
            'PauseEmpty': 'true',
            'AllowCoop': 'true',
            'SleepAllowed': 'false',
            'SleepNeeded': 'false',
            'AnnounceDeath': 'false',
            'NoFire': 'false',
            'AllowDestructionBySledgehammer': 'true',
            'DropOnDeath': '1',
            'SpawnPoint': '0,0,0',
            'Map': 'Muldraugh, KY',
            'ServerWelcomeMessage': 'Welcome to Project Zomboid Dedicated Server!',
            'PlayerSafehouse': 'false',
            'AdminSafehouse': 'false',
            'SafehouseAllowTreassing': 'false',
            'SafehouseAllowFire': 'false',
            'SafehouseAllowLoot': 'false',
            'SafehouseAllowRespawn': 'false',
            'GlobalChat': 'true',
            'SafetySystem': 'true',
            'ShowSafety': 'true',
            'DisplayUserName': 'true',
            'VoiceEnable': 'true',
            'Voice3D': 'true',
            'VoiceMinDistance': '10',
            'VoiceMaxDistance': '100',
            'UseSecureJoin': 'false',
            'AllowNonAsciiUsername': 'false',
            'AutoCreateUserInWhiteList': 'false',
            'MaxAccountsPerUser': '0',
            'SpeedLimit': '70',
            'AdminPassword': '',
            'SaveWorldEveryMinutes': '15',
            'BackupsCount': '5',
            'BackupsPeriod': '0',
            'WorkshopItems': '',
            'Mods': '',
            'ServerRAM': '8',
        }

    # ===== INI File Handling =====
    
    def load_server_ini(self, create_if_missing: bool = True) -> Dict[str, str]:
        """Load server settings from .ini file or provide defaults if missing."""
        if getattr(self, '_ini_cache', None) is not None:
            return dict(self._ini_cache)

        ini_path = self.get_ini_path()
        defaults = self.get_default_server_ini()
        
        if not ini_path.exists():
            logger.info(f"INI file not found at {ini_path}. Using standard defaults.")
            if create_if_missing:
                try:
                    self.save_server_ini(defaults)
                except Exception as e:
                    logger.warning(f"Could not auto-create default INI: {e}")
            self._ini_cache = dict(defaults)
            return dict(defaults)
        
        config = dict(defaults)
        
        try:
            for line in read_lines_safely(ini_path):
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith(';'):
                        continue
                    if '=' in line:
                        key, _, value = line.partition('=')
                        config[key.strip()] = value.strip()
                        
            logger.info(f"Loaded {len(config)} settings from {ini_path}")
            self._ini_cache = dict(config)
            return dict(config)
            
        except Exception as e:
            logger.error(f"Failed to load INI file, falling back to defaults: {e}")
            return defaults
            
    def save_server_ini(self, settings: Dict[str, str]):
        """Save server settings to .ini file, preserving comments and order."""
        self._ini_cache = None
        ini_path = self.get_ini_path()
        ini_path.parent.mkdir(parents=True, exist_ok=True)
        
        if ini_path.exists():
            self._update_ini_file(ini_path, settings)
        else:
            self._create_ini_file(ini_path, settings)
            
        # Also ensure spawn points are present
        self.ensure_spawn_files()
        self._ini_cache = dict(settings)
        logger.info(f"Saved settings to {ini_path}")
        
    def _update_ini_file(self, path: Path, settings: Dict[str, str]):
        """Update existing INI file, preserving comments and unknown keys."""
        lines = []
        updated_keys = set()
        
        for line in read_lines_safely(path):
                original_line = line
                line_stripped = line.strip()
                
                # Keep comments and empty lines
                if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith(';'):
                    lines.append(original_line)
                    continue
                
                # Check if this is a key we want to update
                if '=' in line_stripped:
                    key, _, _ = line_stripped.partition('=')
                    key = key.strip()
                    
                    if key in settings:
                        lines.append(f"{key}={settings[key]}\n")
                        updated_keys.add(key)
                    else:
                        lines.append(original_line)
                else:
                    lines.append(original_line)
        
        # Add any new keys that weren't in the file
        for key, value in settings.items():
            if key not in updated_keys:
                lines.append(f"{key}={value}\n")
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
    def _create_ini_file(self, path: Path, settings: Dict[str, str]):
        """Create a new INI file with the given settings."""
        # Default settings with comments
        default_content = """# Project Zomboid Server Configuration
# Generated by PZ Server Manager

# Server name displayed in the server browser
PublicName={PublicName}
PublicDescription={PublicDescription}

# Server password (leave empty for no password)
Password={Password}

# Maximum number of players
MaxPlayers={MaxPlayers}

# Network ports
DefaultPort={DefaultPort}
SteamPort1={SteamPort1}
RCONPort={RCONPort}
RCONPassword={RCONPassword}

# Server visibility
Open={Open}

# Gameplay settings
PVP={PVP}
PauseEmpty={PauseEmpty}
GlobalChat={GlobalChat}
SafetySystem={SafetySystem}
ShowSafety={ShowSafety}

# Admin settings
AdminPassword={AdminPassword}
SaveWorldEveryMinutes={SaveWorldEveryMinutes}

# Spawn settings
SpawnPoint={SpawnPoint}

# Mods
WorkshopItems=
Mods=

"""
        # Fill in defaults for missing settings
        defaults = {
            'PublicName': 'My PZ Server',
            'PublicDescription': 'A Project Zomboid server',
            'Password': '',
            'MaxPlayers': '16',
            'DefaultPort': '16261',
            'SteamPort1': '8766',
            'RCONPort': '27015',
            'RCONPassword': '',
            'Open': 'true',
            'PVP': 'true',
            'PauseEmpty': 'true',
            'GlobalChat': 'true',
            'SafetySystem': 'true',
            'ShowSafety': 'true',
            'AdminPassword': '',
            'SaveWorldEveryMinutes': '15',
            'SpawnPoint': '0,0,0',
        }
        
        # Merge with provided settings
        all_settings = {**defaults, **settings}
        
        # Format content
        content = default_content.format(**all_settings)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    def get_ini_value(self, key: str, default: str = '') -> str:
        """Get a single value from the INI file."""
        try:
            config = self.load_server_ini()
            return config.get(key, default)
        except FileNotFoundError:
            return default
            
    def set_ini_value(self, key: str, value: str):
        """Set a single value in the INI file."""
        try:
            config = self.load_server_ini()
        except FileNotFoundError:
            config = {}
            
        config[key] = value
        self.save_server_ini(config)
        
    # ===== Lua File Handling =====
    
    def _parse_lua_val(self, value: str) -> Any:
        """Parse raw Lua string value into Python bool, int, float, or str."""
        value = value.strip().rstrip(',')
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return int(value)
        elif '.' in value:
            try:
                f_val = float(value)
                if f_val.is_integer():
                    return int(f_val)
                return f_val
            except ValueError:
                return value.strip('"\'')
        else:
            return value.strip('"\'')

    def get_default_sandbox_vars(self) -> Dict[str, Any]:
        """Return full standard default vanilla SandboxVars dictionary."""
        return {
            'VERSION': 5,
            'Zombies': {'Count': 3},
            'ZombieConfig': {
                'PopulationMultiplier': 1.0,
                'PopulationStartMultiplier': 1.0,
                'PopulationPeakMultiplier': 1.5,
                'PopulationPeakDay': 28,
                'RespawnHours': 72.0,
                'RespawnUnseenHours': 16.0,
                'RespawnMultiplier': 0.1,
                'RedistributeHours': 12.0,
                'FollowSoundDistance': 100,
                'RallyGroupSize': 20,
                'RallyTravelDistance': 20,
                'RallyGroupSeparation': 15,
                'RallyGroupRadius': 3,
            },
            'ZombieLore': {
                'Speed': 2,
                'Strength': 2,
                'Toughness': 2,
                'Transmission': 1,
                'Mortality': 5,
                'Reanimate': 3,
                'Cognition': 3,
                'CrawlUnderVehicle': 5,
                'Memory': 2,
                'Decomp': 1,
                'Sight': 2,
                'Hearing': 2,
                'Smell': 2,
                'EnvironmentalAttacks': True,
                'DamageOnAttack': True,
                'TriggerHouseAlarm': False,
                'ThumpNoChasing': False,
            },
            'GameTime': {
                'StartYear': 1,
                'StartMonth': 7,
                'StartDay': 9,
                'StartTime': 2,
                'DayLength': 2,
            },
            'Loot': {
                'Other': 2,
                'Medical': 2,
                'SurvivalGears': 2,
                'CannedFood': 2,
                'Literature': 2,
                'FreshFood': 2,
                'Weapon': 2,
                'Ammo': 2,
                'Mechanics': 2,
            },
            'Climate': {
                'Temperature': 3,
                'Rain': 3,
                'ErosionSpeed': 3,
                'ErosionDays': 100,
            },
            'Cars': {
                'SpawnRate': 2,
                'VehicleEasyUse': False,
                'ZombieAttractionMultiplier': 1.0,
                'CarGasConsumption': 1.0,
                'ChanceHasGas': 2,
                'InitialGas': 2,
            },
            'Character': {
                'XPMultiplier': 1.0,
                'FreePoints': 0,
                'PlayerDamage': 2,
            },
            'Farming': {
                'FarmingSpeed': 3,
                'PlantResilience': 3,
                'PlantAbundance': 3,
            },
            'Map': {
                'AllowMiniMap': True,
                'AllowWorldMap': True,
                'MapAllKnown': False,
            },
            'WaterShutModifier': 14,
            'ElecShutModifier': 14,
            'TimeSinceApo': 1,
            'NightDarkness': 2,
            'FireSpread': True,
            'Helicopter': 2,
            'MetaEvent': 2,
            'SleepingEvent': 1,
        }

    def _parse_lua_content(self, content: str) -> tuple:
        """Parse Lua content into (vars_dict, meta_comments)."""
        vars_dict = {}
        meta_comments = {}
        current_category = None
        last_comment = []

        for line in content.splitlines():
            s = line.strip()
            if s.startswith('--'):
                last_comment.append(s[2:].strip())
                continue
            if not s or s.startswith('SandboxVars ='):
                last_comment = []
                continue

            # Category start: CategoryName = {
            cat_match = re.match(r'^(\w+)\s*=\s*\{', s)
            if cat_match:
                category_name = cat_match.group(1)
                if category_name != 'SandboxVars':
                    current_category = category_name
                    if current_category not in vars_dict:
                        vars_dict[current_category] = {}
                last_comment = []
                continue

            # Category end: },
            if s.startswith('}') and current_category:
                current_category = None
                last_comment = []
                continue

            # Key = Value,
            kv_match = re.match(r'^(\w+)\s*=\s*([^,\n]+)', s)
            if kv_match:
                key = kv_match.group(1)
                raw_val = kv_match.group(2).strip().rstrip(',')
                val = self._parse_lua_val(raw_val)

                if current_category:
                    vars_dict[current_category][key] = val
                    if last_comment:
                        meta_comments[(current_category, key)] = ' '.join(last_comment)
                else:
                    vars_dict[key] = val
                    if last_comment:
                        meta_comments[key] = ' '.join(last_comment)
                last_comment = []

        return vars_dict, meta_comments

    def load_sandbox_vars_full(self, create_if_missing: bool = True) -> tuple:
        """
        Load sandbox variables and metadata comments from SandboxVars.lua.
        Returns (vars_dict, meta_comments).
        Supports root-level variables, vanilla sub-tables (ZombieLore, ZombieConfig, Map),
        and any custom mod tables (CommonSense, MoreTraits, CompanionDogs, VFE, etc.).
        """
        if getattr(self, '_sandbox_cache', None) is not None:
            return self._sandbox_cache

        lua_path = self.get_sandbox_path()
        defaults = self.get_default_sandbox_vars()

        if not lua_path.exists():
            logger.info(f"Sandbox file not found at {lua_path}. Using standard defaults.")
            if create_if_missing:
                try:
                    self.save_sandbox_vars(defaults)
                except Exception as e:
                    logger.warning(f"Could not auto-create default sandbox vars: {e}")
            return defaults, {}

        try:
            content = read_text_safely(lua_path)

            vars_dict, meta_comments = self._parse_lua_content(content)

            # If current server sandbox file has no mod tables, check other server configs to inherit them!
            vanilla_tables = {'ZombieLore', 'ZombieConfig', 'MultiplierConfig', 'Map', 'Basement', 'SandboxVars'}
            has_mod_tables = any(isinstance(v, dict) and k not in vanilla_tables for k, v in vars_dict.items())

            if not has_mod_tables and self.server_config_dir.exists():
                candidates = sorted(
                    [p for p in self.server_config_dir.glob('*_SandboxVars.lua') if p.name != lua_path.name],
                    key=lambda x: 0 if 'servertest' in x.name.lower() else 1
                )
                for cand in candidates:
                    try:
                        cand_content = read_text_safely(cand)
                        c_dict, c_meta = self._parse_lua_content(cand_content)
                        c_mods = {k: v for k, v in c_dict.items() if isinstance(v, dict) and k not in vanilla_tables}
                        if c_mods:
                            for mk, mv in c_mods.items():
                                if mk not in vars_dict:
                                    vars_dict[mk] = mv
                            for (cat, k), c_text in c_meta.items():
                                if cat in c_mods and (cat, k) not in meta_comments:
                                    meta_comments[(cat, k)] = c_text
                            logger.info(f"Inherited {len(c_mods)} mod tables from {cand.name}")
                            break
                    except Exception as ex:
                        logger.warning(f"Failed to inherit mod tables from {cand}: {ex}")

            logger.info(f"Loaded sandbox vars from {lua_path} ({len(vars_dict)} root/table keys)")
            self._sandbox_cache = (vars_dict, meta_comments)
            return vars_dict, meta_comments

        except Exception as e:
            logger.error(f"Failed to load sandbox vars, using defaults: {e}")
            return defaults, {}

    def load_sandbox_vars(self, create_if_missing: bool = True) -> Dict[str, Any]:
        """Load sandbox variables dictionary."""
        vars_dict, _ = self.load_sandbox_vars_full(create_if_missing=create_if_missing)
        return vars_dict

    def save_sandbox_vars(self, vars_dict: Dict[str, Any]):
        """
        Safely and non-destructively save sandbox variables to SandboxVars.lua.
        Preserves all 1400+ lines of Russian/English comments, formatting, table structure,
        and all installed mod tables without overwriting unknown settings.
        """
        self._sandbox_cache = None
        lua_path = self.get_sandbox_path()
        lua_path.parent.mkdir(parents=True, exist_ok=True)

        def _fmt(val):
            if isinstance(val, bool):
                return 'true' if val else 'false'
            elif isinstance(val, (int, float)):
                return str(val)
            return f'"{val}"'

        if not lua_path.exists():
            # Create fresh Lua file with defaults and provided updates
            lines = ["SandboxVars = {"]
            for key, val in vars_dict.items():
                if isinstance(val, dict):
                    lines.append(f"    {key} = {{")
                    for subk, subv in val.items():
                        lines.append(f"        {subk} = {_fmt(subv)},")
                    lines.append("    },")
                else:
                    lines.append(f"    {key} = {_fmt(val)},")
            lines.append("}")
            with open(lua_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            logger.info(f"Created new sandbox vars at {lua_path}")
            return

        try:
            lines = read_lines_safely(lua_path)

            new_lines = []
            current_category = None
            updated_keys = set()

            for line in lines:
                s = line.strip()

                # Table start: CategoryName = {
                m_tab = re.match(r'^(\s*)(\w+)\s*=\s*\{', line)
                if m_tab and m_tab.group(2) != 'SandboxVars':
                    current_category = m_tab.group(2)
                    new_lines.append(line)
                    continue

                # Table end: },
                if s.startswith('}') and current_category:
                    cat_dict = vars_dict.get(current_category)
                    if isinstance(cat_dict, dict):
                        for k, v in cat_dict.items():
                            if (current_category, k) not in updated_keys:
                                new_lines.append(f"        {k} = {_fmt(v)},\n")
                                updated_keys.add((current_category, k))
                    current_category = None
                    new_lines.append(line)
                    continue

                # Key = Value,
                m_kv = re.match(r'^(\s*)(\w+)\s*=\s*([^,\n]+)(,?.*)$', line)
                if m_kv and not s.startswith('--'):
                    indent = m_kv.group(1)
                    k = m_kv.group(2)
                    rest = m_kv.group(4)
                    trailing_comment = ''
                    if '--' in rest:
                        trailing_comment = ' ' + rest[rest.index('--'):].rstrip('\r\n')

                    if current_category:
                        cat_dict = vars_dict.get(current_category)
                        if isinstance(cat_dict, dict) and k in cat_dict:
                            new_val = _fmt(cat_dict[k])
                            new_lines.append(f"{indent}{k} = {new_val},{trailing_comment}\n")
                            updated_keys.add((current_category, k))
                            continue
                    else:
                        if k in vars_dict and not isinstance(vars_dict[k], dict):
                            new_val = _fmt(vars_dict[k])
                            new_lines.append(f"{indent}{k} = {new_val},{trailing_comment}\n")
                            updated_keys.add((None, k))
                            continue

                new_lines.append(line)

            # Append any completely new tables from vars_dict that were not in the file
            closing_idx = -1
            for idx in range(len(new_lines) - 1, -1, -1):
                if new_lines[idx].strip() == '}':
                    closing_idx = idx
                    break

            if closing_idx != -1:
                new_tables_lines = []
                for cat, cval in vars_dict.items():
                    if isinstance(cval, dict) and cat != 'SandboxVars':
                        # Check if category was processed
                        already_present = any((cat, k) in updated_keys for k in cval)
                        if not already_present:
                            new_tables_lines.append(f"    {cat} = {{\n")
                            for k, v in cval.items():
                                new_tables_lines.append(f"        {k} = {_fmt(v)},\n")
                            new_tables_lines.append("    },\n")

                if new_tables_lines:
                    new_lines[closing_idx:closing_idx] = new_tables_lines

            with open(lua_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            logger.info(f"Non-destructively updated sandbox vars in {lua_path}")

        except Exception as e:
            logger.error(f"Failed to update sandbox vars: {e}")
            raise
            
    def get_sandbox_value(self, category: str, key: str, default: Any = None) -> Any:
        """Get a single sandbox variable."""
        try:
            vars_dict = self.load_sandbox_vars()
            return vars_dict.get(category, {}).get(key, default)
        except FileNotFoundError:
            return default
            
    def set_sandbox_value(self, category: str, key: str, value: Any):
        """Set a single sandbox variable."""
        try:
            vars_dict = self.load_sandbox_vars()
        except FileNotFoundError:
            vars_dict = {}
            
        if category not in vars_dict:
            vars_dict[category] = {}
            
        vars_dict[category][key] = value
        self.save_sandbox_vars(vars_dict)
        
    # ===== Mod Configuration =====
    
    def get_workshop_items(self) -> List[str]:
        """Get list of Workshop item IDs from config."""
        value = self.get_ini_value('WorkshopItems', '')
        if not value:
            return []
        return [id.strip() for id in value.split(';') if id.strip()]
        
    def set_workshop_items(self, items: List[str]):
        """Set list of Workshop item IDs in config."""
        value = ';'.join(items)
        self.set_ini_value('WorkshopItems', value)
        
    def get_mods(self) -> List[str]:
        """Get list of mod IDs from config."""
        value = self.get_ini_value('Mods', '')
        if not value:
            return []
        return [mod.strip() for mod in value.split(';') if mod.strip()]
        
    def set_mods(self, mods: List[str]):
        """Set list of mod IDs in config."""
        value = ';'.join(mods)
        self.set_ini_value('Mods', value)
        
    # ===== Config File Discovery =====
    
    def list_server_configs(self) -> List[str]:
        """List available server configurations (names)."""
        configs = []
        
        if self.server_config_dir.exists():
            for file in self.server_config_dir.glob('*.ini'):
                # Filter out backup files
                if not file.stem.endswith('_backup'):
                    configs.append(file.stem)
                    
        return configs
        
    def config_exists(self) -> bool:
        """Check if the current server config exists."""
        return self.get_ini_path().exists()

    def backup_config(self):
        """Create a backup of the current configuration."""
        import shutil
        from datetime import datetime

        ini_path = self.get_ini_path()
        sandbox_path = self.get_sandbox_path()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if ini_path.exists():
            backup_path = ini_path.with_suffix(f'.ini.backup_{timestamp}')
            shutil.copy2(ini_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

        if sandbox_path.exists():
            backup_path = sandbox_path.with_suffix(f'.lua.backup_{timestamp}')
            shutil.copy2(sandbox_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

    def list_backups(self) -> List[Path]:
        """List all backup files for the current configuration."""
        backups = []
        if self.server_config_dir.exists():
            pattern_ini = f"{self._server_name}.ini.backup_*"
            pattern_lua = f"{self._server_name}_SandboxVars.lua.backup_*"
            backups.extend(sorted(self.server_config_dir.glob(pattern_ini), reverse=True))
            backups.extend(sorted(self.server_config_dir.glob(pattern_lua), reverse=True))
        return backups

    def restore_backup_file(self, backup_file: Path):
        """Restore a specific backup file to active configuration."""
        import shutil
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")

        if '.ini.backup_' in backup_file.name:
            target = self.get_ini_path()
        elif '.lua.backup_' in backup_file.name:
            target = self.get_sandbox_path()
        else:
            raise ValueError(f"Unknown backup file format: {backup_file.name}")

        shutil.copy2(backup_file, target)
        logger.info(f"Restored {backup_file.name} to {target}")

    def get_sandbox_presets(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Return preset dictionary for Sandbox settings."""
        return {
            'beginner': {
                'ZombieLore': {'Speed': 3, 'Strength': 3, 'Toughness': 3, 'Transmission': 1, 'Memory': 3},
                'Zombies': {'PopulationMultiplier': 0.35},
                'Loot': {'Other': 4, 'Medical': 4, 'SurvivalGears': 4, 'CannedFood': 4},
                'Character': {'XPMultiplier': 3.0},
            },
            'survival': {
                'ZombieLore': {'Speed': 2, 'Strength': 2, 'Toughness': 2, 'Transmission': 1, 'Memory': 2},
                'Zombies': {'PopulationMultiplier': 1.0},
                'Loot': {'Other': 2, 'Medical': 2, 'SurvivalGears': 2, 'CannedFood': 2},
                'Character': {'XPMultiplier': 1.0},
            },
            'hardcore': {
                'ZombieLore': {'Speed': 1, 'Strength': 1, 'Toughness': 1, 'Transmission': 1, 'Memory': 1},
                'Zombies': {'PopulationMultiplier': 2.0},
                'Loot': {'Other': 1, 'Medical': 1, 'SurvivalGears': 1, 'CannedFood': 1},
                'Character': {'XPMultiplier': 0.5},
            },
            'horde': {
                'ZombieLore': {'Speed': 2, 'Strength': 2, 'Toughness': 2, 'Transmission': 1, 'Memory': 1},
                'Zombies': {'PopulationMultiplier': 4.0},
                'Loot': {'Other': 2, 'Medical': 2, 'SurvivalGears': 2, 'CannedFood': 2},
                'Character': {'XPMultiplier': 1.5},
            },
            'builder': {
                'ZombieLore': {'Speed': 3, 'Strength': 3, 'Toughness': 3, 'Transmission': 4, 'Memory': 4},
                'Zombies': {'PopulationMultiplier': 0.0},
                'Loot': {'Other': 5, 'Medical': 5, 'SurvivalGears': 5, 'CannedFood': 5},
                'Character': {'XPMultiplier': 2.0},
            },
        }

    def apply_sandbox_preset(self, preset_name: str):
        """Apply a preset to the sandbox configuration."""
        presets = self.get_sandbox_presets()
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")

        self.backup_config()
        try:
            vars_dict = self.load_sandbox_vars()
        except FileNotFoundError:
            vars_dict = {}

        preset_data = presets[preset_name]
        for category, settings in preset_data.items():
            if category not in vars_dict:
                vars_dict[category] = {}
            for key, val in settings.items():
                vars_dict[category][key] = val

        self.save_sandbox_vars(vars_dict)
        logger.info(f"Applied sandbox preset: {preset_name}")

    def ensure_spawn_files(self):
        """Ensure spawnpoints and spawnregions files exist with default vanilla data."""
        self.server_config_dir.mkdir(parents=True, exist_ok=True)

        spawnregions_path = self.get_spawnregions_path()
        if not spawnregions_path.exists():
            default_regions = (
                "function SpawnRegions()\n"
                "\treturn {\n"
                '\t\t{ name = "Muldraugh, KY", file = "media/maps/Muldraugh, KY/spawnpoints.lua" },\n'
                '\t\t{ name = "Riverside, KY", file = "media/maps/Riverside, KY/spawnpoints.lua" },\n'
                '\t\t{ name = "Rosewood, KY", file = "media/maps/Rosewood, KY/spawnpoints.lua" },\n'
                '\t\t{ name = "West Point, KY", file = "media/maps/West Point, KY/spawnpoints.lua" },\n'
                "\t}\n"
                "end\n"
            )
            try:
                with open(spawnregions_path, 'w', encoding='utf-8') as f:
                    f.write(default_regions)
                logger.info(f"Created default spawnregions at {spawnregions_path}")
            except Exception as e:
                logger.error(f"Failed to create spawnregions file: {e}")

        spawnpoints_path = self.get_spawnpoints_path()
        if not spawnpoints_path.exists():
            default_points = (
                "function SpawnPoints()\n"
                "\treturn {\n"
                "\t\tunemployed = {\n"
                "\t\t\t{ posX = 12067, posY = 6801, posZ = 0 },\n"
                "\t\t},\n"
                "\t}\n"
                "end\n"
            )
            try:
                with open(spawnpoints_path, 'w', encoding='utf-8') as f:
                    f.write(default_points)
                logger.info(f"Created default spawnpoints at {spawnpoints_path}")
            except Exception as e:
                logger.error(f"Failed to create spawnpoints file: {e}")

