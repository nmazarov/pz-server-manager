#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mod Manager Module
Handles adding, removing, and managing Steam Workshop mods.
"""

import json
import logging
import urllib.request
import urllib.parse
import re
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict, field

from core.config_manager import read_lines_safely

logger = logging.getLogger(__name__)


@dataclass
class ModInfo:
    """Information about a mod."""
    workshop_id: str
    name: str = "Unknown Mod"
    description: str = ""
    mod_id: str = ""  # Primary mod ID used in Mods= config
    mod_ids: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    required_workshop_ids: List[str] = field(default_factory=list)
    map_folders: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    time_updated: int = 0
    compatibility: str = ""
    compatibility_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ModInfo':
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


class ModManager:
    """Manages Steam Workshop mods for the server."""
    
    def __init__(self, paths: dict):
        self.paths = paths
        self.server_config_dir = paths.get('server_config_dir')
        self.mods: List[ModInfo] = []
        self._mods_file = Path('data') / 'pz_mods.json'
        if not self._mods_file.exists() and Path('pz_mods.json').exists():
            self._mods_file = Path('pz_mods.json')
        self._server_name = "servertest"
        self._steam_details_cache: Dict[str, dict] = {}

        # Load saved mods
        self._load_mods()
        
    def set_server_name(self, name: str):
        """Set the server name."""
        self._server_name = name
        
    def _get_ini_path(self) -> Path:
        """Get path to server ini file."""
        return self.server_config_dir / f"{self._server_name}.ini"
        
    def _load_mods(self):
        """Load mods from local cache file."""
        if self._mods_file.exists():
            try:
                with open(self._mods_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.mods = [ModInfo.from_dict(m) for m in data]
                    for m in self.mods:
                        if m.workshop_id:
                            self._steam_details_cache[str(m.workshop_id)] = {
                                'name': m.name or f"Mod {m.workshop_id}",
                                'mod_ids': m.mod_ids or ([m.mod_id] if m.mod_id else []),
                                'requires': m.requires or [],
                                'required_workshop_ids': m.required_workshop_ids or [],
                                'map_folders': m.map_folders or [],
                                'description': m.description or '',
                                'tags': m.tags or [],
                                'time_updated': m.time_updated or 0
                            }
                logger.info(f"Loaded {len(self.mods)} mods from cache")
            except Exception as e:
                logger.error(f"Failed to load mods cache: {e}")
                self.mods = []
        else:
            # Try to load from server config
            self._load_from_config()
            
    def _save_mods(self):
        """Save mods to local cache file."""
        try:
            self._mods_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._mods_file, 'w', encoding='utf-8') as f:
                json.dump([m.to_dict() for m in self.mods], f, indent=2)
            logger.info(f"Saved {len(self.mods)} mods to cache")
        except Exception as e:
            logger.error(f"Failed to save mods cache: {e}")
            
    def _load_from_config(self):
        """Load mods from server config file."""
        ini_path = self._get_ini_path()
        
        if not ini_path.exists():
            return
            
        try:
            workshop_items = []
            mod_ids = []
            
            for line in read_lines_safely(ini_path):
                    line = line.strip()
                    if line.startswith('WorkshopItems='):
                        items = line.split('=', 1)[1]
                        workshop_items = [i.strip() for i in items.split(';') if i.strip()]
                    elif line.startswith('Mods='):
                        mods = line.split('=', 1)[1]
                        mod_ids = [m.strip() for m in mods.split(';') if m.strip()]
            
            # Create mod info for each workshop item
            for i, workshop_id in enumerate(workshop_items):
                mod_id = mod_ids[i] if i < len(mod_ids) else ""
                self.mods.append(ModInfo(
                    workshop_id=workshop_id,
                    mod_id=mod_id
                ))
                
            if self.mods:
                self._save_mods()
                
        except Exception as e:
            logger.error(f"Failed to load mods from config: {e}")
            
    def get_mods(self) -> List[dict]:
        """Get list of all mods."""
        return [m.to_dict() for m in self.mods]
        
    def add_mod(self, workshop_id: str, mod_id: str = "") -> dict:
        """Add a mod by Workshop ID, running deep analyzer."""
        for mod in self.mods:
            if mod.workshop_id == workshop_id:
                logger.info(f"Mod {workshop_id} already exists")
                return mod.to_dict()

        mod_info = self.analyze_mod(workshop_id, allow_web_scrape=True)
        if mod_id:
            mod_info.mod_id = mod_id
            if mod_id not in mod_info.mod_ids:
                mod_info.mod_ids.insert(0, mod_id)

        self.mods.append(mod_info)
        self._save_mods()

        logger.info(f"Added and analyzed mod: {workshop_id} - {mod_info.name} (Mod IDs: {mod_info.mod_ids or mod_info.mod_id})")
        return mod_info.to_dict()

    def remove_mod(self, workshop_id: str) -> bool:
        """Remove a mod by Workshop ID."""
        for i, mod in enumerate(self.mods):
            if mod.workshop_id == workshop_id:
                del self.mods[i]
                self._save_mods()
                logger.info(f"Removed mod: {workshop_id}")
                return True
        return False

    def clear_mods(self):
        """Remove all mods."""
        self.mods.clear()
        self._save_mods()
        logger.info("Cleared all mods")

    def _find_local_mod_infos(self, workshop_id: str) -> List[dict]:
        """Scan server workshop folder for mod.info files and map folders (cached)."""
        if not hasattr(self, '_local_mod_info_cache'):
            self._local_mod_info_cache = {}
        wid_str = str(workshop_id)
        if wid_str in self._local_mod_info_cache:
            return self._local_mod_info_cache[wid_str]

        results = []
        server_dir = self.paths.get('server_dir')
        if not server_dir:
            return results

        content_dirs = [
            Path(server_dir) / 'steamapps' / 'workshop' / 'content' / '108600' / str(workshop_id),
            Path(server_dir) / 'workshop' / 'content' / '108600' / str(workshop_id),
        ]

        for w_dir in content_dirs:
            if not w_dir.exists():
                continue
            for mod_info_path in w_dir.glob('**/mod.info'):
                try:
                    data = {
                        'id': '', 'name': '', 'require': [], 'description': '', 'maps': [],
                        'versionmin': '', 'versionmax': '', 'pzversion': '', 'modversion': ''
                    }
                    with open(mod_info_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line:
                                k, _, v = line.partition('=')
                                k = k.strip().lower()
                                v = v.strip()
                                if k == 'id':
                                    data['id'] = v
                                elif k == 'name':
                                    data['name'] = v
                                elif k == 'require':
                                    data['require'] = [r.strip() for r in re.split(r'[,;]', v) if r.strip()]
                                elif k == 'description':
                                    data['description'] = v
                                elif k in ('versionmin', 'versionmax', 'pzversion', 'modversion'):
                                    data[k] = v
                    # Check for maps
                    maps_dir = mod_info_path.parent / 'media' / 'maps'
                    if maps_dir.exists():
                        for m in maps_dir.iterdir():
                            if m.is_dir():
                                data['maps'].append(m.name)
                    if data['id']:
                        results.append(data)
                except Exception as e:
                    logger.warning(f"Error reading {mod_info_path}: {e}")
        self._local_mod_info_cache[wid_str] = results
        return results

    def _fetch_batch_steam_details(self, workshop_ids: List[str]) -> Dict[str, dict]:
        """Fetch details for multiple workshop items in batches via Steam Web API."""
        results = {}
        missing = [wid for wid in workshop_ids if str(wid) not in self._steam_details_cache]

        if missing:
            url_files = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
            for i in range(0, len(missing), 50):
                batch = missing[i:i+50]
                params = {'itemcount': len(batch)}
                for idx, wid in enumerate(batch):
                    params[f'publishedfileids[{idx}]'] = wid
                try:
                    b_data = urllib.parse.urlencode(params).encode('utf-8')
                    b_req = urllib.request.Request(url_files, data=b_data, headers={'User-Agent': 'Valve/Steam'})
                    with urllib.request.urlopen(b_req, timeout=6) as b_resp:
                        b_res = json.loads(b_resp.read().decode('utf-8'))
                        for item in b_res.get('response', {}).get('publishedfiledetails', []):
                            wid_str = str(item.get('publishedfileid'))
                            title = item.get('title') or f"Mod {wid_str}"
                            desc = item.get('description', '')

                            desc_mod_ids = re.findall(r'(?:Mod\s*ID|ModID)\s*[:=]\s*([a-zA-Z0-9_\-]+)', desc, re.IGNORECASE)
                            desc_map_folders = re.findall(r'(?:Map\s*Folder|MapFolder)\s*[:=]\s*([a-zA-Z0-9_\-\s]+)', desc, re.IGNORECASE)
                            desc_reqs = re.findall(r'(?:Requires|Requirement|Dependencies|Dependency)\s*[:=]\s*([a-zA-Z0-9_\-,\s]+)', desc, re.IGNORECASE)

                            parsed_reqs = []
                            for req_str in desc_reqs:
                                for r in re.split(r'[,;\s]+', req_str):
                                    r_clean = r.strip()
                                    if r_clean and r_clean not in parsed_reqs:
                                        parsed_reqs.append(r_clean)

                            tags = [t.get('tag') for t in item.get('tags', []) if t.get('tag')]
                            time_updated = int(item.get('time_updated', 0))

                            info = {
                                'name': title,
                                'mod_ids': desc_mod_ids,
                                'requires': parsed_reqs,
                                'required_workshop_ids': [],
                                'map_folders': [m.strip() for m in desc_map_folders if m.strip()],
                                'description': desc,
                                'tags': tags,
                                'time_updated': time_updated
                            }
                            self._steam_details_cache[wid_str] = info
                except Exception as e:
                    logger.warning(f"Batch Steam API details fetch failed for range {i}-{i+50}: {e}")

        for wid in workshop_ids:
            wid_str = str(wid)
            if wid_str in self._steam_details_cache:
                results[wid_str] = self._steam_details_cache[wid_str]
        return results

    def _fetch_steam_details(self, workshop_id: str, allow_web_scrape: bool = False) -> dict:
        """Fetch title, mod IDs, requirements, tags, and map names from Steam Web API or cache."""
        wid_str = str(workshop_id)
        if wid_str in self._steam_details_cache:
            return self._steam_details_cache[wid_str]

        batch_res = self._fetch_batch_steam_details([wid_str])
        if wid_str in batch_res:
            return batch_res[wid_str]

        # Fallback to single web page scrape ONLY if explicitly requested (e.g. single mod addition)
        info = {
            'name': f"Mod {workshop_id}",
            'mod_ids': [],
            'requires': [],
            'required_workshop_ids': [],
            'map_folders': [],
            'description': '',
            'tags': [],
            'time_updated': 0
        }
        if not allow_web_scrape:
            self._steam_details_cache[wid_str] = info
            return info

        try:
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            with urllib.request.urlopen(request, timeout=4) as response:
                html = response.read().decode('utf-8', errors='ignore')

            title_m = re.search(r'<div class="workshopItemTitle">([^<]+)</div>', html)
            if not title_m:
                title_m = re.search(r'<meta property="og:title" content="Steam Workshop::([^"]+)"', html)
            if title_m:
                info['name'] = title_m.group(1).strip()

            desc_m = re.search(r'<div class="workshopItemDescription"[^>]*>(.*?)</div>', html, re.DOTALL)
            desc_text = desc_m.group(1) if desc_m else html

            mod_id_matches = re.findall(r'(?:Mod\s*ID|ModID)\s*[:=]\s*([a-zA-Z0-9_\-]+)', desc_text, re.IGNORECASE)
            for mid in mod_id_matches:
                mid_clean = mid.strip()
                if mid_clean and mid_clean not in info['mod_ids']:
                    info['mod_ids'].append(mid_clean)

            map_matches = re.findall(r'(?:Map\s*Folder|MapFolder)\s*[:=]\s*([a-zA-Z0-9_\-\s]+)', desc_text, re.IGNORECASE)
            for mp in map_matches:
                mp_clean = mp.strip()
                if mp_clean and mp_clean not in info['map_folders']:
                    info['map_folders'].append(mp_clean)

            req_matches = re.findall(r'workshopItemDetails_requiredItems.*?href="[^"]*id=(\d+)"', html, re.DOTALL)
            if not req_matches:
                req_container = re.search(r'<div class="requiredItemsContainer">(.*?)</div>\s*</div>', html, re.DOTALL)
                if req_container:
                    req_matches = re.findall(r'id=(\d+)', req_container.group(1))

            for rid in req_matches:
                if rid != workshop_id and rid not in info['required_workshop_ids']:
                    info['required_workshop_ids'].append(rid)

        except Exception as e:
            logger.warning(f"Could not fetch steam details for {workshop_id}: {e}")

        self._steam_details_cache[wid_str] = info
        return info

    def analyze_mod(self, workshop_id: str, existing_mod: Optional[ModInfo] = None, allow_web_scrape: bool = False) -> ModInfo:
        """Deep analysis of a mod from local files and Steam Workshop."""
        local_infos = self._find_local_mod_infos(workshop_id)
        steam_info = self._fetch_steam_details(workshop_id, allow_web_scrape=allow_web_scrape)

        name = steam_info['name']
        description = steam_info.get('description', '')
        tags = list(steam_info.get('tags', []))
        time_updated = int(steam_info.get('time_updated', 0))
        mod_ids = list(steam_info['mod_ids'])
        requires = list(steam_info['requires'])
        required_workshop_ids = list(steam_info['required_workshop_ids'])
        map_folders = list(steam_info['map_folders'])

        # Preserve previously known valid information if available
        if existing_mod:
            if existing_mod.name and not existing_mod.name.startswith("Mod ") and (not name or name.startswith("Mod ")):
                name = existing_mod.name
            if not description and existing_mod.description:
                description = existing_mod.description
            if not tags and existing_mod.tags:
                tags = list(existing_mod.tags)
            if not time_updated and existing_mod.time_updated:
                time_updated = existing_mod.time_updated
            for mid in existing_mod.mod_ids:
                if mid and mid not in mod_ids:
                    mod_ids.append(mid)
            if existing_mod.mod_id and existing_mod.mod_id not in mod_ids:
                mod_ids.append(existing_mod.mod_id)
            for mp in existing_mod.map_folders:
                if mp and mp not in map_folders:
                    map_folders.append(mp)

        if local_infos:
            name = local_infos[0].get('name') or name
            for li in local_infos:
                mid = li.get('id')
                if mid and mid not in mod_ids:
                    mod_ids.append(mid)
                for req in li.get('require', []):
                    if req not in requires:
                        requires.append(req)
                for mp in li.get('maps', []):
                    if mp not in map_folders:
                        map_folders.append(mp)

        primary_mod_id = mod_ids[0] if mod_ids else str(workshop_id)

        mod_obj = ModInfo(
            workshop_id=str(workshop_id),
            name=name,
            description=description,
            mod_id=primary_mod_id,
            mod_ids=mod_ids,
            requires=requires,
            required_workshop_ids=required_workshop_ids,
            map_folders=map_folders,
            tags=tags,
            time_updated=time_updated,
        )
        compat_status, note = self.check_compatibility(mod_obj)
        mod_obj.compatibility = compat_status
        mod_obj.compatibility_note = note
        return mod_obj

    def check_compatibility(self, mod_or_dict, target_build: int = 42) -> tuple:
        """
        Check if a mod is compatible with the target server build (42 or 41).
        Returns (status, reason), where status is 'compatible', 'incompatible', or 'warning'.
        """
        if isinstance(mod_or_dict, dict):
            title = mod_or_dict.get('name', '')
            desc = mod_or_dict.get('description', '')
            tags = mod_or_dict.get('tags', [])
            wid = mod_or_dict.get('workshop_id', '')
            t_up = mod_or_dict.get('time_updated', 0)
        else:
            title = getattr(mod_or_dict, 'name', '')
            desc = getattr(mod_or_dict, 'description', '')
            tags = getattr(mod_or_dict, 'tags', [])
            wid = getattr(mod_or_dict, 'workshop_id', '')
            t_up = getattr(mod_or_dict, 'time_updated', 0)

        title_lower = title.lower()
        desc_lower = desc.lower()
        tags_lower = [str(t).lower().strip() for t in tags]

        # Scan local mod.info if available
        local_min_ver = ''
        local_max_ver = ''
        local_pz_ver = ''
        local_infos = self._find_local_mod_infos(wid)
        for li in local_infos:
            if li.get('versionmin'):
                local_min_ver = str(li['versionmin']).strip()
            if li.get('versionmax'):
                local_max_ver = str(li['versionmax']).strip()
            if li.get('pzversion'):
                local_pz_ver = str(li['pzversion']).strip()

        if target_build == 42:
            # 1. Red Flags: Incompatible with Build 42
            if any(term in title_lower for term in [
                '[b41 only]', '(b41 only)', 'b41 only', 'build 41 only',
                '[discontinued]', '[deprecated]', '[outdated b41]'
            ]):
                return 'incompatible', 'Только для Build 41 / Заброшен автором'

            if '[b41]' in title_lower and 'b42' not in title_lower:
                return 'incompatible', 'Помечен автором как Build 41'

            incompat_phrases = [
                'not compatible with build 42',
                'not compatible with b42',
                'does not work on build 42',
                'does not work on b42',
                "doesn't work on b42",
                "doesn't work on build 42",
                'b41 only',
                'only for b41',
                'only works on 41',
                'только для build 41',
                'только для b41',
                'не работает на 42',
                'не совместим с 42',
                'broken on b42',
            ]
            if any(p in desc_lower for p in incompat_phrases):
                return 'incompatible', 'В описании мода указано: не работает на Build 42'

            if local_max_ver and (local_max_ver.startswith('41') or local_max_ver.startswith('40')):
                return 'incompatible', f'mod.info ограничивает версию: {local_max_ver}'

            # If tagged Build 41 and NO Build 42 tag and old update date
            if 'build 41' in tags_lower and 'build 42' not in tags_lower:
                if any(k in title_lower for k in ['b42', 'build 42', '42.21', '42.20', '42.19']):
                    return 'compatible', 'В названии заявлена поддержка Build 42'
                if any(k in desc_lower for k in ['b42 compatible', 'works on b42', 'updated for b42', 'updated for build 42']):
                    return 'compatible', 'В описании подтверждена работа на Build 42'
                if t_up > 0 and t_up < 1731600000:
                    return 'incompatible', 'Старый мод Build 41 (не обновлялся под Build 42)'

            # 2. Green Flags: Compatible with Build 42
            if 'build 42' in tags_lower:
                return 'compatible', 'Официальный тег Build 42 в Steam'

            if any(k in title_lower for k in ['b42', 'build 42', '42.21', '42.20', '42.19', '[b42]']):
                return 'compatible', 'В названии указана совместимость с Build 42'

            compat_phrases = [
                'b42 compatible',
                'works on b42',
                'works on build 42',
                'updated for b42',
                'updated for build 42',
                'b42 ready',
                'build 42 ready',
                'build 42 compatibility',
                'поддержка build 42',
                'работает на build 42',
                'адаптирован под 42',
            ]
            if any(p in desc_lower for p in compat_phrases):
                return 'compatible', 'В описании подтверждена работа на Build 42'

            if local_min_ver and local_min_ver.startswith('42'):
                return 'compatible', f'mod.info требует версию: {local_min_ver}'
            if local_pz_ver and '42' in str(local_pz_ver):
                return 'compatible', 'pzversion=42 в mod.info'

            return 'warning', 'Универсальный или требует проверки (нет явных тегов)'

        else:
            # Target build 41 (Legacy)
            if any(k in title_lower for k in ['[b42 only]', 'b42 only', 'build 42 only']):
                return 'incompatible', 'Предназначен только для Build 42'
            if 'build 42' in tags_lower and 'build 41' not in tags_lower:
                if not any(k in title_lower for k in ['b41', 'build 41']):
                    return 'incompatible', 'Создан только для Build 42'
            if 'build 41' in tags_lower:
                return 'compatible', 'Официальный тег Build 41 в Steam'
            if any(k in title_lower for k in ['b41', 'build 41']):
                return 'compatible', 'В названии указана совместимость с Build 41'

            return 'warning', 'Универсальный или требует проверки'

    def check_all_mods_compatibility(self, target_build: int = 42) -> dict:
        """Batch analyze and check compatibility of all loaded mods against target server version."""
        all_wids = [m.workshop_id for m in self.mods]
        self._fetch_batch_steam_details(all_wids)

        updated_mods = []
        compatible_list = []
        incompatible_list = []
        warning_list = []

        for mod in self.mods:
            analyzed = self.analyze_mod(mod.workshop_id, existing_mod=mod)
            status, reason = self.check_compatibility(analyzed, target_build=target_build)
            analyzed.compatibility = status
            analyzed.compatibility_note = reason
            updated_mods.append(analyzed)

            info = {'mod': analyzed, 'reason': reason}
            if status == 'compatible':
                compatible_list.append(info)
            elif status == 'incompatible':
                incompatible_list.append(info)
            else:
                warning_list.append(info)

        self.mods = updated_mods
        self._save_mods()

        return {
            'total': len(self.mods),
            'target_build': target_build,
            'compatible': compatible_list,
            'incompatible': incompatible_list,
            'warning': warning_list
        }

    def analyze_and_order_mods(self) -> dict:
        """Analyze all configured mods, check dependencies, and calculate optimal load order."""
        # Batch prefetch details via Web API for all mods
        all_wids = [m.workshop_id for m in self.mods]
        self._fetch_batch_steam_details(all_wids)

        updated_mods = []
        for mod in self.mods:
            analyzed = self.analyze_mod(mod.workshop_id, existing_mod=mod)
            updated_mods.append(analyzed)
        self.mods = updated_mods
        self._save_mods()

        installed_wids = {m.workshop_id for m in self.mods}
        all_mod_ids = set()
        for m in self.mods:
            if m.mod_ids:
                all_mod_ids.update(m.mod_ids)
            elif m.mod_id:
                all_mod_ids.add(m.mod_id)

        missing_wids = []
        missing_mids = []
        all_maps = []

        for m in self.mods:
            for r_wid in m.required_workshop_ids:
                if r_wid not in installed_wids:
                    missing_wids.append({'workshop_id': r_wid, 'needed_by': m.name})
            for req in m.requires:
                if req not in all_mod_ids:
                    missing_mids.append({'mod_id': req, 'needed_by': m.name})
            for mp in m.map_folders:
                if mp not in all_maps:
                    all_maps.append(mp)

        # Topological sort for Mod IDs
        # If mod A requires mod B, B must be placed earlier
        ordered_mod_ids = []
        visited = set()

        def visit(mid):
            if mid in visited:
                return
            visited.add(mid)
            for m in self.mods:
                if mid in m.mod_ids or mid == m.mod_id:
                    for req in m.requires:
                        visit(req)
            if mid not in ordered_mod_ids:
                ordered_mod_ids.append(mid)

        for m in self.mods:
            mids = m.mod_ids if m.mod_ids else [m.mod_id or m.workshop_id]
            for mid in mids:
                visit(mid)

        return {
            'total_mods': len(self.mods),
            'missing_workshop_ids': missing_wids,
            'missing_mod_ids': missing_mids,
            'ordered_mod_ids': ordered_mod_ids,
            'map_folders': all_maps,
        }

    def _fetch_mod_name(self, workshop_id: str) -> str:
        """Backward-compatible helper to fetch mod name."""
        return self._fetch_steam_details(workshop_id)['name']

    def save_to_config(self) -> dict:
        """Save mods to server configuration file with automatic load order and map integration."""
        ini_path = self._get_ini_path()

        if not ini_path.exists():
            from core.config_manager import ConfigManager
            cm = ConfigManager(self.paths)
            cm.set_server_name(self._server_name)
            cm.load_server_ini(create_if_missing=True)

        report = self.analyze_and_order_mods()
        ordered_mids = report['ordered_mod_ids']
        if not ordered_mids:
            ordered_mids = [m.mod_id or m.workshop_id for m in self.mods]

        workshop_items = ';'.join(m.workshop_id for m in self.mods)
        mods_str = ';'.join(ordered_mids)

        lines = read_lines_safely(ini_path)

        workshop_found = False
        mods_found = False
        new_lines = []
        maps_to_add = report.get('map_folders', [])

        for line in lines:
            line_str = line.strip()
            if line_str.startswith('WorkshopItems='):
                new_lines.append(f'WorkshopItems={workshop_items}\n')
                workshop_found = True
            elif line_str.startswith('Mods='):
                new_lines.append(f'Mods={mods_str}\n')
                mods_found = True
            elif line_str.startswith('Map=') and maps_to_add:
                current_maps = [m.strip() for m in line_str.split('=', 1)[1].split(';') if m.strip()]
                for mp in reversed(maps_to_add):
                    if mp not in current_maps:
                        current_maps.insert(0, mp)
                new_lines.append(f"Map={';'.join(current_maps)}\n")
            else:
                new_lines.append(line)

        if not workshop_found:
            new_lines.append(f'WorkshopItems={workshop_items}\n')
        if not mods_found:
            new_lines.append(f'Mods={mods_str}\n')

        with open(ini_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        logger.info(f"Saved {len(self.mods)} mods with optimized load order to {ini_path}")
        return report
        
    def import_from_file(self, filepath: str):
        """Import mods from a text file (one workshop ID per line or semicolon-separated)."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Handle both newline and semicolon separation
            ids = re.split(r'[;\n]', content)
            ids = [id.strip() for id in ids if id.strip() and id.strip().isdigit()]
            
            for workshop_id in ids:
                self.add_mod(workshop_id)
                
            logger.info(f"Imported {len(ids)} mods from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import mods: {e}")
            raise
            
    def export_to_file(self, filepath: str):
        """Export mods to a text file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Project Zomboid Mod List\n")
                f.write("# One Workshop ID per line\n\n")
                
                for mod in self.mods:
                    f.write(f"# {mod.name}\n")
                    f.write(f"{mod.workshop_id}\n\n")
                    
            logger.info(f"Exported {len(self.mods)} mods to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export mods: {e}")
            raise
            
    def parse_collection_id(self, input_str: str) -> Optional[str]:
        """Extract numeric collection ID from URL or raw ID string."""
        if not input_str:
            return None
        input_str = input_str.strip()
        m = re.search(r'(?:[?&]id=)?(\d{6,12})', input_str)
        return m.group(1) if m else None

    def get_collection_mods(self, collection_url_or_id: str) -> List[str]:
        """
        Get all Workshop Mod IDs from a Steam Workshop collection via Steam Web API.
        Does not require an API key and avoids HTML 429 rate limits.
        """
        cid = self.parse_collection_id(collection_url_or_id)
        if not cid:
            return []

        # 1. Steam Web API GetCollectionDetails
        try:
            url_coll = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
            data = urllib.parse.urlencode({
                'collectioncount': 1,
                'publishedfileids[0]': cid
            }).encode('utf-8')

            req = urllib.request.Request(url_coll, data=data, headers={'User-Agent': 'Valve/Steam'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = json.loads(resp.read().decode('utf-8'))

            details = res.get('response', {}).get('collectiondetails', [])
            if details and details[0].get('result') == 1:
                children = details[0].get('children', [])
                child_ids = [str(c['publishedfileid']) for c in children if str(c.get('publishedfileid')) != cid]
                if child_ids:
                    logger.info(f"Retrieved {len(child_ids)} mods from collection {cid} via Steam Web API")
                    return child_ids
        except Exception as e:
            logger.warning(f"Steam API GetCollectionDetails failed for {cid}: {e}")

        # 2. Fallback: Parse HTML if API was unreachable
        try:
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={cid}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')

            found_ids = re.findall(r'id=["\']sharedfile_(\d+)["\']', html)
            if not found_ids:
                found_ids = re.findall(r'/filedetails/\?id=(\d+)', html)

            clean_ids = []
            seen = set()
            for fid in found_ids:
                if fid != cid and fid not in seen:
                    seen.add(fid)
                    clean_ids.append(fid)
            logger.info(f"Retrieved {len(clean_ids)} mods from collection {cid} via HTML scraping")
            return clean_ids
        except Exception as e:
            logger.error(f"Fallback collection HTML parse failed: {e}")
            return []

    def import_collection(self, collection_url_or_id: str, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> dict:
        """
        Import all mods from a Steam Workshop collection.
        Batch fetches metadata (titles, mod IDs, tags, requirements) and registers them.
        """
        cid = self.parse_collection_id(collection_url_or_id)
        if not cid:
            raise ValueError(f"Invalid collection URL or ID: {collection_url_or_id}")

        mod_ids = self.get_collection_mods(cid)
        if not mod_ids:
            raise ValueError(f"No mods found in collection {cid} or collection is private/inaccessible.")

        total = len(mod_ids)
        logger.info(f"Importing collection {cid} with {total} mods")

        # Batch fetch details for all mods using GetPublishedFileDetails
        items_map = {}
        url_files = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
        for i in range(0, total, 50):
            batch = mod_ids[i:i+50]
            if progress_callback:
                progress_callback(i, total, f"Fetching details {i}/{total}...")
            params = {'itemcount': len(batch)}
            for idx, wid in enumerate(batch):
                params[f'publishedfileids[{idx}]'] = wid
            try:
                b_data = urllib.parse.urlencode(params).encode('utf-8')
                b_req = urllib.request.Request(url_files, data=b_data, headers={'User-Agent': 'Valve/Steam'})
                with urllib.request.urlopen(b_req, timeout=15) as b_resp:
                    b_res = json.loads(b_resp.read().decode('utf-8'))
                    for item in b_res.get('response', {}).get('publishedfiledetails', []):
                        items_map[str(item.get('publishedfileid'))] = item
            except Exception as e:
                logger.warning(f"Batch details fetch failed for range {i}-{i+50}: {e}")

        existing_wids = {m.workshop_id: m for m in self.mods}
        added_count = 0
        updated_count = 0

        for idx, wid in enumerate(mod_ids):
            if progress_callback:
                progress_callback(idx, total, f"Processing mod {wid} ({idx+1}/{total})...")

            item_data = items_map.get(str(wid), {})
            title = item_data.get('title') or f"Mod {wid}"
            desc = item_data.get('description', '')

            # Extract Mod IDs from description
            desc_mod_ids = re.findall(r'(?:Mod\s*ID|ModID)\s*[:=]\s*([a-zA-Z0-9_\-]+)', desc, re.IGNORECASE)
            desc_map_folders = re.findall(r'(?:Map\s*Folder|MapFolder)\s*[:=]\s*([a-zA-Z0-9_\-\s]+)', desc, re.IGNORECASE)

            # Check local files if present
            local_infos = self._find_local_mod_infos(wid)
            for li in local_infos:
                mid = li.get('id')
                if mid and mid not in desc_mod_ids:
                    desc_mod_ids.append(mid)
                for mp in li.get('maps', []):
                    if mp not in desc_map_folders:
                        desc_map_folders.append(mp)

            primary_mod_id = desc_mod_ids[0] if desc_mod_ids else wid

            if wid in existing_wids:
                mod = existing_wids[wid]
                mod.name = title
                mod.mod_id = primary_mod_id
                mod.mod_ids = desc_mod_ids
                mod.map_folders = [m.strip() for m in desc_map_folders if m.strip()]
                updated_count += 1
            else:
                new_mod = ModInfo(
                    workshop_id=str(wid),
                    name=title,
                    mod_id=primary_mod_id,
                    mod_ids=desc_mod_ids,
                    map_folders=[m.strip() for m in desc_map_folders if m.strip()],
                )
                self.mods.append(new_mod)
                existing_wids[wid] = new_mod
                added_count += 1

        self._save_mods()
        self.analyze_and_order_mods()

        return {
            'collection_id': cid,
            'total_items': total,
            'added_count': added_count,
            'updated_count': updated_count,
        }
            
    def update_mod_names(self):
        """Update names for all mods from Steam."""
        for mod in self.mods:
            if mod.name.startswith("Mod ") or mod.name == "Unknown Mod":
                name = self._fetch_mod_name(mod.workshop_id)
                mod.name = name
        self._save_mods()
        logger.info("Updated mod names")
