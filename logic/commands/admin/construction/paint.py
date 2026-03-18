"""
logic/commands/admin/construction/paint.py
Module for brush settings, grid painting, and auto-modes.
"""
import logic.handlers.command_manager as command_manager
from models import Room, Zone
from logic.core.world import get_room_id
from logic.common import get_reverse_direction
from logic.engines import spatial_engine
from utilities.colors import Colors
from utilities.mapper import TERRAIN_MAP
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@brush", admin=True, category="admin_building")
def brush(player, args):
    """
    Configure the painting brush.
    Usage: @brush <attr> <value> | @brush clear | @brush copy
    """
    if not hasattr(player, 'brush_settings'):
        player.brush_settings = {}

    # Logic for selecting attributes
    if args:
        parts = args.split(maxsplit=1)
        sub = parts[0].lower()
        
        if sub == "copy":
            r = player.room
            player.brush_settings = {
                'zone': r.zone_id,
                'terrain': r.terrain,
                'name': r.name,
                'desc': r.description
            }
            player.send_line("Copied current room attributes to brush.")
        elif sub == "clear":
            player.brush_settings = {}
            player.send_line("Brush cleared.")
        elif len(parts) >= 2:
            attr, val = parts[0].lower(), parts[1].strip()
            if attr in ["zone", "terrain", "name", "desc"]:
                if attr == "zone": val = val.lower()
                player.brush_settings[attr] = val
                player.send_line(f"Brush {attr} set to '{val}'.")
            else:
                player.send_line("Invalid brush attribute. Use: zone, terrain, name, desc.")
        else:
            player.send_line("Usage: @brush <attr> <value> | copy | clear")

    # Always show nice output
    bs = player.brush_settings
    terrain = bs.get('terrain', 'default')
    symbol = TERRAIN_MAP.get(terrain, ".")
    
    output = []
    output.append(f"\n{Colors.BOLD}{Colors.DGREY}┌───[ ACTIVE BRUSH ]───────────────────┐{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.DGREY}│ {Colors.WHITE}Symbol:  {symbol} {Colors.DGREY:<24} │{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.DGREY}│ {Colors.WHITE}Terrain: {terrain:<25} {Colors.DGREY}│{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.DGREY}│ {Colors.WHITE}Zone:    {bs.get('zone', 'Current'):<25} {Colors.DGREY}│{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.DGREY}│ {Colors.WHITE}Name:    {bs.get('name', 'None'):<25} {Colors.DGREY}│{Colors.RESET}")
    output.append(f"{Colors.BOLD}{Colors.DGREY}└──────────────────────────────────────┘{Colors.RESET}")
    player.send_line("\n".join(output))

@command_manager.register("@paint", admin=True, category="admin_building")
def paint(player, args):
    """
    Grid-paint rooms. Defaults to 1x1 at current position if no args.
    Usage: @paint [width] [height] [room_name] [direction]
    Examples: @paint, @paint west, @paint 3 3, @paint 5 5 temple east
    """
    parts = args.split() if args else []
    width, height = 1, 1
    direction = None
    name_override = None

    # Parsing logic
    valid_dirs = ['n','s','e','w','ne','nw','se','sw','north','south','east','west','up','down']
    
    # 1. Look for Width/Height at start
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        width = int(parts.pop(0))
        height = int(parts.pop(0))

    # 2. Look for Direction at tail or in parts
    for i, p in enumerate(parts):
        if p.lower() in valid_dirs:
            direction = parts.pop(i)
            break

    # 3. Remaining parts are the name override
    if parts:
        name_override = " ".join(parts)
    bs = getattr(player, 'brush_settings', {}) # Legacy sync
    
    # Try to get from builder_state first (Modern Architect)
    if hasattr(player, 'builder_state') and player.builder_state["active"]:
        from logic.commands.admin.construction.builder_state import _load_kit
        k_data = _load_kit(player.builder_state["kit"])
        if k_data:
            idx = player.builder_state["stencil_index"]
            if 0 < idx <= len(k_data["templates"]):
                stencil = k_data["templates"][idx-1]
                # Merge into a virtual brush
                bs = {**bs, **stencil}

    final_name = name_override or bs.get('name') or player.room.name
    final_zone = bs.get('zone') or player.room.zone_id
    final_terrain = bs.get('terrain') or player.room.terrain
    final_desc = bs.get('desc') or player.room.description
    
    # Coordinates
    off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
    start_x = off_x if off_x is not None else player.room.x - (width // 2)
    start_y = off_y if off_y is not None else player.room.y - (height // 2)
    target_z = construction_utils.get_terrain_z(final_terrain, player.room.z)
    
    spatial = spatial_engine.get_instance(player.game.world)
    created, updated = 0, 0
    
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            room = construction_utils.find_room_at_fuzzy_z(spatial, x, y, target_z)
            if room:
                construction_utils.update_room(room, zone_id=bs.get('zone'), terrain=bs.get('terrain'), name=name_override or bs.get('name'), desc=bs.get('desc'))
                updated += 1
            else:
                new_id = get_room_id(final_zone, x, y, player.room.z)
                nr = Room(new_id, final_name, final_desc)
                nr.x, nr.y, nr.z, nr.zone_id, nr.terrain = x, y, target_z, final_zone, final_terrain
                player.game.world.rooms[new_id] = nr
                created += 1
    
    if created: 
        spatial_engine.invalidate()
        if spatial:
            spatial.rebuild()
    
    # Auto-stitch
    links = 0
    dirs = {"north":(0,-1,0), "south":(0,1,0), "east":(1,0,0), "west":(-1,0,0)}
    for y in range(start_y - 1, start_y + height + 1):
        for x in range(start_x - 1, start_x + width + 1):
            r = construction_utils.find_room_at_fuzzy_z(spatial, x, y, target_z)
            if not r: continue
            for d, (dx, dy, dz) in dirs.items():
                if d in r.exits: continue
                n = construction_utils.find_room_at_fuzzy_z(spatial, x+dx, y+dy, target_z+dz, 0)
                if n:
                    r.add_exit(d, n)
                    rev = get_reverse_direction(d)
                    if rev: n.add_exit(rev, r)
                    links += 1
                    
    player.send_line(f"Painted {created} new, updated {updated}. Links: {links}.")

@command_manager.register("@auto", admin=True, category="admin_building")
def auto_modes(player, args):
    """
    Toggle auto-modes.
    Usage: @auto [dig|paste|stitch] [on|off]
    """
    if not args:
        d = getattr(player, 'autodig', False)
        p = getattr(player, 'autopaste', False)
        s = getattr(player, 'autostitch', False)
        player.send_line(f"Auto-Modes: Dig:{d}, Paste:{p}, Stitch:{s}")
        return
        
    parts = args.split()
    mode = parts[0].lower()
    val = (parts[1].lower() == 'on') if len(parts) > 1 else None
    
    if mode == "dig":
        player.autodig = val if val is not None else not getattr(player, 'autodig', False)
        player.send_line(f"Auto-dig: {player.autodig}")
    elif mode == "paste":
        player.autopaste = val if val is not None else not getattr(player, 'autopaste', False)
        player.send_line(f"Auto-paste: {player.autopaste}")
    elif mode == "stitch":
        player.autostitch = val if val is not None else not getattr(player, 'autostitch', False)
        player.send_line(f"Auto-stitch: {player.autostitch}")
    else:
        player.send_line("Modes: dig, paste, stitch")
