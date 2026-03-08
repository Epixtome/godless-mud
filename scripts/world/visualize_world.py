import json
import os
import sys
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# --- CONFIG ---
ZONE_FOLDER = "data/zones"
SCALE = 10  # 1 character in terminal = 10 coordinates. Adjust if map is too big/small.

def visualize_world():
    print(f"Scanning {ZONE_FOLDER}...")
    
    if not os.path.exists(ZONE_FOLDER):
        print(f"Error: {ZONE_FOLDER} not found.")
        return

    # Data structures
    # exact_map: (x, y, z) -> list of (zone_id, room_id)
    exact_map = defaultdict(list)
    
    # visual_map: (grid_x, grid_y) -> set of zone_ids
    visual_map = defaultdict(set)
    
    zone_colors = {} # zone_id -> char
    zone_ids = set()

    # 1. Load Data
    for filename in os.listdir(ZONE_FOLDER):
        if not filename.endswith(".json"):
            continue
            
        path = os.path.join(ZONE_FOLDER, filename)
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                
            # Get Zone ID
            if 'zones' in data and len(data['zones']) > 0:
                zid = data['zones'][0]['id']
            else:
                zid = filename.replace(".json", "")
            
            zone_ids.add(zid)
            
            for r in data.get('rooms', []):
                x, y, z = r.get('x', 0), r.get('y', 0), r.get('z', 0)
                
                # Track exact overlap
                exact_map[(x, y, z)].append((zid, r['id']))
                
                # Track visual grid (2D projection of Z=0 mostly, or flatten Z)
                # We flatten Z for the visual map to see vertical stacks as one block
                gx, gy = x // SCALE, y // SCALE
                visual_map[(gx, gy)].add(zid)
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    if not zone_ids:
        print("No zones found.")
        return

    # 2. Assign Characters to Zones
    # We use a simple list to assign A-Z, a-z, 0-9
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    sorted_zones = sorted(list(zone_ids))
    for i, zid in enumerate(sorted_zones):
        char = chars[i % len(chars)]
        zone_colors[zid] = char

    # 3. Detect Exact Overlaps
    # Filter for coordinates where more than 1 UNIQUE zone exists
    overlaps = {k: v for k, v in exact_map.items() if len(set(t[0] for t in v)) > 1}
    
    if overlaps:
        print(f"\n{len(overlaps)} CRITICAL OVERLAPS DETECTED!")
        print("==========================================")
        count = 0
        for coord, occupants in overlaps.items():
            if count > 20:
                print(f"... and {len(overlaps) - 20} more.")
                break
            
            zones_involved = set(t[0] for t in occupants)
            print(f"At {coord}: Overlap between {', '.join(zones_involved)}")
            for zid, rid in occupants:
                print(f"  - {zid}: {rid}")
            count += 1
        print("==========================================\n")
    else:
        print("\nNo exact coordinate overlaps detected.\n")

    # 4. Render Visual Grid
    if not visual_map:
        return

    xs = [k[0] for k in visual_map.keys()]
    ys = [k[1] for k in visual_map.keys()]
    
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    print(f"=== WORLD MAP (Scale 1 char : {SCALE} units) ===")
    print(f"Bounds: X[{min_x*SCALE}, {max_x*SCALE}] Y[{min_y*SCALE}, {max_y*SCALE}]")
    
    # Print Legend
    print("Legend:")
    for zid in sorted_zones:
        print(f"  {zone_colors[zid]} : {zid}")
    print("  ! : Overlap/Conflict")
    print("  . : Empty")
    print("-" * 40)

    for y in range(min_y - 1, max_y + 2):
        row_str = ""
        for x in range(min_x - 1, max_x + 2):
            zones_here = visual_map.get((x, y), set())
            
            if not zones_here:
                row_str += ". "
            elif len(zones_here) > 1:
                row_str += "! "
            else:
                # Single zone
                zid = list(zones_here)[0]
                row_str += f"{zone_colors[zid]} "
        print(row_str)

if __name__ == "__main__":
    visualize_world()
