#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Zomboid Dedicated Server Manager
Main entry point for the application.

This application provides a GUI for installing, configuring, and managing
a Project Zomboid dedicated server on Windows, macOS, and Linux.
"""

import sys
import os
import logging
import platform
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

import traceback
from main_window import MainWindow
from server_installer import ServerInstaller, find_existing_server_installations
from config_manager import ConfigManager
from translations import set_language, tr

# Ensure logs directory exists
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / 'pz_manager.log'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def global_exception_hook(exctype, value, tb):
    """Global exception handler logging to logs/pz_manager.log and showing dialog."""
    err_msg = "".join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"Unhandled exception:\n{err_msg}")
    
    # Try to show QMessageBox if QApplication instance exists
    app = QApplication.instance()
    if app:
        QMessageBox.critical(
            None,
            tr('app_title') or "Critical Error",
            f"An unexpected error occurred:\n{str(value)}\n\n"
            f"Details saved to {LOG_FILE.resolve()}"
        )
    sys.__excepthook__(exctype, value, tb)


sys.excepthook = global_exception_hook



def is_admin() -> bool:
    """Check if the application is running with elevated privileges."""
    if os.name == 'nt':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        # Unix: check if running as root
        return os.geteuid() == 0


def request_admin():
    """Request elevated privileges by relaunching the application."""
    if os.name == 'nt':
        try:
            import ctypes
            script = sys.argv[0]
            params = ' '.join(sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            return True
        except Exception as e:
            logger.error(f"Failed to request admin: {e}")
            return False
    else:
        # On Unix, suggest running with sudo
        logger.info("On macOS/Linux, re-run with: sudo python3 main.py")
        return False


def get_default_paths() -> dict:
    """Get default paths for server installation and configuration."""
    system = platform.system()

    if system == 'Windows':
        home = Path(os.environ.get('USERPROFILE', Path.home()))
        return {
            'server_dir': Path('C:/PZServer'),
            'steamcmd_dir': Path('C:/PZServer/steamcmd'),
            'zomboid_dir': home / 'Zomboid',
            'server_config_dir': home / 'Zomboid' / 'Server',
        }
    else:
        # macOS and Linux
        home = Path.home()
        return {
            'server_dir': home / 'pzserver',
            'steamcmd_dir': home / 'pzserver' / 'steamcmd',
            'zomboid_dir': home / 'Zomboid',
            'server_config_dir': home / 'Zomboid' / 'Server',
        }


def ensure_directories(paths: dict) -> None:
    """Create necessary directories if they don't exist."""
    for name, path in paths.items():
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {path}: {e}")


def check_server_installed(paths: dict) -> bool:
    """Check if Project Zomboid server is already installed."""
    server_dir = paths['server_dir']
    # Windows executables
    candidates = [
        server_dir / 'ProjectZomboid64.exe',
        server_dir / 'StartServer64.bat',
    ]
    # Unix executables
    candidates += [
        server_dir / 'start-server.sh',
        server_dir / 'ProjectZomboid64',
    ]
    return any(c.exists() for c in candidates)


def _get_platform_font() -> QFont:
    """Get appropriate font for the current platform."""
    system = platform.system()
    if system == 'Windows':
        return QFont("Segoe UI", 10)
    elif system == 'Darwin':
        return QFont("SF Pro Text", 11)
    else:
        return QFont("Noto Sans", 10)


def main():
    """Main entry point for the application."""
    # Load language preference
    try:
        with open('language.cfg', 'r') as f:
            lang = f.read().strip()
            if lang in ('en', 'ru'):
                set_language(lang)
    except Exception:
        set_language('ru')  # Default to Russian

    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("PZ Server Manager")
    app.setOrganizationName("PZServerManager")

    # Set application-wide font (platform-aware)
    font = _get_platform_font()
    app.setFont(font)

    # Determine monospace font family for stylesheets
    system = platform.system()
    if system == 'Windows':
        mono_font = 'Consolas'
    elif system == 'Darwin':
        mono_font = 'Menlo'
    else:
        mono_font = 'DejaVu Sans Mono'

    # Apply dark theme stylesheet
    app.setStyleSheet(f"""
        QMainWindow, QWidget {{
            background-color: #2b2b2b;
            color: #ffffff;
        }}
        QTabWidget::pane {{
            border: 1px solid #3d3d3d;
            background-color: #2b2b2b;
        }}
        QTabBar::tab {{
            background-color: #3d3d3d;
            color: #ffffff;
            padding: 8px 20px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: #4a4a4a;
            border-bottom: 2px solid #5294e2;
        }}
        QPushButton {{
            background-color: #3d3d3d;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 8px 16px;
            border-radius: 4px;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #4a4a4a;
        }}
        QPushButton:pressed {{
            background-color: #5294e2;
        }}
        QPushButton:disabled {{
            background-color: #2b2b2b;
            color: #666666;
        }}
        QPushButton#startBtn {{
            background-color: #2e7d32;
        }}
        QPushButton#startBtn:hover {{
            background-color: #388e3c;
        }}
        QPushButton#stopBtn {{
            background-color: #c62828;
        }}
        QPushButton#stopBtn:hover {{
            background-color: #d32f2f;
        }}
        QLineEdit, QSpinBox, QComboBox {{
            background-color: #3d3d3d;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 4px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            width: 0px;
            height: 0px;
            border: none;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 1px solid #5294e2;
        }}
        QTextEdit, QPlainTextEdit {{
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3d3d3d;
            font-family: {mono_font}, monospace;
        }}
        QListWidget {{
            background-color: #3d3d3d;
            color: #ffffff;
            border: 1px solid #555555;
        }}
        QListWidget::item:selected {{
            background-color: #5294e2;
        }}
        QProgressBar {{
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #3d3d3d;
        }}
        QProgressBar::chunk {{
            background-color: #5294e2;
        }}
        QLabel {{
            color: #ffffff;
        }}
        QGroupBox {{
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            color: #5294e2;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }}
        QCheckBox {{
            color: #ffffff;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
        }}
        QScrollBar:vertical {{
            background-color: #2b2b2b;
            width: 12px;
        }}
        QScrollBar::handle:vertical {{
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: #666666;
        }}
        QMenuBar {{
            background-color: #2b2b2b;
            color: #ffffff;
        }}
        QMenuBar::item:selected {{
            background-color: #3d3d3d;
        }}
        QMenu {{
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #3d3d3d;
        }}
        QMenu::item:selected {{
            background-color: #5294e2;
        }}
    """)

    try:
        # Get default paths
        paths = get_default_paths()

        # Check if server is installed in default path
        server_installed = check_server_installed(paths)

        # Auto-detect manually installed server in common system paths if default not installed
        if not server_installed:
            existing = find_existing_server_installations()
            if existing:
                detected_path = existing[0]
                res = QMessageBox.question(
                    None,
                    tr('server_detected_title'),
                    tr('server_detected_msg', path=str(detected_path)),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if res == QMessageBox.Yes:
                    paths['server_dir'] = detected_path
                    paths['steamcmd_dir'] = detected_path / 'steamcmd'
                    server_installed = True

        # Create and show main window
        window = MainWindow(paths, server_installed)
        window.show()

        # If server is still not installed, offer automated first-run installation
        if not server_installed:
            result = QMessageBox.question(
                window,
                tr('first_run_title'),
                tr('first_run_msg'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if result == QMessageBox.Yes:
                window.show_install_tab()

        sys.exit(app.exec_())

    except Exception as e:
        logger.exception("Application error")
        QMessageBox.critical(
            None,
            "Error",
            f"An error occurred:\n{str(e)}\n\nCheck pz_server_manager.log for details."
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
