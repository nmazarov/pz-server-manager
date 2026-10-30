import os
import sys
import json
import math
import struct
from pathlib import Path

# Category mapping definitions
CATEGORIES = [
    {
        "id": "police",
        "name_ru": "Полиция",
        "name_en": "Police",
        "color": "#3b82f6",
        "icon": "🛡️",
        "keywords": ["policestation", "police", "jail", "prison"]
    },
    {
        "id": "guns",
        "name_ru": "Оружие и охота",
        "name_en": "Guns & Hunting",
        "color": "#f97316",
        "icon": "🎯",
        "keywords": ["gunstore", "hunting", "armory", "shooting", "surplus"]
    },
    {
        "id": "medical",
        "name_ru": "Медицина и аптеки",
        "name_en": "Medical & Pharmacy",
        "color": "#ef4444",
        "icon": "🏥",
        "keywords": ["pharmacy", "hospital", "clinic", "dentist", "morgue", "medical"]
    },
    {
        "id": "fire",
        "name_ru": "Пожарная часть",
        "name_en": "Fire Department",
        "color": "#ea580c",
        "icon": "🚒",
        "keywords": ["firestation", "firedept", "fire"]
    },
    {
        "id": "fuel",
        "name_ru": "Заправка (Топливо)",
        "name_en": "Gas Station",
        "color": "#eab308",
        "icon": "⛽",
        "keywords": ["gasstore", "gasstation", "fossoil", "gas2go"]
    },
    {
        "id": "food",
        "name_ru": "Супермаркет и еда",
        "name_en": "Grocery & Food",
        "color": "#22c55e",
        "icon": "🛒",
        "keywords": ["gigamart", "grocery", "supermarket", "spiffo", "bakery", "produce"]
    },
    {
        "id": "tools",
        "name_ru": "Склады и инструменты",
        "name_en": "Tools & Warehouse",
        "color": "#d97706",
        "icon": "🔨",
        "keywords": ["hardware", "toolstore", "factory", "warehouse"]
    },
    {
        "id": "bank",
        "name_ru": "Банк и сейфы",
        "name_en": "Bank",
        "color": "#eab308",
        "icon": "🏦",
        "keywords": ["bank", "bankstorage"]
    }
]

TOWNS = [
    {"name": "Muldraugh", "x": 11181, "y": 9725},
    {"name": "West Point", "x": 11581, "y": 6916},
    {"name": "Riverside", "x": 6300, "y": 5668},
    {"name": "Rosewood", "x": 8446, "y": 11556},
    {"name": "Louisville", "x": 12800, "y": 2500},
    {"name": "March Ridge", "x": 9921, "y": 12603},
    {"name": "Fallas Lake", "x": 7348, "y": 8371},
    {"name": "Valley Station", "x": 13056, "y": 6031},
    {"name": "Dixie", "x": 11500, "y": 8850},
    {"name": "Ekron", "x": 1020, "y": 9838},
    {"name": "Brandenburg", "x": 2314, "y": 6253},
    {"name": "Echo Creek", "x": 4235, "y": 11069},
    {"name": "Irvington", "x": 2729, "y": 13797}
]

def find_closest_town(x: int, y: int) -> str:
    best_dist = float("inf")
    best_name = "Knox County"
    for t in TOWNS:
        dist = math.hypot(x - t["x"], y - t["y"])
        if dist < best_dist:
            best_dist = dist
            best_name = t["name"]
    return best_name if best_dist < 4000 else "Knox County"

def parse_lotheader(p: Path):
    try:
        data = p.read_bytes()
        if not data.startswith(b"LOTH"):
            return None
        ver, num_tiles = struct.unpack("<II", data[4:12])
        offset = 12
        for _ in range(num_tiles):
            end = data.find(b"\n", offset)
            if end == -1: return None
            offset = end + 1

        blocks_x, blocks_y, min_z, max_z = struct.unpack("<iiii", data[offset:offset+16])
        offset += 16
        num_rooms = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4

        rooms = []
        for _ in range(num_rooms):
            end = data.find(b"\n", offset)
            if end == -1: return None
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

        if offset >= len(data):
            return rooms, []

        num_buildings = struct.unpack("<i", data[offset:offset+4])[0]
        offset += 4

        buildings = []
        for b_idx in range(num_buildings):
            if offset + 4 > len(data): break
            num_b_rooms = struct.unpack("<i", data[offset:offset+4])[0]
            offset += 4
            if offset + num_b_rooms * 4 > len(data): break
            room_indices = struct.unpack(f"<{num_b_rooms}i", data[offset:offset+num_b_rooms*4])
            offset += num_b_rooms * 4
            b_rooms = [rooms[idx] for idx in room_indices if 0 <= idx < len(rooms)]
            buildings.append({
                "id": b_idx,
                "rooms": b_rooms
            })
        return rooms, buildings
    except Exception:
        return None

def build_pois():
    maps_dir = Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media\maps\Muldraugh, KY")
    if not maps_dir.exists():
        print("Muldraugh map not found!")
        return

    pois = []
    seen_coords = set()

    for f in sorted(maps_dir.glob("*.lotheader")):
        # Parse cell x and y
        try:
            parts = f.stem.split("_")
            cx, cy = int(parts[0]), int(parts[1])
        except Exception:
            continue

        res = parse_lotheader(f)
        if not res: continue
        rooms, buildings = res

        # Check each building
        for b in buildings:
            all_room_names = [r["name"].lower() for r in b["rooms"]]
            matched_cat = None
            matched_kw = None
            for cat in CATEGORIES:
                for kw in cat["keywords"]:
                    if any(kw in rname for rname in all_room_names):
                        matched_cat = cat
                        matched_kw = kw
                        break
                if matched_cat:
                    break

            if not matched_cat:
                continue

            # Calculate bounds
            all_rects = []
            for r in b["rooms"]:
                for rx, ry, rw, rh in r["rects"]:
                    wx = cx * 256 + rx
                    wy = cy * 256 + ry
                    all_rects.append((wx, wy, rw, rh))

            if not all_rects:
                continue

            min_x = min(r[0] for r in all_rects)
            min_y = min(r[1] for r in all_rects)
            max_x = max(r[0] + r[2] for r in all_rects)
            max_y = max(r[1] + r[3] for r in all_rects)
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2

            coord_key = (round(center_x, -1), round(center_y, -1))
            if coord_key in seen_coords:
                continue
            seen_coords.add(coord_key)

            town = find_closest_town(center_x, center_y)

            # Build label
            label = f"{matched_cat['name_ru']} ({town})"

            pois.append({
                "id": f"{cx}_{cy}_{b['id']}",
                "category": matched_cat["id"],
                "category_name_ru": matched_cat["name_ru"],
                "category_name_en": matched_cat["name_en"],
                "label": label,
                "town": town,
                "x": center_x,
                "y": center_y,
                "bounds": [min_x, min_y, max_x - min_x, max_y - min_y],
                "color": matched_cat["color"],
                "icon": matched_cat["icon"],
                "room_count": len(b["rooms"])
            })

    out_file = Path("data/map_pois.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(pois, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(pois)} POIs saved to {out_file} ({out_file.stat().st_size} bytes)!")

if __name__ == "__main__":
    build_pois()
