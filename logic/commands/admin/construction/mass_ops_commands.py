"""
logic/commands/admin/construction/mass_ops_commands.py
Bulk operations: Copying rooms, Mass editing, and Text replacement.
"""
import logic.handlers.command_manager as command_manager
import logic.commands.admin.construction.utils as construction_utils
from logic.commands import movement_commands as movement
from logic.commands.info_commands import look
from utilities import mapper

@command_manager.register("@copyroom", admin=True, category="admin_building")
def copy_room(player, args):
    """Copy room attributes to a neighbor or create a line."""
    if not args:
        player.send_line("Usage: @copyroom <direction> [length]")
        return
        
    parts = args.split()
    direction = construction_utils.parse_direction(parts[0])
    length = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    
    src = player.room
    s_name, s_desc, s_zone, s_terr = src.name, src.description, src.zone_id, src.terrain
    
    if player in src.players: src.players.remove(player)
    
    count = 0
    for _ in range(length):
        curr = player.room
        if direction in curr.exits:
            nxt = curr.exits[direction]
            construction_utils.update_room(nxt, zone_id=s_zone, terrain=s_terr, name=s_name, desc=s_desc)
            player.room = nxt
            count += 1
        else:
            nr = movement.dig_room(player, direction, s_name, terrain=s_terr)
            if nr:
                nr.description, nr.zone_id = s_desc, s_zone
                player.room = nr
                count += 1
            else: break
            
    if player not in player.room.players: player.room.players.append(player)
    player.send_line(f"Copied {count} rooms {direction}.")
    look(player, "")

@command_manager.register("@massedit", admin=True, category="admin_building")
def mass_edit(player, args):
    """Bulk edit rooms by zone, terrain, or name match."""
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
    scope, s_arg, attr, val = parts[0].lower(), parts[1], parts[2].lower(), " ".join(parts[3:])
    
    count = 0
    for r in player.game.world.rooms.values():
        match = False
        if scope == "zone": match = (r.zone_id == s_arg)
        elif scope == "terrain": match = (r.terrain == s_arg)
        elif scope == "name_match": match = (s_arg.lower() in r.name.lower())
        
        if match:
            if attr == "name": r.name = val
            elif attr == "desc": r.description = val
            elif attr == "terrain": r.terrain = val
            elif attr == "zone": r.zone_id = val.lower()
            elif attr == "z": 
                try: r.z = int(val)
                except: pass
            count += 1
    player.send_line(f"Updated {count} rooms.")

@command_manager.register("@replace", admin=True, category="admin_building")
def replace_text(player, args):
    """Search and replace text in room descriptions/names in current zone."""
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
    player.send_line(f"Replaced text in {count} fields.")
