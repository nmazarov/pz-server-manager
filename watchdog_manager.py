#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watchdog & Automation Module for PZ Server Manager.
Handles crash auto-restart, scheduled restarts, and Discord webhook notifications.
"""

import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, time
from typing import Optional, Callable
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Sends formatted embed notifications to a Discord Webhook."""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url.strip()
        self.enabled = bool(self.webhook_url)

    def set_webhook_url(self, url: str):
        self.webhook_url = url.strip()
        self.enabled = bool(self.webhook_url)

    def send_embed(self, title: str, description: str, color: int = 0x3498DB, fields: list = None) -> bool:
        if not self.enabled or not self.webhook_url:
            return False

        payload = {
            "username": "PZ Server Watchdog",
            "avatar_url": "https://media.steampowered.com/steamcommunity/public/images/apps/108600/e681b9e078ef37fa1be6629ad01ff80e2f5b5b04.ico",
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "fields": fields or [],
                "footer": {"text": "PZ Server Manager"},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }]
        }

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'PZServerManager/2.0'
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.status in (200, 204)
        except Exception as e:
            logger.warning(f"Failed to send Discord webhook: {e}")
            return False

    def notify_server_started(self, server_name: str, ip: str = "", port: str = "16261"):
        fields = []
        if ip:
            fields.append({"name": "Connect IP", "value": f"`{ip}:{port}`", "inline": True})
        self.send_embed(
            "🟢 Server Online",
            f"Server **{server_name}** has started successfully and is ready for players.",
            color=0x2ECC71,
            fields=fields
        )

    def notify_server_stopped(self, server_name: str, reason: str = "Manual stop"):
        self.send_embed(
            "🔴 Server Offline",
            f"Server **{server_name}** has stopped. Reason: *{reason}*",
            color=0xE74C3C
        )

    def notify_server_crashed(self, server_name: str, exit_code: int, restart_attempt: int):
        self.send_embed(
            "⚠️ Server Crash Detected",
            f"Server **{server_name}** exited unexpectedly (Exit Code: `{exit_code}`).\n"
            f"Initiating auto-restart (Attempt #{restart_attempt})...",
            color=0xF1C40F
        )

    def notify_scheduled_restart(self, server_name: str, minutes_left: int):
        self.send_embed(
            "⏰ Scheduled Restart",
            f"Server **{server_name}** will restart in **{minutes_left} minutes** for maintenance.",
            color=0x9B59B6
        )


