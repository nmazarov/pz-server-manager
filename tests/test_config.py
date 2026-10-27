import pytest
from pathlib import Path
from core.config_manager import ConfigManager

def test_config_manager_default_values(tmp_path):
    # Mock paths
    paths = {'zomboid_dir': tmp_path}
    cm = ConfigManager(paths)
    
    defaults = cm.get_default_server_ini()
    assert defaults['DefaultPort'] == '16261'
    assert defaults['MaxPlayers'] == '16'
    assert defaults['PublicName'] == 'My PZ Server'
