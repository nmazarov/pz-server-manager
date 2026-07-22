# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PZ Server Manager.
Includes monkey-patch for Qt5 non-ASCII path resolution on Windows.
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

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5.sip',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'config_manager',
        'main_window',
        'mod_manager',
        'server_installer',
        'server_process',
        'translations',
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
    [],
    exclude_binaries=True,
    name='PZ Server Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PZ Server Manager',
)