class WatchdogManager(QObject):
    """
    Supervises server health, automates crash restarts and scheduled restarts.
    """
    log_message = pyqtSignal(str)
    restart_requested = pyqtSignal(str)  # Emits reason
    command_requested = pyqtSignal(str)  # Send command to server console

    def __init__(self, parent=None):
        super().__init__(parent)
        self.auto_restart_on_crash = True
        self.max_crash_retries = 3
        self.crash_retry_delay_sec = 10
        self.current_crash_count = 0
        self.expected_shutdown = False

        # Scheduled restarts
        self.scheduled_restart_enabled = False
        self.scheduled_times = ["04:00"]  # HH:MM list
        self.warn_minutes_before = [15, 5, 1]
        self._sent_warnings = set()

        # Discord
        self.notifier = DiscordNotifier()

        # Check timer (runs every 30 seconds for schedule)
        self._schedule_timer = QTimer(self)
        self._schedule_timer.timeout.connect(self._check_schedule)
        self._schedule_timer.start(30000)

        # Crash recovery timer
        self._restart_timer = QTimer(self)
        self._restart_timer.setSingleShot(True)
        self._restart_timer.timeout.connect(self._trigger_restart)

    def set_config(self, config: dict):
        """Update watchdog settings from dictionary."""
        self.auto_restart_on_crash = config.get("auto_restart_on_crash", True)
        self.max_crash_retries = config.get("max_crash_retries", 3)
        self.crash_retry_delay_sec = config.get("crash_retry_delay_sec", 10)
        self.scheduled_restart_enabled = config.get("scheduled_restart_enabled", False)
        self.scheduled_times = config.get("scheduled_times", ["04:00"])
        self.notifier.set_webhook_url(config.get("discord_webhook", ""))

    def to_dict(self) -> dict:
        return {
            "auto_restart_on_crash": self.auto_restart_on_crash,
            "max_crash_retries": self.max_crash_retries,
            "crash_retry_delay_sec": self.crash_retry_delay_sec,
            "scheduled_restart_enabled": self.scheduled_restart_enabled,
            "scheduled_times": self.scheduled_times,
            "discord_webhook": self.notifier.webhook_url
        }

    def on_server_starting(self):
        self.expected_shutdown = False

    def on_server_started_ok(self, server_name: str, ip: str = "", port: str = "16261"):
        self.current_crash_count = 0
        self.notifier.notify_server_started(server_name, ip, port)
        self.log_message.emit("🛡️ Watchdog: Server is running normally. Crash counter reset.")

    def on_server_manual_stop(self, server_name: str):
        self.expected_shutdown = True
        self._restart_timer.stop()
        self.notifier.notify_server_stopped(server_name, "Manual Administrator Stop")

    def on_server_process_ended(self, exit_code: int, server_name: str):
        if self.expected_shutdown:
            logger.info("Server process ended as expected.")
            return

        # Unexpected crash
        self.current_crash_count += 1
        msg = f"⚠️ Watchdog: Unexpected server termination detected! (Exit code: {exit_code}, Attempt {self.current_crash_count}/{self.max_crash_retries})"
        logger.warning(msg)
        self.log_message.emit(msg)

        if self.auto_restart_on_crash:
            if self.current_crash_count <= self.max_crash_retries:
                self.notifier.notify_server_crashed(server_name, exit_code, self.current_crash_count)
                self.log_message.emit(f"🛡️ Watchdog: Restarting in {self.crash_retry_delay_sec} seconds...")
                self._restart_timer.start(self.crash_retry_delay_sec * 1000)
            else:
                err = f"❌ Watchdog: Max crash retries ({self.max_crash_retries}) reached. Halting auto-restart."
                logger.error(err)
                self.log_message.emit(err)
                self.notifier.send_embed(
                    "❌ Auto-Restart Aborted",
                    f"Server **{server_name}** crashed {self.max_crash_retries} times in a row. Please check logs before restarting.",
                    color=0xC0392B
                )

    def _trigger_restart(self):
        self.log_message.emit("🛡️ Watchdog: Triggering server restart now.")
        self.restart_requested.emit("Crash Recovery")

    def _check_schedule(self):
        if not self.scheduled_restart_enabled or not self.scheduled_times:
            return

        now = datetime.now()
        current_hm = now.strftime("%H:%M")

        for sched_str in self.scheduled_times:
            try:
                target_hour, target_min = map(int, sched_str.strip().split(":"))
            except ValueError:
                continue

            target_dt = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
            diff_sec = (target_dt - now).total_seconds()

            # Handle same-day timing
            if 0 <= diff_sec <= 900:  # Within 15 minutes
                mins_left = int(diff_sec // 60) + 1
                for warn_m in self.warn_minutes_before:
                    key = f"{sched_str}_{warn_m}"
                    if mins_left == warn_m and key not in self._sent_warnings:
                        self._sent_warnings.add(key)
                        warning_msg = f'servermsg "Server scheduled restart in {warn_m} minute(s)!"'
                        self.command_requested.emit(warning_msg)
                        self.log_message.emit(f"⏰ Watchdog: Broadcasted {warn_m} min warning.")
                        self.notifier.notify_scheduled_restart("servertest", warn_m)

            if current_hm == sched_str:
                key = f"{sched_str}_restart_{now.strftime('%Y%m%d')}"
                if key not in self._sent_warnings:
                    self._sent_warnings.add(key)
                    self.command_requested.emit('servermsg "Server restarting NOW for daily maintenance!"')
                    self.command_requested.emit("save")
                    self.log_message.emit("⏰ Watchdog: Executing scheduled daily restart.")
                    QTimer.singleShot(5000, lambda: self.restart_requested.emit("Scheduled Maintenance"))
