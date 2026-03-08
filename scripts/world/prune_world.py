import json
import os
import sys

# Add project root to path so we can import core
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from logic.core import loader

# Define expected bounds for zones to detect ghosts
# Format: zone_id: (min_x, max_x, min_y, max_y)
# We allow a generous buffer (e.g. +/- 50) but catch the gross errors (like x=7 vs x=100)
ZONE_BOUNDS = {
    "light_cap": (-50, 50, -250, -150),      # Target: 0, -200
    "light_mine": (50, 150, -250, -150),     # Target: 100, -200
    "light_farm": (-50, 50, -150, -50),      # Target: 0, -100
    "hub": (-50, 50, -50, 50),               # Target: 0, 0
    "dark_swamp": (50, 150, -50, 50),        # Target: 100, 0
    "dark_cap": (150, 250, -50, 50),         # Target: 200, 0
    "instinct_riv": (-150, -50, -50, 50),    # Target: -100, 0
    "instinct_cap": (-250, -150, -50, 50),   # Target: -200, 0
    
    # Expansions
    "light_desert": (-50, 50, -350, -250),   # Target: 0, -300
    "light_mtn": (-50, 50, -450, -350),      # Target: 0, -400
    "light_war": (-50, 50, -550, -450),      # Target: 0, -500
    "dark_dungeon": (250, 350, -50, 50),     # Target: 300, 0
    "dark_void": (350, 450, -50, 50),        # Target: 400, 0
    "dark_war": (450, 550, -50, 50),         # Target: 500, 0
    "instinct_cyn": (-350, -250, -50, 50),   # Target: -300, 0
    "instinct_ice": (-450, -350, -50, 50),   # Target: -400, 0
    "instinct_war": (-550, -450, -50, 50),   # Target: -500, 0
    "overgrowth": (-50, 50, 450, 550),       # Target: 0, 500
}

def prune_world():
    print("Loading world data...")
    # Load raw JSON data to get the "Source of Truth"
    valid_room_ids = set()
    
    # 1. Load all Zone JSONs
    zone_dir = "data/zones"
    if os.path.exists(zone_dir):
        for filename in os.listdir(zone_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(zone_dir, filename), 'r') as f:
                        data = json.load(f)
                        for r in data.get('rooms', []):
                            valid_room_ids.add(r['id'])
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

    print(f"Found {len(valid_room_ids)} valid static rooms.")

    # 2. Load World State (Dynamic)
    # We want to KEEP dynamic rooms if they are important, but for this cleanup, 
    # we assume anything not in the static files is a "mistake" or "ghost".
    # However, we must be careful not to delete the player's current room if possible,
    # or move them if we do.
    
    # Actually, we need to modify the `world_state.json` to remove these rooms,
    # AND we need to tell the user to restart.
    # But `world_state.json` only stores *deltas* (items/mobs). It doesn't store the room existence itself usually,
    # unless we have a full persistence DB. 
    # In this engine, `loader.py` loads static files, then applies `world_state.json`.
    # If a room exists in memory but not in static files, it must have been created at runtime (e.g. @dig).
    # These runtime rooms are NOT saved to `zones/*.json` unless `@savezone` is called.
    # If the user called `@savezone`, the room is in the JSON and thus in `valid_room_ids`.
    # If they didn't, the room is ephemeral and will vanish on restart.
    
    # So, if the user sees these rooms AFTER a restart, they MUST be in the JSON files.
    
    print("Scanning JSON files for anomalies...")
    
    anomalies = []
    for filename in os.listdir(zone_dir):
        if filename.endswith(".json"):
            path = os.path.join(zone_dir, filename)
            with open(path, 'r') as f:
                data = json.load(f)
            
            modified = False
            new_rooms = []
            for r in data.get('rooms', []):
                zone_id = r.get('zone_id')
                if not zone_id and data.get('zones'):
                    zone_id = data['zones'][0]['id']
                
                if zone_id in ZONE_BOUNDS:
                    min_x, max_x, min_y, max_y = ZONE_BOUNDS[zone_id]
                    x, y = r.get('x', 0), r.get('y', 0)
                    
                    # Check if room is wildly out of bounds for its zone
                    if not (min_x <= x <= max_x and min_y <= y <= max_y):
                        print(f"Anomaly: Room {r['id']} ({x},{y}) is out of bounds for {zone_id} (Expected X:{min_x}-{max_x})")
                        anomalies.append(r['id'])
                        modified = True
                        continue
                
                # Also remove any room with 'cave' terrain if it's in light_cap (Sanctum shouldn't have caves)
                if zone_id == 'light_cap' and r.get('terrain') == 'cave':
                    print(f"Anomaly: Cave found in light_cap: {r['id']} at {r.get('x')},{r.get('y')}")
                    anomalies.append(r['id'])
                    modified = True
                    continue

                new_rooms.append(r)
            
            if modified:
                data['rooms'] = new_rooms
                with open(path, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"Pruned anomalies from {filename}")

    print("Done. Restart server to apply changes.")

if __name__ == "__main__":
    prune_world()
