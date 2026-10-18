#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication & Session Management for PZ Server Manager Web Dashboard.
"""

import os
import json
import secrets
import hashlib
from pathlib import Path
from typing import Optional

AUTH_FILE = Path("web_auth.json")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()


class AuthManager:
    """Manages web dashboard password, salt, and session tokens."""

    def __init__(self, auth_path: Path = AUTH_FILE, default_password: Optional[str] = None):
        self.auth_path = auth_path
        self.active_sessions: set[str] = set()
        self._load_or_create(default_password)

    def _load_or_create(self, default_password: Optional[str] = None):
        if self.auth_path.exists():
            try:
                with open(self.auth_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.salt = data.get('salt', '')
                    self.hashed_pw = data.get('hashed_pw', '')
                    if self.salt and self.hashed_pw:
                        return
            except Exception:
                pass

        # Generate new credentials
        self.salt = secrets.token_hex(16)
        password = default_password if default_password else secrets.token_urlsafe(10)
        self.hashed_pw = _hash_password(password, self.salt)
        self._initial_plain_password = password

        self._save()

    def _save(self):
        try:
            with open(self.auth_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'salt': self.salt,
                    'hashed_pw': self.hashed_pw
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving auth config: {e}")

    def get_initial_password(self) -> Optional[str]:
        return getattr(self, '_initial_plain_password', None)

    def set_password(self, new_password: str):
        self.salt = secrets.token_hex(16)
        self.hashed_pw = _hash_password(new_password, self.salt)
        self.active_sessions.clear()
        self._save()

    def verify_password(self, password: str) -> bool:
        if not password:
            return False
        return _hash_password(password, self.salt) == self.hashed_pw

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
