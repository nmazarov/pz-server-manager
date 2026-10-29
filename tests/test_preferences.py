# -*- coding: utf-8 -*-
"""
Tests for user preferences persistence (RAM allocation, server name, web sync).
"""
import pytest
from pathlib import Path
from core.config_manager import AppPreferences


@pytest.fixture
def temp_paths(tmp_path):
    zomboid_dir = tmp_path / "Zomboid"
    zomboid_dir.mkdir(parents=True, exist_ok=True)
    server_dir = tmp_path / "server"
    server_dir.mkdir(parents=True, exist_ok=True)
    return {
        'zomboid_dir': zomboid_dir,
        'server_dir': server_dir,
        'server_config_dir': zomboid_dir / 'Server',
        'steamcmd_dir': server_dir / 'steamcmd'
    }


def test_app_preferences_ram_persistence(temp_paths):
    # Verify initial default
    prefs = AppPreferences.load(temp_paths)
    assert prefs.get('last_ram_gb', 6) == 6

    # Save 12 GB
    AppPreferences.save(temp_paths, {'last_ram_gb': 12, 'last_server_name': 'tactical_pz'})

    # Reload and verify
    reloaded = AppPreferences.load(temp_paths)
    assert reloaded['last_ram_gb'] == 12
    assert reloaded['last_server_name'] == 'tactical_pz'

    # Save another field without overwriting ram
    AppPreferences.save(temp_paths, {'auto_backup': True})
    reloaded2 = AppPreferences.load(temp_paths)
    assert reloaded2['last_ram_gb'] == 12
    assert reloaded2['auto_backup'] is True


def test_web_preferences_endpoint(temp_paths):
    from fastapi.testclient import TestClient
    from web.server import create_app
    from web.auth import AuthManager

    am = AuthManager()
    token = am.create_session()

    app = create_app(paths=temp_paths, auth_manager=am)
    client = TestClient(app)

    # Initial preferences
    res = client.get("/api/preferences", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

    # Save via Web API
    save_res = client.post(
        "/api/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"last_ram_gb": 16, "last_server_name": "survivor_hub"}
    )
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # Check status endpoint returns the saved RAM and server name
    status_res = client.get("/api/status", headers={"Authorization": f"Bearer {token}"})
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["ram_gb"] == 16
    assert data["server_name"] == "survivor_hub"
