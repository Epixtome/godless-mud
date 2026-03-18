"""
logic/commands/admin/construction/edit.py
Module for manual and bulk editing of room properties.
"""
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from models import Zone
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@set", admin=True, category="admin_building")
def set_property(player, args):
    """
    Set properties of the current room or target.
    Usage: @set <attr> <value>
    Attrs: name, desc, terrain, zone, symbol, elevation
    """
    if not args:
        player.send_line("Usage: @set <attr> <value>. Categories: room, item, mob.")
        return
        
    parts = args.split(maxsplit=1)
    attr = parts[0].lower()
    val = parts[1] if len(parts) > 1 else ""

    # Delegate to sharded logic if Category is specified
    if attr in ["item", "mob", "class"]:
        # These are handled in the main editor.py dispatcher
        # But we could potentially shard them here too.
        # For now, let's just handle 'room' or 'direct attr'
        return
    
    # Direct Room attribute setting
    r = player.room
    if attr == "name": r.name = val
    elif attr == "desc": r.description = val
    elif attr == "terrain": 
        construction_utils.update_room(r, terrain=val)
    elif attr == "zone":
        val = val.lower()
        r.zone_id = val
        if val not in player.game.world.zones:
            player.game.world.zones[val] = Zone(val, f"Zone {val}")
    elif attr == "elevation":
        try: r.elevation = int(val)
        except: pass
    elif attr == "symbol":
        r.symbol = val
    else:
        player.send_line(f"Unknown attribute: {attr}")
        return

    r.dirty = True
    player.send_line(f"Room {attr} updated.")

@command_manager.register("@massedit", admin=True, category="admin_building")
def mass_edit(player, args):
    """
    Bulk edit rooms.
    Usage: @massedit <scope> <scope_arg> <attr> <value>
    Scopes: zone, terrain, name_match
    """
    if not args:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
        
    parts = args.split()
    if len(parts) < 4:
        player.send_line("Usage: @massedit <scope> <scope_arg> <attr> <value>")
        return
        
    scope, scope_arg, attr, value = parts[0].lower(), parts[1], parts[2].lower(), " ".join(parts[3:])
    
    targets = []
    for r in player.game.world.rooms.values():
        match = False
        if scope == "zone" and r.zone_id == scope_arg: match = True
        elif scope == "terrain" and r.terrain == scope_arg: match = True
        elif scope == "name_match" and scope_arg.lower() in r.name.lower(): match = True
        if match: targets.append(r)
            
    if not targets:
        player.send_line("No rooms matched criteria.")
        return
        
    for r in targets:
        if attr == "name": r.name = value
        elif attr == "desc": r.description = value
        elif attr == "terrain": construction_utils.update_room(r, terrain=value)
        elif attr == "zone":
            value = value.lower()
            r.zone_id = value
            if value not in player.game.world.zones:
                player.game.world.zones[value] = Zone(value, f"Zone {value}")
        elif attr == "z":
            try: r.z = int(value)
            except: pass
        r.dirty = True
        
    player.send_line(f"Updated {len(targets)} rooms.")

@command_manager.register("@replace", admin=True, category="admin_building")
def replace_text(player, args):
    """Search and replace text in current zone."""
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
            if count > 0: r.dirty = True
    player.send_line(f"Replaced {count} instances in zone '{current_zone}'.")
