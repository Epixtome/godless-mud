import os
import math
import json
from architect_data import SYM_MAP, TERRAIN_ELEVS
from architect_common import get_biome_description, get_direction_text

def run_phase_6_export(grid, width, height, offset_x, offset_y, offset_z, zone_prefix, config):
    """[V8.1 UPGRADE] Biomatic Region Sharding with Fragment Merging."""
    print(f"\n--- Running Phase 6: Optimized Biomatic Sharding ---")
    
    region_map = [["" for _ in range(width)] for _ in range(height)]
    zone_assignments = {} # id -> data
    
    BIOME_GROUPS = {
        "peaks": ["peak", "high_mountain", "mountain"],
        "woodlands": ["forest", "dense_forest", "grass", "scrubland"],
        "fields": ["plains", "meadow"],
        "arid": ["desert", "wasteland"],
        "wetlands": ["swamp", "mangroves", "water", "lake"],
        "infrastructure": ["city", "road", "cobblestone", "bridge", "docks", "shrine", "dirt_road"],
        "coastal": ["beach", "ocean"]
    }
    
    # 1. First Pass: Flood Fill
    for y in range(height):
        for x in range(width):
            if region_map[y][x] != "": continue
            cell = grid[y][x]
            b_type = "wilderness"
            for b_name, b_list in BIOME_GROUPS.items():
                if cell in b_list: b_type = b_name; break
            
            region_id = f"{zone_prefix}{b_type}_{y}_{x}"
            queue = [(x, y)]
            region_map[y][x] = region_id
            
            while queue:
                cx, cy = queue.pop(0)
                for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < width and 0 <= ny < height and region_map[ny][nx] == "":
                        if grid[ny][nx] in BIOME_GROUPS.get(b_type, []):
                            region_map[ny][nx] = region_id
                            queue.append((nx, ny))
            zone_assignments[region_id] = {"rooms_coords": []}

    # 2. Fragment Merging Pass - Merge shards < 30 rooms into neighbor
    for rid in list(zone_assignments.keys()):
        # Count rooms in this rid
        coords = [(x, y) for y in range(height) for x in range(width) if region_map[y][x] == rid]
        if len(coords) < 30:
            # Find a neighbor to merge into
            neighbor_rid = None
            for x, y in coords:
                for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < width and 0 <= ny < height:
                        other_rid = region_map[ny][nx]
                        if other_rid != rid and other_rid != "":
                            neighbor_rid = other_rid; break
                if neighbor_rid: break
            
            if neighbor_rid:
                for x, y in coords: region_map[y][x] = neighbor_rid
                del zone_assignments[rid]

    # 3. Final Room Build
    final_shards = {}
    hubs = [{"id": k_id, "name": k_data["name"], "coords": k_data["center"]} 
            for k_id, k_data in config.get("kingdoms", {}).items()]

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            zid = region_map[y][x]
            if not zid: continue 
            if zid not in final_shards: 
                b_type = zid.split('_')[1] if '_' in zid else "region"
                final_shards[zid] = {
                    "metadata": {
                        "id": zid, 
                        "name": f"{b_type.title()} Zone",
                        "security_level": "low_sec" if b_type != "coastal" else "safe",
                        "grid_logic": True,
                        "target_cr": int(config.get("bias_cr", [[0.5]*width for _ in range(height)])[y][x] * 100)
                    }, 
                    "rooms": []
                }
            
            real_x, real_y, real_z = x + offset_x, y + offset_y, offset_z
            room_id = f"{zid}.{real_x}.{real_y}.{real_z}"
            
            desc_intro = get_biome_description(cell)
            landmark_txt = ""
            
            hub_distances = []
            for h in hubs:
                if h.get("coords"):
                    hx, hy = h["coords"]; dist = math.sqrt((x-hx)**2 + (y-hy)**2)
                    hub_distances.append((h["name"], dist, hx, hy))
            
            if hub_distances:
                hub_distances.sort(key=lambda h: h[1])
                nearest_name, nearest_dist, hx, hy = hub_distances[0]
                
                if nearest_dist < 40:
                    dir_txt = get_direction_text(x, y, hx, hy)
                    prefix = f"\n[ Region: {nearest_name} Hinterlands. ]" if nearest_dist < 10 else f"\n[ Navigation: Scent of {nearest_name} smoke to the {dir_txt}. ]"
                    landmark_txt = prefix
            else:
                nearest_name = "Wilderness"

            elev = TERRAIN_ELEVS.get(cell, 0)
            
            room_data = {
                "id": room_id, "zone_id": zid, "name": f"{cell.replace('_', ' ').title()}", 
                "description": f"{desc_intro}\nAtmosphere: {zid.split('_')[1].upper() if '_' in zid else 'WILD'} area.{landmark_txt}",
                "terrain": cell, "symbol": SYM_MAP.get(cell), "x": real_x, "y": real_y, "z": real_z, 
                "elevation": int(elev), "exits": {}, "tags": [cell, zid, "regional_v8", nearest_name.lower()],
                "monsters": [], "items": [],
                "level": int(config.get("bias_cr", [[0.5]*width for _ in range(height)])[y][x] * 100),
                "spawn_rate": float(config.get("bias_spawn", [[0.5]*width for _ in range(height)])[y][x]),
                "sovereignty": nearest_name
            }
            
            for d_name, (dx, dy) in {"north":(0,-1), "south":(0,1), "east":(1,0), "west":(-1,0)}.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    n_zone = region_map[ny][nx]
                    if n_zone: room_data["exits"][d_name] = f"{n_zone}.{real_x+dx}.{real_y+dy}.{real_z}"

            final_shards[zid]["rooms"].append(room_data)

    # Export
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    zone_dir = os.path.join(base_dir, "data", "zones")
    
    count = 0
    for z_id, data in final_shards.items():
        if not data["rooms"]: continue
        p = os.path.join(zone_dir, f"{z_id}.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f: json.dump(data, f, indent=4)
        count += 1
            
    print(f"Exported {count} biological shards to {zone_dir}")
    return True
