import logic.handlers.command_manager as command_manager
from logic.core.world import get_room_id
from utilities.colors import Colors

@command_manager.register("@vision", admin=True, category="admin_tools")
def vision(player, args):
    """
    Shows all rooms at the current X, Y coordinates across different Z-levels.
    """
    x, y = player.room.x, player.room.y
    
    matches = []
    for r in player.game.world.rooms.values():
        if r.x == x and r.y == y:
            matches.append(r)
            
    if not matches:
        player.send_line("No rooms found? That's impossible.")
        return
        
    # Sort by Z descending (highest first)
    matches.sort(key=lambda r: r.z, reverse=True)
    
    player.send_line(f"\n{Colors.BOLD}--- Vision: Stack at {x}, {y} ({player.room.zone_id}) ---{Colors.RESET}")
    for r in matches:
        marker = " <--- YOU" if r == player.room else ""
        color = Colors.GREEN if r == player.room else Colors.CYAN
        player.send_line(f"{color}Z={r.z:<3} | ID: {r.id:<25} | Zone: {r.zone_id:<15} | Name: {r.name}{marker}{Colors.RESET}")

@command_manager.register("@setlayer", admin=True, category="admin_building")
def layer_room(player, args):
    """
    Moves the current room to a specific Z-level.
    Usage: @setlayer <z>
    """
    if not args:
        player.send_line("Usage: @setlayer <z>")
        return
        
    parts = args.split()
    try:
        new_z = int(parts[0])
    except ValueError:
        player.send_line("Z-level must be an integer.")
        return
        
    old_z = player.room.z
    player.room.z = new_z
    
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    
    player.send_line(f"Moved room '{player.room.name}' from Z={old_z} to Z={new_z}.")
    
    # Check for ID mismatch warning
    try:
        # Heuristic: Check if ID ends in .<z> or .<z>.0
        id_parts = player.room.id.split('.')
        if len(id_parts) >= 3:
            # Assuming format zone.x.y.z
            id_z = int(id_parts[-1])
            if id_z != new_z:
                 player.send_line(f"{Colors.YELLOW}Warning: Room ID '{player.room.id}' implies Z={id_z}, but room is now Z={new_z}.{Colors.RESET}")
    except:
        pass

@command_manager.register("@audit", admin=True, category="admin_tools")
def audit_zone(player, args):
    """
    Scans zone for ID mismatches and broken exits.
    Usage: @audit [zone_id]
    """
    zone_id = args if args else player.room.zone_id
    player.send_line(f"Auditing zone '{zone_id}'...")
    
    issues = 0
    for r in player.game.world.rooms.values():
        if r.zone_id != zone_id: continue
        
        # 1. ID Mismatch
        expected = get_room_id(r.zone_id, r.x, r.y, r.z)
        if r.id != expected:
            player.send_line(f"{Colors.YELLOW}[ID Mismatch]{Colors.RESET} {r.name} ({r.id}) -> Should be {expected}")
            issues += 1
            
        # 2. Self Links
        for d, target in r.exits.items():
            if target == r:
                player.send_line(f"{Colors.RED}[Self Link]{Colors.RESET} {r.name} links to itself ({d})")
                issues += 1
                
    if issues == 0:
        player.send_line("No issues found.")
    else:
        player.send_line(f"Found {issues} issues. Use @fixids to correct IDs.")

@command_manager.register("@fixids", admin=True, category="admin_building")
def fix_ids(player, args):
    """
    Renames rooms in the zone to match their coordinates.
    Usage: @fixids [zone_id]
    """
    zone_id = args if args else player.room.zone_id
    world = player.game.world
    renames = {} # old_id -> new_id
    
    # 1. Calculate Renames
    for r_id, room in world.rooms.items():
        if room.zone_id != zone_id: continue
        
        expected_id = get_room_id(room.zone_id, room.x, room.y, room.z)
        
        if r_id != expected_id:
            if expected_id in world.rooms:
                player.send_line(f"Skipping {r_id} -> {expected_id} (Target ID already exists).")
            else:
                renames[r_id] = expected_id

    if not renames:
        player.send_line(f"No ID mismatches found in zone '{zone_id}'.")
        return
        
    # 2. Apply Renames
    count = 0
    for old_id, new_id in renames.items():
        # Move in dictionary
        room = world.rooms.pop(old_id)
        room.id = new_id
        world.rooms[new_id] = room
        count += 1
        
    player.send_line(f"Fixed {count} room IDs in '{zone_id}'. Exits preserved.")

@command_manager.register("@dbcheck", admin=True, category="admin_system")
def db_check(player, args):
    """
    Checks the status of the Shelve persistence database.
    Usage: @dbcheck
    """
    import shelve
    import os
    
    # Shelve creates files like world_state.dat, .db, or .dir depending on OS
    db_base = 'data/world_state'
    exists = False
    for ext in ['', '.dat', '.db', '.dir', '.bak']:
        if os.path.exists(db_base + ext):
            exists = True
            break
            
    if not exists:
        player.send_line(f"{Colors.RED}Shelve DB file not found.{Colors.RESET} (This is normal if no changes have been saved yet).")
        return

    try:
        with shelve.open(db_base, flag='r') as db:
            keys = list(db.keys())
            count = len(keys)
            player.send_line(f"\n{Colors.BOLD}--- Shelve DB Status ---{Colors.RESET}")
            player.send_line(f"Status: {Colors.GREEN}ONLINE{Colors.RESET}")
            player.send_line(f"Dirty Rooms Persisted: {Colors.CYAN}{count}{Colors.RESET}")
            
            if player.room.id in db:
                player.send_line(f"Current Room: {Colors.YELLOW}DIRTY{Colors.RESET} (Saved in DB)")
            else:
                player.send_line(f"Current Room: {Colors.GREEN}CLEAN{Colors.RESET} (Using Static JSON)")
                
    except Exception as e:
        player.send_line(f"{Colors.RED}Error opening DB: {e}{Colors.RESET}")
