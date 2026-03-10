import logic.handlers.command_manager as command_manager
from models import Room
from logic.core.world import get_room_id
from logic.common import get_reverse_direction
from utilities.mapper import TERRAIN_HEIGHTS
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@brush", admin=True)
def brush(player, args):
    """
    Configure the painting brush for digging.
    Usage: @brush <attr> <value> | @brush clear | @brush copy
    Attrs: zone, terrain, name
    """
    if not hasattr(player, 'brush_settings'):
        player.brush_settings = {}
        
    if not args:
        player.send_line(f"Current Brush: {player.brush_settings}")
        return
        
    if args.lower() == "copy":
        player.brush_settings = {
            'zone': player.room.zone_id,
            'terrain': player.room.terrain,
            'name': player.room.name,
            'desc': player.room.description
        }
        player.send_line("Copied current room attributes to brush.")
        return
        
    if args.lower() == "clear":
        player.brush_settings = {}
        player.send_line("Brush cleared.")
        return
        
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        player.send_line("Usage: @brush <attr> <value>")
        return
        
    attr = parts[0].lower()
    val = parts[1].strip()
    
    if attr == "zone":
        val = val.lower()
    
    if attr in ["zone", "terrain", "name"]:
        player.brush_settings[attr] = val
        player.send_line(f"Brush {attr} set to '{val}'.")
    else:
        player.send_line("Invalid brush attribute. Use: zone, terrain, name.")

@command_manager.register("@paste", admin=True)
def paste_room(player, args):
    """
    Applies brush settings to the current room or a neighbor.
    Usage: @paste [direction | room_id]
    """
    if not hasattr(player, 'brush_settings') or not player.brush_settings:
        player.send_line("Brush is empty. Use '@brush copy' first.")
        return
        
    target_room = player.room
    
    if args:
        arg = args.lower()
        # 1. Try Direction
        if arg in player.room.exits:
            target_room = player.room.exits[arg]
        # 2. Try Room ID
        elif arg in player.game.world.rooms:
            target_room = player.game.world.rooms[arg]
        else:
            player.send_line(f"Target '{args}' not found (not a direction or room ID).")
            return

    r = target_room
    bs = player.brush_settings
    
    z_id = bs.get('zone')
    if z_id and z_id not in player.game.world.zones:
        from models import Zone
        player.game.world.zones[z_id] = Zone(z_id, f"Zone {z_id}")
        player.send_line(f"Created new zone entry: '{z_id}'.")

    construction_utils.update_room(
        r,
        zone_id=bs.get('zone'),
        terrain=bs.get('terrain'),
        name=bs.get('name'),
        desc=bs.get('desc')
    )

    player.send_line(f"Pasted brush attributes to {r.name} ({r.id}).")

@command_manager.register("@autopaste", admin=True)
def autopaste(player, args):
    """
    Toggle auto-paste mode.
    When enabled, moving into a room applies the current brush settings to it.
    """
    if not hasattr(player, 'autopaste'):
        player.autopaste = False
    
    player.autopaste = not player.autopaste
    state = "enabled" if player.autopaste else "disabled"
    player.send_line(f"Auto-paste {state}.")
    
    if player.autopaste and (not hasattr(player, 'brush_settings') or not player.brush_settings):
        player.send_line("Warning: Brush is empty. Use '@brush copy' or '@brush <attr> <val>' first.")

@command_manager.register("@auto", admin=True)
def auto_toggle(player, args):
    """
    Toggles all construction auto-modes (dig and paste).
    Usage: @auto [on|off]
    """
    # Initialize if missing
    if not hasattr(player, 'autodig'): player.autodig = False
    if not hasattr(player, 'autopaste'): player.autopaste = False

    # Determine target state
    if args:
        arg = args.lower()
        if arg == "on":
            new_state = True
        elif arg == "off":
            new_state = False
        else:
            player.send_line("Usage: @auto [on|off]")
            return
    else:
        # If either is on, turn both off. If both off, turn both on.
        if player.autodig or player.autopaste:
            new_state = False
        else:
            new_state = True

    player.autodig = new_state
    player.autopaste = new_state
    
    # Clean up autodig palette if disabling
    if not new_state and hasattr(player, 'autodig_palette'):
        del player.autodig_palette
    
    state_str = "enabled" if new_state else "disabled"
    player.send_line(f"Auto-dig and Auto-paste {state_str}.")
    
    if new_state and (not hasattr(player, 'brush_settings') or not player.brush_settings):
        player.send_line("Warning: Brush is empty. Auto-paste/dig may rely on brush settings.")
        
    from logic.commands.info_commands import look
    look(player, "")

