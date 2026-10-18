#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Runner for Project Zomboid Server Manager (VPS Web Dashboard).
Starts the headless FastAPI server with live WebSockets, REST API, and web interface.
"""

import os
import sys
import argparse
import platform
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from web.auth import AuthManager
from web.server import create_app
from network_helper import NetworkHelper


def setup_paths(custom_server_dir: str = None) -> dict:
    """Resolve default Project Zomboid server and configuration paths."""
    system = platform.system()

    if custom_server_dir:
        server_dir = Path(custom_server_dir).resolve()
    else:
        # Check adjacent directory, then default
        if (ROOT_DIR / 'PZServer').exists():
            server_dir = ROOT_DIR / 'PZServer'
        elif (ROOT_DIR / 'server').exists():
            server_dir = ROOT_DIR / 'server'
        elif (ROOT_DIR / 'servertest').exists():
            server_dir = ROOT_DIR / 'servertest'
        elif system == 'Windows':
            server_dir = Path('C:/PZServer')
        else:
            server_dir = Path.home() / 'pzserver'

    if system == 'Windows':
        zomboid_dir = Path.home() / 'Zomboid'
    elif system == 'Darwin':
        zomboid_dir = Path.home() / 'Zomboid'
    else:
        zomboid_dir = Path.home() / 'Zomboid'

    server_config_dir = zomboid_dir / 'Server'
    steamcmd_dir = server_dir / 'steamcmd'

    server_dir.mkdir(parents=True, exist_ok=True)
    server_config_dir.mkdir(parents=True, exist_ok=True)
    steamcmd_dir.mkdir(parents=True, exist_ok=True)

    return {
        'server_dir': server_dir,
        'server_config_dir': server_config_dir,
        'steamcmd_dir': steamcmd_dir,
        'zomboid_dir': zomboid_dir,
        'zomboid_data_dir': zomboid_dir
    }


def main():
    parser = argparse.ArgumentParser(description="PZ Server Manager - VPS Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--password", default=None, help="Set admin password")
    parser.add_argument("--server-dir", default=None, help="Custom server directory path")

    args = parser.parse_args()

    paths = setup_paths(args.server_dir)
    auth_mgr = AuthManager(default_password=args.password)
    if args.password:
        auth_mgr.set_password(args.password)

    app = create_app(paths, auth_manager=auth_mgr)

    local_ip = NetworkHelper.get_local_ip()
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    init_pw = auth_mgr.get_initial_password()

    print("\n" + "=" * 62)
    print("  [PZ] Project Zomboid Server Manager - Web Dashboard (VPS)")
    print("=" * 62)
    print(f"  * Web Dashboard URL:   http://{local_ip}:{args.port}")
    print(f"  * Localhost:           http://127.0.0.1:{args.port}")
    if init_pw:
        print(f"  * Admin Password:      {init_pw}")
        print("    (Saved in web_auth.json - remember or change in web settings)")
    else:
        print("  * Admin Password:      [Existing password from web_auth.json]")
    print(f"  * Server Directory:    {paths['server_dir']}")
    print("=" * 62 + "\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
