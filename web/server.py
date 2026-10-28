#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Server & WebSockets Backend for PZ Server Manager Web Dashboard.
Exposes full server control, live console, settings, sandbox, and mod compatibility.
"""

import os
import sys
import json
import asyncio
import logging
import platform
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config_manager import ConfigManager
from core.server_process import ServerProcess, check_ports_in_use
from core.mod_manager import ModManager
from core.server_installer import (
    ServerInstaller, fetch_available_server_branches,
    get_installed_server_buildid, buildid_to_game_version,
    check_server_update_available
)
from core.backup_manager import BackupManager
from core.player_manager import PlayerManager
from core.watchdog_manager import WatchdogManager
from core.network_helper import NetworkHelper
from web.auth import AuthManager

logger = logging.getLogger("pz_web")

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    _base_dir = Path(sys._MEIPASS)
    STATIC_DIR = _base_dir / "web" / "static" if (_base_dir / "web" / "static").exists() else _base_dir / "static"
else:
    STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(
    paths: Dict[str, Path],
    auth_manager: Optional[AuthManager] = None,
    server_process: Optional[ServerProcess] = None,
    config_manager: Optional[ConfigManager] = None,
    mod_manager: Optional[ModManager] = None,
    installer: Optional[ServerInstaller] = None,
    player_manager: Optional[PlayerManager] = None,
) -> FastAPI:
    """Create and configure the FastAPI web application."""
    limiter = Limiter(key_func=get_remote_address)
    app = FastAPI(title="PZ Server Manager Web", version="1.2.1")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?://.*", # Allow LAN and localhost
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if auth_manager is None:
        auth_manager = AuthManager()

    if config_manager is None:
        config_manager = ConfigManager(paths)
    if server_process is None:
        server_process = ServerProcess(paths)
    if mod_manager is None:
        mod_manager = ModManager(paths)
    if installer is None:
        installer = ServerInstaller(paths)
    if player_manager is None:
        player_manager = PlayerManager(paths)

    watchdog_enabled = [True]
    current_srv_name = ["servertest"]
    current_srv_ram = [6]

    def on_proc_exit(code: int):
        if watchdog_enabled[0] and code != 0 and not server_process.is_running:
            logger.warning(f"Watchdog: Server exited unexpectedly (code {code}), restarting in 5s...")
            add_console_line(f"🛡️ [Watchdog]: Обнаружен краш сервера (код {code}). Авто-перезапуск через 5 сек...")
            def do_restart():
                if watchdog_enabled[0] and not server_process.is_running:
                    server_process.start_server(name=current_srv_name[0], ram_gb=current_srv_ram[0])
            threading.Timer(5.0, do_restart).start()

    if hasattr(server_process, 'process_exited'):
        try:
            server_process.process_exited.connect(on_proc_exit)
        except Exception:
            pass

    server_process.output_received.connect(lambda text: player_manager.parse_console_line(text))
    server_process.server_stopped.connect(lambda: player_manager.clear_online_players())

    # ── Console Log Buffer ──────────────────────────────────────────
    console_history: List[str] = []
    MAX_HISTORY = 1000

    def add_console_line(line: str):
        ts = datetime.now().strftime('%H:%M:%S')
        entry = f"[{ts}] {line}"
        console_history.append(entry)
        if len(console_history) > MAX_HISTORY:
            console_history.pop(0)

    # Connect server process signals to web log buffer
    server_process.output_received.connect(lambda text: add_console_line(text))
    server_process.error_received.connect(lambda text: add_console_line(f"ERROR: {text}"))

    # ── Active WebSockets Manager ───────────────────────────────────
    class ConnectionManager:
        def __init__(self):
            self.active_connections: List[WebSocket] = []

        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)

        def disconnect(self, websocket: WebSocket):
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

        async def broadcast(self, data: dict):
            for conn in list(self.active_connections):
                try:
                    await conn.send_json(data)
                except Exception:
                    self.disconnect(conn)

    ws_manager = ConnectionManager()

    # Hook server output directly to active WebSockets via event loop
    loop_holder = {"loop": None}

    def on_live_output(text: str):
        loop = loop_holder.get("loop")
        if loop and ws_manager.active_connections:
            ts = datetime.now().strftime('%H:%M:%S')
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast({"type": "console", "line": f"[{ts}] {text}"}),
                loop
            )

    server_process.output_received.connect(on_live_output)
    server_process.error_received.connect(lambda err: on_live_output(f"ERROR: {err}"))

    # ── Installation Worker State ───────────────────────────────────
    install_state = {
        "running": False,
        "progress": 0,
        "message": "Ready",
        "logs": []
    }

    # ── Auth Dependency ─────────────────────────────────────────────
    def get_token(
        authorization: Optional[str] = Header(None),
        token: Optional[str] = Query(None)
    ) -> str:
        t = token
        if not t and authorization:
            if authorization.startswith("Bearer "):
                t = authorization[7:]
            else:
                t = authorization
        if not auth_manager.validate_session(t):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session token"
            )
        return t

    # ── System Metrics Helper ───────────────────────────────────────
    def get_system_metrics() -> dict:
        total_gb, used_gb, pct = 0.0, 0.0, 0
        if os.name == 'nt':
            try:
                import ctypes
                from ctypes import wintypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', wintypes.DWORD),
                        ('dwMemoryLoad', wintypes.DWORD),
                        ('ullTotalPhys', ctypes.c_uint64),
                        ('ullAvailPhys', ctypes.c_uint64),
                        ('ullTotalPageFile', ctypes.c_uint64),
                        ('ullAvailPageFile', ctypes.c_uint64),
                        ('ullTotalVirtual', ctypes.c_uint64),
                        ('ullAvailVirtual', ctypes.c_uint64),
                        ('sullAvailExtendedVirtual', ctypes.c_uint64),
                    ]
                mem = MEMORYSTATUSEX()
                mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                    used_gb = (mem.ullTotalPhys - mem.ullAvailPhys) / (1024 ** 3)
                    total_gb = mem.ullTotalPhys / (1024 ** 3)
                    pct = int(mem.dwMemoryLoad)
            except Exception:
                pass
        else:
            try:
                meminfo = {}
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        p = line.split(':')
                        if len(p) == 2:
                            meminfo[p[0].strip()] = int(p[1].split()[0])
                t_kb = meminfo.get('MemTotal', 0)
                a_kb = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
                u_kb = t_kb - a_kb
                if t_kb > 0:
                    pct = int(u_kb / t_kb * 100)
                    used_gb = u_kb / (1024 * 1024)
                    total_gb = t_kb / (1024 * 1024)
            except Exception:
                pass

        srv_ram_mb = 0
        root_pid = server_process.get_pid() if server_process.is_running() else None
        if root_pid:
            if os.name == 'nt':
                try:
                    import ctypes
                    from ctypes import wintypes
                    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
                        _fields_ = [
                            ('cb', wintypes.DWORD),
                            ('PageFaultCount', wintypes.DWORD),
                            ('PeakWorkingSetSize', ctypes.c_size_t),
                            ('WorkingSetSize', ctypes.c_size_t),
                            ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                            ('QuotaPagedPoolUsage', ctypes.c_size_t),
                            ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                            ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                            ('PagefileUsage', ctypes.c_size_t),
                            ('PeakPagefileUsage', ctypes.c_size_t),
                            ('PrivateUsage', ctypes.c_size_t),
                        ]
                    handle = ctypes.windll.kernel32.OpenProcess(0x0410, False, root_pid)
                    if handle:
                        c = PROCESS_MEMORY_COUNTERS_EX()
                        c.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
                        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(c), c.cb):
                            srv_ram_mb = c.WorkingSetSize // (1024 * 1024)
                        ctypes.windll.kernel32.CloseHandle(handle)
                except Exception:
                    pass
            else:
                try:
                    with open(f'/proc/{root_pid}/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                srv_ram_mb = int(line.split()[1]) // 1024
                                break
                except Exception:
                    pass

        return {
            "vps_ram_used_gb": round(used_gb, 2),
            "vps_ram_total_gb": round(total_gb, 2),
            "vps_ram_percent": pct,
            "server_ram_mb": srv_ram_mb,
            "server_running": server_process.is_running(),
            "server_pid": root_pid
        }

    # ── Background Metrics Broadcast Task ───────────────────────────
    async def metrics_broadcaster():
        while True:
            await asyncio.sleep(2.0)
            if ws_manager.active_connections:
                metrics = get_system_metrics()
                await ws_manager.broadcast({"type": "metrics", "data": metrics})

    @app.on_event("startup")
    async def on_startup():
        loop_holder["loop"] = asyncio.get_event_loop()
        asyncio.create_task(metrics_broadcaster())

    # ── Models ──────────────────────────────────────────────────────
    class LoginReq(BaseModel):
        password: str

    class StartReq(BaseModel):
        server_name: Optional[str] = "servertest"
        ram_gb: Optional[int] = 6

    class CommandReq(BaseModel):
        command: str

    class QuickActionReq(BaseModel):
        action: str
        extra: Optional[str] = ""

    class ModReq(BaseModel):
        id_or_url: str

    class InstallReq(BaseModel):
        branch: Optional[str] = ""
        password: Optional[str] = ""

    # ── REST API Endpoints ──────────────────────────────────────────

    @app.post("/api/login")
    @limiter.limit("5/minute")
    def api_login(request: Request, req: LoginReq):
        if auth_manager.verify_password(req.password):
            token = auth_manager.create_session()
            return {"success": True, "token": token}
        raise HTTPException(status_code=400, detail="Invalid password")

    @app.post("/api/logout")
    def api_logout(token: str = Depends(get_token)):
        auth_manager.revoke_session(token)
        return {"success": True}

    @app.get("/api/status")
    def api_status(token: str = Depends(get_token)):
        p = paths['server_dir']
        is_installed = any(
            (p / n).exists() for n in [
                'ProjectZomboid64.exe', 'StartServer64.bat',
                'start-server.sh', 'ProjectZomboid64'
            ]
        )
        target_version = 42
        try:
            bid = get_installed_server_buildid(p)
            if bid:
                v = buildid_to_game_version(bid)
                if v.startswith("41"):
                    target_version = 41
        except Exception:
            pass

        return {
            "installed": is_installed,
            "running": server_process.is_running(),
            "target_version": target_version,
            "public_ip": NetworkHelper.get_local_ip(),
            "metrics": get_system_metrics()
        }

    @app.post("/api/server/start")
    def api_server_start(req: StartReq, token: str = Depends(get_token)):
        if server_process.is_running():
            return {"success": False, "message": "Server is already running."}

        name = req.server_name.strip() or "servertest"
        # Pre-launch auto backup
        try:
            bm = BackupManager(paths, server_name=name)
            bm.create_backup(tag="launch")
            add_console_line(f"📦 Pre-launch auto-backup created for world '{name}'")
        except Exception as e:
            logger.warning(f"Backup error: {e}")

        try:
            server_process.start(name, ram_gb=req.ram_gb)
            add_console_line(f"Starting server '{name}' with {req.ram_gb} GB RAM...")
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @app.post("/api/server/stop")
    def api_server_stop(token: str = Depends(get_token)):
        if not server_process.is_running():
            return {"success": False, "message": "Server is not running."}
        server_process.stop()
        add_console_line("Stopping server...")
        return {"success": True}

    @app.post("/api/server/restart")
    def api_server_restart(token: str = Depends(get_token)):
        server_process.restart()
        add_console_line("Restarting server...")
        return {"success": True}

    @app.post("/api/server/command")
    def api_server_command(req: CommandReq, token: str = Depends(get_token)):
        cmd = req.command.strip()
        if not cmd:
            return {"success": False, "message": "Empty command"}
        server_process.send_command(cmd)
        add_console_line(f"> {cmd}")
        return {"success": True}

    @app.post("/api/server/quick-action")
    def api_quick_action(req: QuickActionReq, token: str = Depends(get_token)):
        act = req.action.lower()
        if act == "save":
            server_process.send_command("save")
            add_console_line("> [Admin Action]: save")
            return {"success": True, "message": "Save command sent"}
        elif act == "rain":
            cmd = "stoprain" if getattr(server_process, "_rain", False) else "startrain"
            server_process._rain = not getattr(server_process, "_rain", False)
            server_process.send_command(cmd)
            add_console_line(f"> [Admin Action]: {cmd}")
            return {"success": True, "message": f"Rain command: {cmd}"}
        elif act == "chopper":
            server_process.send_command("chopper")
            add_console_line("> [Admin Action]: chopper (Helicopter event triggered)")
            return {"success": True, "message": "Helicopter triggered"}
        elif act == "broadcast":
            msg = req.extra.strip().replace('"', "'")
            server_process.send_command(f'servermsg "{msg}"')
            add_console_line(f'> [Admin Announcement]: servermsg "{msg}"')
            return {"success": True, "message": f"Broadcast sent: {msg}"}
        elif act == "gunshot":
            server_process.send_command("gunshot")
            add_console_line("> [Admin Action]: gunshot (Ambient gunshot event)")
            return {"success": True, "message": "Gunshot event triggered"}
        return {"success": False, "message": "Unknown action"}

    # ── Live Player Dashboard & Watchdog ────────────────────────────

    class PlayerActionReq(BaseModel):
        action: str  # kick, ban, teleport, admin, whitelist_add, whitelist_remove, refresh
        player: Optional[str] = ""
        target: Optional[str] = ""
        reason: Optional[str] = "Action by Administrator"
        level: Optional[str] = "admin"

    @app.get("/api/players")
    def api_get_players(token: str = Depends(get_token)):
        online = player_manager.get_online_players()
        return {
            "players": online,
            "count": len(online)
        }

    @app.post("/api/players/action")
    def api_player_action(req: PlayerActionReq, token: str = Depends(get_token)):
        act = req.action.lower()
        if act == "refresh":
            if server_process.is_running:
                server_process.send_command("players")
            return {"success": True, "players": player_manager.get_online_players()}
        elif act == "kick":
            cmd = player_manager.cmd_kick(req.player, req.reason or "Kicked by Administrator")
        elif act == "ban":
            cmd = player_manager.cmd_ban(req.player, req.reason or "Banned by Administrator")
        elif act == "teleport":
            cmd = player_manager.cmd_teleport(req.player, req.target)
        elif act == "admin":
            cmd = player_manager.cmd_set_access(req.player, req.level or "admin")
        elif act == "whitelist_add":
            ok = player_manager.add_to_whitelist(req.player)
            return {"success": ok}
        elif act == "whitelist_remove":
            ok = player_manager.remove_from_whitelist(req.player)
            return {"success": ok}
        else:
            return {"success": False, "message": "Unknown action"}

        if cmd and server_process.is_running:
            server_process.send_command(cmd)
            add_console_line(f"> [Player Action]: {cmd}")
            return {"success": True, "command": cmd}
        elif not server_process.is_running:
            return {"success": False, "message": "Сервер не запущен"}
        return {"success": True}

    @app.get("/api/watchdog")
    def api_get_watchdog(token: str = Depends(get_token)):
        return {"enabled": watchdog_enabled[0]}

    @app.post("/api/watchdog/toggle")
    def api_toggle_watchdog(req: Dict[str, Any], token: str = Depends(get_token)):
        watchdog_enabled[0] = bool(req.get("enabled", True))
        return {"success": True, "enabled": watchdog_enabled[0]}

    # ── Settings & Sandbox ──────────────────────────────────────────

    @app.get("/api/settings")
    def api_get_settings(token: str = Depends(get_token)):
        return config_manager.load_server_ini()

    @app.post("/api/settings")
    def api_save_settings(data: Dict[str, Any], token: str = Depends(get_token)):
        try:
            current = config_manager.load_server_ini()
            current.update(data)
            config_manager.save_server_ini(current)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @app.get("/api/sandbox")
    def api_get_sandbox(token: str = Depends(get_token)):
        return config_manager.load_sandbox_vars()

    @app.get("/api/sandbox/full")
    def api_get_sandbox_full(token: str = Depends(get_token)):
        try:
            sb, meta = config_manager.load_sandbox_vars_full()
            json_meta = {}
            if meta:
                for k, v in meta.items():
                    if isinstance(k, tuple) and len(k) == 2:
                        json_meta[f"{k[0]}.{k[1]}"] = str(v)
            return {"vars": sb, "meta": json_meta}
        except Exception as e:
            return {"vars": config_manager.load_sandbox_vars(), "meta": {}, "error": str(e)}

    @app.post("/api/sandbox")
    def api_save_sandbox(data: Dict[str, Any], token: str = Depends(get_token)):
        try:
            current = config_manager.load_sandbox_vars()
            def deep_merge(target, src):
                for k, v in src.items():
                    if isinstance(v, dict) and isinstance(target.get(k), dict):
                        deep_merge(target[k], v)
                    else:
                        target[k] = v
            deep_merge(current, data)
            config_manager.save_sandbox_vars(current)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── Mods Management with Color Compatibility ───────────────────

    def get_target_build_version() -> int:
        try:
            bid = get_installed_server_buildid(paths['server_dir'])
            if bid:
                v = buildid_to_game_version(bid)
                if v.startswith("41"):
                    return 41
        except Exception:
            pass
        return 42

    @app.get("/api/mods")
    def api_get_mods(token: str = Depends(get_token)):
        target_version = get_target_build_version()
        is_installed = any((paths['server_dir'] / exe).exists() for exe in ["ProjectZomboid64.exe", "StartServer64.bat", "start-server.sh", "ProjectZomboid64"])
        bid = get_installed_server_buildid(paths['server_dir'])
        installed_version = buildid_to_game_version(bid) if bid else None

        mods_data = []
        for mod in mod_manager.get_mods():
            status_code, reason = mod_manager.check_compatibility(mod, target_build=target_version)
            mods_data.append({
                "workshop_id": mod.get("workshop_id"),
                "name": mod.get("name", "Unknown"),
                "mod_ids": mod.get("mod_ids") or ([mod.get("mod_id")] if mod.get("mod_id") else []),
                "tags": mod.get("tags", []),
                "status": status_code,  # 'compatible', 'incompatible', 'warning'
                "reason": reason
            })
        return {
            "server_installed": is_installed,
            "installed_version": installed_version,
            "target_version": target_version,
            "mods": mods_data
        }

    @app.post("/api/mods/add")
    def api_add_mod(req: ModReq, token: str = Depends(get_token)):
        cid = mod_manager.parse_collection_id(req.id_or_url.strip())
        if not cid:
            return {"success": False, "message": "Invalid Workshop ID or URL"}

        # Check if it is a collection
        col = mod_manager.get_collection_mods(cid)
        if len(col) > 1:
            res = mod_manager.import_collection(cid)
            return {
                "success": True,
                "is_collection": True,
                "message": f"Collection imported: {res['added_count']} new mods added."
            }

        try:
            info = mod_manager.add_mod(cid)
            target_version = get_target_build_version()
            status_code, reason = mod_manager.check_compatibility(info, target_build=target_version)
            return {
                "success": True,
                "mod": info,
                "status": status_code,
                "reason": reason
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    @app.post("/api/mods/remove")
    def api_remove_mod(req: ModReq, token: str = Depends(get_token)):
        mod_manager.remove_mod(req.id_or_url.strip())
        return {"success": True}

    @app.post("/api/mods/clear")
    def api_clear_mods(token: str = Depends(get_token)):
        mod_manager.clear_mods()
        return {"success": True}

    @app.post("/api/mods/check")
    def api_check_mods(token: str = Depends(get_token)):
        target_version = get_target_build_version()
        report = mod_manager.check_all_mods_compatibility(target_build=target_version)
        return {
            "success": True,
            "total": report["total"],
            "compatible": len(report["compatible"]),
            "incompatible": len(report["incompatible"]),
            "warning": len(report["warning"]),
            "target_version": target_version
        }

    @app.post("/api/mods/preset")
    def api_apply_preset(req: QuickActionReq, token: str = Depends(get_token)):
        presets = {
            "vehicles": ["1510950729", "2642246942", "2618213077", "2386577907", "2788520752"],
            "weapons": ["2169435992", "2297098490", "2200145665", "2460154811"],
            "qol": ["2169435992", "2875848298", "2004998206", "2544353492", "2657661246", "2847184718"],
            "hardcore": ["2557792704", "2913137586", "2335368829", "2818577583"]
        }
        pack = presets.get(req.action.lower())
        if not pack:
            return {"success": False, "message": "Unknown preset pack"}

        added = 0
        for wid in pack:
            try:
                mod_manager.add_mod(wid)
                added += 1
            except Exception:
                pass
        return {"success": True, "added": added}

    @app.post("/api/mods/analyze")
    def api_analyze_mods(token: str = Depends(get_token)):
        report = mod_manager.analyze_and_order_mods()
        return {"success": True, "report": report}

    @app.post("/api/mods/save")
    def api_save_mods(token: str = Depends(get_token)):
        try:
            mod_manager.save_to_config()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── Installer & Updates ─────────────────────────────────────────

    @app.get("/api/install/branches")
    def api_branches(token: str = Depends(get_token)):
        return fetch_available_server_branches()

    @app.get("/api/install/status")
    def api_install_status(token: str = Depends(get_token)):
        return {
            "running": install_state["running"],
            "in_progress": install_state["running"],
            "progress": install_state["progress"],
            "message": install_state["message"],
            "logs": install_state["logs"],
            "log": "\n".join(install_state["logs"][-150:])
        }

    @app.post("/api/install/start")
    def api_install_start(req: InstallReq, token: str = Depends(get_token)):
        if install_state["running"]:
            return {"success": False, "message": "Installation already in progress"}

        install_state["running"] = True
        install_state["progress"] = 0
        install_state["message"] = "Starting installation..."
        install_state["logs"] = []

        def worker():
            try:
                branch = req.branch.strip()
                if branch.lower() == 'public':
                    branch = ''
                pwd = (req.password or "").strip()
                installer.install_or_update(
                    beta_branch=branch,
                    beta_password=pwd,
                    progress_callback=lambda v, m: (
                        install_state.update({"progress": v, "message": m})
                    ),
                    log_callback=lambda l: (
                        install_state["logs"].append(l),
                        on_live_output(f"[Installer]: {l}")
                    )
                )
                install_state["progress"] = 100
                install_state["message"] = "Installation Complete!"
            except Exception as e:
                install_state["message"] = f"Failed: {e}"
            finally:
                install_state["running"] = False

        threading.Thread(target=worker, daemon=True).start()
        return {"success": True}

    @app.get("/api/install/check-update")
    def api_check_update(token: str = Depends(get_token)):
        return check_server_update_available(paths['server_dir'])

    # ── Backups ─────────────────────────────────────────────────────

    @app.get("/api/backups")
    def api_get_backups(token: str = Depends(get_token)):
        bm = BackupManager(paths)
        return bm.list_backups()

    class BackupCreateReq(BaseModel):
        tag: Optional[str] = "manual"

    @app.post("/api/backups/create")
    def api_create_backup(req: Optional[BackupCreateReq] = None, token: str = Depends(get_token)):
        try:
            bm = BackupManager(paths)
            tag = req.tag if (req and req.tag) else "manual"
            b_path = bm.create_backup(tag=tag)
            return {"success": True, "file": Path(b_path).name}
        except Exception as e:
            return {"success": False, "message": str(e)}

    class BackupRestoreReq(BaseModel):
        filename: str

    @app.post("/api/backups/restore")
    def api_restore_backup(req: BackupRestoreReq, token: str = Depends(get_token)):
        try:
            bm = BackupManager(paths)
            b_file = bm.backup_dir / req.filename
            if not b_file.exists():
                return {"success": False, "message": "Файл резервной копии не найден"}
            bm.restore_backup(b_file)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @app.delete("/api/backups/{filename}")
    def api_delete_backup(filename: str, token: str = Depends(get_token)):
        try:
            bm = BackupManager(paths)
            b_file = bm.backup_dir / filename
            if not b_file.exists():
                return {"success": False, "message": "Файл не найден"}
            bm.delete_backup(b_file)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── WebSocket for Live Console ──────────────────────────────────

    @app.websocket("/ws/console")
    async def websocket_console(websocket: WebSocket, token: Optional[str] = Query(None)):
        if not auth_manager.validate_session(token):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await ws_manager.connect(websocket)

        # Send initial console history
        for line in console_history[-100:]:
            await websocket.send_json({"type": "console", "line": line})

        # Send initial metrics
        await websocket.send_json({"type": "metrics", "data": get_system_metrics()})

        try:
            while True:
                msg = await websocket.receive_json()
                m_type = msg.get("type")
                if m_type == "command":
                    cmd = msg.get("text", "").strip()
                    if cmd:
                        server_process.send_command(cmd)
                        add_console_line(f"> {cmd}")
                        await ws_manager.broadcast({"type": "console", "line": f"> {cmd}"})
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception:
            ws_manager.disconnect(websocket)

    # ── Static UI Mounting ──────────────────────────────────────────
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/")
        def serve_index():
            return FileResponse(STATIC_DIR / "index.html")

    return app
