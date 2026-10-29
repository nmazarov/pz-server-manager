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
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase

import traceback
from ui import MainWindow
from core.server_installer import ServerInstaller, find_existing_server_installations, get_installed_server_buildid, buildid_to_game_version
from core.config_manager import ConfigManager
from core.translations import set_language, tr, get_language

# Reconfigure standard streams to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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


def get_app_root_dir() -> Path:
    """Get the root directory of the application manager."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).parent.resolve()


def get_default_paths(server_name: str = "servertest") -> dict:
    """Get default paths for server installation and configuration."""
    app_root = get_app_root_dir()
    home = Path(os.environ.get('USERPROFILE', Path.home()))

    # Default server folder placed right next to the manager (app_root / 'PZServer')
    # If app_root contains Cyrillic / non-ASCII, SteamCMD requires an ASCII-safe fallback
    try:
        str(app_root).encode('ascii')
        server_dir = app_root / "PZServer"
    except UnicodeEncodeError:
        system_drive = os.environ.get("SystemDrive", "C:")
        server_dir = Path(f"{system_drive}/PZServer")

    steamcmd_dir = server_dir / 'steamcmd'

    return {
        'server_dir': server_dir,
        'steamcmd_dir': steamcmd_dir,
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
    server_dir = paths.get('server_dir')
    if not server_dir:
        return False
    server_dir = Path(server_dir)
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
    if any(c.exists() for c in candidates):
        return True

    # Check nested steamapps folder in steamcmd
    steamcmd_dir = paths.get('steamcmd_dir', server_dir / 'steamcmd')
    nested = Path(steamcmd_dir) / 'steamapps' / 'common' / 'Project Zomboid Dedicated Server'
    if (nested / 'StartServer64.bat').exists() or (nested / 'ProjectZomboid64.exe').exists():
        try:
            import shutil
            server_dir.mkdir(parents=True, exist_ok=True)
            for item in nested.iterdir():
                dest = server_dir / item.name
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest, ignore_errors=True)
                    else:
                        dest.unlink(missing_ok=True)
                shutil.move(str(item), str(server_dir))
            return True
        except Exception:
            pass

    return any(c.exists() for c in candidates)


def _load_custom_fonts():
    """Load bundled Inter and JetBrains Mono fonts into Qt font database."""
    base_dirs = []
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            base_dirs.append(Path(sys._MEIPASS))
        base_dirs.append(Path(sys.executable).parent)
    base_dirs.append(Path(__file__).resolve().parent)

    inter_found = False
    jb_found = False
    for base in base_dirs:
        if not inter_found:
            for font_name in ["Inter-Regular.ttf", "Inter-Bold.ttf", "Inter.ttf"]:
                inter_file = base / "assets" / "fonts" / font_name
                if inter_file.exists():
                    QFontDatabase.addApplicationFont(str(inter_file))
                    inter_found = True
        if not jb_found:
            jb_file = base / "assets" / "fonts" / "JetBrainsMono.ttf"
            if jb_file.exists():
                QFontDatabase.addApplicationFont(str(jb_file))
                jb_found = True


def _get_platform_font() -> QFont:
    """Get Inter font for clean, modern UI aesthetic, with system fallbacks."""
    families = QFontDatabase().families()
    if "Inter" in families:
        return QFont("Inter", 10)
    system = platform.system()
    if system == 'Windows':
        return QFont("Segoe UI", 10)
    elif system == 'Darwin':
        return QFont("SF Pro Text", 11)
    else:
        return QFont("Noto Sans", 10)


def _get_monospace_font() -> str:
    """Get JetBrains Mono font for logs and console, with system fallbacks."""
    families = QFontDatabase().families()
    if "JetBrains Mono" in families:
        return "JetBrains Mono"
    system = platform.system()
    if system == 'Windows':
        return 'Consolas'
    elif system == 'Darwin':
        return 'Menlo'
    else:
        return 'DejaVu Sans Mono'


def load_theme_stylesheet(mono_font: str = "JetBrains Mono") -> str:
    """Load the modern dark tactical QSS stylesheet, supporting both dev and frozen mode."""
    candidates = []
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        candidates.append(Path(sys._MEIPASS) / 'assets' / 'theme.qss')
    candidates.append(Path(__file__).resolve().parent / 'assets' / 'theme.qss')
    candidates.append(Path('assets/theme.qss'))

    for p in candidates:
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    qss = f.read()
                    qss = qss.replace('{mono_font}', mono_font)
                    chk_p = (p.parent / 'checkmark.png').resolve().as_posix()
                    qss = qss.replace('{checkmark_url}', f"url('{chk_p}')")
                    return qss
            except Exception as e:
                logger.warning(f"Failed to read stylesheet from {p}: {e}")
    return ""


def main():
    """Main entry point for the application."""
    # Check if invoked in web server mode
    if any(arg in sys.argv for arg in ['--web', '--web-only', 'web_main.py']):
        import web_main
        web_main.main()
        return

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

    # Load custom fonts
    _load_custom_fonts()

    # Set application-wide font (Exo 2 tactical)
    font = _get_platform_font()
    app.setFont(font)

    # Determine monospace font family for stylesheets (JetBrains Mono)
    mono_font = _get_monospace_font()
    # Apply modern dark tactical theme stylesheet
    theme_qss = load_theme_stylesheet(mono_font)
    if theme_qss:
        app.setStyleSheet(theme_qss)

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
                installed_id = get_installed_server_buildid(detected_path)
                ver_name = buildid_to_game_version(installed_id)
                msg_text = tr('server_detected_msg', path=str(detected_path))
                if ver_name:
                    msg_text += f"\n\nВерсия игры: Build {ver_name}" if get_language() == 'ru' else f"\n\nGame version: Build {ver_name}"
                res = QMessageBox.question(
                    None,
                    tr('server_detected_title'),
                    msg_text,
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
