"""
logic/commands/admin/construction/world.py
Module for structural world auditing, linking, and zone management.
"""
import os
import glob
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.engines import spatial_engine
from logic.common import get_reverse_direction
import logic.commands.admin.construction.utils as construction_utils
from models.world import Door

@command_manager.register("@link", admin=True, category="admin_building")
def link(player, args):
    """
    Manually link current room to another or auto-link neighbors.
    Usage: @link <dir1> [dir2...] [room_id] [one-way] [door]
    """
    if not args:
        player.send_line("Usage: @link <dir1> [dir2...] [room_id] [one-way] [door]")
        return
    
    parts = args.split()
    one_way = "one-way" in [p.lower() for p in parts]
    has_door = "door" in [p.lower() for p in parts]
    
    # Valid direction keys for identification
    valid_dirs = ['n','s','e','w','u','d','ne','nw','se','sw','north','south','east','west','up','down']
    
    directions_raw = []
    target_id = None
    
    for part in parts:
        p_low = part.lower()
        if p_low in ["one-way", "door"]:
            continue
        if p_low in valid_dirs:
            directions_raw.append(p_low)
        elif not target_id:
            target_id = part

    if not directions_raw:
        player.send_line("No valid directions specified.")
        return
        
    world = player.game.world
    spatial = spatial_engine.get_instance(world)
    links_created = 0
    
    for d_raw in directions_raw:
        direction = construction_utils.parse_direction(d_raw)
        target_room = None
        
        if target_id:
            target_room = world.rooms.get(target_id)
            if not target_room:
                for r in world.rooms.values():
                    if r.name.lower() == target_id.lower():
                        target_room = r
                        break
        else:
            # AUTO-LINK
            dx, dy, dz = construction_utils.get_offset_scalars(direction)
            tx, ty, tz = player.room.x + dx, player.room.y + dy, player.room.z + dz
            target_room = construction_utils.find_room_at_fuzzy_z(spatial, tx, ty, tz, tolerance=1)
            
        if not target_room:
            player.send_line(f"No target room found to the {direction}.")
            continue
            
        player.room.add_exit(direction, target_room)
        player.room.manual_exits = True # Take control of geometry
        if has_door:
            player.room.doors[direction] = Door("door", "closed")
            
        if not one_way:
            rev = get_reverse_direction(direction)
            if rev:
                target_room.add_exit(rev, player.room)
                target_room.manual_exits = True # Take control of geometry
                if has_door:
                    target_room.doors[rev] = Door("door", "closed")
                target_room.dirty = True
            
        player.room.dirty = True
        links_created += 1
        
    player.send_line(f"Successfully created {links_created} link(s).")

@command_manager.register("@door", admin=True, category="admin_building")
def add_door(player, args):
    """
    Adds a door to an existing exit.
    Usage: @door <direction> [name] [state] [one-way]
    """
    if not args:
        player.send_line("Usage: @door <direction> [name] [state] [one-way]")
        return
        
    parts = args.split()
    direction = parts[0].lower()
    
    if direction not in player.room.exits:
        player.send_line(f"No exit found to the {direction}. Use @link first.")
        return
        
    # Name and State (defaults)
    name = "door"
    state = "closed"
    one_way = False
    
    # Simple parser for remainders
    for part in parts[1:]:
        if part.lower() in ["open", "closed", "locked"]:
            state = part.lower()
        elif part.lower() == "one-way":
            one_way = True
        else:
            name = part.strip('"')

    player.room.doors[direction] = Door(name, state)
    player.room.manual_exits = True # Doors require manual control
    player.room.dirty = True
    
    target_id = player.room.exits[direction]
    target_room = player.game.world.rooms.get(target_id)
    
    if not one_way and target_room:
        rev = get_reverse_direction(direction)
        if rev and rev in target_room.exits and target_room.exits[rev] == player.room.id:
            target_room.doors[rev] = Door(name, state)
            target_room.manual_exits = True
            target_room.dirty = True
            player.send_line(f"Bidirectional {state} {name} created to the {direction}.")
            return
            
    player.send_line(f"One-way {state} {name} created to the {direction}.")

