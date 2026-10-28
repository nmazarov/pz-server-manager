import pytest
from pathlib import Path
from web.auth import AuthManager

def test_auth_manager_creation_and_verification(tmp_path):
    auth_file = tmp_path / "web_auth.json"
    am = AuthManager(auth_path=auth_file, default_password="my_secret_password_123")
    
    assert auth_file.exists()
    assert am.verify_password("my_secret_password_123") is True
    assert am.verify_password("wrong_password") is False

def test_auth_manager_session(tmp_path):
    auth_file = tmp_path / "web_auth.json"
    am = AuthManager(auth_path=auth_file, default_password="session_test_pass")
    token = am.create_session()
    assert token is not None
    assert am.validate_session(token) is True
    
    am.revoke_session(token)
    assert am.validate_session(token) is False
