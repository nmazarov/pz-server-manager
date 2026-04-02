#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mod Manager Module
Handles adding, removing, and managing Steam Workshop mods.
"""

import json
import logging
import urllib.request
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ModInfo:
    """Information about a mod."""
    workshop_id: str
    name: str = "Unknown Mod"
    description: str = ""
    mod_id: str = ""  # Internal mod ID used in Mods= config
    
    def to_dict(self) -> dict:
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: dict) -> 'ModInfo':
        return cls(**data)


class ModManager:
    """Manages Steam Workshop mods for the server."""
    
    def __init__(self, paths: dict):
        self.paths = paths
        self.server_config_dir = paths['server_config_dir']
        self.mods: List[ModInfo] = []
        self._mods_file = Path('pz_mods.json')
        self._server_name = "servertest"
        
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
            
            with open(ini_path, 'r', encoding='utf-8') as f:
                for line in f:
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
        """Add a mod by Workshop ID."""
        # Check if already exists
        for mod in self.mods:
            if mod.workshop_id == workshop_id:
                logger.info(f"Mod {workshop_id} already exists")
                return mod.to_dict()
        
        # Try to get mod info from Steam
        name = self._fetch_mod_name(workshop_id)
        
        # Create mod info
        mod_info = ModInfo(
            workshop_id=workshop_id,
            name=name,
            mod_id=mod_id or workshop_id  # Use workshop ID as fallback
        )
        
        self.mods.append(mod_info)
        self._save_mods()
        
        logger.info(f"Added mod: {workshop_id} - {name}")
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
        
    def _fetch_mod_name(self, workshop_id: str) -> str:
        """Try to fetch mod name from Steam Workshop."""
        try:
            # Steam Workshop page URL
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
            
            # Create request with browser-like headers
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            # Try to extract title from HTML
            # Look for: <div class="workshopItemTitle">Mod Name</div>
            title_match = re.search(r'<div class="workshopItemTitle">([^<]+)</div>', html)
            if title_match:
                return title_match.group(1).strip()
            
            # Alternative: look for og:title meta tag
            og_match = re.search(r'<meta property="og:title" content="Steam Workshop::([^"]+)"', html)
            if og_match:
                return og_match.group(1).strip()
                
        except Exception as e:
            logger.warning(f"Could not fetch mod name for {workshop_id}: {e}")
            
        return f"Mod {workshop_id}"
        
    def save_to_config(self):
        """Save mods to server configuration file."""
        ini_path = self._get_ini_path()
        
        if not ini_path.exists():
            logger.warning("Server config file not found. Start the server first to create it.")
            raise FileNotFoundError("Server config not found")
        
        # Build workshop items and mods strings
        workshop_items = ';'.join(m.workshop_id for m in self.mods)
        mod_ids = ';'.join(m.mod_id or m.workshop_id for m in self.mods)
        
        # Read current config
        with open(ini_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Update or add WorkshopItems and Mods lines
        workshop_found = False
        mods_found = False
        new_lines = []
        
        for line in lines:
            if line.strip().startswith('WorkshopItems='):
                new_lines.append(f'WorkshopItems={workshop_items}\n')
                workshop_found = True
            elif line.strip().startswith('Mods='):
                new_lines.append(f'Mods={mod_ids}\n')
                mods_found = True
            else:
                new_lines.append(line)
        
        # Add lines if not found
        if not workshop_found:
            new_lines.append(f'WorkshopItems={workshop_items}\n')
        if not mods_found:
            new_lines.append(f'Mods={mod_ids}\n')
        
        # Write back
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        logger.info(f"Saved {len(self.mods)} mods to config")
        
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
            
    def get_collection_mods(self, collection_id: str) -> List[str]:
        """
        Try to get mod IDs from a Steam Workshop collection.
        Note: This is limited without Steam API key.
        """
        try:
            url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'Mozilla/5.0')
            
            with urllib.request.urlopen(request, timeout=15) as response:
                html = response.read().decode('utf-8', errors='ignore')
            
            # Try to find mod IDs in collection page
            # Look for: href="/sharedfiles/filedetails/?id=123456789"
            mod_ids = re.findall(r'href="\?id=(\d+)"', html)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_ids = []
            for id in mod_ids:
                if id not in seen and id != collection_id:
                    seen.add(id)
                    unique_ids.append(id)
                    
            return unique_ids
            
        except Exception as e:
            logger.error(f"Failed to get collection mods: {e}")
            return []
            
    def update_mod_names(self):
        """Update names for all mods from Steam."""
        for mod in self.mods:
            if mod.name.startswith("Mod ") or mod.name == "Unknown Mod":
                name = self._fetch_mod_name(mod.workshop_id)
                mod.name = name
        self._save_mods()
        logger.info("Updated mod names")
