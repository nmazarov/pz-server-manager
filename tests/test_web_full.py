import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from web.server import create_app
from web.auth import AuthManager
from core.config_manager import ConfigManager
import tempfile
import shutil

@pytest.fixture
def temp_env():
    td = Path(tempfile.mkdtemp())
    server_dir = td / "server"
    server_dir.mkdir(parents=True)
    config_dir = td / "Zomboid" / "Server"
    config_dir.mkdir(parents=True)
    paths = {
        'zomboid_dir': td / "Zomboid",
        'server_config_dir': config_dir,
        'server_dir': server_dir,
        'steamcmd_dir': server_dir / 'steamcmd',
        'app_data': td
    }
    yield {"temp_dir": td, "paths": paths}
    shutil.rmtree(td, ignore_errors=True)

def test_web_index_html_has_all_ids():
    index_path = Path("web/static/index.html")
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")

    required_ids = [
        "btn-lang", "autoscroll-chk", "backups-container", "badge-srv-ram", "badge-version",
        "badge-vps-ram", "beta-access-code", "beta-code-msg", "beta-hidden-branch",
        "btn-do-install", "btn-restart", "btn-start", "btn-stop", "chk-auto-backup",
        "chk-watchdog", "conn-text", "console-cmd", "console-output", "install-branch",
        "install-log-output", "install-progress-fill", "install-status-msg",
        "install-status-pct", "login-error", "login-modal", "login-password",
        "mod-input-id", "mods-container", "players-count-lbl", "players-list-box",
        "pulse-led", "sb-Loot-Food", "sb-Loot-Literature", "sb-Loot-Medical",
        "sb-Loot-Weapon", "sb-ZombieLore-Speed", "sb-ZombieLore-Strength",
        "sb-ZombieLore-Toughness", "sb-ZombieLore-Transmission", "srv-name",
        "srv-ram", "status-sub", "status-title", "steam-branch-rows", "toast",
        "sandbox-preset", "btn-del-preset", "ini-PublicName", "ini-Password", "ini-MaxPlayers",
        "ini-DefaultPort", "ini-PVP", "ini-AutoCreateUserInWhiteList",
        "sb-ZombieLore-Decomposition", "sb-NightDarkness", "sb-TimeSinceApo",
        "sb-SpeedLimit", "sb-ZombieAttractionMultiplier", "sb-RecentlySurvivorVehicles",
        "sb-LockedCar", "sb-SirenShutoffHours"
    ]

    for elem_id in required_ids:
        assert f'id="{elem_id}"' in content, f"Missing id={elem_id} in index.html"

def test_web_settings_and_sandbox_api(temp_env):
    paths = temp_env["paths"]
    cfg_mgr = ConfigManager(paths)
    am = AuthManager()
    token = am.create_session()
    headers = {"Authorization": f"Bearer {token}"}

    app = create_app(
        paths=paths,
        auth_manager=am,
        config_manager=cfg_mgr
    )

    client = TestClient(app)

    # 1. Settings INI
    res = client.get("/api/settings", headers=headers)
    assert res.status_code == 200
    ini_data = res.json()
    assert isinstance(ini_data, dict)

    save_res = client.post("/api/settings", json={
        "PublicName": "My Awesome Server",
        "MaxPlayers": "24",
        "PVP": "true",
        "AutoCreateUserInWhiteList": "true",
        "SafetySystem": "true",
        "VoiceMinDistance": "15",
        "SpeedLimit": "90"
    }, headers=headers)
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    res2 = client.get("/api/settings", headers=headers)
    assert res2.json().get("PublicName") == "My Awesome Server"
    assert res2.json().get("VoiceMinDistance") == "15"
    assert res2.json().get("SpeedLimit") == "90"

    # 2. Sandbox
    res = client.get("/api/sandbox", headers=headers)
    assert res.status_code == 200
    sb_data = res.json()
    assert isinstance(sb_data, dict)

    save_sb = client.post("/api/sandbox", json={
        "ZombieLore": {"Speed": 1, "Strength": 2, "Toughness": 3, "Transmission": 1, "Decomposition": 2},
        "ZombieConfig": {"RallyGroupSize": 25, "RallyGroupRadius": 4},
        "Loot": {"Food": 2, "Weapon": 1, "Literature": 3, "Medical": 4},
        "NightDarkness": 2,
        "TimeSinceApo": 3,
        "SpeedLimit": 90,
        "ZombieAttractionMultiplier": 1.5,
        "RecentlySurvivorVehicles": 2,
        "LockedCar": 3
    }, headers=headers)
    assert save_sb.status_code == 200
    assert save_sb.json()["success"] is True

    # 3. Translations endpoint
    trans_res = client.get("/api/translations")
    assert trans_res.status_code == 200
    trans_data = trans_res.json()
    assert "ru" in trans_data
    assert "en" in trans_data
    assert trans_data["ru"]["tab_server"] != ""
    assert trans_data["en"]["tab_server"] != ""

def test_web_sandbox_subtabs_exist():
    index_path = Path("web/static/index.html")
    content = index_path.read_text(encoding="utf-8")
    subtabs = [
        "subtab-btn-zombies", "subtab-btn-loot", "subtab-btn-world",
        "subtab-btn-vehicles", "subtab-btn-character", "subtab-btn-mods",
        "sandbox-subtab-zombies", "sandbox-subtab-loot", "sandbox-subtab-world",
        "sandbox-subtab-vehicles", "sandbox-subtab-character", "sandbox-subtab-mods"
    ]
    for s in subtabs:
        assert s in content, f"Missing {s} in index.html"
