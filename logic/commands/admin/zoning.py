import logic.handlers.command_manager as command_manager
from logic.common import get_reverse_direction
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@stitch", admin=True)
def stitch_zones_cmd(player, args):
    """Stitch a zone to an anchor room to fix coordinates."""
    if not args:
        player.send_line("Usage: @stitch <zone_id> <anchor_room_id> <target_room_id> <direction>")
        return
        
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @stitch <zone_id> <anchor_room_id> <target_room_id> <direction>")
        return
        
    zone_id = parts[0]
    anchor_id = parts[1]
    target_id = parts[2]
    direction = parts[3].lower()
    
    from utilities import coordinate_fixer
    if coordinate_fixer.stitch_zones(player.game.world, zone_id, anchor_id, target_id, direction):
        player.send_line(f"Zone '{zone_id}' stitched successfully.")
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
    else:
        player.send_line("Stitch failed. Check server logs.")

@command_manager.register("@snapzone", admin=True)
def snap_zone(player, args):
    """
    Snaps a zone to an anchor room and links them.
    Usage: @snapzone <moving_room_id> <anchor_room_id> <direction>
    """
    if not args:
        player.send_line("Usage: @snapzone <moving_room_id> <anchor_room_id> <direction>")
        return
    
    parts = args.split()
    if len(parts) < 3:
        player.send_line("Usage: @snapzone <moving_room_id> <anchor_room_id> <direction>")
        return

    moving_room_id = parts[0]
    anchor_room_id = parts[1]
    direction = parts[2].lower()

    world = player.game.world
    moving_room = world.rooms.get(moving_room_id)
    anchor_room = world.rooms.get(anchor_room_id)

    if not moving_room:
        player.send_line(f"Moving room '{moving_room_id}' not found.")
        return
    if not anchor_room:
        player.send_line(f"Anchor room '{anchor_room_id}' not found.")
        return

    # Calculate target coordinates based on direction (North is -Y in this engine)
    ax, ay, az = anchor_room.x, anchor_room.y, anchor_room.z
    
    dx, dy, dz = 0, 0, 0
    if direction == "north": dy = -1
    elif direction == "south": dy = 1
    elif direction == "east": dx = 1
    elif direction == "west": dx = -1
    elif direction == "up": dz = 1
    elif direction == "down": dz = -1
    else:
        player.send_line("Invalid direction. Use: north, south, east, west, up, down.")
        return

    target_x = ax + dx
    target_y = ay + dy
    target_z = az + dz

    # Calculate shift
    mx, my, mz = moving_room.x, moving_room.y, moving_room.z
    shift_x = target_x - mx
    shift_y = target_y - my
    shift_z = target_z - mz

    moving_zone_id = moving_room.zone_id
    if not moving_zone_id:
        player.send_line("Moving room has no zone ID.")
        return

    # Shift all rooms in zone
    count = 0
    for r in world.rooms.values():
        if r.zone_id == moving_zone_id:
            r.x += shift_x
            r.y += shift_y
            r.z += shift_z
            count += 1

    # Link exits
    anchor_room.add_exit(direction, moving_room)
    rev_dir = get_reverse_direction(direction)
    if rev_dir:
        moving_room.add_exit(rev_dir, anchor_room)

    player.send_line(f"Snapped zone '{moving_zone_id}' ({count} rooms) to '{anchor_room.name}'.")
    player.send_line(f"Shifted by X:{shift_x}, Y:{shift_y}, Z:{shift_z}.")
    player.send_line(f"Linked {direction} <-> {rev_dir}.")
    from logic.engines import spatial_engine
    spatial_engine.invalidate()

