import os
import sys
import json
from collections import defaultdict

# Add root for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.world import reset_world

# --- Configuration ---

# 1. Generation Scripts (from master_generator.py)
GENERATION_SCRIPTS = [
    "scripts/world/generate_hub.py",
    "scripts/world/generate_sanctum.py",
    "scripts/world/generate_golden_fields.py",
    "scripts/world/generate_crystal_caverns.py",
    "scripts/world/generate_noxus.py",
    "scripts/world/generate_whispering_vale.py",
    "scripts/world/generate_dark_swamp.py",
    "scripts/world/generate_ironbark.py",
    "scripts/world/generate_verdant_river.py",
    "scripts/world/generate_elderwood.py",
    "scripts/world/generate_expansion_zones.py",
    "scripts/world/generate_borderlands.py"
]

# 2. Link Definitions (The Master Blueprint)
# Format: (SourceZone, SourceRoomName, Direction, TargetZone, TargetRoomName)
ZONE_LINKS = [
    # --- Light Kingdom (North) ---
    ("hub", "Hub North Gate", "north", "light_farm", "Southern Outpost"),
    ("light_farm", "North Gate Approach", "north", "light_cap", "The Golden Gate"),
    ("light_cap", "Market Row", "east", "light_mine", "Mine Entrance"),
    ("light_cap", "North Gate", "north", "light_desert", "South Gate"),
    ("light_desert", "North Gate", "north", "light_mtn", "South Gate"),
    ("light_mtn", "North Gate", "north", "light_war", "South Gate"),

    # --- Dark Kingdom (East) ---
    # Layout: Hub -> Swamp -> Dungeon -> Capital -> Void -> War
    ("hub", "Hub East Gate", "east", "dark_swamp", "Marsh Edge"),
    ("dark_swamp", "East Gate", "east", "dark_dungeon", "West Gate"),
    ("dark_dungeon", "East Gate", "east", "dark_cap", "West Gate"),
    ("dark_cap", "The Gate of Whispers", "south", "dark_forest", "Gate of Whispers Approach"),
    ("dark_cap", "East Gate", "east", "dark_void", "West Gate"),
    ("dark_void", "East Gate", "east", "dark_war", "West Gate"),

    # --- Instinct Kingdom (West) ---
    ("hub", "Hub West Gate", "west", "instinct_riv", "River Crossing"),
    ("instinct_riv", "West Gate", "west", "instinct_cap", "East Gate"),
    ("instinct_cap", "South Gate", "south", "elderwood", "Elderwood Entrance"),
    ("instinct_cap", "West Gate", "west", "instinct_cyn", "East Gate"),
    ("instinct_cyn", "West Gate", "west", "instinct_ice", "East Gate"),
    ("instinct_ice", "West Gate", "west", "instinct_war", "East Gate"),

    # --- Borderlands (The Outer Loop) ---
    ("light_war", "East Gate", "east", "ashlands", "West Gate"),
    ("ashlands", "South Gate", "south", "dark_war", "The Dark Citadel"),
    ("dark_war", "South Gate", "south", "overgrowth", "North Gate"),
    ("overgrowth", "West Gate", "west", "instinct_war", "The Great Den"),
    ("instinct_war", "South Gate", "south", "storm_peaks", "North Gate"),
    ("storm_peaks", "East Gate", "east", "light_war", "West Gate")
]

# --- Helper Functions ---

def load_zone(zone_id):
    path = f"data/zones/{zone_id}.json"
    if not os.path.exists(path):
        print(f"  - Warning: {path} not found. Skipping.")
        return None
    with open(path, 'r') as f:
        return json.load(f)

def save_zone(zone_id, data):
    path = f"data/zones/{zone_id}.json"
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

def find_room_fuzzy(rooms, name_hint):
    """Finds a room matching the hint, ignoring case and 'The ' prefix."""
    hint = name_hint.lower().replace("the ", "").strip()
    for r in rooms:
        r_name = r['name'].lower().replace("the ", "").strip()
        if hint == r_name or hint in r_name:
            return r
    return None

# --- Main Functions ---

def generate_all_zones():
    print("\n--- Step 1: Generating All Zones ---")
    for script in GENERATION_SCRIPTS:
        print(f"Running {script}...")
        if os.system(f"{sys.executable} {script}") != 0:
            print(f"  - ERROR: Script {script} failed. Aborting.")
            return False
    print("Zone generation complete.")
    return True

