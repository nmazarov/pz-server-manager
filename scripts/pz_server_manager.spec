# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PZ Server Manager (Single-file .exe edition).
Builds a single standalone dist/PZ Server Manager.exe file.
"""

import sys
import os
import PyQt5

# Fix Qt5 non-ASCII path resolution on Windows (e.g. 'Рабочий стол')
qt_path = os.path.abspath(os.path.dirname(PyQt5.__file__))
plugins_path = os.path.join(qt_path, 'Qt5', 'plugins')
if not os.path.exists(plugins_path):
    plugins_path = os.path.join(qt_path, 'plugins')

os.environ['QT_PLUGIN_PATH'] = plugins_path

try:
    import PyInstaller.utils.hooks.qt as pyi_qt
    _orig_collect_plugins = pyi_qt.QtLibraryInfo.collect_plugins

    def _patched_collect_plugins(self, plugin_type):
        p_dir = os.path.join(plugins_path, plugin_type)
        if os.path.exists(p_dir):
            return [(p_dir, os.path.join('PyQt5', 'Qt5', 'plugins', plugin_type))]
        try:
            return _orig_collect_plugins(self, plugin_type)
        except Exception:
            return []

    pyi_qt.QtLibraryInfo.collect_plugins = _patched_collect_plugins
except Exception as e:
    print(f"Qt patch note: {e}")

block_cipher = None

project_root = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'assets'), 'assets'),
        (os.path.join(project_root, 'web', 'static'), 'web/static'),
        (os.path.join(project_root, 'data'), 'data'),
    ],
    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'core',
        'core.config_manager',
        'core.mod_manager',
        'core.server_installer',
        'core.server_process',
        'core.translations',
        'core.backup_manager',
        'core.network_helper',
        'core.diagnostics_manager',
        'core.player_manager',
        'core.profile_manager',
        'core.watchdog_manager',
        'core.map_manager',
        'ui',
        'ui.main_window',
        'ui.dialogs',
        'ui.server_tab',
        'ui.settings_tab',
        'ui.sandbox_tab',
        'ui.mods_tab',
        'ui.install_tab',
        'ui.map_tab',
        'web',
        'web.server',
        'web.auth',
        'web_main',
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.responses',
        'starlette',
        'starlette.staticfiles',
        'starlette.responses',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
        'pydantic',
        'pydantic_core',
        'websockets',
        'psutil',
        'bcrypt',
        'slowapi',
        'limits',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PZ Server Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
    icon=os.path.join(project_root, 'assets', 'icon.ico'),
)
