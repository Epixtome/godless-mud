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
    
    # Load from Kits (v7.0 Standard)
    kit_name = getattr(player, 'builder_state', {}).get("kit", "default")
    k_data = _load_kit(kit_name)
    
    theme_template = None
    if k_data and theme_key:
        for tpl in k_data.get("templates", []):
            if theme_key in tpl['id'].lower() or theme_key in tpl['name'].lower():
                theme_template = tpl
                break
    
    # Fallback to legacy themes (hardcoded) for common staples
    if not theme_template:
        theme = themes.get(theme_key) if theme_key else None
        if theme: theme_template = theme

    # Re-apply theme over a grid
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    
    off_x, off_y = construction_utils.get_directional_offsets(player, width, height, direction)
    start_x = off_x if off_x is not None else player.room.x - (width // 2)
    start_y = off_y if off_y is not None else player.room.y - (height // 2)
    target_z = player.room.z
    
    count = 0
    if theme_template:
        for y in range(start_y, start_y + height):
            for x in range(start_x, start_x + width):
                r = construction_utils.find_room_at_fuzzy_z(spatial, x, y, target_z)
                if r:
                    construction_utils.update_room(
                        r, 
                        terrain=theme_template.get('terrain'),
                        name=theme_template.get('name'),
                        desc=theme_template.get('description'),
                        symbol=theme_template.get('symbol'),
                        elevation=theme_template.get('elevation'),
                        items=theme_template.get('items'),
                        monsters=theme_template.get('monsters')
                    )
                    count += 1
        player.send_line(f"{Colors.GREEN}Furnished {count} rooms with '{theme_template.get('name')}' theme from '{kit_name}'.{Colors.RESET}")
    else:
        player.send_line(f"No theme found matching '{theme_key}'. Try: {', '.join(themes.keys())} or kit-stencils.")
