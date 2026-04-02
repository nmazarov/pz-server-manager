#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server Process Module
Handles starting, stopping, and communicating with the game server process.
Supports Windows, macOS, and Linux.
"""

import os
import logging
import subprocess
import signal
import platform
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class OutputReader(QThread):
    """Thread for reading server output asynchronously."""

    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    process_ended = pyqtSignal()

    def __init__(self, process: subprocess.Popen):
        super().__init__()
        self.process = process
        self._running = True

    def run(self):
        """Read output from the process."""
        try:
            while self._running and self.process.poll() is None:
                # Read stdout
                if self.process.stdout:
                    line = self.process.stdout.readline()
                    if line:
                        self.output_received.emit(line.strip())

        except Exception as e:
            logger.error(f"Error reading process output: {e}")
        finally:
            self.process_ended.emit()

    def stop(self):
        """Stop the reader thread."""
        self._running = False


class ServerProcess(QObject):
    """Manages the game server process."""

    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()

    def __init__(self, paths: dict):
        super().__init__()
        self.paths = paths
        self.server_dir = paths['server_dir']
        self.process: Optional[subprocess.Popen] = None
        self.output_reader: Optional[OutputReader] = None
        self._server_name = "servertest"

    def start(self, server_name: str = "servertest"):
        """Start the game server."""
        if self.is_running():
            logger.warning("Server is already running")
            return

        self._server_name = server_name

        # Find the server executable
        server_exe = self._find_server_executable()
        if not server_exe:
            raise FileNotFoundError(
                f"Server executable not found in {self.server_dir}. "
                "Please install the server first."
            )

        logger.info(f"Starting server with executable: {server_exe}")

        try:
            # Build command based on executable type
            if server_exe.suffix == '.bat':
                # Windows batch file
                cmd = [str(server_exe)]
            elif server_exe.suffix == '.sh':
                # Unix shell script
                cmd = ["bash", str(server_exe)]
            else:
                # Direct executable with arguments
                cmd = [
                    str(server_exe),
                    "-servername", server_name,
                    "-statistic", "0"
                ]

            # Set up environment
            env = os.environ.copy()

            # Platform-specific process creation
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'stdin': subprocess.PIPE,
                'text': True,
                'bufsize': 1,
                'cwd': str(self.server_dir),
                'env': env,
            }

            if os.name == 'nt':
                # Windows-specific: STARTUPINFO and creation flags
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_MINIMIZE
                kwargs['startupinfo'] = startupinfo
                kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                # Unix: start in new process group for clean signal handling
                kwargs['preexec_fn'] = os.setsid

            self.process = subprocess.Popen(cmd, **kwargs)

            # Start output reader thread
            self.output_reader = OutputReader(self.process)
            self.output_reader.output_received.connect(self._handle_output)
            self.output_reader.error_received.connect(self._handle_error)
            self.output_reader.process_ended.connect(self._handle_process_ended)
            self.output_reader.start()

            # Emit started signal
            logger.info(f"Server process started with PID: {self.process.pid}")
            self.server_started.emit()

        except Exception as e:
            logger.exception("Failed to start server")
            raise RuntimeError(f"Failed to start server: {e}")

    def stop(self, timeout: int = 30):
        """Stop the game server gracefully."""
        if not self.is_running():
            logger.warning("Server is not running")
            self.server_stopped.emit()
            return

        logger.info("Stopping server...")

        try:
            # Try to send quit command first
            self.send_command("quit")

            # Wait for process to end
            try:
                self.process.wait(timeout=10)
                logger.info("Server stopped gracefully")
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't respond to quit command, forcing termination...")
                self._force_terminate()

        except Exception as e:
            logger.error(f"Error stopping server: {e}")
            self._force_terminate()
        finally:
            self._cleanup()
            self.server_stopped.emit()

    def _force_terminate(self):
        """Force terminate the server process."""
        if self.process:
            try:
                if os.name == 'nt':
                    # On Windows, use taskkill for process tree
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                        capture_output=True
                    )
                else:
                    # On Unix, send SIGTERM to the process group, then SIGKILL
                    try:
                        pgid = os.getpgid(self.process.pid)
                        os.killpg(pgid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            pgid = os.getpgid(self.process.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass

            except Exception as e:
                logger.error(f"Error force terminating: {e}")

    def _cleanup(self):
        """Clean up process resources."""
        if self.output_reader:
            self.output_reader.stop()
            self.output_reader.wait(2000)  # Wait up to 2 seconds
            self.output_reader = None

        self.process = None

    def send_command(self, command: str):
        """Send a command to the server console."""
        if not self.is_running():
            logger.warning("Cannot send command - server not running")
            return

        try:
            if self.process and self.process.stdin:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                logger.info(f"Sent command: {command}")
        except Exception as e:
            logger.error(f"Failed to send command: {e}")

    def is_running(self) -> bool:
        """Check if the server process is running."""
        return self.process is not None and self.process.poll() is None

    def _find_server_executable(self) -> Optional[Path]:
        """Find the server executable (platform-aware)."""
        candidates = []

        if os.name == 'nt':
            # Windows candidates
            candidates = [
                self.server_dir / "StartServer64.bat",
                self.server_dir / "StartServer.bat",
                self.server_dir / "ProjectZomboid64.exe",
                self.server_dir / "ProjectZomboid32.exe",
            ]
        else:
            # Unix candidates (macOS / Linux)
            candidates = [
                self.server_dir / "start-server.sh",
                self.server_dir / "ProjectZomboid64",
                # Fallback: Windows-like names under Wine/Proton won't apply,
                # but check just in case
                self.server_dir / "StartServer64.bat",
            ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def _handle_output(self, line: str):
        """Handle output line from the server."""
        # Filter out empty lines
        if line.strip():
            self.output_received.emit(line)

            # Check for important messages
            if "Server started" in line or "SERVER STARTED" in line:
                logger.info("Server reports as started")
            elif "error" in line.lower():
                self.error_received.emit(line)

    def _handle_error(self, line: str):
        """Handle error output from the server."""
        if line.strip():
            self.error_received.emit(line)

    def _handle_process_ended(self):
        """Handle when the server process ends."""
        logger.info("Server process ended")
        self._cleanup()
        self.server_stopped.emit()

    def get_pid(self) -> Optional[int]:
        """Get the server process ID."""
        if self.process:
            return self.process.pid
        return None

    def get_memory_usage(self) -> Optional[int]:
        """Get the server's memory usage in MB (cross-platform)."""
        if not self.is_running():
            return None

        pid = self.process.pid
        system = platform.system()

        try:
            if system == 'Windows':
                import ctypes
                from ctypes import wintypes

                # Use Windows API to get memory info
                process_handle = ctypes.windll.kernel32.OpenProcess(
                    0x0400 | 0x0010,  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
                    False,
                    pid
                )

                if process_handle:
                    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                        _fields_ = [
                            ("cb", wintypes.DWORD),
                            ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t),
                        ]

                    pmc = PROCESS_MEMORY_COUNTERS()
                    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)

                    if ctypes.windll.psapi.GetProcessMemoryInfo(
                        process_handle,
                        ctypes.byref(pmc),
                        ctypes.sizeof(pmc)
                    ):
                        ctypes.windll.kernel32.CloseHandle(process_handle)
                        return pmc.WorkingSetSize // (1024 * 1024)  # Convert to MB

                    ctypes.windll.kernel32.CloseHandle(process_handle)

            elif system == 'Linux':
                # Read from /proc on Linux
                status_file = Path(f"/proc/{pid}/status")
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                # Value is in kB
                                kb = int(line.split()[1])
                                return kb // 1024  # Convert to MB

            elif system == 'Darwin':
                # Use ps on macOS
                result = subprocess.run(
                    ['ps', '-o', 'rss=', '-p', str(pid)],
                    capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    kb = int(result.stdout.strip())
                    return kb // 1024  # Convert to MB

        except Exception as e:
            logger.debug(f"Could not get memory usage: {e}")

        return None


class ServerMonitor(QObject):
    """Monitors server status and health."""

    status_changed = pyqtSignal(dict)  # Status info dict

    def __init__(self, server_process: ServerProcess):
        super().__init__()
        self.server_process = server_process
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_status)

    def start(self, interval_ms: int = 5000):
        """Start monitoring."""
        self.timer.start(interval_ms)

    def stop(self):
        """Stop monitoring."""
        self.timer.stop()

    def _check_status(self):
        """Check server status."""
        status = {
            'running': self.server_process.is_running(),
            'pid': self.server_process.get_pid(),
            'memory_mb': self.server_process.get_memory_usage(),
        }
        self.status_changed.emit(status)
