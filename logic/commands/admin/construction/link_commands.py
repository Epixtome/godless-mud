"""
logic/commands/admin/construction/link_commands.py
Commands for connecting rooms: Linking, Portals, and Unlinking.
"""
import logic.handlers.command_manager as command_manager
from logic.common import get_reverse_direction
from logic.core.world import get_room_id
from models import Room
from logic.engines import spatial_engine
from logic.commands.info_commands import look
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@link", admin=True, category="admin_building")
def link_room(player, args):
    """Link the current room to another room."""
    if not args:
        player.send_line("Usage: @link <direction> [target_room_id] [one-way]")
        return
    parts = args.split()
    direction = parts[0].lower()
    target_str, one_way = None, False
    rem = parts[1:]
    if rem:
        if rem[-1].lower() in ["one-way", "single", "oneway"]:
            one_way = True
            rem.pop()
        if rem: target_str = " ".join(rem)
    
    target_room = None
    if target_str:
        target_room = construction_utils.find_room(player.game.world, target_str)
        if not target_room:
            player.send_line(f"Target room '{target_str}' not found.")
            return
    else:
        # Auto-detect neighbor
        spatial = spatial_engine.get_instance(player.game.world)
        dx, dy, dz = construction_utils.get_offset_scalars(direction)
        if dx is None and dy is None and dz is None:
            player.send_line("Invalid direction.")
            return
        target_room = construction_utils.find_room_at_fuzzy_z(spatial, player.room.x + dx, player.room.y + dy, player.room.z + dz)
        if not target_room:
            player.send_line(f"No room found {direction} to link to.")
            return

    player.room.add_exit(direction, target_room)
    msg = f"Linked {direction} to {target_room.name} ({target_room.id})"
    if not one_way:
        rev = get_reverse_direction(direction)
        if rev:
            target_room.add_exit(rev, player.room)
            msg += f" and back ({rev})"
    player.send_line(f"{msg}.")

@command_manager.register("@unlink", admin=True, category="admin_building")
def unlink_room(player, args):
    """Remove an exit. Unlinks both ways by default."""
    if not args:
        player.send_line("Usage: @unlink <direction> [one-way]")
        return
    parts = args.split()
    direction = parts[0].lower()
    one_way = len(parts) > 1 and parts[1].lower() in ["one-way", "single", "oneway"]
    
    if direction in player.room.exits:
        target_id = player.room.exits[direction]
        target_room = player.game.world.rooms.get(target_id)
        del player.room.exits[direction]
        player.room.dirty = True
        msg = f"Removed exit {direction}"
        if not one_way and target_room:
            rev = get_reverse_direction(direction)
            if rev and rev in target_room.exits and target_room.exits[rev] == player.room.id:
                del target_room.exits[rev]
                target_room.dirty = True
                msg += f" and reciprocal exit {rev}"
        player.send_line(f"{msg}.")
    else:
        player.send_line("No exit in that direction.")

@command_manager.register("@dig_portal", admin=True, category="admin_building")
def dig_portal(player, args):
    """Create a portal to a distant pocket dimension."""
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: @dig_portal <enter_dir> <exit_dir> [name]")
        return
    enter_dir, exit_dir = parts[0].lower(), parts[1].lower()
    name = " ".join(parts[2:]) if len(parts) > 2 else "Interior"
    tx, ty, tz = player.room.x + 5000, player.room.y + 5000, player.room.z
    spatial = spatial_engine.get_instance(player.game.world)
    if not spatial:
        player.send_line("Spatial index unavailable.")
        return
    while spatial.get_room(tx, ty, tz): tx += 10
    
    nid = get_room_id(player.room.zone_id, tx, ty, tz)
    nr = Room(nid, name, "An interior space.")
    nr.x, nr.y, nr.z, nr.zone_id, nr.terrain = tx, ty, tz, player.room.zone_id, "indoors"
    player.game.world.rooms[nid] = nr
    spatial.rebuild()
    player.room.exits[enter_dir] = nr
    nr.exits[exit_dir] = player.room
    
    player.send_line(f"Created portal '{enter_dir}' to {nr.name}.")
    player.room.players.remove(player)
    player.room = nr
    nr.players.append(player)
    look(player, "")
