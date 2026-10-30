#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from core.map_manager import MapManager, DEFAULT_TOWNS
from web.server import create_app
from web.auth import AuthManager
from main import get_default_paths


def test_map_manager_info_and_towns(tmp_path):
    paths = {
        'server_dir': tmp_path / 'PZServer',
        'zomboid_dir': tmp_path / 'Zomboid',
        'server_config_dir': tmp_path / 'Zomboid' / 'Server',
        'steamcmd_dir': tmp_path / 'PZServer' / 'steamcmd'
    }
    mm = MapManager(paths, 'test_server')
    info = mm.get_info()

    assert info['ok'] is True
    assert 'bounds' in info
    assert len(info['bounds']) == 4
    assert info['bounds'] == [0, 0, 19968, 16128]
    assert len(info['towns']) >= len(DEFAULT_TOWNS)
    # Check major towns
    names = [t['name'] for t in info['towns']]
    assert 'Muldraugh' in names
    assert 'West Point' in names
    assert 'Rosewood' in names
    assert 'Riverside' in names
    assert 'Louisville' in names


def test_map_api_endpoints(tmp_path):
    paths = {
        'server_dir': tmp_path / 'PZServer',
        'zomboid_dir': tmp_path / 'Zomboid',
        'server_config_dir': tmp_path / 'Zomboid' / 'Server',
        'steamcmd_dir': tmp_path / 'PZServer' / 'steamcmd'
    }
    auth = AuthManager()
    token = auth.create_session()
    app = create_app(paths, auth_manager=auth)
    client = TestClient(app)

    headers = {'Authorization': f'Bearer {token}'}

    # 1. Info endpoint
    info_resp = client.get('/api/map/info', headers=headers)
    assert info_resp.status_code == 200
    data = info_resp.json()
    assert data['ok'] is True
    assert 'towns' in data
    assert 'bounds' in data

    # 2. Players endpoint
    p_resp = client.get('/api/map/players', headers=headers)
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert p_data['ok'] is True
    assert isinstance(p_data['players'], list)

    # 3. Teleport endpoint
    tp_resp = client.post(
        '/api/map/teleport',
        json={'username': 'Survivor1', 'x': 11181, 'y': 9725, 'z': 0},
        headers=headers
    )
    assert tp_resp.status_code == 200
    assert tp_resp.json()['ok'] is True

    # 4. Save endpoint
    save_resp = client.post('/api/map/save', headers=headers)
    assert save_resp.status_code == 200
    assert save_resp.json()['ok'] is True

    # 5. POIs endpoint
    pois_resp = client.get('/api/map/pois', headers=headers)
    assert pois_resp.status_code == 200
    pois_data = pois_resp.json()
    assert pois_data['ok'] is True
    assert isinstance(pois_data['pois'], list)

    # 6. Buildings endpoint
    blds_resp = client.get('/api/map/buildings?x0=10600&y0=9700&x1=10800&y1=9900', headers=headers)
    assert blds_resp.status_code == 200
    blds_data = blds_resp.json()
    assert blds_data['ok'] is True
    assert isinstance(blds_data['buildings'], list)
