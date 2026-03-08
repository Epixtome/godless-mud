import logic.handlers.command_manager as command_manager
from models import Room
from logic.core.world import get_room_id
from logic.common import get_reverse_direction
from utilities.colors import Colors
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@dig", admin=True)
def dig(player, args):
    """Dig a new room in a direction."""
    if not args:
        player.send_line("Usage: @dig <direction> [room_name]")
        return
        
    parts = args.split(maxsplit=1)
    direction = parts[0].lower()
    name = parts[1] if len(parts) > 1 else "New Room"
    
    # Validate direction
    valid_dirs = ['north', 'south', 'east', 'west', 'up', 'down']
    if direction not in valid_dirs:
        player.send_line(f"Invalid direction. Use: {', '.join(valid_dirs)}")
        return
    
    if direction in player.room.exits:
        player.send_line("There is already an exit there!")
        return
        
    from logic.commands import movement_commands as movement
    new_room = movement.dig_room(player, direction, name)
    
    if new_room:
        # Apply Brush Settings if active
        if hasattr(player, 'brush_settings') and player.brush_settings:
            z_id = player.brush_settings.get('zone')
            if z_id and z_id not in player.game.world.zones:
                from models import Zone
                player.game.world.zones[z_id] = Zone(z_id, f"Zone {z_id}")
                player.send_line(f"Created new zone entry: '{z_id}'.")

            construction_utils.update_room(
                new_room,
                zone_id=player.brush_settings.get('zone'),
                terrain=player.brush_settings.get('terrain'),
                name=player.brush_settings.get('name')
            )

        # Auto-stitch if enabled
        if getattr(player, 'autostitch', False):
            construction_utils.stitch_room(new_room, player.game.world)

        player.send_line(f"Dug {direction} to {new_room.name} ({new_room.id}).")
        player.room.broadcast(f"{player.name} reshapes reality, creating a path {direction}.")

@command_manager.register("@autodig", admin=True)
def autodig(player, args):
    """
    Toggle auto-dig mode.
    Usage: @autodig [palette_id | copy] (Use @auto stitch to toggle linking)
    """
    if not hasattr(player, 'autodig'):
        player.autodig = False
    
    if args:
        mode = args.strip()
        player.autodig = True
        player.autodig_palette = mode
        if mode.lower() == 'copy':
            player.send_line("Auto-dig enabled (Copy Mode). New rooms will inherit attributes from the previous room.")
        else:
            player.send_line(f"Auto-dig enabled (Palette: '{mode}').")
    else:
        player.autodig = not player.autodig
        if hasattr(player, 'autodig_palette'):
            del player.autodig_palette
        
        state = "enabled" if player.autodig else "disabled"
        player.send_line(f"Auto-dig {state}.")

@command_manager.register("@link", admin=True)
def link_room(player, args):
    """
    Link the current room to another room.
    Usage: @link <direction> [target_room_id] [one-way]
    If target_room_id is omitted, attempts to link to the spatial neighbor.
    """
    if not args:
        player.send_line("Usage: @link <direction> [target_room_id] [one-way]")
        return
    
    parts = args.split()
    direction = parts[0].lower()
    
    target_str = None
    one_way = False
    
    # Parse arguments (Handle multi-word names)
    remaining = parts[1:]
    if remaining:
        # Check for one-way flag at the end
        if remaining[-1].lower() in ["one-way", "single", "oneway"]:
            one_way = True
            remaining.pop()
        
        if remaining:
            target_str = " ".join(remaining)
    
    target_room = None
    
    if target_str:
        target_room = construction_utils.find_room(player.game.world, target_str)
        if not target_room:
            player.send_line(f"Target room '{target_str}' not found.")
            return
    else:
        # Auto-detect neighbor based on coordinates
        x, y, z = player.room.x, player.room.y, player.room.z
        dx, dy, dz = 0, 0, 0
        
        if direction == 'north': dy = -1
        elif direction == 'south': dy = 1
        elif direction == 'east': dx = 1
        elif direction == 'west': dx = -1
        elif direction == 'up': dz = 1
        elif direction == 'down': dz = -1
        else:
            player.send_line("Invalid direction for auto-link. Specify target ID.")
            return
            
        from logic.engines import spatial_engine
        spatial = spatial_engine.get_instance(player.game.world)
        
        # Scan +/- 5 Z for target
        target_room = construction_utils.find_room_at_fuzzy_z(spatial, x + dx, y + dy, z + dz)
        
        if not target_room:
            player.send_line(f"No room found {direction} to link to.")
            return

    # Perform Link
    player.room.add_exit(direction, target_room)
    msg = f"Linked {direction} to {target_room.name} ({target_room.id})"
    
    # Reciprocal Link
    if not one_way:
        rev = get_reverse_direction(direction)
        if rev:
            target_room.add_exit(rev, player.room)
            msg += f" and back ({rev})"
    
    player.send_line(f"{msg}.")

@command_manager.register("@unlink", admin=True)
def unlink_room(player, args):
    """
    Remove an exit. Unlinks both ways by default.
    Usage: @unlink <direction> [one-way]
    """
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
                msg += f" and reciprocal exit {rev} in target room"
        
        player.send_line(f"{msg}.")
    else:
        player.send_line("No exit in that direction.")

