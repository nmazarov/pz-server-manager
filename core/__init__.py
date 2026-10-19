#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core package for Project Zomboid Server Manager.
Contains server management, process lifecycle, configuration, mods,
watchdog, backup, and localization engines.
"""

from core.translations import tr, set_language, get_language
from core.config_manager import ConfigManager, AppPreferences
try:
    from core.server_process import ServerProcess, check_ports_in_use
    from core.server_installer import (
        ServerInstaller, find_existing_server_installations,
        get_installed_server_buildid, buildid_to_game_version,
        check_server_update_available, fetch_available_server_branches
    )
    from core.mod_manager import ModManager
    from core.player_manager import PlayerManager
    from core.backup_manager import BackupManager
    from core.watchdog_manager import WatchdogManager
    from core.diagnostics_manager import DiagnosticsManager
    from core.profile_manager import ProfileManager
except ImportError:
    # Running in headless environment without PyQt5 (e.g. VPS web dashboard)
    pass
from core.network_helper import NetworkHelper

__all__ = [
    'tr',
    'set_language',
    'get_language',
    'ConfigManager',
    'AppPreferences',
    'ServerProcess',
    'check_ports_in_use',
    'ServerInstaller',
    'find_existing_server_installations',
    'get_installed_server_buildid',
    'buildid_to_game_version',
    'check_server_update_available',
    'fetch_available_server_branches',
    'ModManager',
    'PlayerManager',
    'BackupManager',
    'WatchdogManager',
    'DiagnosticsManager',
    'ProfileManager',
    'NetworkHelper',
]
