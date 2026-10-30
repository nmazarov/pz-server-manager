import pytest
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
import sys

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    return app

def test_map_tab_dropdown_and_towns(qapp):
    from ui.map_tab import MapTabMixin
    from core.map_manager import MapManager
    from main import get_default_paths

    class DummyWindow(QMainWindow, MapTabMixin):
        def __init__(self):
            super().__init__()
            self.tabs = QTabWidget()
            self.paths = get_default_paths()
            self.current_server_name = "servertest"
            self.map_manager = MapManager(self.paths, self.current_server_name)
            self.create_map_tab()

    w = DummyWindow()

    assert hasattr(w, "cb_map_towns"), "cb_map_towns should exist"
    assert w.cb_map_towns.minimumWidth() >= 180, "cb_map_towns minimumWidth should be >= 180"
    assert w.cb_map_towns.view().minimumWidth() >= 200, "cb_map_towns popup view minimumWidth should be >= 200"

    assert hasattr(w, "btn_map_layers"), "btn_map_layers should exist"
    assert hasattr(w, "cat_checkboxes"), "cat_checkboxes should exist"
    assert "police" in w.cat_checkboxes, "police checkbox should exist"
    assert "guns" in w.cat_checkboxes, "guns checkbox should exist"

    # Test toggling category
    w.cat_checkboxes["police"].setChecked(False)
    assert w.pz_map_canvas.category_filters.get("police") is False
    w.cat_checkboxes["police"].setChecked(True)
    assert w.pz_map_canvas.category_filters.get("police") is True

    # Test select/deselect all
    w._deselect_all_map_categories()
    assert all(chk.isChecked() is False for chk in w.cat_checkboxes.values())
    w._select_all_map_categories()
    assert all(chk.isChecked() is True for chk in w.cat_checkboxes.values())
    w.cleanup_map_tab()

def test_web_map_dropdown():
    with open("web/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    assert "id=\"map-categories-menu\"" in html
    assert "id=\"map-category-checkboxes\"" in html
    assert "data-cat=\"police\"" in html
    assert "data-cat=\"guns\"" in html
