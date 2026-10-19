#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Player Management & RCON Action Palette Module.
Tracks live players, manages SQLite whitelist/banlist, and generates admin commands.
"""

import sqlite3
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class PlayerManager(QObject):
    """
    Manages online players, whitelist, bans, and provides quick admin commands.
    """
    player_joined = pyqtSignal(str)     # username
    player_left = pyqtSignal(str)       # username
    players_updated = pyqtSignal(list)  # list of usernames

    def __init__(self, paths: dict, server_name: str = "servertest"):
        super().__init__()
        self.paths = paths
        self.server_name = server_name
        self.online_players = set()
        self.db_path = self._get_db_path()

    def set_server_name(self, server_name: str):
        self.server_name = server_name
        self.db_path = self._get_db_path()

    def _get_db_path(self) -> Path:
        """Get path to the server SQLite database in ~/Zomboid/db/."""
        zomboid_dir = self.paths.get('zomboid_dir', Path.home() / 'Zomboid')
        return zomboid_dir / 'db' / f"{self.server_name}.db"

    # ================= Live Console Parsing =================
    def parse_console_line(self, line: str):
        """Parse server output line to update online players list."""
        line = line.strip()

        # Connect patterns:
        # "User User123 is connected" or "Login attempt for User123" or "connected as player"
        join_match = re.search(r'User\s+([a-zA-Z0-9_\-]+)\s+is\s+connected', line, re.IGNORECASE)
        if not join_match:
            join_match = re.search(r'Player\s+([a-zA-Z0-9_\-]+)\s+connected', line, re.IGNORECASE)
        if not join_match:
            join_match = re.search(r'Login attempt for\s+([a-zA-Z0-9_\-]+).*accepted', line, re.IGNORECASE)

        if join_match:
            username = join_match.group(1).strip()
            if username not in self.online_players:
                self.online_players.add(username)
                logger.info(f"Player joined: {username}")
                self.player_joined.emit(username)
                self.players_updated.emit(list(self.online_players))
            return

        # Disconnect patterns:
        # "User User123 disconnected" or "User User123 has left" or "disconnecting player User123"
        leave_match = re.search(r'User\s+([a-zA-Z0-9_\-]+)\s+(?:disconnected|has left)', line, re.IGNORECASE)
        if not leave_match:
            leave_match = re.search(r'disconnecting player\s+([a-zA-Z0-9_\-]+)', line, re.IGNORECASE)

        if leave_match:
            username = leave_match.group(1).strip()
            if username in self.online_players:
                self.online_players.remove(username)
                logger.info(f"Player left: {username}")
                self.player_left.emit(username)
                self.players_updated.emit(list(self.online_players))
            return

        # Response to 'players' command in console:
        # "Players connected (2):"
        # "- Player1"
        # "- Player2"
        if line.startswith("- ") and len(line) > 2:
            candidate = line[2:].strip().split()[0]
            if candidate and candidate not in self.online_players:
                self.online_players.add(candidate)
                self.players_updated.emit(list(self.online_players))

    def get_online_players(self) -> List[str]:
        return sorted(list(self.online_players))

    def clear_online_players(self):
        self.online_players.clear()
        self.players_updated.emit([])

    # ================= SQLite Whitelist & Ban Management =================
    def _execute_query(self, query: str, params: tuple = (), fetch: bool = False):
        if not self.db_path.exists():
            return [] if fetch else None

        try:
            with sqlite3.connect(str(self.db_path), timeout=5) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                if fetch:
                    return [dict(r) for r in cursor.fetchall()]
                conn.commit()
                return True
        except Exception as e:
            logger.warning(f"Database query failed ({query[:30]}): {e}")
            return [] if fetch else False

    def get_whitelist(self) -> List[Dict]:
        """Fetch all registered users from whitelist table."""
        return self._execute_query("SELECT username, accesslevel, password FROM whitelist", fetch=True) or []

    def add_to_whitelist(self, username: str, password: str = "", access_level: str = "") -> bool:
        """Add or update player in whitelist."""
        query = """
            INSERT INTO whitelist (username, password, accesslevel)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
            password=excluded.password, accesslevel=excluded.accesslevel
        """
        return bool(self._execute_query(query, (username, password, access_level)))

    def remove_from_whitelist(self, username: str) -> bool:
        """Remove player from whitelist."""
        return bool(self._execute_query("DELETE FROM whitelist WHERE username = ?", (username,)))

    def get_banned_players(self) -> List[Dict]:
        """Fetch banned Steam IDs / accounts."""
        banned = []
        b_steam = self._execute_query("SELECT steamid, reason FROM bannedsteamids", fetch=True) or []
        for b in b_steam:
            banned.append({"type": "SteamID", "target": b.get("steamid", ""), "reason": b.get("reason", "")})

        b_ips = self._execute_query("SELECT ip, reason FROM bannedips", fetch=True) or []
        for b in b_ips:
            banned.append({"type": "IP", "target": b.get("ip", ""), "reason": b.get("reason", "")})
        return banned

    def unban(self, target: str, target_type: str = "SteamID") -> bool:
        if target_type == "IP":
            return bool(self._execute_query("DELETE FROM bannedips WHERE ip = ?", (target,)))
        return bool(self._execute_query("DELETE FROM bannedsteamids WHERE steamid = ?", (target,)))

    # ================= Quick Admin Command Generators =================
    @staticmethod
    def cmd_kick(username: str, reason: str = "Kicked by Administrator") -> str:
        return f'kickuser "{username}" -r "{reason}"'

    @staticmethod
    def cmd_ban(username: str, reason: str = "Banned by Administrator") -> str:
        return f'banuser "{username}" -r "{reason}"'

    @staticmethod
    def cmd_unban(username: str) -> str:
        return f'unbanuser "{username}"'

    @staticmethod
    def cmd_teleport(source_player: str, target_player: str) -> str:
        return f'teleport "{source_player}" "{target_player}"'

    @staticmethod
    def cmd_set_access(username: str, level: str = "admin") -> str:
        # levels: none, gm, overseer, moderator, admin
        return f'setaccesslevel "{username}" "{level}"'

    @staticmethod
    def cmd_godmode(username: str, enabled: bool = True) -> str:
        state = "-true" if enabled else "-false"
        return f'godmode "{username}" {state}'

    @staticmethod
    def cmd_servermsg(message: str) -> str:
        return f'servermsg "{message}"'

    @staticmethod
    def cmd_save() -> str:
        return 'save'

    @staticmethod
    def cmd_startrain() -> str:
        return 'startrain'

    @staticmethod
    def cmd_stoprain() -> str:
        return 'stoprain'

    @staticmethod
    def cmd_gunshot() -> str:
        return 'gunshot'

    @staticmethod
    def cmd_chopper() -> str:
        return 'chopper'

    @staticmethod
    def cmd_add_item(username: str, item_id: str, count: int = 1) -> str:
        return f'additem "{username}" "{item_id}" {count}'
