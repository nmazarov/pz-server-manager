import pytest
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    return app

def test_theme_qss_combobox_arrow():
    from main import load_theme_stylesheet
    qss = load_theme_stylesheet("Consolas")
    assert "arrow_down.png" in qss, "arrow_down.png must be present in loaded stylesheet"
    assert "arrow_down_hover.png" in qss, "arrow_down_hover.png must be present in loaded stylesheet"
    assert "border-left: 4px solid transparent" not in qss, "Broken 0px border triangle must be removed"

def test_desktop_sandbox_vehicle_controls(qapp, tmp_path):
    from ui.sandbox_tab import SandboxTabMixin
    from core.config_manager import ConfigManager
    from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLineEdit

    class DummyWindow(QMainWindow, SandboxTabMixin):
        def __init__(self):
            super().__init__()
            self.tabs = QTabWidget()
            self.setCentralWidget(self.tabs)
            self.statusBar = QStatusBar()
            self.server_name_input = QLineEdit("testserver")
            self.paths = {
                'server_config_dir': tmp_path / "Server",
                'zomboid_dir': tmp_path,
            }
            self.config_manager = ConfigManager(self.paths)
            self.create_sandbox_tab()

    win = DummyWindow()
    win.show()

    # 1. Check all 17 vehicle settings exist
    assert hasattr(win, 'sandbox_enable_vehicles')
    assert hasattr(win, 'sandbox_car_spawn')
    assert hasattr(win, 'sandbox_car_condition')
    assert hasattr(win, 'sandbox_recent_survivor')
    assert hasattr(win, 'sandbox_locked_car')
    assert hasattr(win, 'sandbox_vehicle_easy_use')
    assert hasattr(win, 'sandbox_traffic_jam')
    assert hasattr(win, 'sandbox_speed_limit')
    assert hasattr(win, 'sandbox_zombie_attraction')
    assert hasattr(win, 'sandbox_chance_gas')
    assert hasattr(win, 'sandbox_initial_gas')
    assert hasattr(win, 'sandbox_gas_consumption')
    assert hasattr(win, 'sandbox_car_alarm')
    assert hasattr(win, 'sandbox_siren_shutoff')
    assert hasattr(win, 'sandbox_car_damage_impact')
    assert hasattr(win, 'sandbox_damage_hit_by_car')
    assert hasattr(win, 'sandbox_crash_damage')

    # 2. Check preset toolbar buttons
    assert hasattr(win, 'b_save_preset')
    assert hasattr(win, 'b_del_preset')
    assert hasattr(win, 'preset_combo')

    # 3. Test gather and apply state
    win.sandbox_speed_limit.setValue(115)
    win.sandbox_car_spawn.setCurrentIndex(4) # high
    win.sandbox_enable_vehicles.setChecked(False)

    state = win._gather_sandbox_state()
    assert state['SpeedLimit'] == 115
    assert state['EnableVehicles'] is False

    # Change widgets, then re-apply state
    win.sandbox_speed_limit.setValue(60)
    win.sandbox_enable_vehicles.setChecked(True)
    assert win.sandbox_speed_limit.value() == 60

    win._apply_sandbox_state(state)
    assert win.sandbox_speed_limit.value() == 115
    assert win.sandbox_enable_vehicles.isChecked() is False

    # 4. Test custom preset saving and applying
    win.custom_presets['MyCustomPreset'] = state
    win._populate_presets_combo(select_preset='⭐ MyCustomPreset')
    assert win.preset_combo.currentText() == '⭐ MyCustomPreset'
    assert win.b_del_preset.isHidden() is False