@command_manager.register("@unlink", admin=True, category="admin_building")
def unlink(player, args):
    """
    Remove links in specific directions.
    Usage: @unlink <dir1> [dir2...] [one-way]
    """
    if not args:
        player.send_line("Usage: @unlink <dir1> [dir2...] [one-way]")
        return
        
    parts = args.split()
    one_way = "one-way" in [p.lower() for p in parts]
    
    # Filter directions from flags
    directions_raw = [p.lower() for p in parts if p.lower() != "one-way"]
    
    count = 0
    for d_raw in directions_raw:
        direction = construction_utils.parse_direction(d_raw)
        
        if direction not in player.room.exits:
            continue
            
        target_id = player.room.exits[direction]
        target_room = player.game.world.rooms.get(target_id)
        
        # Remove primary exit and door
        del player.room.exits[direction]
        player.room.manual_exits = True # Explicit unlinking overrides grid logic
        if direction in player.room.doors:
            del player.room.doors[direction]
            
        player.room.dirty = True
        
        if not one_way and target_room:
            rev = get_reverse_direction(direction)
            if rev and rev in target_room.exits:
                if target_room.exits[rev] == player.room.id:
                    del target_room.exits[rev]
                    target_room.manual_exits = True
                    if rev in target_room.doors:
                        del target_room.doors[rev]
                    target_room.dirty = True
                    
        count += 1
                
    player.send_line(f"Removed {count} {'one-way ' if one_way else ''}link(s).")

@command_manager.register("@statecheck", admin=True, category="admin_system")
def state_check(player, args):
    """Checks the status of shards and deltas."""
    delta_files = glob.glob("data/live/*.json")
    shard_files = glob.glob("data/zones/*.json")
    
    player.send_line(f"\n{Colors.BOLD}--- World State Audit ---{Colors.RESET}")
    player.send_line(f"Active Rooms: {len(player.game.world.rooms)}")
    player.send_line(f"Loaded Shards: {len(shard_files)}")
    player.send_line(f"Live Deltas: {len(delta_files)}")
    
    z_id = player.room.zone_id
    player.send_line(f"\n[Current Zone: {z_id}]")
    player.send_line(f"Dirty: {player.room.dirty}")

@command_manager.register("@audit", admin=True, category="admin_building")
def audit_zone(player, args):
    """Checks for disconnected rooms and errors in the zone."""
    target_zone = args.lower() if args else player.room.zone_id
    rooms = [r for r in player.game.world.rooms.values() if r.zone_id == target_zone]
    
    orphans = []
    broken_exits = 0
    for r in rooms:
        if not r.exits: orphans.append(r)
        for d, tid in r.exits.items():
            if tid not in player.game.world.rooms:
                broken_exits += 1
                
    player.send_line(f"Audit for {target_zone}: {len(rooms)} rooms.")
    player.send_line(f"Orphans: {len(orphans)}")
    player.send_line(f"Broken Exits: {broken_exits}")

@command_manager.register("@vision", admin=True, category="admin_building")
def vision_command(player, args):
    """Shows rooms at the same X,Y but different Z-levels."""
    x, y = player.room.x, player.room.y
    matches = []
    for r in player.game.world.rooms.values():
        if r.x == x and r.y == y:
            matches.append(r)
    
    player.send_line(f"\n--- Vertical Slice at {x}, {y} ---")
    for r in sorted(matches, key=lambda r: r.z, reverse=True):
        marker = " (HERE)" if r == player.room else ""
        player.send_line(f"Z: {r.z:<3} | {r.name} ({r.id}){marker}")

@command_manager.register("@setlayer", admin=True, category="admin_building")
def set_layer(player, args):
    """Moves current room to a specific Z-level."""
    if not args:
        player.send_line("Usage: @setlayer <z>")
        return
    try:
        new_z = int(args)
        player.room.z = new_z
        spatial_engine.invalidate()
        player.room.dirty = True
        player.send_line(f"Room moved to Z={new_z}.")
    except:
        player.send_line("Z must be an integer.")

@command_manager.register("@fixids", admin=True, category="admin_building")
def fix_ids(player, args):
    """Re-syncs room IDs with their coordinates if they've drifted."""
    from logic.core.world import get_room_id
    count = 0
    current_zone = player.room.zone_id
    rooms = list(player.game.world.rooms.values())
    
    for r in rooms:
        if r.zone_id != current_zone: continue
        expected_id = get_room_id(r.zone_id, r.x, r.y, r.z)
        if r.id != expected_id:
            # Swap in world dictionary
            del player.game.world.rooms[r.id]
            r.id = expected_id
            player.game.world.rooms[r.id] = r
            r.dirty = True
            count += 1
            
    player.send_line(f"Synchronized {count} room IDs.")
