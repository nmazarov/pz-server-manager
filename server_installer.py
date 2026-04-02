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
import shutil
import stat
import platform
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# Constants
PZ_APP_ID = "380870"  # Project Zomboid Dedicated Server


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


class InstallWorker(QThread):
    """Worker thread for installation process."""

    progress = pyqtSignal(int, str)  # Progress value and message
    log = pyqtSignal(str)  # Log message
    finished = pyqtSignal()  # Installation complete
    error = pyqtSignal(str)  # Error message

    def __init__(self, installer: 'ServerInstaller', paths: dict):
        super().__init__()
        self.installer = installer
        self.paths = paths

    def run(self):
        """Run the installation process."""
        try:
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
            self.progress.emit(50, "Installing Project Zomboid Server...")
            self.log.emit("Installing Project Zomboid Dedicated Server...")
            self.log.emit("This may take a while depending on your connection...")

            self.installer.install_pz_server(
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
            # Download with progress
            def reporthook(block_num, block_size, total_size):
                if total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, downloaded * 100 // total_size)
                    if callback and block_num % 10 == 0:
                        callback(f"Downloaded: {downloaded // 1024}KB / {total_size // 1024}KB ({percent}%)")

            urllib.request.urlretrieve(url, archive_path, reporthook)

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

            if callback:
                callback(f"Installing PZ Dedicated Server (App ID: {PZ_APP_ID})...")
                callback(f"Install directory: {server_dir_str}")

            # Create SteamCMD script file for more reliable execution
            script_path = self.steamcmd_dir / "pz_install.txt"
            script_content = f"""@ShutdownOnFailedCommand 0
@NoPromptForPassword 1
force_install_dir "{server_dir_str}"
login anonymous
app_update {PZ_APP_ID} validate
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
                self._install_alternative(callback, progress_callback)

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

        # Use direct command line arguments
        cmd = [
            str(steamcmd_exe),
            "+@ShutdownOnFailedCommand", "0",
            "+@NoPromptForPassword", "1",
            "+force_install_dir", server_dir_str,
            "+login", "anonymous",
            "+app_update", PZ_APP_ID, "-validate",
            "+quit"
        ]

        kwargs = {
            'stdout': subprocess.PIPE,
            'stderr': subprocess.STDOUT,
            'text': True,
            'cwd': str(self.steamcmd_dir),
            'shell': True,  # Try with shell
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
        return any(c.exists() for c in candidates)

    def get_server_version(self) -> Optional[str]:
        """Try to get the server version from files."""
        version_file = self.server_dir / "version.txt"
        if version_file.exists():
            with open(version_file, 'r') as f:
                return f.read().strip()
        return None
