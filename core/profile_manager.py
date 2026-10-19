#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Server Profile Manager Module for Project Zomboid Dedicated Server.
Allows creating, cloning, switching, and deleting different server profiles.
"""

import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class ProfileManager(QObject):
    """
    Manages multiple server profiles, each with its own configs, mods, database, and world saves.
    """
    profile_changed = pyqtSignal(str)   # new profile name
    profile_created = pyqtSignal(str)   # created profile name
    profile_deleted = pyqtSignal(str)   # deleted profile name

    def __init__(self, paths: dict, current_profile: str = "servertest"):
        super().__init__()
        self.paths = paths
        self.current_profile = current_profile
        self.server_config_dir = paths.get('server_config_dir', Path.home() / 'Zomboid' / 'Server')
        self.zomboid_dir = paths.get('zomboid_dir', Path.home() / 'Zomboid')

    def list_profiles(self) -> List[Dict]:
        """Scan ~/Zomboid/Server for all available server *.ini profiles."""
        profiles = []
        if not self.server_config_dir.exists():
            return [{"name": "servertest", "active": True, "has_save": False}]

        ini_files = list(self.server_config_dir.glob("*.ini"))
        for ini in ini_files:
            prof_name = ini.stem
            # Ignore non-server files
            if prof_name in ("options", "latestSave", "config"):
                continue

            save_folder = self.zomboid_dir / 'Saves' / 'Multiplayer' / prof_name
            has_save = save_folder.exists() and any(save_folder.iterdir()) if save_folder.exists() else False

            profiles.append({
                "name": prof_name,
                "active": (prof_name == self.current_profile),
                "ini_path": str(ini),
                "has_save": has_save
            })

        if not any(p["name"] == self.current_profile for p in profiles):
            profiles.insert(0, {
                "name": self.current_profile,
                "active": True,
                "ini_path": str(self.server_config_dir / f"{self.current_profile}.ini"),
                "has_save": False
            })

        return profiles

    def set_current_profile(self, profile_name: str) -> bool:
        """Switch the active server profile."""
        profile_name = profile_name.strip()
        if not profile_name:
            return False

        self.current_profile = profile_name
        logger.info(f"Active server profile switched to: {profile_name}")
        self.profile_changed.emit(profile_name)
        return True

    def create_profile(self, new_profile_name: str, clone_from: Optional[str] = None) -> bool:
        """
        Create a new server profile, optionally cloning INI and Sandbox files from an existing profile.
        """
        name = "".join(c for c in new_profile_name if c.isalnum() or c in ('_', '-')).strip()
        if not name:
            raise ValueError("Profile name must be alphanumeric.")

        self.server_config_dir.mkdir(parents=True, exist_ok=True)
        new_ini = self.server_config_dir / f"{name}.ini"
        new_sandbox = self.server_config_dir / f"{name}_SandboxVars.lua"
        new_regions = self.server_config_dir / f"{name}_spawnregions.lua"
        new_points = self.server_config_dir / f"{name}_spawnpoints.lua"

        if clone_from:
            src_ini = self.server_config_dir / f"{clone_from}.ini"
            src_sandbox = self.server_config_dir / f"{clone_from}_SandboxVars.lua"
            src_regions = self.server_config_dir / f"{clone_from}_spawnregions.lua"
            src_points = self.server_config_dir / f"{clone_from}_spawnpoints.lua"

            if src_ini.exists():
                shutil.copy2(src_ini, new_ini)
            if src_sandbox.exists():
                shutil.copy2(src_sandbox, new_sandbox)
            if src_regions.exists():
                shutil.copy2(src_regions, new_regions)
            if src_points.exists():
                shutil.copy2(src_points, new_points)
        else:
            from core.config_manager import ConfigManager
            cm = ConfigManager(self.paths)
            cm.set_server_name(name)
            cm.ensure_spawn_files()
            cm.load_server_ini(create_if_missing=True)
            cm.load_sandbox_vars(create_if_missing=True)

        logger.info(f"Created server profile '{name}' (cloned from {clone_from})")
        self.profile_created.emit(name)
        return True

    def delete_profile(self, profile_name: str, delete_save_world: bool = False) -> bool:
        """Delete profile configuration files and optionally the world save."""
        if profile_name == self.current_profile:
            raise ValueError("Cannot delete the currently active profile. Switch to another profile first.")

        # Delete config files
        for p in self.server_config_dir.glob(f"{profile_name}*"):
            try:
                p.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete {p}: {e}")

        # Delete database
        db_file = self.zomboid_dir / 'db' / f"{profile_name}.db"
        if db_file.exists():
            db_file.unlink(missing_ok=True)

        # Delete save world if requested
        if delete_save_world:
            save_folder = self.zomboid_dir / 'Saves' / 'Multiplayer' / profile_name
            if save_folder.exists():
                shutil.rmtree(save_folder, ignore_errors=True)

        logger.info(f"Deleted server profile '{profile_name}'")
        self.profile_deleted.emit(profile_name)
        return True
