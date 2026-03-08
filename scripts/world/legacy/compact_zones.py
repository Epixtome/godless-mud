import json
import glob
import os
import re

def parse_id(room_id):
    """
    Attempts to parse a room ID into (zone_id, x, y, z).
    Handles both 'region_0_0.1.1.0' and legacy 'region_0_0_1_1_0'.
    """
    # Try Dot format first (New)
    # Assumes zone_id does not contain dots, but coordinates might have minus signs
    if '.' in room_id:
        parts = room_id.split('.')
        if len(parts) >= 4:
            z_id = ".".join(parts[:-3])
            return z_id, int(parts[-3]), int(parts[-2]), int(parts[-1])

    # Try Underscore format (Old)
    # This is trickier because zone_id has underscores.
    # We assume the last 3 parts are coords.
    parts = room_id.split('_')
    if len(parts) >= 4:
        # Handle 'n' for negative numbers in legacy format
        def parse_coord(c):
            return int(c.replace('n', '-'))
        
        try:
            z = parse_coord(parts[-1])
            y = parse_coord(parts[-2])
            x = parse_coord(parts[-3])
            z_id = "_".join(parts[:-3])
            return z_id, x, y, z
        except ValueError:
            pass
            
    return None, 0, 0, 0

def compact_zones():
    zone_files = glob.glob("data/zones/*.json")
    
    zone_map = {} # old_zone_id -> new_zone_id
    room_map = {} # old_room_id -> new_room_id
    
    print(f"Found {len(zone_files)} zone files.")

    # --- PASS 1: Generate Mappings ---
    for i, filepath in enumerate(zone_files):
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON: {filepath}")
                continue
            
        # Determine Old Zone ID
        old_z_id = None
        if 'zones' in data and data['zones']:
            old_z_id = data['zones'][0]['id']
        elif 'id' in data:
            old_z_id = data['id']
            
        if not old_z_id:
            print(f"Skipping {filepath}: Could not determine Zone ID.")
            continue
            
        # Generate New Zone ID (z0, z1, z2...)
        new_z_id = f"z{i}"
        zone_map[old_z_id] = new_z_id
        print(f"Mapping {old_z_id} -> {new_z_id}")
        
        # Map Rooms
        for room in data.get('rooms', []):
            x, y, z = room.get('x', 0), room.get('y', 0), room.get('z', 0)
            
            # Calculate New ID
            new_r_id = f"{new_z_id}.{x}.{y}.{z}"
            
            # Map existing ID if present
            if 'id' in room:
                room_map[room['id']] = new_r_id
            
            # Map implicit/legacy IDs to ensure exits pointing to them get updated
            # Legacy Underscore
            legacy_id = f"{old_z_id}_{x}_{y}_{z}".replace("-", "n")
            room_map[legacy_id] = new_r_id
            
            # Current Dot
            dot_id = f"{old_z_id}.{x}.{y}.{z}"
            room_map[dot_id] = new_r_id

    # --- PASS 2: Rewrite Files ---
    print("\nRewriting files...")
    for filepath in zone_files:
        with open(filepath, 'r') as f:
            try:
                data = json.load(f)
            except:
                continue
            
        old_z_id = None
        if 'zones' in data and data['zones']:
            old_z_id = data['zones'][0]['id']
        elif 'id' in data:
            old_z_id = data['id']
            
        if old_z_id not in zone_map:
            continue
            
        new_z_id = zone_map[old_z_id]
        
        # 1. Update Zone Header
        if 'zones' in data:
            data['zones'][0]['id'] = new_z_id
        else:
            data['id'] = new_z_id
            
        # 2. Update Rooms
        new_rooms = []
        for room in data.get('rooms', []):
            # Remove redundant zone_id (compression)
            if 'zone_id' in room:
                del room['zone_id']
            
            # Update ID
            x, y, z = room.get('x', 0), room.get('y', 0), room.get('z', 0)
            room['id'] = f"{new_z_id}.{x}.{y}.{z}"
            
            # Update Exits
            if 'exits' in room:
                new_exits = {}
                for d, target in room['exits'].items():
                    # Case A: Target is a known static room
                    if target in room_map:
                        new_exits[d] = room_map[target]
                    else:
                        # Case B: Target is a generated room (not in room_map)
                        # We must parse it and swap the zone prefix
                        tz_id, tx, ty, tz = parse_id(target)
                        if tz_id and tz_id in zone_map:
                            new_target_z = zone_map[tz_id]
                            new_exits[d] = f"{new_target_z}.{tx}.{ty}.{tz}"
                        else:
                            # Keep original if we can't figure it out
                            new_exits[d] = target
                room['exits'] = new_exits
                
            new_rooms.append(room)
        
        data['rooms'] = new_rooms
        
        # 3. Save New File
        new_filename = f"data/zones/{new_z_id}.json"
        with open(new_filename, 'w') as f:
            json.dump(data, f, indent=4)
            
        # 4. Rename Old File (Backup)
        os.rename(filepath, filepath + ".bak")
        
    print("\nDone! Old files renamed to .bak. New files created with short IDs.")
    print("IMPORTANT: Delete data/world_state.json and data/saves/ before restarting.")

if __name__ == "__main__":
    compact_zones()
