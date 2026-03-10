"""
logic/commands/admin/construction/cleanup_commands.py
Commands for room deletion, merging, and map maintenance.
"""
from logic.handlers import command_manager
import logic.commands.admin.construction.utils as construction_utils
from utilities import mapper

@command_manager.register("@deleteroom", admin=True)
def delete_room(player, args):
    """
    Delete a room, a line of rooms, or a grid of rooms.
    Usage: @deleteroom | @deleteroom <id> | @deleteroom <len> <dir> | @deleteroom <w> <h> <dir>
    """
    targets = []
    valid_dirs = ['north', 'south', 'east', 'west', 'up', 'down', 'n', 's', 'e', 'w', 'u', 'd']
    parts = args.split() if args else []
    
    if not parts:
        targets.append(player.room)
    elif parts[-1].lower() in valid_dirs:
        direction = construction_utils.parse_direction(parts[-1])
        dims = parts[:-1]
        from logic.engines import spatial_engine
        spatial = spatial_engine.get_instance(player.game.world)
        if len(dims) <= 1:
            length = int(dims[0]) if dims else 1
            dx, dy, dz = construction_utils.get_offset_scalars(direction)
            cx, cy, cz = player.room.x, player.room.y, player.room.z
            for i in range(1, length + 1):
                room = spatial.get_room(cx + dx*i, cy + dy*i, cz + dz*i)
                if room: targets.append(room)
        elif len(dims) == 2:
            width, height = int(dims[0]), int(dims[1])
            off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
            if off_x is None:
                off_x, off_y = player.room.x - (width//2), player.room.y - (height//2)
            for y in range(off_y, off_y + height):
                for x in range(off_x, off_x + width):
                    room = spatial.get_room(x, y, player.room.z)
                    if room: targets.append(room)
    else:
        if args in player.game.world.rooms: targets.append(player.game.world.rooms[args])
        else: player.send_line("Room not found."); return

    if not targets: return
    start_room = player.game.world.start_room or list(player.game.world.rooms.values())[0]
    if start_room in targets: targets.remove(start_room)
    
    target_ids = {r.id for r in targets}
    for r in player.game.world.rooms.values():
        to_rem = [d for d, tid in r.exits.items() if tid in target_ids]
        for d in to_rem: del r.exits[d]; r.dirty = True

    for room in targets:
        for p in list(room.players):
            p.room = start_room
            start_room.players.append(p)
            room.players.remove(p)
            from logic.commands.info.exploration import look
            look(p, "")
        if room.id in player.game.world.rooms:
            if not hasattr(player.game.world, 'deleted_rooms'): player.game.world.deleted_rooms = set()
            player.game.world.deleted_rooms.add(room.id)
            del player.game.world.rooms[room.id]
            construction_utils.scrub_room_from_memory(player.game, room.id)
            
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    player.send_line(f"Deleted {len(targets)} rooms.")

@command_manager.register("@prunemap", admin=True)
def prune_map(player, args):
    """Deletes overlapping rooms (same X,Y,Z)."""
    target_zone = args if args else player.room.zone_id
    columns = {}
    for r in player.game.world.rooms.values():
        if target_zone != 'all' and r.zone_id != target_zone: continue
        coord = (r.x, r.y, r.z)
        if coord not in columns: columns[coord] = []
        columns[coord].append(r)
        
    deleted_count = 0
    for rooms in columns.values():
        if len(rooms) > 1:
            rooms.sort(key=lambda r: mapper.TERRAIN_PRIORITY.index(r.terrain) if r.terrain in mapper.TERRAIN_PRIORITY else 999)
            for victim in rooms[1:]:
                if victim.id in player.game.world.rooms:
                    if not hasattr(player.game.world, 'deleted_rooms'): player.game.world.deleted_rooms = set()
                    player.game.world.deleted_rooms.add(victim.id)
                    del player.game.world.rooms[victim.id]
                    construction_utils.scrub_room_from_memory(player.game, victim.id)
                    deleted_count += 1
    if deleted_count > 0:
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
    player.send_line(f"Pruned {deleted_count} rooms in '{target_zone}'.")

@command_manager.register("@merge", admin=True)
def merge_rooms(player, args):
    """Combines overlapping rooms into current."""
    candidates = [r for r in player.game.world.rooms.values() if r.zone_id == player.room.zone_id and r.x == player.room.x and r.y == player.room.y and r != player.room]
    if not candidates: return
    target = player.room
    for victim in candidates:
        for d, dest in victim.exits.items():
            if d not in target.exits: target.exits[d] = dest
        if target.terrain == "default": target.terrain = victim.terrain
        for p in list(victim.players): p.room = target; target.players.append(p)
        for m in list(victim.monsters): m.room = target; target.monsters.append(m)
        target.items.extend(victim.items)
        if victim.id in player.game.world.rooms:
            if not hasattr(player.game.world, 'deleted_rooms'): player.game.world.deleted_rooms = set()
            player.game.world.deleted_rooms.add(victim.id)
            del player.game.world.rooms[victim.id]
            construction_utils.scrub_room_from_memory(player.game, victim.id)
    from logic.engines import spatial_engine
    spatial_engine.invalidate()
    player.send_line("Merge complete.")

@command_manager.register("@flatten", admin=True)
def flatten(player, args):
    """Forces grid to specific Z-level."""
    parts = args.split()
    if len(parts) < 3: return
    try:
        tz, w, h = int(parts[0]), int(parts[1]), int(parts[2])
    except: return
    direction = parts[3] if len(parts) > 3 else None
    off_x, off_y = construction_utils.get_directional_offsets(player, w, h, direction)
    if off_x is None: off_x, off_y = player.room.x - w//2, player.room.y - h//2
    count = 0
    for r in player.game.world.rooms.values():
        if off_x <= r.x < off_x + w and off_y <= r.y < off_y + h:
            if r.z != tz: r.z = tz; count += 1
    if count > 0:
        from logic.engines import spatial_engine
        spatial_engine.invalidate()
    player.send_line(f"Flattened {count} rooms.")
