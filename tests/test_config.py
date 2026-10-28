import pytest
from pathlib import Path
from core.config_manager import ConfigManager

def test_config_manager_default_values(tmp_path):
    # Mock paths
    paths = {
        'zomboid_dir': tmp_path,
        'server_config_dir': tmp_path / 'Server',
        'server_dir': tmp_path / 'PZServer',
        'steamcmd_dir': tmp_path / 'PZServer' / 'steamcmd',
    }
    cm = ConfigManager(paths)
    
    defaults = cm.get_default_server_ini()
    assert defaults['DefaultPort'] == '16261'
    assert defaults['MaxPlayers'] == '16'
    assert defaults['PublicName'] == 'My PZ Server'

def test_config_manager_save_and_load(tmp_path):
    config_dir = tmp_path / 'Server'
    config_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        'zomboid_dir': tmp_path,
        'server_config_dir': config_dir,
        'server_dir': tmp_path / 'PZServer',
        'steamcmd_dir': tmp_path / 'PZServer' / 'steamcmd',
    }
    cm = ConfigManager(paths)
    cm.set_server_name("test_server")
    
    ini = cm.get_default_server_ini()
    ini['PublicName'] = 'Awesome PZ Server'
    cm.save_server_ini(ini)
    
    loaded = cm.load_server_ini()
    assert loaded['PublicName'] == 'Awesome PZ Server'
