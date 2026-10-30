#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Map Manager for Project Zomboid Server Manager.

Handles discovering and reading Project Zomboid world map tiles from `pyramid.zip`,
reading player locations from `players.db` in SQLite read-only mode,
and coordinating interactive map data (towns, coordinates, teleports).
"""

import os
import sys
import re
import json
import struct
import sqlite3
import zipfile
import logging
import threading
from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Category definitions for POIs and building footprint highlights
MAP_CATEGORIES = [
    {"id": "police", "name_ru": "Полиция", "name_en": "Police", "color": "#3b82f6", "icon": "🛡️", "keywords": ["policestation", "police", "jail", "prison"]},
    {"id": "guns", "name_ru": "Оружие и охота", "name_en": "Guns & Hunting", "color": "#f97316", "icon": "🎯", "keywords": ["gunstore", "hunting", "armory", "shooting", "surplus"]},
    {"id": "medical", "name_ru": "Медицина и аптеки", "name_en": "Medical", "color": "#ef4444", "icon": "🏥", "keywords": ["pharmacy", "hospital", "clinic", "dentist", "morgue", "medical"]},
    {"id": "fire", "name_ru": "Пожарная часть", "name_en": "Fire Dept", "color": "#ea580c", "icon": "🚒", "keywords": ["firestation", "firedept", "fire"]},
    {"id": "fuel", "name_ru": "АЗС и топливо", "name_en": "Gas Station", "color": "#eab308", "icon": "⛽", "keywords": ["gasstore", "gasstation", "fossoil", "gas2go"]},
    {"id": "food", "name_ru": "Супермаркет и еда", "name_en": "Grocery & Food", "color": "#22c55e", "icon": "🛒", "keywords": ["gigamart", "grocery", "supermarket", "spiffo", "bakery", "produce", "restaurant", "bar", "diner"]},
    {"id": "bank", "name_ru": "Банки и сейфы", "name_en": "Bank", "color": "#f59e0b", "icon": "🏦", "keywords": ["bank", "bankstorage"]},
    {"id": "tools", "name_ru": "Склады и инструменты", "name_en": "Tools & Warehouse", "color": "#d97706", "icon": "🔨", "keywords": ["hardware", "toolstore", "factory", "warehouse"]},
    {"id": "mechanics", "name_ru": "Автомастерские", "name_en": "Auto & Mechanics", "color": "#94a3b8", "icon": "🔧", "keywords": ["mechanic", "garage", "autoparts", "storagegarage"]},
    {"id": "books", "name_ru": "Книги и библиотеки", "name_en": "Books & School", "color": "#8b5cf6", "icon": "📚", "keywords": ["bookstore", "library", "school", "classroom"]},
    {"id": "clothing", "name_ru": "Одежда", "name_en": "Clothing", "color": "#ec4899", "icon": "👕", "keywords": ["clothing", "clothes", "apparel", "shoes", "laundry"]},
    {"id": "electronics", "name_ru": "Электроника", "name_en": "Electronics", "color": "#06b6d4", "icon": "💻", "keywords": ["electronics", "computer", "radiostation"]},
    {"id": "church", "name_ru": "Церковь", "name_en": "Church", "color": "#cbd5e1", "icon": "⛪", "keywords": ["church", "chapel"]},
    {"id": "office", "name_ru": "Офисы и учреждения", "name_en": "Office", "color": "#64748b", "icon": "🏢", "keywords": ["office", "post", "townhall", "court"]},
    {"id": "residential", "name_ru": "Жилой дом", "name_en": "Residential", "color": "#475569", "icon": "🏠", "keywords": ["bedroom", "livingroom", "bathroom", "kitchen"]}
]

ROOM_TRANSLATIONS = {
    "gunstore": {"ru": "Оружейный магазин", "en": "Gun Store"},
    "policestation": {"ru": "Полицейский участок", "en": "Police Station"},
    "policeoffice": {"ru": "Офис полиции", "en": "Police Office"},
    "jail": {"ru": "Тюремная камера", "en": "Jail Cell"},
    "prison": {"ru": "Тюрьма", "en": "Prison"},
    "security": {"ru": "Комната охраны", "en": "Security Room"},
    "pharmacy": {"ru": "Аптека", "en": "Pharmacy"},
    "hospital": {"ru": "Больница / Палата", "en": "Hospital Room"},
    "medical": {"ru": "Медицинский кабинет", "en": "Medical Room"},
    "clinic": {"ru": "Клиника", "en": "Clinic"},
    "dentist": {"ru": "Стоматология", "en": "Dentist"},
    "morgue": {"ru": "Морг", "en": "Morgue"},
    "firestation": {"ru": "Пожарная станция", "en": "Fire Station"},
    "firedept": {"ru": "Пожарный департамент", "en": "Fire Dept"},
    "gasstore": {"ru": "Магазин АЗС", "en": "Gas Station Store"},
    "gasstation": {"ru": "Заправочная станция", "en": "Gas Station"},
    "grocery": {"ru": "Продуктовый магазин", "en": "Grocery"},
    "supermarket": {"ru": "Супермаркет", "en": "Supermarket"},
    "gigamart": {"ru": "Гипермаркет Gigamart", "en": "Gigamart"},
    "bakery": {"ru": "Пекарня", "en": "Bakery"},
    "restaurant": {"ru": "Ресторан", "en": "Restaurant"},
    "cafekitchen": {"ru": "Кухня кафе", "en": "Cafe Kitchen"},
    "dining": {"ru": "Обеденный зал", "en": "Dining Room"},
    "spiffo": {"ru": "Ресторан Spiffo's", "en": "Spiffo's Restaurant"},
    "bar": {"ru": "Бар / Паб", "en": "Bar / Pub"},
    "diner": {"ru": "Закусочная", "en": "Diner"},
    "bank": {"ru": "Банковское отделение", "en": "Bank"},
    "bankstorage": {"ru": "Банковское хранилище", "en": "Bank Vault"},
    "warehouse": {"ru": "Склад", "en": "Warehouse"},
    "storage": {"ru": "Кладовая / Склад", "en": "Storage"},
    "hardware": {"ru": "Строительный магазин", "en": "Hardware Store"},
    "toolstore": {"ru": "Магазин инструментов", "en": "Tool Store"},
    "factory": {"ru": "Завод / Фабрика", "en": "Factory"},
    "mechanic": {"ru": "Автомастерская", "en": "Mechanic Shop"},
    "garage": {"ru": "Гараж", "en": "Garage"},
    "storagegarage": {"ru": "Гаражный бокс", "en": "Storage Garage"},
    "bookstore": {"ru": "Книжный магазин", "en": "Bookstore"},
    "library": {"ru": "Библиотека", "en": "Library"},
    "school": {"ru": "Школа / Класс", "en": "School / Classroom"},
    "clothing": {"ru": "Магазин одежды", "en": "Clothing Store"},
    "laundry": {"ru": "Прачечная", "en": "Laundromat"},
    "electronics": {"ru": "Магазин электроники", "en": "Electronics Store"},
    "office": {"ru": "Офис", "en": "Office"},
    "post": {"ru": "Почтовое отделение", "en": "Post Office"},
    "church": {"ru": "Церковь", "en": "Church"},
    "bedroom": {"ru": "Спальня", "en": "Bedroom"},
    "livingroom": {"ru": "Гостиная", "en": "Living Room"},
    "kitchen": {"ru": "Кухня", "en": "Kitchen"},
    "bathroom": {"ru": "Ванная комната", "en": "Bathroom"},
    "hall": {"ru": "Коридор / Холл", "en": "Hallway"},
    "closet": {"ru": "Гардеробная", "en": "Closet"},
    "janitor": {"ru": "Комната уборщика", "en": "Janitor Room"},
    "emptyoutside": {"ru": "Крыльцо / Двор", "en": "Patio / Porch"}
}

# Official Knox County Towns and Key Coordinates (center positions)
DEFAULT_TOWNS = [
    {"name": "Muldraugh", "x": 11181, "y": 9725, "desc": "Центральный промышленный город"},
    {"name": "West Point", "x": 11581, "y": 6916, "desc": "Густонаселенный город у реки"},
    {"name": "Riverside", "x": 6300, "y": 5668, "desc": "Богатый прибрежный курортный город"},
    {"name": "Rosewood", "x": 8446, "y": 11556, "desc": "Тюрьма округа, пожарная часть и полиция"},
    {"name": "Louisville", "x": 12800, "y": 2500, "desc": "Огромный мегаполис за карантинной стеной"},
    {"name": "March Ridge", "x": 9921, "y": 12603, "desc": "Военный городок и спальный район"},
    {"name": "Fallas Lake (Ekron)", "x": 7348, "y": 8371, "desc": "Поселение у озера с церковью и магазинами"},
    {"name": "Valley Station", "x": 13056, "y": 6031, "desc": "Перекресток по дороге в Луисвилл"},
    {"name": "Dixie Trailer Park", "x": 11500, "y": 8850, "desc": "Трейлерный парк между Малдро и Вест-Пойнтом"},
    {"name": "Ekron", "x": 1020, "y": 9838, "desc": "Фермерский регион"},
    {"name": "Brandenburg", "x": 2314, "y": 6253, "desc": "Западное поселение у реки Огайо"},
    {"name": "Echo Creek", "x": 4235, "y": 11069, "desc": "Юго-западный городок"},
    {"name": "Irvington", "x": 2729, "y": 13797, "desc": "Южный пограничный город"}
]


class MapManager:
    """Manages PZ map tiles, player coordinates, and spatial queries with high-performance caching."""

    def __init__(self, paths: Dict[str, Path], server_name: str = "servertest"):
        self.paths = paths
        self.server_name = server_name
        self._lock = threading.Lock()
        self._zip_lock = threading.Lock()
        self._tile_cache: OrderedDict[str, bytes] = OrderedDict()
        self._max_cache_size = 1500

        self.bounds = [0, 0, 19968, 16128]
        self.tile_size = 256
        self.levels = [0, 1, 2, 3, 4]
        self.towns = list(DEFAULT_TOWNS)

        self._zip: Optional[zipfile.ZipFile] = None
        self._available_tiles: set = set()
        self._buildings_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._pois: Optional[List[Dict[str, Any]]] = None

        # Locate POIs data file
        if getattr(sys, "frozen", False):
            base_dir = Path(getattr(sys, "_MEIPASS", Path.cwd()))
        else:
            base_dir = Path(__file__).resolve().parent.parent
        self.pois_file = base_dir / "data" / "map_pois.json"

        self.pyramid_path = self.locate_pyramid()
        self.maps_dir = self.pyramid_path.parent if self.pyramid_path else None
        if self.pyramid_path:
            self._init_pyramid_metadata()
            self._scan_for_additional_towns()

    def __del__(self):
        if self._zip:
            try:
                self._zip.close()
            except Exception:
                pass

    def locate_pyramid(self) -> Optional[Path]:
        """Locates pyramid.zip in server directory, steam directory, or custom paths."""
        candidates: List[Path] = []

        # 1. Server directory media/maps
        server_dir = self.paths.get('server_dir')
        if server_dir:
            candidates.append(Path(server_dir) / 'media' / 'maps' / 'Muldraugh, KY' / 'pyramid.zip')

        # 2. Local game files in Steam (Windows)
        candidates.append(Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media\maps\Muldraugh, KY\pyramid.zip"))
        candidates.append(Path(r"C:\Program Files\Steam\steamapps\common\ProjectZomboid\media\maps\Muldraugh, KY\pyramid.zip"))

        # 3. Steam library folders from libraryfolders.vdf
        steam_roots = [
            Path(r"C:\Program Files (x86)\Steam"),
            Path(r"C:\Program Files\Steam"),
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam"
        ]
        for sroot in steam_roots:
            vdf = sroot / "steamapps" / "libraryfolders.vdf"
            if vdf.exists():
                try:
                    content = vdf.read_text(encoding="utf-8", errors="ignore")
                    for m in re.finditer(r'"path"\s+"([^"]+)"', content):
                        lib_path = Path(m.group(1).replace(r"\\", os.sep).replace("/", os.sep))
                        candidates.append(lib_path / "steamapps" / "common" / "ProjectZomboid" / "media" / "maps" / "Muldraugh, KY" / "pyramid.zip")
                except Exception as e:
                    logger.debug(f"Error parsing libraryfolders.vdf in {sroot}: {e}")

        # 4. Linux Steam paths
        home = Path.home()
        candidates.append(home / ".steam" / "steam" / "steamapps" / "common" / "ProjectZomboid" / "media" / "maps" / "Muldraugh, KY" / "pyramid.zip")
        candidates.append(home / ".local" / "share" / "Steam" / "steamapps" / "common" / "ProjectZomboid" / "media" / "maps" / "Muldraugh, KY" / "pyramid.zip")

        for c in candidates:
            try:
                if c.exists() and c.is_file():
                    logger.info(f"Detected Project Zomboid map pyramid at: {c}")
                    return c
            except Exception:
                continue

        logger.warning("Project Zomboid pyramid.zip not found automatically.")
        return None

    def _init_pyramid_metadata(self) -> None:
        """Reads bounds and available zoom levels from persistent pyramid.zip instance."""
        if not self.pyramid_path:
            return

        try:
            # Keep persistent ZipFile instance open
            self._zip = zipfile.ZipFile(self.pyramid_path, "r")
            namelist = self._zip.namelist()
            self._available_tiles = set(namelist)

            # Read pyramid.txt if present
            if "pyramid.txt" in self._available_tiles:
                txt = self._zip.read("pyramid.txt").decode("utf-8", errors="ignore")
                for line in txt.splitlines():
                    if line.startswith("bounds="):
                        parts = line.split("=")[1].strip().split()
                        if len(parts) >= 4:
                            self.bounds = [int(p) for p in parts[:4]]

            # Find available zoom levels
            levels = set()
            for name in namelist:
                parts = name.split("/")
                if len(parts) > 1 and parts[0].isdigit():
                    levels.add(int(parts[0]))
            if levels:
                self.levels = sorted(list(levels))
        except Exception as e:
            logger.error(f"Failed to read pyramid metadata: {e}")

    def _scan_for_additional_towns(self) -> None:
        """Scans media/maps directory for additional town definitions with zoomX and zoomY."""
        if not self.pyramid_path:
            return

        maps_dir = self.pyramid_path.parent.parent
        if not maps_dir.exists() or not maps_dir.is_dir():
            return

        discovered = {}
        try:
            for folder in maps_dir.iterdir():
                if not folder.is_dir():
                    continue
                info_file = folder / "map.info"
                if not info_file.exists():
                    continue
                content = info_file.read_text(encoding="utf-8", errors="ignore")
                zx_match = re.search(r"^zoomX=(\d+)", content, re.MULTILINE)
                zy_match = re.search(r"^zoomY=(\d+)", content, re.MULTILINE)
                if zx_match and zy_match:
                    name = folder.name.replace(", KY", "").replace("_KY", "").strip()
                    discovered[name] = {
                        "name": name,
                        "x": int(zx_match.group(1)),
                        "y": int(zy_match.group(1)),
                        "desc": f"Официальный сектор {name}"
                    }
        except Exception as e:
            logger.debug(f"Scan for towns error: {e}")

        # Merge discovered towns with defaults, updating coords if discovered
        for d_name, d_data in discovered.items():
            existing = next((t for t in self.towns if t["name"].lower() == d_name.lower()), None)
            if existing:
                existing["x"] = d_data["x"]
                existing["y"] = d_data["y"]
            else:
                self.towns.append(d_data)

    def get_info(self) -> Dict[str, Any]:
        """Returns map bounding box, zoom levels, available towns, categories, and tile status."""
        return {
            "ok": True,
            "hasTiles": self.pyramid_path is not None and self.pyramid_path.exists(),
            "pyramidPath": str(self.pyramid_path) if self.pyramid_path else None,
            "bounds": self.bounds,
            "levels": self.levels,
            "tileSize": self.tile_size,
            "towns": self.towns,
            "categories": MAP_CATEGORIES
        }

    def get_categories(self) -> List[Dict[str, Any]]:
        """Returns the list of map POI and building highlight categories."""
        return list(MAP_CATEGORIES)

    @staticmethod
    def translate_room(room_name: str, lang: str = "ru") -> str:
        """Translates an internal game room name into a human-friendly string."""
        raw = room_name.strip().lower()
        if raw in ROOM_TRANSLATIONS:
            return ROOM_TRANSLATIONS[raw].get(lang, ROOM_TRANSLATIONS[raw].get("ru", room_name))
        # Format snake_case or compound names nicely
        words = re.findall(r"[A-Za-z]+|\d+", raw)
        return " ".join(w.capitalize() for w in words) if words else room_name

    def get_pois(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Returns Points of Interest (POIs) such as police, guns, medical, fire, gas, and groceries.
        Loaded once from cached JSON with O(1) in-memory delivery.
        """
        with self._lock:
            if self._pois is None:
                if self.pois_file.exists():
                    try:
                        self._pois = json.loads(self.pois_file.read_text(encoding="utf-8"))
                    except Exception as e:
                        logger.error(f"Failed to load POIs from {self.pois_file}: {e}")
                        self._pois = []
                else:
                    self._pois = []

            if not category:
                return list(self._pois)
            return [p for p in self._pois if p.get("category") == category]

    def _parse_lotheader_cell(self, cx: int, cy: int) -> List[Dict[str, Any]]:
        """
        Parses a single cell's .lotheader binary file with in-memory caching.
        Extracts all buildings, rooms, levels, and footprint rectangles.
        """
        cell_key = f"{cx}_{cy}"
        with self._lock:
            if cell_key in self._buildings_cache:
                return self._buildings_cache[cell_key]

        buildings: List[Dict[str, Any]] = []
        if not self.maps_dir:
            with self._lock:
                self._buildings_cache[cell_key] = buildings
            return buildings

        lot_file = self.maps_dir / f"{cx}_{cy}.lotheader"
        if not lot_file.exists():
            with self._lock:
                self._buildings_cache[cell_key] = buildings
            return buildings

        try:
            data = lot_file.read_bytes()
            if not data.startswith(b"LOTH"):
                with self._lock:
                    self._buildings_cache[cell_key] = buildings
                return buildings

            ver, num_tiles = struct.unpack("<II", data[4:12])
            offset = 12
            for _ in range(num_tiles):
                end = data.find(b"\n", offset)
                if end == -1:
                    break
                offset = end + 1

            blocks_x, blocks_y, min_z, max_z = struct.unpack("<iiii", data[offset:offset+16])
            offset += 16
            num_rooms = struct.unpack("<I", data[offset:offset+4])[0]
            offset += 4

            rooms = []
            for _ in range(num_rooms):
                end = data.find(b"\n", offset)
                if end == -1:
                    break
                name = data[offset:end].decode("latin1", "ignore").strip()
                offset = end + 1
                layer, num_rects = struct.unpack("<ii", data[offset:offset+8])
                offset += 8
                rects = []
                for _ in range(num_rects):
                    rx, ry, rw, rh = struct.unpack("<iiii", data[offset:offset+16])
                    rects.append((rx, ry, rw, rh))
                    offset += 16
                num_objects = struct.unpack("<i", data[offset:offset+4])[0]
                offset += 4 + num_objects * 12
                rooms.append({"name": name, "layer": layer, "rects": rects})

            if offset < len(data):
                num_buildings = struct.unpack("<i", data[offset:offset+4])[0]
                offset += 4

                for b_idx in range(num_buildings):
                    if offset + 4 > len(data):
                        break
                    num_b_rooms = struct.unpack("<i", data[offset:offset+4])[0]
                    offset += 4
                    if offset + num_b_rooms * 4 > len(data):
                        break
                    room_indices = struct.unpack(f"<{num_b_rooms}i", data[offset:offset+num_b_rooms*4])
                    offset += num_b_rooms * 4

                    b_rooms = [rooms[idx] for idx in room_indices if 0 <= idx < len(rooms)]
                    if not b_rooms:
                        continue

                    # Categorize building
                    all_room_names = [r["name"].lower() for r in b_rooms]
                    matched_cat = None
                    for cat in MAP_CATEGORIES:
                        if cat["id"] == "residential":
                            continue
                        for kw in cat["keywords"]:
                            if any(kw in rname for rname in all_room_names):
                                matched_cat = cat
                                break
                        if matched_cat:
                            break

                    if not matched_cat:
                        matched_cat = next(c for c in MAP_CATEGORIES if c["id"] == "residential")

                    # Compute world coordinates & rects
                    all_rects = []
                    floors_set = set()
                    rooms_by_floor: Dict[str, List[str]] = {}

                    for r in b_rooms:
                        layer = r["layer"]
                        floors_set.add(layer)
                        rname = r["name"]
                        str_layer = str(layer)
                        if str_layer not in rooms_by_floor:
                            rooms_by_floor[str_layer] = []
                        trans_name = self.translate_room(rname)
                        if trans_name not in rooms_by_floor[str_layer]:
                            rooms_by_floor[str_layer].append(trans_name)

                        for rx, ry, rw, rh in r["rects"]:
                            wx = cx * 256 + rx
                            wy = cy * 256 + ry
                            all_rects.append([wx, wy, rw, rh, layer, rname])

                    if not all_rects:
                        continue

                    min_x = min(r[0] for r in all_rects)
                    min_y = min(r[1] for r in all_rects)
                    max_x = max(r[0] + r[2] for r in all_rects)
                    max_y = max(r[1] + r[3] for r in all_rects)
                    center_x = (min_x + max_x) // 2
                    center_y = (min_y + max_y) // 2

                    buildings.append({
                        "id": f"{cx}_{cy}_{b_idx}",
                        "category": matched_cat["id"],
                        "category_name": matched_cat["name_ru"],
                        "category_name_en": matched_cat["name_en"],
                        "color": matched_cat["color"],
                        "icon": matched_cat["icon"],
                        "center": [center_x, center_y],
                        "bounds": [min_x, min_y, max_x - min_x, max_y - min_y],
                        "rects": all_rects,
                        "floors": sorted(list(floors_set)),
                        "rooms_by_floor": rooms_by_floor,
                        "cell": [cx, cy]
                    })

        except Exception as e:
            logger.debug(f"Error parsing lotheader {cx}_{cy}: {e}")

        with self._lock:
            self._buildings_cache[cell_key] = buildings
        return buildings

    def get_buildings_in_bounds(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        floor: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries all building footprints intersecting the viewport bounds [x0, y0, x1, y1].
        Fast on-demand cell streaming with caching.
        """
        min_x, max_x = min(x0, x1), max(x0, x1)
        min_y, max_y = min(y0, y1), max(y0, y1)

        cx0 = max(0, int(min_x // 256))
        cx1 = min(99, int(max_x // 256))
        cy0 = max(0, int(min_y // 256))
        cy1 = min(99, int(max_y // 256))

        # Guard against excessively large queries when zoomed out too far
        if (cx1 - cx0 + 1) * (cy1 - cy0 + 1) > 64:
            return []

        results: List[Dict[str, Any]] = []
        seen_ids = set()

        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                cell_buildings = self._parse_lotheader_cell(cx, cy)
                for b in cell_buildings:
                    if b["id"] in seen_ids:
                        continue
                    if category and b["category"] != category:
                        continue
                    if floor is not None and floor not in b["floors"]:
                        continue

                    bx, by, bw, bh = b["bounds"]
                    # AABB intersection
                    if not (bx + bw < min_x or bx > max_x or by + bh < min_y or by > max_y):
                        seen_ids.add(b["id"])
                        results.append(b)

        return results

    def get_building_at(self, x: float, y: float, floor: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Returns the specific building situated at world coordinate (x, y)."""
        cx = int(x // 256)
        cy = int(y // 256)
        cell_buildings = self._parse_lotheader_cell(cx, cy)
        for b in cell_buildings:
            bx, by, bw, bh = b["bounds"]
            if bx <= x <= bx + bw and by <= y <= by + bh:
                for r in b["rects"]:
                    rx, ry, rw, rh, r_layer, _ = r
                    if floor is not None and r_layer != floor:
                        continue
                    if rx <= x <= rx + rw and ry <= y <= ry + rh:
                        return b
        return None

    def get_tile(self, level: int, x: int, y: int) -> Optional[bytes]:
        """
        Extracts a 256x256 PNG tile from pyramid.zip with persistent handle and fast LRU cache.
        Returns bytes in < 0.1ms if cached or < 2ms if read from archive.
        """
        tile_name = f"{level}/tile{x}x{y}.png"

        # Fast O(1) set membership check (no exception overhead)
        if tile_name not in self._available_tiles:
            return None

        # Check in-memory cache
        with self._lock:
            if tile_name in self._tile_cache:
                self._tile_cache.move_to_end(tile_name)
                return self._tile_cache[tile_name]

        # Read from open ZipFile with lock
        data = None
        with self._zip_lock:
            try:
                if self._zip is None and self.pyramid_path:
                    self._zip = zipfile.ZipFile(self.pyramid_path, "r")
                if self._zip:
                    data = self._zip.read(tile_name)
            except Exception as e:
                logger.debug(f"Failed to read tile {tile_name}: {e}")
                return None

        if data is not None:
            with self._lock:
                if len(self._tile_cache) >= self._max_cache_size:
                    # Pop oldest 100 entries
                    for _ in range(100):
                        if self._tile_cache:
                            self._tile_cache.popitem(last=False)
                self._tile_cache[tile_name] = data
            return data

        return None

    def find_players_db(self) -> Optional[Path]:
        """Finds active server players.db file in Zomboid Saves directory."""
        zomboid_dir = self.paths.get('zomboid_dir', Path.home() / 'Zomboid')
        candidates: List[Path] = []

        # 1. Direct multiplayer save for current server_name
        candidates.append(zomboid_dir / 'Saves' / 'Multiplayer' / self.server_name / 'players.db')

        # 2. Any other multiplayer saves
        mp_dir = zomboid_dir / 'Saves' / 'Multiplayer'
        if mp_dir.exists():
            for p in sorted(mp_dir.glob('*/players.db'), key=lambda x: x.stat().st_mtime, reverse=True):
                candidates.append(p)

        # 3. Sandbox saves
        sandbox_dir = zomboid_dir / 'Saves' / 'Sandbox'
        if sandbox_dir.exists():
            for p in sorted(sandbox_dir.glob('*/players.db'), key=lambda x: x.stat().st_mtime, reverse=True):
                candidates.append(p)

        for c in candidates:
            if c.exists() and c.is_file():
                return c

        return None

    def get_players(self, online_usernames: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Reads players coordinates from players.db in SQLite read-only mode,
        merging with currently online player usernames.
        """
        online_set = set(u.lower() for u in (online_usernames or []))
        players_db = self.find_players_db()

        if not players_db:
            return {
                "ok": True,
                "players": [],
                "count": 0,
                "saved_at": None,
                "message": "Файл players.db еще не создан сервером (мир новый)."
            }

        characters = []
        saved_at = int(players_db.stat().st_mtime * 1000)

        try:
            # Connect in read-only URI mode to avoid locking issues with game server
            uri_path = f"file:{players_db.as_posix()}?mode=ro"
            with sqlite3.connect(uri_path, uri=True, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Check if networkPlayers table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='networkPlayers';")
                if not cursor.fetchone():
                    # Check localPlayers as fallback
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='localPlayers';")
                    table_name = "localPlayers" if cursor.fetchone() else None
                else:
                    table_name = "networkPlayers"

                if table_name:
                    cursor.execute(f"SELECT username, name, steamid, x, y, z, isDead FROM {table_name}")
                    for row in cursor.fetchall():
                        uname = row["username"] or "Unknown"
                        char_name = row["name"] or uname
                        is_dead = bool(row["isDead"])
                        is_online = uname.lower() in online_set

                        characters.append({
                            "username": uname,
                            "character": char_name,
                            "steamid": row["steamid"] or "",
                            "x": round(float(row["x"] or 0), 1),
                            "y": round(float(row["y"] or 0), 1),
                            "z": int(row["z"] or 0),
                            "dead": is_dead,
                            "online": is_online
                        })

        except Exception as e:
            logger.error(f"Error querying {players_db}: {e}")
            return {
                "ok": False,
                "error": str(e),
                "players": [],
                "saved_at": saved_at
            }

        # Also add any online players that haven't been saved to players.db yet
        saved_unames = set(c["username"].lower() for c in characters)
        for on_user in (online_usernames or []):
            if on_user.lower() not in saved_unames:
                characters.append({
                    "username": on_user,
                    "character": on_user,
                    "steamid": "",
                    "x": 10000.0,
                    "y": 9000.0,
                    "z": 0,
                    "dead": False,
                    "online": True
                })

        return {
            "ok": True,
            "players": characters,
            "count": len(characters),
            "saved_at": saved_at,
            "db_path": str(players_db)
        }
