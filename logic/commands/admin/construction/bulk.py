import logic.handlers.command_manager as command_manager
import logic.commands.admin.construction.utils as construction_utils
from utilities import mapper

@command_manager.register("@deleteroom", admin=True)
def delete_room(player, args):
    """
    Delete a room, a line of rooms, or a grid of rooms.
    Usage:
      @deleteroom                  (Delete current room)
      @deleteroom <room_id>        (Delete specific room)
      @deleteroom <dir>            (Delete neighbor in direction)
      @deleteroom <len> <dir>      (Delete line of rooms)
      @deleteroom <w> <h> <dir>    (Delete grid of rooms)
    """
    targets = []
    
    valid_dirs = ['north', 'south', 'east', 'west', 'up', 'down', 'n', 's', 'e', 'w', 'u', 'd']
    parts = args.split() if args else []
    
    # 1. Identify Target Rooms
    if not parts:
        # Case: Current Room
        targets.append(player.room)
        
    elif parts[-1].lower() in valid_dirs:
        # Case: Directional Delete (Line or Grid)
        direction = construction_utils.parse_direction(parts[-1])
        dims = parts[:-1]
        
        from logic.engines import spatial_engine
        spatial = spatial_engine.get_instance(player.game.world)
        
        if len(dims) <= 1:
            # Line: <len> <dir> or just <dir>
            length = int(dims[0]) if dims else 1
            
            dx, dy, dz = 0, 0, 0
            if direction == 'north': dy = -1
            elif direction == 'south': dy = 1
            elif direction == 'east': dx = 1
            elif direction == 'west': dx = -1
            elif direction == 'up': dz = 1
            elif direction == 'down': dz = -1
            
            cx, cy, cz = player.room.x, player.room.y, player.room.z
            
            # Start from the NEXT room to avoid deleting the one we stand in (unless length is huge and loops back)
            for i in range(1, length + 1):
                tx, ty, tz = cx + (dx * i), cy + (dy * i), cz + (dz * i)
                room = spatial.get_room(tx, ty, tz)
                if room:
                    targets.append(room)
                    
        elif len(dims) == 2 and dims[0].isdigit() and dims[1].isdigit():
            # Grid: <w> <h> <dir>
            width = int(dims[0])
            height = int(dims[1])
            
            off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
            if off_x is None:
                off_x = player.room.x - (width // 2)
                off_y = player.room.y - (height // 2)
            
            start_z = player.room.z
            for y in range(off_y, off_y + height):
                for x in range(off_x, off_x + width):
                    room = spatial.get_room(x, y, start_z)
                    if room:
                        targets.append(room)
        else:
            player.send_line("Invalid format. Use <len> <dir> or <w> <h> <dir>.")
            return
    else:
        # Case: Specific Room ID
        target_id = args
        if target_id in player.game.world.rooms:
            targets.append(player.game.world.rooms[target_id])
        else:
            player.send_line(f"Room '{target_id}' not found.")
            return

    # 2. Validation & Execution
    start_room = player.game.world.start_room or list(player.game.world.rooms.values())[0]
    if start_room in targets:
        player.send_line(f"Cannot delete the start room ({start_room.id}). Skipping it.")
        targets.remove(start_room)
        
    if not targets:
        player.send_line("No rooms found to delete.")
        return

    player.send_line(f"Deleting {len(targets)} rooms...")
    target_ids = set(r.id for r in targets)
    
    # Remove links from the world (Batch operation)
    link_count = 0
    for r in player.game.world.rooms.values():
        to_remove = []
        for d, target_id in r.exits.items():
            if target_id in target_ids:
                to_remove.append(d)
        for d in to_remove:
            del r.exits[d]
            r.dirty = True
            link_count += 1
    
    # Evacuate and Delete
    for room in targets:
        # Move players
        for p in list(room.players):
            p.send_line("The world dissolves around you...")
            p.room = start_room
            start_room.players.append(p)
            if p in room.players:
                room.players.remove(p)
            p.send_line("You materialize in a safe place.")
            from logic.commands import info_commands as information
            information.look(p, "")
            
        # Delete
        if room.id in player.game.world.rooms:
            if not hasattr(player.game.world, 'deleted_rooms'):
                player.game.world.deleted_rooms = set()
            player.game.world.deleted_rooms.add(room.id)
            del player.game.world.rooms[room.id]
            construction_utils.scrub_room_from_memory(player.game, room.id)
    
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    
    player.send_line(f"Deleted {len(targets)} rooms. Removed {link_count} links.")

@command_manager.register("@prunemap", admin=True)
def prune_map(player, args):
    """
    Scans for overlapping rooms (same X,Y,Z) and deletes duplicates.
    Keeps the room with the highest terrain priority.
    Usage: @prunemap [zone_id | 'all']
    """
    target_zone = args if args else player.room.zone_id
    
    # Group rooms by X,Y,Z
    columns = {}
    for r in player.game.world.rooms.values():
        if target_zone != 'all' and r.zone_id != target_zone:
            continue
        
        coord = (r.x, r.y, r.z)
        if coord not in columns:
            columns[coord] = []
        columns[coord].append(r)
        
    deleted_count = 0
    
    for coord, rooms in columns.items():
        if len(rooms) > 1:
            # Conflict found!
            # Sort by Priority: 
            # 1. Terrain Priority (lower index = higher priority)
            
            def sort_key(r):
                t_prio = 999
                if r.terrain in mapper.TERRAIN_PRIORITY:
                    t_prio = mapper.TERRAIN_PRIORITY.index(r.terrain)
                return t_prio # Min priority index
            
            rooms.sort(key=sort_key)
            
            # Keep the first one, delete the rest
            keeper = rooms[0]
            to_delete = rooms[1:]
            
            player.send_line(f"Conflict at {coord}: Keeping {keeper.name} ({keeper.id}). Deleting {len(to_delete)} others.")
            
            for victim in to_delete:
                if victim.id in player.game.world.rooms:
                    player.send_line(f"  - Deleted: {victim.name} ({victim.id})")
                    if not hasattr(player.game.world, 'deleted_rooms'):
                        player.game.world.deleted_rooms = set()
                    player.game.world.deleted_rooms.add(victim.id)
                    del player.game.world.rooms[victim.id]
                    construction_utils.scrub_room_from_memory(player.game, victim.id)
                    deleted_count += 1
                    
    if deleted_count > 0:
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        
    player.send_line(f"Pruned {deleted_count} overlapping rooms in '{target_zone}'.")

@command_manager.register("@merge", admin=True)
def merge_rooms(player, args):
    """
    Merges overlapping rooms at the current location into the current room.
    Combines exits, moves entities, and preserves non-default attributes.
    """
    # Find candidates at current X,Y in current Zone
    x, y = player.room.x, player.room.y
    current_zone = player.room.zone_id
    
    candidates = []
    for r in player.game.world.rooms.values():
        if r.zone_id == current_zone and r.x == x and r.y == y and r != player.room:
            candidates.append(r)
            
    if not candidates:
        player.send_line("No other rooms found at this location to merge.")
        return
        
    target = player.room
    merged_count = 0
    
    for victim in candidates:
        player.send_line(f"Merging {victim.name} ({victim.id}) into {target.name}...")
        
        # 1. Merge Exits
        for direction, dest in victim.exits.items():
            if direction not in target.exits:
                target.exits[direction] = dest
                player.send_line(f"  - Added exit: {direction}")
                
        # 2. Merge Attributes (Prioritize custom over default)
        if target.terrain == "default" and victim.terrain != "default":
            target.terrain = victim.terrain
            player.send_line(f"  - Adopted terrain: {victim.terrain}")
            
        if target.name in ["New Room", "Empty Room"] and victim.name not in ["New Room", "Empty Room"]:
            target.name = victim.name
            target.description = victim.description
            player.send_line(f"  - Adopted details: {victim.name}")
            
        # 3. Move Entities (Players, Mobs, Items)
        for p in list(victim.players):
            p.room = target
            target.players.append(p)
            p.send_line("The world shifts around you.")
        for m in list(victim.monsters):
            m.room = target
            target.monsters.append(m)
        for i in list(victim.items):
            target.items.append(i)
            
        # 4. Delete Victim
        if victim.id in player.game.world.rooms:
            if not hasattr(player.game.world, 'deleted_rooms'):
                player.game.world.deleted_rooms = set()
            player.game.world.deleted_rooms.add(victim.id)
            del player.game.world.rooms[victim.id]
            construction_utils.scrub_room_from_memory(player.game, victim.id)
            merged_count += 1
            
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    player.send_line(f"Merge complete. Combined {merged_count} rooms into {target.id}.")

@command_manager.register("@flatten", admin=True)
def flatten(player, args):
    """
    Forces rooms in a grid to a specific Z-level.
    Usage: @flatten <z> <width> <height> [direction]
    """
    if not args:
        player.send_line("Usage: @flatten <z> <width> <height> [direction]")
        return
        
    parts = args.split()
    if len(parts) < 3:
        player.send_line("Usage: @flatten <z> <width> <height> [direction]")
        return

    try:
        target_z = int(parts[0])
        width = int(parts[1])
        height = int(parts[2])
    except ValueError:
        player.send_line("Z, Width, and Height must be integers.")
        return
        
    direction = parts[3] if len(parts) > 3 else None
    
    off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
    if off_x is None:
        off_x = player.room.x - (width // 2)
        off_y = player.room.y - (height // 2)
        
    count = 0
    for r in player.game.world.rooms.values():
        if off_x <= r.x < off_x + width and off_y <= r.y < off_y + height:
            if r.z != target_z:
                r.z = target_z
                count += 1
                
    if count > 0:
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        player.send_line(f"Flattened {count} rooms to Z={target_z}. Use @prunemap if overlaps occurred.")
    else:
        player.send_line("No rooms found to flatten (or all already at target Z).")

@command_manager.register("@copyroom", admin=True)
def copy_room(player, args):
    """
    Copy room attributes to a neighbor or create a line.
    Usage: @copyroom <direction> [length]
    """
    if not args:
        player.send_line("Usage: @copyroom <direction> [length]")
        return
        
    parts = args.split()
    direction = parts[0].lower()
    length = 1
    if len(parts) > 1 and parts[1].isdigit():
        length = int(parts[1])
        
    valid_dirs = ['north', 'south', 'east', 'west', 'up', 'down']
    if direction not in valid_dirs:
        player.send_line("Invalid direction.")
        return
        
    from logic.commands import movement_commands as movement
    
    # Capture source attributes
    src_room = player.room
    src_name = src_room.name
    src_desc = src_room.description
    src_zone = src_room.zone_id
    src_terrain = src_room.terrain
    
    player.send_line(f"Copying source: '{src_name}' (Terrain: {src_terrain})")
    
    # Remove player from source list temporarily to avoid ghosting during rapid movement
    if player in src_room.players:
        src_room.players.remove(player)
        
    count = 0
    for _ in range(length):
        curr_room = player.room
        
        if direction in curr_room.exits:
            # Update existing
            next_room = curr_room.exits[direction]
            construction_utils.update_room(
                next_room,
                zone_id=src_zone,
                terrain=src_terrain,
                name=src_name,
                desc=src_desc
            )
            player.room = next_room
            count += 1
        else:
            # Dig new
            new_room = movement.dig_room(player, direction, src_name, terrain=src_terrain)
            if new_room:
                new_room.description = src_desc
                new_room.zone_id = src_zone
                player.room = new_room
                count += 1
            else:
                break
                
    # Re-add player to the final room
    if player not in player.room.players:
        player.room.players.append(player)
        
    player.send_line(f"Copied/Dug {count} rooms {direction}. You are now at the end.")
    
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    
    from logic.commands import info_commands as information
    information.look(player, "")

@command_manager.register("@massedit", admin=True)
def mass_edit(player, args):
    """
    Bulk edit rooms.
    Usage: @massedit <scope> <scope_arg> <attr> <value>
    Scopes: zone, terrain, name_match
    Attrs: name, desc, terrain, zone, z
    Example: @massedit zone placeholder terrain forest
    """
    if not args:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
        
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
        
    scope = parts[0].lower()
    scope_arg = parts[1]
    attr = parts[2].lower()
    value = " ".join(parts[3:])
    
    count = 0
    
    # 1. Identify Target Rooms
    targets = []
    for r in player.game.world.rooms.values():
        match = False
        if scope == "zone":
            if r.zone_id == scope_arg: match = True
        elif scope == "terrain":
            if r.terrain == scope_arg: match = True
        elif scope == "name_match":
            if scope_arg.lower() in r.name.lower(): match = True
            
        if match:
            targets.append(r)
            
    if not targets:
        player.send_line("No rooms matched criteria.")
        return
        
    # 2. Apply Changes
    for r in targets:
        if attr == "name":
            r.name = value
        elif attr == "desc":
            r.description = value
        elif attr == "terrain":
            r.terrain = value
        elif attr == "zone":
            value = value.lower()
            r.zone_id = value
            # Ensure zone exists if we are mass assigning it
            if value not in player.game.world.zones:
                from models import Zone
                player.game.world.zones[value] = Zone(value, f"Zone {value}")
                player.send_line(f"Created new zone entry: '{value}'.")
        elif attr == "z":
            try:
                r.z = int(value)
            except:
                pass
        count += 1
        
    # Invalidate spatial if coords changed (Z)
    if attr == "z":
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
        
    player.send_line(f"Updated {count} rooms.")

@command_manager.register("@replace", admin=True)
def replace_text(player, args):
    """
    Search and replace text in room descriptions/names in current zone.
    Usage: @replace <target_text> WITH <replacement_text>
    """
    if " WITH " not in args:
        player.send_line("Usage: @replace <old> WITH <new>")
        return
        
    old, new = args.split(" WITH ", 1)
    current_zone = player.room.zone_id
    count = 0
    
    for r in player.game.world.rooms.values():
        if r.zone_id == current_zone:
            if old in r.description:
                r.description = r.description.replace(old, new)
                count += 1
            if old in r.name:
                r.name = r.name.replace(old, new)
                count += 1
                
    player.send_line(f"Replaced instances in {count} fields in zone '{current_zone}'.")