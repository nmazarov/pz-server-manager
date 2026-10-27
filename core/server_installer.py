#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Installer Module
Handles downloading SteamCMD and installing/updating the Project Zomboid server.
Supports Windows, macOS, and Linux.
"""

import os
import sys
import logging
import zipfile
import tarfile
import subprocess
import urllib.request
import json
import shutil
import stat
import platform
import re
import datetime
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# Constants
PZ_APP_ID = "380870"  # Project Zomboid Dedicated Server


def format_steam_date(timestamp: int or str, lang: str = "ru") -> str:
    """Format UNIX timestamp in the exact Steam style: '28 сент. 2026 г.' or 'Sep 28, 2026'."""
    try:
        dt = datetime.datetime.fromtimestamp(int(timestamp))
    except Exception:
        return ""
    ru_months = {
        1: 'янв.', 2: 'февр.', 3: 'мар.', 4: 'апр.', 5: 'мая', 6: 'июн.',
        7: 'июл.', 8: 'авг.', 9: 'сент.', 10: 'окт.', 11: 'нояб.', 12: 'дек.'
    }
    if lang == 'ru':
        return f"{dt.day} {ru_months.get(dt.month, str(dt.month))} {dt.year} г."
    return dt.strftime("%b %d, %Y")


def fetch_available_server_branches(lang: str = "ru") -> list:
    """
    Fetch the currently available public beta branches and versions from Steam for App 380870.
    Matches Steam's exact UI strings and layout:
    - Name & Description (e.g. 'Стандартная общедоступная версия' / 'Самая распространённая версия игры')
    - Last updated date (e.g. '28 сент. 2026 г.')
    """
    url = f"https://api.steamcmd.net/v1/info/{PZ_APP_ID}"
    branches_list = []

    # Canonical metadata matching Steam's exact Russian & English UI
    CANONICAL_META = {
        'public': {
            'order': 0,
            'name_ru': 'Стандартная общедоступная версия',
            'desc_ru': 'Самая распространённая версия игры',
            'name_en': 'Default public version',
            'desc_en': 'Most common version of the game',
            'default_ts': 1790597203,
            'default_buildid': '25485538',
        },
        'unstable': {
            'order': 1,
            'name_ru': 'unstable',
            'desc_ru': 'Unstable',
            'name_en': 'unstable',
            'desc_en': 'Unstable',
            'default_ts': 1790178694,
            'default_buildid': '25485538',
        },
        '42.19': {
            'order': 2,
            'name_ru': '42.19',
            'desc_ru': 'Build 42.19.2',
            'name_en': '42.19',
            'desc_en': 'Build 42.19.2',
            'default_ts': 1787742952,
            'default_buildid': '24929695',
        },
        'legacy41': {
            'order': 3,
            'name_ru': 'legacy41',
            'desc_ru': 'Build 41.78.21',
            'name_en': 'legacy41',
            'desc_en': 'Build 41.78.21',
            'default_ts': 1787742984,
            'default_buildid': '24928750',
        },
    }

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            raw_branches = data.get('data', {}).get(PZ_APP_ID, {}).get('depots', {}).get('branches', {})
            for b_key, b_info in raw_branches.items():
                if b_info.get('pwdrequired') == '1':
                    continue
                build_id = b_info.get('buildid', '')
                desc_api = b_info.get('description', '')
                ts = b_info.get('timeupdated') or b_info.get('timebuildupdated')

                meta = CANONICAL_META.get(b_key, {})
                order = meta.get('order', 10)
                name_ru = meta.get('name_ru', b_key)
                name_en = meta.get('name_en', b_key)
                desc_ru = meta.get('desc_ru', desc_api or f"Branch {b_key}")
                desc_en = meta.get('desc_en', desc_api or f"Branch {b_key}")

                if not ts:
                    ts = meta.get('default_ts', 0)

                date_ru = format_steam_date(ts, 'ru')
                date_en = format_steam_date(ts, 'en')
                date_str = date_ru if lang == 'ru' else date_en

                name = name_ru if lang == 'ru' else name_en
                desc = desc_ru if lang == 'ru' else desc_en

                label = f"{name} — {desc} [{date_str}]" if date_str else f"{name} — {desc}"

                branches_list.append({
                    'branch': '' if b_key == 'public' else b_key,
                    'key': b_key,
                    'name': name,
                    'name_ru': name_ru,
                    'name_en': name_en,
                    'description': desc,
                    'desc_ru': desc_ru,
                    'desc_en': desc_en,
                    'date_str': date_str,
                    'date_ru': date_ru,
                    'date_en': date_en,
                    'timeupdated': int(ts) if ts else 0,
                    'buildid': build_id,
                    'label': label,
                    'order': order,
                })
        logger.info(f"Loaded {len(branches_list)} server branches from Steam for App {PZ_APP_ID}")
    except Exception as e:
        logger.warning(f"Failed to fetch live branches from api.steamcmd.net: {e}")

    if not branches_list:
        # Fallback offline list matching Steam's exact layout and dates
        for b_key, meta in CANONICAL_META.items():
            ts = meta['default_ts']
            date_ru = format_steam_date(ts, 'ru')
            date_en = format_steam_date(ts, 'en')
            date_str = date_ru if lang == 'ru' else date_en
            name = meta['name_ru'] if lang == 'ru' else meta['name_en']
            desc = meta['desc_ru'] if lang == 'ru' else meta['desc_en']
            label = f"{name} — {desc} [{date_str}]"
            branches_list.append({
                'branch': '' if b_key == 'public' else b_key,
                'key': b_key,
                'name': name,
                'name_ru': meta['name_ru'],
                'name_en': meta['name_en'],
                'description': desc,
                'desc_ru': meta['desc_ru'],
                'desc_en': meta['desc_en'],
                'date_str': date_str,
                'date_ru': date_ru,
                'date_en': date_en,
                'timeupdated': ts,
                'buildid': meta['default_buildid'],
                'label': label,
                'order': meta['order'],
            })

    # Sort strictly by Steam order
    branches_list.sort(key=lambda x: (x.get('order', 10), -x.get('timeupdated', 0)))

    return branches_list


def get_steamcmd_url() -> str:
    """Get the SteamCMD download URL for the current platform."""
    system = platform.system()
    if system == 'Windows':
        return "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
    elif system == 'Darwin':
        return "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_osx.tar.gz"
    else:  # Linux
        return "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"


def get_steamcmd_executable_name() -> str:
    """Get the SteamCMD executable name for the current platform."""
    if os.name == 'nt':
        return "steamcmd.exe"
    else:
        return "steamcmd.sh"


def check_disk_space(target_path: Path, required_gb: float = 5.0) -> tuple:
    """Check free disk space in GB on target_path drive."""
    try:
        # Resolve existing parent directory for check
        check_dir = target_path
        while not check_dir.exists() and check_dir.parent != check_dir:
            check_dir = check_dir.parent
        usage = shutil.disk_usage(check_dir)
        free_gb = usage.free / (1024 ** 3)
        return (free_gb >= required_gb, free_gb)
    except Exception as e:
        logger.warning(f"Could not check disk space on {target_path}: {e}")
        return (True, 999.0)


KNOWN_BUILD_VERSIONS = {
    '25485538': '42.21',
    '25485521': '42.21',
    '24929695': '42.19.2',
    '24928750': '41.78.21',
    '22418194': '41.78.18',
}


def buildid_to_game_version(build_id: Optional[str], default_branch: str = "public") -> str:
    """Convert Steam buildid or branch to human-readable game version string like 42.21."""
    if not build_id:
        return "42.21" if default_branch in ('public', 'unstable', '') else "41.78.21"
    
    clean_id = str(build_id).strip()
    if clean_id in KNOWN_BUILD_VERSIONS:
        return KNOWN_BUILD_VERSIONS[clean_id]
    
    # If build id is newer than known 42.21 build
    try:
        val = int(clean_id)
        if val >= 25485538:
            return "42.21+"
        elif val >= 24929695:
            return "42.19"
        else:
            return "41.78"
    except Exception:
        pass
    return "42.21"


def get_installed_server_buildid(server_dir: Path) -> Optional[str]:
    """
    Detect the installed BuildID for Project Zomboid Dedicated Server.
    Checks steamapps/appmanifest_380870.acf in server_dir and its parent directories.
    """
    if not server_dir:
        return None
    server_dir = Path(server_dir)
    candidates = [
        server_dir / "steamapps" / f"appmanifest_{PZ_APP_ID}.acf",
        server_dir.parent / "steamapps" / f"appmanifest_{PZ_APP_ID}.acf",
        server_dir.parent.parent / f"appmanifest_{PZ_APP_ID}.acf",
        server_dir / "steamcmd" / "steamapps" / f"appmanifest_{PZ_APP_ID}.acf",
    ]
    for acf_path in candidates:
        if acf_path.exists():
            try:
                with open(acf_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        m = re.search(r'"buildid"\s+"(\d+)"', line)
                        if m:
                            return m.group(1)
            except Exception as e:
                logger.debug(f"Could not read {acf_path}: {e}")
    return None


def find_existing_server_installations() -> list:
    """Scan common paths for an existing Project Zomboid Dedicated Server, sorted by newest build first."""
    program_data = os.environ.get("ProgramData", "C:\\ProgramData")
    app_root = Path(sys.executable).parent.resolve() if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent

    candidates = [
        app_root / "servertest",
        app_root / "PZServer",
        Path("C:/PZServer"),
        Path("C:/Program Files (x86)/Steam/steamapps/common/Project Zomboid Dedicated Server"),
        Path("C:/Program Files/Steam/steamapps/common/Project Zomboid Dedicated Server"),
        Path("D:/SteamLibrary/steamapps/common/Project Zomboid Dedicated Server"),
        Path("E:/SteamLibrary/steamapps/common/Project Zomboid Dedicated Server"),
        Path("F:/SteamLibrary/steamapps/common/Project Zomboid Dedicated Server"),
        Path("G:/SteamLibrary/steamapps/common/Project Zomboid Dedicated Server"),
        Path("H:/SteamLibrary/steamapps/common/Project Zomboid Dedicated Server"),
        Path(program_data) / "PZServer",
        Path.home() / "pzserver",
    ]
    found = []
    for c in candidates:
        try:
            if c.exists() and (
                (c / "StartServer64.bat").exists() or 
                (c / "ProjectZomboid64.exe").exists() or 
                (c / "start-server.sh").exists()
            ):
                found.append(c)
        except Exception:
            pass

    # Sort so that newer builds (Build 42) come before older legacy builds (Build 41)
    def _sort_key(p):
        bid = get_installed_server_buildid(p)
        try:
            return int(bid) if bid else 0
        except Exception:
            return 0

    found.sort(key=_sort_key, reverse=True)
    return found


def check_server_update_available(server_dir: Path, beta_branch: str = "") -> dict:
    """
    Check if a new version of the PZ Dedicated Server is available on Steam.
    Returns:
        {
            'update_available': bool,
            'installed_version': str,
            'latest_version': str,
            'installed_buildid': str or None,
            'latest_buildid': str or None,
            'branch': str,
            'description': str
        }
    """
    installed_id = get_installed_server_buildid(server_dir)
    branches = fetch_available_server_branches()
    target_key = beta_branch if beta_branch else 'public'
    latest_id = None
    desc = ''

    for b in branches:
        if b['key'] == target_key:
            latest_id = b.get('buildid')
            desc = b.get('label', '')
            break

    if not latest_id and branches:
        # Fallback to public branch
        for b in branches:
            if b['key'] == 'public':
                latest_id = b.get('buildid')
                desc = b.get('label', '')
                break

    installed_ver = buildid_to_game_version(installed_id, target_key)
    latest_ver = buildid_to_game_version(latest_id, target_key)

    update_available = False
    if installed_id and latest_id and installed_id != latest_id:
        update_available = True

    return {
        'update_available': update_available,
        'installed_version': installed_ver,
        'latest_version': latest_ver,
        'installed_buildid': installed_id,
        'latest_buildid': latest_id,
        'branch': target_key,
        'description': desc
    }


class ServerUpdateCheckerWorker(QThread):
    """Background worker to check for Project Zomboid server updates on Steam."""

    update_found = pyqtSignal(dict)  # Emits update info dict when an update is available

    def __init__(self, server_dir: Path, beta_branch: str = ""):
        super().__init__()
        self.server_dir = server_dir
        self.beta_branch = beta_branch

    def run(self):
        try:
            res = check_server_update_available(self.server_dir, self.beta_branch)
            if res.get('update_available'):
                self.update_found.emit(res)
        except Exception as e:
            logger.debug(f"Background server update check failed: {e}")


class InstallWorker(QThread):
    """Worker thread for installation process."""

    progress = pyqtSignal(int, str)  # Progress value and message
    log = pyqtSignal(str)  # Log message
    finished = pyqtSignal()  # Installation complete
    error = pyqtSignal(str)  # Error message

    def __init__(self, installer: 'ServerInstaller', paths: dict, beta_branch: str = "", beta_password: str = ""):
        super().__init__()
        self.installer = installer
        self.paths = paths
        self.beta_branch = beta_branch
        self.beta_password = beta_password
        # Sync installer directories with current paths chosen by user
        if 'server_dir' in paths:
            self.installer.server_dir = paths['server_dir']
        if 'steamcmd_dir' in paths:
            self.installer.steamcmd_dir = paths['steamcmd_dir']
        self.installer._sanitize_paths()

    def run(self):
        """Run the installation process."""
        try:
            # Step 0: Check disk space (minimum 5 GB)
            server_dir = self.paths.get('server_dir', Path("C:/PZServer"))
            has_space, free_gb = check_disk_space(server_dir, required_gb=5.0)
            if not has_space:
                raise RuntimeError(
                    f"Insufficient disk space on target drive! Required: 5.0 GB, Free: {free_gb:.2f} GB."
                )

            # Step 1: Download SteamCMD
            self.progress.emit(5, "Downloading SteamCMD...")
            self.log.emit("Starting SteamCMD download...")

            self.installer.download_steamcmd(
                callback=lambda msg: self.log.emit(msg)
            )

            self.progress.emit(20, "SteamCMD downloaded")
            self.log.emit("SteamCMD download complete")

            # Step 2: Extract SteamCMD
            self.progress.emit(25, "Extracting SteamCMD...")
            self.log.emit("Extracting SteamCMD...")

            self.installer.extract_steamcmd()

            self.progress.emit(30, "SteamCMD extracted")
            self.log.emit("SteamCMD extraction complete")

            # Step 3: Update SteamCMD
            self.progress.emit(35, "Initializing SteamCMD...")
            self.log.emit("Initializing SteamCMD (first run)...")

            self.installer.initialize_steamcmd(
                callback=lambda msg: self.log.emit(msg)
            )

            self.progress.emit(45, "SteamCMD ready")
            self.log.emit("SteamCMD initialization complete")

            # Step 4: Install/Update Project Zomboid Server
            branch_info = f" ({self.beta_branch})" if self.beta_branch else ""
            self.progress.emit(50, f"Installing Project Zomboid Server{branch_info}...")
            self.log.emit(f"Installing Project Zomboid Dedicated Server{branch_info}...")
            self.log.emit("This may take a while depending on your connection...")

            self.installer.install_pz_server(
                beta_branch=self.beta_branch,
                beta_password=self.beta_password,
                callback=lambda msg: self.log.emit(msg),
                progress_callback=lambda p: self.progress.emit(50 + int(p * 0.45), "Downloading server files...")
            )

            self.progress.emit(95, "Installation complete")
            self.log.emit("Project Zomboid Server installed successfully!")

            # Step 5: Create startup scripts
            self.progress.emit(98, "Creating helper scripts...")
            self.installer.create_helper_scripts()

            self.progress.emit(100, "Done!")
            self.log.emit("Installation completed successfully!")

            self.finished.emit()

        except Exception as e:
            logger.exception("Installation failed")
            self.error.emit(str(e))


class ServerInstaller:
    """Handles server installation and updates."""

    def __init__(self, paths: dict):
        self.paths = paths
        self.server_dir = paths['server_dir']
        self.steamcmd_dir = paths['steamcmd_dir']
        self._sanitize_paths()

    def _sanitize_paths(self):
        """Sanitize paths to ensure SteamCMD runs on pure ASCII path."""
        try:
            str(self.steamcmd_dir).encode('ascii')
        except UnicodeEncodeError:
            system_drive = os.environ.get("SystemDrive", "C:")
            self.steamcmd_dir = Path(f"{system_drive}/PZServer/steamcmd")

        try:
            str(self.server_dir).encode('ascii')
        except UnicodeEncodeError:
            system_drive = os.environ.get("SystemDrive", "C:")
            self.server_dir = Path(f"{system_drive}/PZServer")

    def ensure_directories(self):
        """Create necessary directories."""
        self.server_dir.mkdir(parents=True, exist_ok=True)
        self.steamcmd_dir.mkdir(parents=True, exist_ok=True)

    def _get_steamcmd_path(self) -> Path:
        """Get the full path to the SteamCMD executable."""
        return self.steamcmd_dir / get_steamcmd_executable_name()

    def download_steamcmd(self, callback: Optional[Callable[[str], None]] = None):
        """Download SteamCMD archive."""
        self.ensure_directories()

        url = get_steamcmd_url()

        # Determine archive filename from URL
        if url.endswith('.zip'):
            archive_name = "steamcmd.zip"
        else:
            archive_name = "steamcmd.tar.gz"

        archive_path = self.steamcmd_dir / archive_name

        if callback:
            callback(f"Downloading from {url}")

        try:
            import ssl
            ctx = ssl.create_default_context()

            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )

            with urllib.request.urlopen(req, context=ctx) as response, open(archive_path, 'wb') as out_file:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                block_size = 65536

                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out_file.write(buffer)

                    if total_size > 0 and callback:
                        percent = min(100, int(downloaded * 100 / total_size))
                        if downloaded % (block_size * 5) == 0 or percent == 100:
                            callback(f"Downloaded: {downloaded // 1024}KB / {total_size // 1024}KB ({percent}%)")

            if callback:
                callback("Download complete")

        except Exception as e:
            logger.error(f"Failed to download SteamCMD: {e}")
            raise RuntimeError(f"Failed to download SteamCMD: {e}")

    def extract_steamcmd(self):
        """Extract SteamCMD archive (zip on Windows, tar.gz on Unix)."""
        # Try zip first (Windows), then tar.gz (macOS/Linux)
        zip_path = self.steamcmd_dir / "steamcmd.zip"
        tar_path = self.steamcmd_dir / "steamcmd.tar.gz"

        if zip_path.exists():
            archive_path = zip_path
            is_zip = True
        elif tar_path.exists():
            archive_path = tar_path
            is_zip = False
        else:
            raise FileNotFoundError(
                "SteamCMD archive not found. Please download first."
            )

        try:
            if is_zip:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(self.steamcmd_dir)
            else:
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(self.steamcmd_dir)

            # Remove archive after extraction
            archive_path.unlink()

            # On Unix, make steamcmd.sh executable
            if os.name != 'nt':
                steamcmd_sh = self.steamcmd_dir / "steamcmd.sh"
                if steamcmd_sh.exists():
                    steamcmd_sh.chmod(
                        steamcmd_sh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
                    )
                # Also make the linux32/steamcmd executable if it exists
                linux32_cmd = self.steamcmd_dir / "linux32" / "steamcmd"
                if linux32_cmd.exists():
                    linux32_cmd.chmod(
                        linux32_cmd.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
                    )

            logger.info(f"SteamCMD extracted to {self.steamcmd_dir}")

        except Exception as e:
            logger.error(f"Failed to extract SteamCMD: {e}")
            raise RuntimeError(f"Failed to extract SteamCMD: {e}")

    def initialize_steamcmd(self, callback: Optional[Callable[[str], None]] = None):
        """Initialize SteamCMD (first run to update itself)."""
        steamcmd_exe = self._get_steamcmd_path()

        if not steamcmd_exe.exists():
            raise FileNotFoundError(
                f"{steamcmd_exe.name} not found. Please extract first."
            )

        try:
            if callback:
                callback("Running SteamCMD first-time setup...")

            # Build command
            cmd = [str(steamcmd_exe), "+quit"]

            # Platform-specific process flags
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'text': True,
                'cwd': str(self.steamcmd_dir),
            }
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(cmd, **kwargs)

            # Read output
            for line in process.stdout:
                line = line.strip()
                if line and callback:
                    callback(line)

            process.wait()

            if callback:
                callback("SteamCMD initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize SteamCMD: {e}")
            raise RuntimeError(f"Failed to initialize SteamCMD: {e}")

    def install_pz_server(
        self,
        beta_branch: str = "",
        beta_password: str = "",
        callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        """Install or update Project Zomboid Dedicated Server."""
        steamcmd_exe = self._get_steamcmd_path()

        if not steamcmd_exe.exists():
            raise FileNotFoundError(f"{steamcmd_exe.name} not found")

        try:
            # Ensure server directory exists and is valid
            self.server_dir.mkdir(parents=True, exist_ok=True)

            # Convert to absolute path
            server_dir_str = str(self.server_dir.resolve())
            # On Windows, normalize to backslashes
            if os.name == 'nt':
                server_dir_str = server_dir_str.replace('/', '\\')

            branch_clean = beta_branch.strip()
            pwd_clean = beta_password.strip()

            beta_arg = ""
            if branch_clean:
                beta_arg = f"-beta {branch_clean} "
                if pwd_clean:
                    beta_arg += f"-betapassword {pwd_clean} "

            if callback:
                branch_msg = f" [Branch: {branch_clean}]" if branch_clean else " [Build 42 Public]"
                if pwd_clean:
                    branch_msg += " [Password Protected]"
                callback(f"Installing PZ Dedicated Server (App ID: {PZ_APP_ID}){branch_msg}...")
                callback(f"Install directory: {server_dir_str}")

            # Create SteamCMD script file for more reliable execution
            script_path = self.steamcmd_dir / "pz_install.txt"
            script_content = f"""@ShutdownOnFailedCommand 0
