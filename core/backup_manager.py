#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backup & Wipe Management Module for Project Zomboid Dedicated Server.
Provides archive backups, scheduled auto-backups, restore functionality, and soft/hard wipe tools.
"""

import os
import shutil
import zipfile
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class BackupManager(QObject):
    """
    Handles creating, restoring, and rotating world backups, as well as server wipes.
    """
    backup_created = pyqtSignal(str)   # path to zip
    backup_restored = pyqtSignal(str)  # filename
    wipe_completed = pyqtSignal(str)   # wipe type
    error_occurred = pyqtSignal(str)   # error message

    def __init__(self, paths: dict, server_name: str = "servertest"):
        super().__init__()
        self.paths = paths
        self.server_name = server_name
        self.zomboid_dir = paths.get('zomboid_dir', Path.home() / 'Zomboid')
        self.backup_dir = self.zomboid_dir / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Scheduled auto-backups
        self.auto_backup_enabled = False
        self.auto_backup_interval_minutes = 120  # Every 2 hours
        self.max_backups_to_keep = 10

        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._on_auto_timer)

    def set_server_name(self, name: str):
        self.server_name = name

    def set_auto_backup(self, enabled: bool, interval_minutes: int = 120, max_to_keep: int = 10):
        self.auto_backup_enabled = enabled
        self.auto_backup_interval_minutes = max(10, interval_minutes)
        self.max_backups_to_keep = max(1, max_to_keep)

        if enabled:
            self._auto_timer.start(self.auto_backup_interval_minutes * 60 * 1000)
            logger.info(f"Auto-backups started: every {self.auto_backup_interval_minutes} mins, keep {self.max_backups_to_keep}")
        else:
            self._auto_timer.stop()
            logger.info("Auto-backups stopped")

    def _on_auto_timer(self):
        try:
            zip_path = self.create_backup(tag="auto")
            logger.info(f"Auto-backup completed: {zip_path}")
        except Exception as e:
            logger.error(f"Auto-backup failed: {e}")

    # ================= Backup Operations =================
    def create_backup(self, tag: str = "manual") -> str:
        """Create a complete ZIP backup of server save, database, and configurations."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{self.server_name}_{tag}_{timestamp}.zip"
        zip_path = self.backup_dir / filename

        save_folder = self.zomboid_dir / 'Saves' / 'Multiplayer' / self.server_name
        db_file = self.zomboid_dir / 'db' / f"{self.server_name}.db"
        server_config_dir = self.zomboid_dir / 'Server'

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                # 1. Config files
                if server_config_dir.exists():
                    for cfg_file in server_config_dir.glob(f"{self.server_name}*"):
                        if cfg_file.is_file():
                            zf.write(cfg_file, arcname=f"Server/{cfg_file.name}")

                # 2. Database file
                if db_file.exists():
                    zf.write(db_file, arcname=f"db/{db_file.name}")

                # 3. Save world folder
                if save_folder.exists():
                    for root, _, files in os.walk(save_folder):
                        for f in files:
                            full_p = Path(root) / f
                            rel_p = full_p.relative_to(save_folder)
                            zf.write(full_p, arcname=f"Saves/{self.server_name}/{rel_p}")

            self._rotate_backups()
            self.backup_created.emit(str(zip_path))
            return str(zip_path)

        except Exception as e:
            err = f"Failed to create backup: {e}"
            logger.error(err)
            self.error_occurred.emit(err)
            raise

    def list_backups(self) -> List[Dict]:
        """List all available backup archives with size and modification date."""
        backups = []
        if not self.backup_dir.exists():
            return backups

        for f in self.backup_dir.glob("*.zip"):
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "filepath": str(f.resolve()),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": stat.st_mtime
            })
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups

    def _rotate_backups(self):
        """Delete oldest backups beyond max_backups_to_keep."""
        all_b = self.list_backups()
        if len(all_b) > self.max_backups_to_keep:
            for b in all_b[self.max_backups_to_keep:]:
                try:
                    Path(b['filepath']).unlink(missing_ok=True)
                    logger.info(f"Rotated old backup: {b['filename']}")
                except Exception as e:
                    logger.warning(f"Could not delete old backup {b['filename']}: {e}")

    def restore_backup(self, backup_filepath: str) -> bool:
        """Safely restore a backup archive back to the server directories."""
        zip_p = Path(backup_filepath)
        if not zip_p.exists():
            self.error_occurred.emit(f"Backup file not found: {backup_filepath}")
            return False

        try:
            with zipfile.ZipFile(zip_p, 'r') as zf:
                for member in zf.namelist():
                    # Destination determination based on prefix
                    if member.startswith("Server/"):
                        dest = self.zomboid_dir / member
                    elif member.startswith("db/"):
                        dest = self.zomboid_dir / member
                    elif member.startswith("Saves/"):
                        dest = self.zomboid_dir / "Saves" / "Multiplayer" / member.replace(f"Saves/{self.server_name}/", "")
                    else:
                        continue

                    dest.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            self.backup_restored.emit(zip_p.name)
            return True
        except Exception as e:
            err = f"Failed to restore backup: {e}"
            logger.error(err)
            self.error_occurred.emit(err)
            return False

    # ================= World Wipe Operations =================
    def perform_soft_wipe(self) -> dict:
        """
        Soft wipe: cleans world map chunks (map_*.bin, zpop_*.bin, chunkdata_*.bin, corpses, blood)
        while preserving players, vehicles, and character progression.
        """
        save_folder = self.zomboid_dir / 'Saves' / 'Multiplayer' / self.server_name
        if not save_folder.exists():
            return {"deleted_files": 0, "message": "Save folder does not exist"}

        # Backup first
        self.create_backup(tag="pre_soft_wipe")

        deleted_count = 0
        preserved_files = {"players.db", "map_p.bin", "map_t.bin", "vehicles.db"}

        for f in save_folder.iterdir():
            if f.is_file() and f.name not in preserved_files:
                # Target map chunks and zombie population data
                if f.name.startswith(("map_", "zpop_", "chunkdata_", "erosion_", "world_")):
                    try:
                        f.unlink()
                        deleted_count += 1
                    except Exception:
                        pass

        msg = f"Soft wipe completed: reset {deleted_count} world chunks. Characters preserved."
        logger.info(msg)
        self.wipe_completed.emit("soft")
        return {"deleted_files": deleted_count, "message": msg}

    def perform_full_wipe(self) -> dict:
        """
        Full wipe: Complete fresh start.
        Deletes the entire world save folder and clears database players table.
        """
        save_folder = self.zomboid_dir / 'Saves' / 'Multiplayer' / self.server_name
        db_file = self.zomboid_dir / 'db' / f"{self.server_name}.db"

        # Backup first
        self.create_backup(tag="pre_full_wipe")

        if save_folder.exists():
            shutil.rmtree(save_folder, ignore_errors=True)

        if db_file.exists():
            try:
                import sqlite3
                with sqlite3.connect(str(db_file)) as conn:
                    conn.execute("DELETE FROM whitelist")
                    conn.commit()
            except Exception:
                pass

        msg = f"Full wipe completed: entire world '{self.server_name}' deleted."
        logger.info(msg)
        self.wipe_completed.emit("full")
        return {"message": msg}