def assemble_world():
    print("\n--- Step 2: Assembling World (Relative Stitching) ---")
    
    # 1. Load all zones into memory
    zones = {}
    zone_files = os.listdir("data/zones")
    for zf in zone_files:
        if zf.endswith(".json"):
            zid = zf.replace(".json", "")
            zones[zid] = load_zone(zid)

    if "hub" not in zones:
        print("CRITICAL: 'hub' zone not found. Cannot assemble world.")
        return

    # 2. Initialize Placement
    # Set of placed zone IDs
    placed_zones = set(["hub"]) 
    # Map of occupied coordinates to detect collisions: (x,y,z) -> room_id
    occupied_coords = {}
    
    # Register Hub coordinates
    for r in zones["hub"]["rooms"]:
        occupied_coords[(r['x'], r['y'], r['z'])] = r['id']

    # 3. Iterative Stitching
    # We loop through links. If Source is placed and Target is NOT, we snap Target to Source.
    # We repeat this until no new zones are placed in a pass.
    
    something_changed = True
    while something_changed:
        something_changed = False
        
        for src_z, src_hint, direction, tgt_z, tgt_hint in ZONE_LINKS:
            if src_z in placed_zones and tgt_z not in placed_zones:
                if tgt_z not in zones:
                    print(f"Warning: Target zone '{tgt_z}' not found in data.")
                    continue

                # Find Anchor Room in Source
                src_data = zones[src_z]
                src_room = find_room_fuzzy(src_data['rooms'], src_hint)
                
                # Find Entry Room in Target
                tgt_data = zones[tgt_z]
                tgt_room = find_room_fuzzy(tgt_data['rooms'], tgt_hint)
                
                if not src_room or not tgt_room:
                    print(f"Skipping link {src_z}->{tgt_z}: Could not find rooms '{src_hint}' or '{tgt_hint}'.")
                    continue

                print(f"  Link: {src_z}[{src_room['name']}]({src_room['x']},{src_room['y']}) -> {tgt_z}[{tgt_room['name']}]({tgt_room['x']},{tgt_room['y']})")

                # Calculate Target Coordinates
                # Target should be 1 step in 'direction' from Source
                tx, ty, tz = src_room['x'], src_room['y'], src_room['z']
                if direction == 'north': ty -= 1
                elif direction == 'south': ty += 1
                elif direction == 'east': tx += 1
                elif direction == 'west': tx -= 1
                elif direction == 'up': tz += 1
                elif direction == 'down': tz -= 1
                
                # Calculate Offset
                ox = tx - tgt_room['x']
                oy = ty - tgt_room['y']
                oz = tz - tgt_room['z']
                
                print(f"Stitching {tgt_z} to {src_z} ({direction}). Offset: {ox}, {oy}, {oz}")
                
                # Apply Offset to ALL rooms in Target Zone
                collision_detected = False
                for r in tgt_data['rooms']:
                    r['x'] += ox
                    r['y'] += oy
                    r['z'] += oz
                    
                    coord = (r['x'], r['y'], r['z'])
                    if coord in occupied_coords:
                        print(f"  ! COLLISION DETECTED at {coord}: {r['id']} overlaps {occupied_coords[coord]}")
                        collision_detected = True
                    occupied_coords[coord] = r['id']
                
                if collision_detected:
                    print(f"  ! WARNING: Zone {tgt_z} overlaps with existing rooms!")

                placed_zones.add(tgt_z)
                something_changed = True

    # 4. Save updated coordinates
    for z_id in placed_zones:
        save_zone(z_id, zones[z_id])
        
    print(f"Assembly complete. Placed {len(placed_zones)} zones.")
    unplaced = set(zones.keys()) - placed_zones
    if unplaced:
        print(f"Warning: The following zones were NOT linked and remain at (0,0): {', '.join(unplaced)}")

def link_all_zones():
    print("\n--- Step 3: Linking Zone Exits ---")
    world_map = {z_id.replace(".json", ""): load_zone(z_id.replace(".json", "")) for z_id in os.listdir("data/zones") if z_id.endswith(".json")}

    for src_z, src_hint, direction, tgt_z, tgt_hint in ZONE_LINKS:
        if not world_map.get(src_z) or not world_map.get(tgt_z): continue

        src_room = find_room_fuzzy(world_map[src_z]['rooms'], src_hint)
        tgt_room = find_room_fuzzy(world_map[tgt_z]['rooms'], tgt_hint)
                
        if src_room and tgt_room:
            src_room['exits'][direction] = tgt_room['id']
            rev_dir = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}.get(direction)
            if rev_dir: tgt_room['exits'][rev_dir] = src_room['id']
            print(f"Linked {src_z} ({src_room['name']}) -> {tgt_z} ({tgt_room['name']})")
        else:
            print(f"  - FAILURE: Could not link {src_z} -> {tgt_z}. Missing room.")

    for zone_id, data in world_map.items():
        if data: save_zone(zone_id, data)
    print("Zone linking complete.")

if __name__ == "__main__":
    print("Godless World Builder")
    print("This script will RESET, GENERATE, and ASSEMBLE the entire game world.")
    if input("This is a destructive operation. Type 'BUILD' to proceed: ") == "BUILD":
        reset_world.reset_generated_zones()
        if generate_all_zones():
            assemble_world()
            link_all_zones()
            print("\nWorld build process finished successfully.")
    else:
        print("Aborted.")