@NoPromptForPassword 1
force_install_dir "{server_dir_str}"
login anonymous
app_update {PZ_APP_ID} {beta_arg}validate
quit
"""
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            if callback:
                callback(f"Created install script: {script_path}")

            # Build SteamCMD command using script file
            cmd = [str(steamcmd_exe), "+runscript", str(script_path)]

            if callback:
                callback(f"Running: {steamcmd_exe.name} +runscript pz_install.txt")

            # Platform-specific process flags
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'text': True,
                'cwd': str(self.steamcmd_dir),
            }
            if os.name == 'nt':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(cmd, **kwargs)

            # Track progress
            error_messages = []

            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                if callback:
                    callback(line)

                # Collect error messages
                if "error" in line.lower() or "failed" in line.lower():
                    error_messages.append(line)

                # Try to parse progress from SteamCMD output
                if "progress:" in line.lower() or "%" in line:
                    try:
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                        if match and progress_callback:
                            percent = float(match.group(1))
                            progress_callback(percent / 100.0)
                    except Exception:
                        pass

            process.wait()

            # Handle exit codes
            if process.returncode != 0:
                error_info = self._get_steamcmd_error_info(process.returncode)
                if callback:
                    callback(f"SteamCMD exit code: {process.returncode}")
                    callback(f"Error info: {error_info}")

                # Exit code 7 often means success with warnings, try to continue
                if process.returncode == 7:
                    if callback:
                        callback("Exit code 7: Checking if installation succeeded anyway...")
                elif process.returncode == 8:
                    # Code 8: Usually path or permission issue
                    raise RuntimeError(
                        f"SteamCMD error (code 8): Check that the path '{server_dir_str}' "
                        f"is valid and you have write permissions. "
                        f"Try running with elevated privileges or choose a different folder."
                    )
                else:
                    # For other codes, check if files exist anyway
                    pass

            # Verify installation — check platform-appropriate files
            if self.is_installed():
                if callback:
                    callback("Server installation verified!")
                logger.info("Project Zomboid server installed successfully")
            else:
                # Try alternative installation method
                if callback:
                    callback("Files not found, trying alternative method...")
                self._install_alternative(beta_branch, callback, progress_callback)

        except Exception as e:
            logger.error(f"Failed to install server: {e}")
            raise RuntimeError(f"Failed to install server: {e}")

    def _get_steamcmd_error_info(self, code: int) -> str:
        """Get human-readable error info for SteamCMD exit codes."""
        errors = {
            1: "Generic error",
            2: "No connection to Steam servers",
            3: "Login failed",
            5: "Invalid password",
            6: "Already logged in",
            7: "Success with warnings (usually OK)",
            8: "Invalid install path or no write permission",
            10: "App not found or not available",
        }
        return errors.get(code, f"Unknown error code {code}")

    def _install_alternative(
        self,
        beta_branch: str = "",
        callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        """Alternative installation method with direct commands."""
        steamcmd_exe = self._get_steamcmd_path()
        server_dir_str = str(self.server_dir.resolve())
        if os.name == 'nt':
            server_dir_str = server_dir_str.replace('/', '\\')

        if callback:
            callback("Trying alternative installation method...")

        branch_clean = beta_branch.strip()
        cmd = [
            str(steamcmd_exe),
            "+@ShutdownOnFailedCommand", "0",
            "+@NoPromptForPassword", "1",
            "+force_install_dir", server_dir_str,
            "+login", "anonymous",
        ]
        if branch_clean:
            cmd.extend(["+app_update", PZ_APP_ID, "-beta", branch_clean, "validate"])
        else:
            cmd.extend(["+app_update", PZ_APP_ID, "validate"])
        cmd.append("+quit")

        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'text': True,
            'cwd': str(self.steamcmd_dir),
        }
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(cmd, **kwargs)

        for line in process.stdout:
            line = line.strip()
            if line and callback:
                callback(line)

        process.wait()

        # Final verification
        if not self.is_installed():
            if os.name == 'nt':
                raise RuntimeError(
                    f"Server installation failed. Please try:\n"
                    f"1. Run the app as Administrator\n"
                    f"2. Use a simpler path (e.g., C:\\PZServer)\n"
                    f"3. Check disk space (need ~3GB)\n"
                    f"4. Temporarily disable antivirus"
                )
            else:
                raise RuntimeError(
                    f"Server installation failed. Please try:\n"
                    f"1. Run with sudo: sudo python3 main.py\n"
                    f"2. Check disk space (need ~3GB)\n"
                    f"3. On Linux, install lib32gcc-s1: sudo apt install lib32gcc-s1\n"
                    f"4. Check file permissions on {self.server_dir}"
                )

    def create_helper_scripts(self):
        """Create helper scripts for server management (platform-aware)."""
        if os.name == 'nt':
            self._create_windows_scripts()
        else:
            self._create_unix_scripts()

        logger.info("Helper scripts created")

    def _create_windows_scripts(self):
        """Create helper batch scripts for Windows."""
        # Create a custom start script
        start_script = self.server_dir / "StartServer_Custom.bat"
        start_content = f'''@echo off
title Project Zomboid Server
cd /d "{self.server_dir}"
echo Starting Project Zomboid Server...
echo.
echo Press Ctrl+C to stop the server gracefully
echo.

REM Check for 64-bit or 32-bit
if exist "ProjectZomboid64.exe" (
    ProjectZomboid64.exe -statistic 0 %*
) else if exist "StartServer64.bat" (
    call StartServer64.bat %*
) else (
    echo ERROR: Server executable not found!
    pause
)
'''

        with open(start_script, 'w') as f:
            f.write(start_content)

        # Create an update script
        update_script = self.server_dir / "UpdateServer.bat"
        update_content = f'''@echo off
title Update Project Zomboid Server
cd /d "{self.steamcmd_dir}"
echo Updating Project Zomboid Server...
echo.
steamcmd.exe +force_install_dir "{self.server_dir}" +login anonymous +app_update {PZ_APP_ID} validate +quit
echo.
echo Update complete!
pause
'''

        with open(update_script, 'w') as f:
            f.write(update_content)

    def _create_unix_scripts(self):
        """Create helper shell scripts for macOS/Linux."""
        # Create a custom start script
        start_script = self.server_dir / "start_server_custom.sh"
        start_content = f'''#!/bin/bash
echo "Starting Project Zomboid Server..."
echo "Press Ctrl+C to stop the server gracefully"
echo ""

cd "{self.server_dir}"

if [ -f "./start-server.sh" ]; then
    bash ./start-server.sh "$@"
elif [ -f "./ProjectZomboid64" ]; then
    ./ProjectZomboid64 -statistic 0 "$@"
else
    echo "ERROR: Server executable not found!"
    exit 1
fi
'''

        with open(start_script, 'w') as f:
            f.write(start_content)
        start_script.chmod(start_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        # Create an update script
        update_script = self.server_dir / "update_server.sh"
        update_content = f'''#!/bin/bash
echo "Updating Project Zomboid Server..."
echo ""

cd "{self.steamcmd_dir}"
./steamcmd.sh +force_install_dir "{self.server_dir}" +login anonymous +app_update {PZ_APP_ID} validate +quit

echo ""
echo "Update complete!"
'''

        with open(update_script, 'w') as f:
            f.write(update_content)
        update_script.chmod(update_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _relocate_nested_server_files(self, callback: Optional[Callable[[str], None]] = None):
        """Move files if SteamCMD installed them into nested steamapps/common folder."""
        possible_nested_dirs = [
            self.steamcmd_dir / "steamapps" / "common" / "Project Zomboid Dedicated Server",
            self.server_dir / "steamapps" / "common" / "Project Zomboid Dedicated Server",
            self.steamcmd_dir / "steamapps" / "common" / "project zomboid dedicated server",
            self.server_dir / "steamapps" / "common" / "project zomboid dedicated server",
        ]
        for nested in possible_nested_dirs:
            if nested.exists() and any(nested.iterdir()):
                msg = f"Detected downloaded server in nested directory: {nested}. Moving to {self.server_dir}..."
                logger.info(msg)
                if callback:
                    callback(msg)
                self.server_dir.mkdir(parents=True, exist_ok=True)
                for item in list(nested.iterdir()):
                    dest = self.server_dir / item.name
                    try:
                        if dest.exists():
                            if dest.is_dir():
                                shutil.rmtree(dest, ignore_errors=True)
                            else:
                                dest.unlink(missing_ok=True)
                        shutil.move(str(item), str(self.server_dir))
                    except Exception as e:
                        logger.warning(f"Error moving {item.name}: {e}")
                break

        # Also copy appmanifest if present in steamcmd/steamapps
        manifest_candidates = [
            self.steamcmd_dir / "steamapps" / f"appmanifest_{PZ_APP_ID}.acf",
            self.server_dir.parent / "steamapps" / f"appmanifest_{PZ_APP_ID}.acf",
        ]
        manifest_dst_dir = self.server_dir / "steamapps"
        for m_src in manifest_candidates:
            if m_src.exists():
                try:
                    manifest_dst_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(m_src), str(manifest_dst_dir / m_src.name))
                    break
                except Exception as e:
                    logger.warning(f"Error copying appmanifest: {e}")

    def is_installed(self) -> bool:
        """Check if the server is already installed."""
        candidates = [
            # Windows
            self.server_dir / "ProjectZomboid64.exe",
            self.server_dir / "StartServer64.bat",
            # Unix
            self.server_dir / "start-server.sh",
            self.server_dir / "ProjectZomboid64",
        ]
        if any(c.exists() for c in candidates):
            return True
        self._relocate_nested_server_files()
        return any(c.exists() for c in candidates)

    def get_server_version(self) -> Optional[str]:
        """Try to get the server version from files."""
        version_file = self.server_dir / "version.txt"
        if version_file.exists():
            with open(version_file, 'r') as f:
                return f.read().strip()
        return None

    def install_or_update(
        self,
        beta_branch: str = "",
        beta_password: str = "",
        progress_callback: Optional[Callable[[int, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """Full automated headless pipeline to download SteamCMD if needed, and install/update server."""
        if log_callback:
            log_callback("Checking disk space...")
        has_space, free_gb = check_disk_space(self.server_dir, required_gb=3.0)
        if not has_space:
            raise RuntimeError(f"Insufficient disk space! Free: {free_gb:.2f} GB, Required: 3.0 GB")

        steamcmd_exe = self._get_steamcmd_path()
        if not steamcmd_exe.exists():
            if progress_callback:
                progress_callback(10, "Downloading SteamCMD...")
            self.download_steamcmd(callback=log_callback)
            if progress_callback:
                progress_callback(25, "Extracting SteamCMD...")
            self.extract_steamcmd()
            if progress_callback:
                progress_callback(35, "Initializing SteamCMD...")
            self.initialize_steamcmd(callback=log_callback)

        if progress_callback:
            progress_callback(50, "Installing server files...")
        self.install_pz_server(
            beta_branch=beta_branch,
            beta_password=beta_password,
            callback=log_callback,
            progress_callback=lambda p: progress_callback(50 + int(p * 45), "Downloading server files...") if progress_callback else None
        )
        if progress_callback:
            progress_callback(100, "Installation complete!")