@command_manager.register("@paint", admin=True)
def paint_zone(player, args):
    """
    Creates or updates a grid of rooms.
    Usage: @paint <width> <height> [room_name] [direction]
    """
    if not args:
        player.send_line("Usage: @paint <width> <height> [room_name] [direction]")
        return
        
    parts = args.split()
    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError:
        player.send_line("Width and Height must be integers.")
        return
        
    # Check for direction in last arg
    direction = None
    possible_dir = parts[-1].lower().strip()
    if possible_dir in ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw', 'north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest']:
        direction = possible_dir
        parts = parts[:-1]

    # Determine explicit overrides (Command Args > Brush > None)
    arg_name = " ".join(parts[2:]) if len(parts) > 2 else None
    
    brush_zone = None
    brush_terrain = None
    brush_name = None
    brush_desc = None
    
    if hasattr(player, 'brush_settings') and player.brush_settings:
        brush_zone = player.brush_settings.get('zone')
        brush_terrain = player.brush_settings.get('terrain')
        brush_name = player.brush_settings.get('name')
        brush_desc = player.brush_settings.get('desc')
    
    # Final Target Values (For NEW rooms)
    # Priority: Arg Name > Brush Name > Current Room Name
    final_name = arg_name or brush_name or player.room.name
    final_zone = brush_zone or player.room.zone_id
    final_terrain = brush_terrain or player.room.terrain
    final_desc = brush_desc or player.room.description
    
    if final_zone and final_zone not in player.game.world.zones:
        from models import Zone
        player.game.world.zones[final_zone] = Zone(final_zone, f"Zone {final_zone}")
        player.send_line(f"Created new zone entry: '{final_zone}'.")
    
    # Calculate Start Coords
    off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
    if off_x is not None:
        start_x, start_y = off_x, off_y
    else:
        # Default: Center around player
        start_x = player.room.x - (width // 2)
        start_y = player.room.y - (height // 2)
        
    z = player.room.z
    
    # Determine target Z based on terrain
    target_z = construction_utils.get_terrain_z(final_terrain, z)
    
    created = 0
    updated = 0
    
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)

    # Create/Update rooms
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            # Scan for existing room in column (+/- 5 Z) to handle slopes
            room = construction_utils.find_room_at_fuzzy_z(spatial, x, y, target_z)
            
            if room:
                # Update existing room ONLY with explicit overrides
                construction_utils.update_room(
                    room,
                    zone_id=brush_zone,
                    terrain=brush_terrain,
                    name=arg_name or brush_name,
                    desc=brush_desc
                )
                
                updated += 1
            else:
                # Create Room
                new_id = get_room_id(final_zone, x, y, z)
                new_room = Room(new_id, final_name, final_desc)
                new_room.x, new_room.y, new_room.z = x, y, target_z
                new_room.zone_id = final_zone
                new_room.terrain = final_terrain
                
                player.game.world.rooms[new_id] = new_room
                created += 1
            
    # Rebuild index to include new rooms
    if created > 0:
        spatial_engine.invalidate()
        spatial.rebuild()
    
    # Auto-stitch the area (Local)
    links = 0
    directions = {
        "north": (0, -1, 0), "south": (0, 1, 0),
        "east": (1, 0, 0), "west": (-1, 0, 0)
    }
    
    # Iterate the painted bounds + buffer to link to existing world
    for y in range(start_y - 1, start_y + height + 1):
        for x in range(start_x - 1, start_x + width + 1):
            # Find the room we just painted (or existing one)
            room = construction_utils.find_room_at_fuzzy_z(spatial, x, y, target_z)
                
            if not room: continue
            
            for d_name, (dx, dy, dz) in directions.items():
                if d_name in room.exits: continue
                
                # Scan for neighbor
                neighbor = construction_utils.find_room_at_fuzzy_z(spatial, x + dx, y + dy, target_z + dz)

                if neighbor:
                    room.add_exit(d_name, neighbor)
                    # Reciprocal
                    rev = get_reverse_direction(d_name)
                    if rev and rev not in neighbor.exits:
                        neighbor.add_exit(rev, room)
                    links += 1
                    
    player.send_line(f"Painted {created} new rooms, updated {updated} rooms. Created {links} links.")
