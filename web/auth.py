#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication & Session Management for PZ Server Manager Web Dashboard.
"""

import os
import json
import secrets
import bcrypt
from pathlib import Path
from typing import Optional

import sys

def get_auth_file_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve() / "web_auth.json"
    return Path(__file__).resolve().parent.parent / "web_auth.json"


def _hash_password(password: str) -> str:
    # bcrypt handles salt internally
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class AuthManager:
    """Manages web dashboard password, salt, and session tokens."""

    def __init__(self, auth_path: Optional[Path] = None, default_password: Optional[str] = None):
        self.auth_path = auth_path if auth_path else get_auth_file_path()
        self.active_sessions: set[str] = set()
        self._load_or_create(default_password)

    def _load_or_create(self, default_password: Optional[str] = None):
        if self.auth_path.exists():
            try:
                with open(self.auth_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self.hashed_pw = data.get('hashed_pw', '')
                    if self.hashed_pw:
                        return
            except Exception:
                pass

        # Generate new credentials
        password = default_password if default_password else secrets.token_urlsafe(16)
        self.hashed_pw = _hash_password(password)
        self._initial_plain_password = password

        # Save initial password for user
        with open(self.auth_path.parent / "initial_password.txt", "w") as f:
            f.write(password)

        self._save()

    def _save(self):
        try:
            with open(self.auth_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'hashed_pw': self.hashed_pw
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving auth config: {e}")

    def get_initial_password(self) -> Optional[str]:
        return getattr(self, '_initial_plain_password', None)

    def set_password(self, new_password: str):
        self.hashed_pw = _hash_password(new_password)
        self.active_sessions.clear()
        self._save()

    def verify_password(self, password: str) -> bool:
        if not password:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_pw.encode('utf-8'))

    def create_session(self) -> str:
        token = secrets.token_hex(32)
        self.active_sessions.add(token)
        return token

    def validate_session(self, token: Optional[str]) -> bool:
        if not token:
            return False
        return token in self.active_sessions

    def revoke_session(self, token: str):
        self.active_sessions.discard(token)
