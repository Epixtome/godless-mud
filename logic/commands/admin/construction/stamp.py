"""
logic/commands/admin/construction/stamp.py
Redesigned Templating and Stamping system.
Supports injecting structural blueprints into the world.
"""
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.commands.admin.construction.dig_logic import dig_room
from logic.commands.admin.construction.builder_state import _load_kit
import logic.commands.admin.construction.utils as construction_utils

@command_manager.register("@stamp", admin=True, category="admin_building")
def stamp(player, args):
    """
    Applies a complex template (Stencil) to the current location or direction.
    Usage: @stamp [here|dir] <stencil_id>
    """
    if not args:
        player.send_line("Usage: @stamp [here|dir] <stencil_id>")
        return
        
    parts = args.split()
    target = parts[0].lower()
    tpl_id = parts[1] if len(parts) > 1 else None
    
    if not tpl_id:
        # If they just gave one arg, assume it's the stencil ID for 'here'
        tpl_id = target
        target = "here"

    # Load from Kits
    kit_name = getattr(player, 'builder_state', {}).get("kit", "default")
    k_data = _load_kit(kit_name)
    
    template = None
    if k_data:
        for tpl in k_data.get("templates", []):
            if tpl_id.lower() in tpl['id'].lower() or tpl_id.lower() in tpl['name'].lower():
                template = tpl
                break
                
    if not template:
        player.send_line(f"Stencil '{tpl_id}' not found in current kit '{kit_name}'.")
        return

    dest_room = player.room
    if target != "here":
        # Create new room in direction
        dest_room = dig_room(player, target, name=template.get('name', "Staged Room"))
        if not dest_room:
             player.send_line("Failed to create room for stamp.")
             return

    # Injection
    construction_utils.update_room(
        dest_room,
        name=template.get('name'),
        desc=template.get('description'),
        terrain=template.get('terrain'),
        symbol=template.get('symbol')
    )
    
    player.send_line(f"{Colors.GREEN}Successfully stamped '{template['name']}' at {target}.{Colors.RESET}")

@command_manager.register("@furnish", admin=True, category="admin_building")
def furnish(player, args):
    """
    Apply a theme to a room or grid. Defaults to 1x1 at current position.
    Usage: @furnish [width] [height] [theme] [direction]
    Themes: shop, temple, forge, den
    """
    themes = {
        "shop": {"name": "General Store", "desc": "Shelves of goods line the walls.", "terrain": "indoors", "tags": ["shop"]},
        "temple": {"name": "Quiet Shrine", "desc": "Incense hangs heavy in the air.", "terrain": "holy", "tags": ["sanctuary"]},
        "forge": {"name": "Active Smithy", "desc": "Intense heat and an anvil.", "terrain": "indoors", "tags": ["industrial"]},
        "den": {"name": "Animal Den", "desc": "Scattered bones and fur.", "terrain": "forest", "tags": ["wild"]},
    }

    parts = args.split() if args else []
    width, height = 1, 1
    direction = None
    theme_key = None

    # Parsing logic (similar to @paint)
    valid_dirs = ['n','s','e','w','ne','nw','se','sw','north','south','east','west','up','down']
    
    # 1. Look for Width/Height at start
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        width = int(parts.pop(0))
        height = int(parts.pop(0))

    # 2. Look for Direction
    for i, p in enumerate(parts):
        if p.lower() in valid_dirs:
            direction = parts.pop(i)
            break

    # 3. Last remaining part is likely the theme
    if parts:
        theme_key = parts[0].lower()

    if not theme_key and not args:
        player.send_line(f"Available Themes: {', '.join(themes.keys())}")
        player.send_line("Usage: @furnish [w] [h] <theme> [dir]")
        return
        
    theme = themes.get(theme_key) if theme_key else None
    if theme_key and not theme:
        player.send_line(f"Theme '{theme_key}' not found. Available: {', '.join(themes.keys())}")
        return

    # Fallback to default if no theme found but dimensions provided
    final_theme = theme or {"name": "Furnished Room", "desc": "A newly furnished area.", "terrain": "indoors", "tags": []}

    # Area calculation
    from logic.engines import spatial_engine
    from logic.core.world import get_room_id
    from models import Room
    
    off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
    start_x = off_x if off_x is not None else player.room.x - (width // 2)
    start_y = off_y if off_y is not None else player.room.y - (height // 2)
    target_z = player.room.z
    
    spatial = spatial_engine.get_instance(player.game.world)
    created, updated = 0, 0
    
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            room = construction_utils.find_room_at_fuzzy_z(spatial, x, y, target_z)
            if room:
                room.name = str(final_theme["name"])
                room.description = str(final_theme["desc"])
                room.terrain = str(final_theme["terrain"])
                room.dirty = True
                updated += 1
            else:
                new_id = get_room_id(player.room.zone_id, x, y, target_z)
                nr = Room(new_id, str(final_theme["name"]), str(final_theme["desc"]))
                nr.x, nr.y, nr.z, nr.zone_id, nr.terrain = x, y, target_z, player.room.zone_id, str(final_theme["terrain"])
                player.game.world.rooms[new_id] = nr
                created += 1
    
    if created: 
        spatial_engine.invalidate()
        if spatial: spatial.rebuild()
    
    player.send_line(f"Furnished {created + updated} rooms with '{theme_key or 'default'}' theme.")
