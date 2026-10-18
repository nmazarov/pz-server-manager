#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostics & Log Analyzer Module for Project Zomboid Dedicated Server.
Detects runtime Lua/Java exceptions, missing dependencies, map conflicts, and workshop updates.
"""

import os
import re
import json
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class DiagnosticsManager:
    """Analyzes server logs, detects conflicts, and checks mod updates."""

    def __init__(self, paths: dict):
        self.paths = paths
        self.zomboid_dir = paths.get('zomboid_dir', Path.home() / 'Zomboid')

    def analyze_server_logs(self, max_lines: int = 500) -> dict:
        """
        Scan server console log files for errors, Lua exceptions, and common server failures.
        Returns categorized findings with human-readable explanations.
        """
        candidates = [
            self.zomboid_dir / 'server-console.txt',
            self.zomboid_dir / 'coop-console.txt',
            self.zomboid_dir / 'console.txt'
        ]

        target_file = None
        for c in candidates:
            if c.exists() and c.stat().st_size > 0:
                target_file = c
                break

        if not target_file:
            return {
                "log_file": None,
                "errors_found": 0,
                "warnings_found": 0,
                "categories": {},
                "summary": "No log file found yet. Start the server at least once to generate logs."
            }

        findings = {
            "java_memory": [],
            "lua_errors": [],
            "missing_mods": [],
            "port_conflicts": [],
            "general_errors": []
        }

        try:
            with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()[-max_lines:]

            for line in lines:
                line_str = line.strip()

                # 1. Out of memory
                if "OutOfMemoryError" in line_str or "Java heap space" in line_str:
                    findings["java_memory"].append(line_str)

                # 2. Lua exceptions
                elif "stack traceback:" in line_str or "Lua error:" in line_str or "attempt to index" in line_str:
                    findings["lua_errors"].append(line_str)

                # 3. Missing mods or workshop files
                elif "Workshop item" in line_str and ("failed" in line_str or "missing" in line_str):
                    findings["missing_mods"].append(line_str)
                elif "Mod \"" in line_str and "not found" in line_str:
                    findings["missing_mods"].append(line_str)

                # 4. Port conflicts
                elif "Address already in use" in line_str or "BindException" in line_str:
                    findings["port_conflicts"].append(line_str)

                # 5. General ERROR
                elif " ERROR: " in line_str or line_str.startswith("ERROR:"):
                    findings["general_errors"].append(line_str)

            total_errs = sum(len(v) for v in findings.values())

            # Generate smart advice
            advice = []
            if findings["java_memory"]:
                advice.append("⚠️ Server ran out of RAM. Increase 'ServerRAM' in Server Settings (e.g., from 4GB/8GB to 12GB+).")
            if findings["port_conflicts"]:
                advice.append("⚠️ Port conflict detected. Another PZ server or app is using ports 16261/16262. Close conflicting tasks.")
            if findings["missing_mods"]:
                advice.append("⚠️ Missing mod files or failed Steam Workshop downloads detected. Check internet or re-download mods.")
            if findings["lua_errors"]:
                advice.append(f"⚠️ Found {len(findings['lua_errors'])} Lua runtime errors. Some mods may be incompatible with this game build.")

            if not advice:
                advice.append("✅ No critical server crashes or memory errors detected in recent logs.")

            return {
                "log_file": str(target_file.name),
                "total_lines_analyzed": len(lines),
                "errors_found": total_errs,
                "categories": findings,
                "advice": advice
            }

        except Exception as e:
            logger.error(f"Failed to analyze log file {target_file}: {e}")
            return {"error": str(e)}

    def check_map_conflicts(self, mods: list) -> List[dict]:
        """
        Check if multiple installed mods register conflicting map folders.
        """
        conflicts = []
        map_to_mods = {}

        for m in mods:
            m_name = getattr(m, 'name', '') or m.get('name', 'Unknown')
            maps = getattr(m, 'map_folders', []) or m.get('map_folders', [])
            for mp in maps:
                mp_lower = mp.strip().lower()
                if mp_lower not in map_to_mods:
                    map_to_mods[mp_lower] = []
                map_to_mods[mp_lower].append(m_name)

        for map_folder, mod_list in map_to_mods.items():
            if len(mod_list) > 1:
                conflicts.append({
                    "map_folder": map_folder,
                    "conflicting_mods": mod_list,
                    "warning": f"Duplicate map folder '{map_folder}' used by: {', '.join(mod_list)}"
                })

        return conflicts

    def check_workshop_mod_updates(self, workshop_ids: List[str]) -> List[dict]:
        """
        Query Steam Web API to check if any Workshop items have been updated recently.
        """
        updates = []
        if not workshop_ids:
            return updates

        url_files = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
        for i in range(0, len(workshop_ids), 50):
            batch = workshop_ids[i:i+50]
            params = {'itemcount': len(batch)}
            for idx, wid in enumerate(batch):
                params[f'publishedfileids[{idx}]'] = wid
            try:
                b_data = urllib.parse.urlencode(params).encode('utf-8')
                b_req = urllib.request.Request(url_files, data=b_data, headers={'User-Agent': 'Valve/Steam'})
                with urllib.request.urlopen(b_req, timeout=12) as b_resp:
                    b_res = json.loads(b_resp.read().decode('utf-8'))
                    for item in b_res.get('response', {}).get('publishedfiledetails', []):
                        wid = str(item.get('publishedfileid'))
                        title = item.get('title') or f"Mod {wid}"
                        time_updated = item.get('time_updated', 0)
                        updates.append({
                            "workshop_id": wid,
                            "title": title,
                            "time_updated": time_updated
                        })
            except Exception as e:
                logger.warning(f"Failed to check updates for batch {i}: {e}")

        return updates