@command_manager.register("@shiftzone", admin=True)
def shift_zone(player, args):
    """
    Manually shift a zone by x, y, z.
    Usage: @shiftzone <zone_id> <dx> <dy> <dz>
    """
    if not args:
        player.send_line("Usage: @shiftzone <zone_id> <dx> <dy> <dz>")
        return
    
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @shiftzone <zone_id> <dx> <dy> <dz>")
        return
        
    zone_id = parts[0]
    try:
        dx = int(parts[1])
        dy = int(parts[2])
        dz = int(parts[3])
    except ValueError:
        player.send_line("Offsets must be integers.")
        return
        
    count = 0
    for r in player.game.world.rooms.values():
        if r.zone_id == zone_id:
            r.x += dx
            r.y += dy
            r.z += dz
            count += 1
            
    if count == 0:
        player.send_line(f"No rooms found in zone '{zone_id}'.")
    else:
        player.send_line(f"Shifted {count} rooms in '{zone_id}' by ({dx}, {dy}, {dz}).")
        from logic.engines import spatial_engine
        spatial_engine.invalidate()

@command_manager.register("@autostitch", admin=True)
def autostitch_cmd(player, args):
    """
    Automatically links adjacent rooms that are missing exits.
    """
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0),
        "up": (0, 0, 1), "down": (0, 0, -1)
    }
    
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    
    for room in player.game.world.rooms.values():
        for d_name, (dx, dy, dz) in directions.items():
            if d_name in room.exits: continue
            
            # Target coordinates
            tx, ty, tz = room.x + dx, room.y + dy, room.z + dz
            
            # Scan Z range for slopes
            best_neighbor = construction_utils.find_room_at_fuzzy_z(spatial, tx, ty, tz, tolerance=3)
            if best_neighbor == room: best_neighbor = None # Don't link to self
            
            if best_neighbor:
                room.add_exit(d_name, best_neighbor)
                links += 1
                
    player.send_line(f"Stitching complete. Created {links} new links.")

@command_manager.register("@floodzone", admin=True)
def flood_zone(player, args):
    """
    Flood fills a zone ID to connected rooms of the same terrain.
    Useful for rezoning irregular shapes (e.g. a forest valley).
    Usage: @floodzone <new_zone_id> [limit]
    """
    if not args:
        player.send_line("Usage: @floodzone <new_zone_id> [limit]")
        return
        
    parts = args.split()
    new_zone = parts[0].lower()
    limit = 2000
    if len(parts) > 1 and parts[1].isdigit():
        limit = int(parts[1])
        
    if new_zone not in player.game.world.zones:
        from models import Zone
        player.game.world.zones[new_zone] = Zone(new_zone, f"Zone {new_zone}")
        player.send_line(f"Created new zone entry: '{new_zone}'.")
        
    start_room = player.room
    target_terrain = start_room.terrain
    
    queue = [start_room]
    visited = set([start_room.id])
    changed_count = 0
    
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    
    # Cardinal directions
    directions = [(0, -1, 0), (0, 1, 0), (1, 0, 0), (-1, 0, 0)]
    
    player.send_line(f"Flood filling zone '{new_zone}' on contiguous '{target_terrain}'...")
    
    while queue and changed_count < limit:
        curr = queue.pop(0)
        
        if curr.zone_id != new_zone:
            curr.zone_id = new_zone
            changed_count += 1
            
        for dx, dy, dz in directions:
            neighbor = construction_utils.find_room_at_fuzzy_z(spatial, curr.x + dx, curr.y + dy, curr.z + dz)
            if neighbor and neighbor.id not in visited:
                if neighbor.terrain == target_terrain:
                    visited.add(neighbor.id)
                    queue.append(neighbor)
                    
    player.send_line(f"Rezoned {changed_count} rooms to '{new_zone}'.")
    spatial_engine.invalidate()

@command_manager.register("@exportzone", admin=True)
def export_zone_cmd(player, args):
    """
    Exports a zone from the DB to a JSON file.
    REQUIRED before migrating to a different OS (Windows -> Linux).
    Usage: @exportzone <zone_id> | all
    """
    from logic.core import loader
    if not args:
        args = player.room.zone_id
        
    if args.lower() == 'all':
        for z_id in player.game.world.zones:
            loader.export_zone_to_json(player.game.world, z_id)
        player.send_line("All zones exported to data/zones/*.json.")
    else:
        success, msg = loader.export_zone_to_json(player.game.world, args)
        player.send_line(msg)