@command_manager.register("@dig_portal", admin=True)
def dig_portal(player, args):
    """
    Digs a portal to a new room in a 'pocket dimension' (far coordinates).
    Useful for interiors that are larger than their exterior.
    Usage: @dig_portal <enter_dir> <exit_dir> [room_name]
    Example: @dig_portal enter out My House
    """
    if not args:
        player.send_line("Usage: @dig_portal <enter_dir> <exit_dir> [room_name]")
        return
        
    parts = args.split()
    if len(parts) < 2:
        player.send_line("Usage: @dig_portal <enter_dir> <exit_dir> [room_name]")
        return
        
    enter_dir = parts[0].lower()
    exit_dir = parts[1].lower()
    room_name = " ".join(parts[2:]) if len(parts) > 2 else "Interior"
    zone_id = player.room.zone_id
    
    # Determine new coordinates (Shift X/Y by 5000 to ensure isolation)
    start_x, start_y, start_z = player.room.x, player.room.y, player.room.z
    target_x = start_x + 5000
    target_y = start_y + 5000
    target_z = start_z
    
    # Check for collision and shift until free
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    while spatial.get_room(target_x, target_y, target_z):
        target_x += 10 
    
    # Create Room
    new_id = get_room_id(zone_id, target_x, target_y, target_z)
    new_room = Room(new_id, room_name, "An interior space.")
    new_room.x, new_room.y, new_room.z = target_x, target_y, target_z
    new_room.zone_id = zone_id
    new_room.terrain = "indoors"
    
    player.game.world.rooms[new_id] = new_room
    spatial.rebuild() # Update index
    
    # Link
    player.room.exits[enter_dir] = new_room
    new_room.exits[exit_dir] = player.room
    
    player.send_line(f"Created portal '{enter_dir}' to {new_room.name} (Zone: {zone_id}).")
    
    # Teleport player inside
    player.room.players.remove(player)
    player.room = new_room
    new_room.players.append(player)
    from logic.commands import info_commands as information
    information.look(player, "")

@command_manager.register("@auto", admin=True)
def auto_toggle(player, args):
    """
    Toggles construction auto-modes.
    Usage: @auto [on|off] | @auto stitch
    """
    # Initialize if missing
    if not hasattr(player, 'autodig'): player.autodig = False
    if not hasattr(player, 'autopaste'): player.autopaste = False
    if not hasattr(player, 'autostitch'): player.autostitch = False

    # Determine target state
    if args:
        arg = args.lower()
        if arg == "stitch":
            player.autostitch = not player.autostitch
            state = "enabled" if player.autostitch else "disabled"
            player.send_line(f"Auto-stitch {state} (4-way linking on dig).")
            return
        elif arg == "on":
            new_state = True
        elif arg == "off":
            new_state = False
        else:
            player.send_line("Usage: @auto [on|off] | @auto stitch")
            return
    else:
        # If either is on, turn both off. If both off, turn both on.
        if player.autodig or player.autopaste:
            new_state = False
        del player.autodig_palette
    
    state_str = "enabled" if new_state else "disabled"
    stitch_str = " (Stitch: ON)" if player.autostitch else ""
    player.send_line(f"Auto-dig and Auto-paste {state_str}{stitch_str}.")
    
    if new_state and (not hasattr(player, 'brush_settings') or not player.brush_settings):
        player.send_line("Warning: Brush is empty. Auto-paste/dig may rely on brush settings.")

@command_manager.register("@building", admin=True)
def building_help(player, args):
    """Shows a guide for building commands."""
    player.send_line(f"\n{Colors.BOLD}--- Building Commands ---{Colors.RESET}")
    
    cmds = [
        ("@dig <dir> [name]", "Create a room in a direction."),
        ("@autodig [palette|copy]", "Toggle auto-digging when walking."),
        ("@paint <w> <h> [name] [dir]", "Create/Update a grid of rooms."),
        ("@gen_grid <zone> <w> <h> [terr] [name] [dir]", "Generate a new zone grid."),
        ("@brush <attr> <val>|copy", "Set properties for dig/paint."),
        ("@paste", "Apply brush to current room."),
        ("@link <dir> [id] [one-way]", "Link exit to a room."),
        ("@unlink <dir>", "Remove an exit."),
        ("@copyroom <dir> [len]", "Copy current room attributes in a line."),
        ("@deleteroom [id]", "Delete a room."),
        ("@stitch <zone> <anc> <tgt> <dir>", "Connect two zones."),
        ("@snapzone <mov> <anc> <dir>", "Move a zone to connect to anchor."),
        ("@shiftzone <zone> <x> <y> <z>", "Move a zone by offset."),
        ("@dig_portal <in> <out> [name]", "Create a pocket dimension room."),
        ("@prunemap [zone]", "Delete overlapping rooms (fix map glitches)."),
        ("@flatten <z> <w> <h> [dir]", "Force rooms in area to Z-level."),
        ("@merge", "Combine overlapping rooms at current location."),
        ("@vision", "Show stacked rooms at current location."),
        ("@setlayer <z>", "Move current room to Z-level."),
        ("@audit [zone]", "Check for map errors."),
        ("@fixids [zone]", "Rename rooms to match coords.")
    ]
    
    for c, d in cmds:
        player.send_line(f"{Colors.CYAN}{c:<40}{Colors.RESET} {d}")
        
    player.send_line(f"\n{Colors.YELLOW}Directions:{Colors.RESET} n, s, e, w, ne, nw, se, sw")
    player.send_line(f"{Colors.YELLOW}Example:{Colors.RESET} @gen_grid swamp 10 10 swamp 'Dark Swamp' east")