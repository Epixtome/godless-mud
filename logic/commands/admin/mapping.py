#@tp (and @teleport), @worldmap, @zonemap, @zone
import logic.handlers.command_manager as command_manager
from models import Room, Zone
from logic.core.world import get_room_id
from utilities.colors import Colors
from collections import defaultdict
from utilities import mapper
import logic.commands.admin.construction.utils as construction_utils
from logic.engines import vision_engine

@command_manager.register("@tp", "@teleport", admin=True)
def teleport(player, room_name):
    """Teleport to a room or zone."""
    target_room = None
    if room_name in player.game.world.rooms:
        target_room = player.game.world.rooms[room_name]
    else:
        # Check for Coordinates (x y z)
        try:
            parts = room_name.split()
            if len(parts) == 3:
                tx, ty, tz = int(parts[0]), int(parts[1]), int(parts[2])
                from logic.engines import spatial_engine
                spatial = spatial_engine.get_instance(player.game.world)
                found = spatial.get_room(tx, ty, tz)
                if found:
                    target_room = found
                else:
                    # Check column before auto-digging
                    existing = construction_utils.find_room_at_fuzzy_z(spatial, tx, ty, tz)
                    if existing:
                        target_room = existing
                        player.send_line(f"Adjusted to existing room at Z={existing.z}.")
                    else:
                        # Auto-dig if coordinates don't exist
                        zone_id = player.room.zone_id if player.room else "void"
                        new_id = get_room_id(zone_id, tx, ty, tz)
                        
                        new_room = Room(new_id, "New Room", "Created by teleportation.")
                        new_room.x, new_room.y, new_room.z = tx, ty, tz
                        new_room.zone_id = zone_id
                        
                        player.game.world.rooms[new_id] = new_room
                        from logic.engines import spatial_engine
                        spatial_engine.invalidate()
                        
                        player.send_line(f"Created new room at {tx}, {ty}, {tz}.")
                        target_room = new_room
        except ValueError:
            pass

        for r in player.game.world.rooms.values():
            if r.name.lower() == room_name.lower():
                target_room = r
                break
    
    # Check Zone ID (Teleport to first room in zone)
    if not target_room and room_name in player.game.world.zones:
        for r in player.game.world.rooms.values():
            if r.zone_id == room_name:
                target_room = r
                break
        if target_room:
            player.send_line(f"Teleporting to zone '{room_name}' start.")
    
    # Check Zone Name (Teleport to first room in zone)
    if not target_room:
        search_name = room_name.lower()
        target_zone_id = None
        
        # 1. Exact Name Match
        for zid, z in player.game.world.zones.items():
            if z.name.lower() == search_name:
                target_zone_id = zid
                break
        
        # 2. Partial Name Match
        if not target_zone_id:
            for zid, z in player.game.world.zones.items():
                if search_name in z.name.lower():
                    target_zone_id = zid
                    break
        
        if target_zone_id:
            for r in player.game.world.rooms.values():
                if r.zone_id == target_zone_id:
                    target_room = r
                    break
            if target_room:
                zone_obj = player.game.world.zones[target_zone_id]
                player.send_line(f"Teleporting to zone '{zone_obj.name}' ({target_zone_id}).")

    if target_room:
        player.room.players.remove(player)
        player.room.broadcast(f"{player.name} vanishes in a puff of smoke.")
        player.room = target_room
        player.room.players.append(player)
        if hasattr(player, 'visited_rooms'):
            # Ensure list format
            if isinstance(player.visited_rooms, set):
                player.visited_rooms = list(player.visited_rooms)
            
            if target_room.id not in player.visited_rooms:
                player.visited_rooms.append(target_room.id)
                if len(player.visited_rooms) > 200:
                    player.visited_rooms = player.visited_rooms[-200:]
        player.room.broadcast(f"{player.name} appears from thin air.")
        from logic.commands import info_commands as information
        information.look(player, "")
    else:
        player.send_line(f"Destination '{room_name}' not found.")

@command_manager.register("@worldmap", admin=True)
def world_map_visual(player, args):
    """
    Visualizes the world grid.
    Usage: @worldmap [scale] [mode: zones|kingdoms|terrain] [z<level>] [r<radius>]
    Example: @worldmap 20 terrain z0 r100
    """
    args_parts = args.split() if args else []
    scale = 20  # Default scale (1 char = 20 rooms)
    mode = "terrain"  # Default to terrain view for building
    z_filter = None
    radius = 300  # Default radius to prevent rendering far-off tardis rooms
    
    for arg in args_parts:
        if arg.isdigit():
            scale = int(arg)
            if scale < 1: scale = 1
        elif arg.lower() in ["zones", "kingdoms", "terrain"]:
            mode = arg.lower()
        elif arg.lower().startswith('z'):
            try:
                z_filter = int(arg[1:])
            except ValueError:
                pass
        elif arg.lower().startswith('r'):
            try:
                val = arg[1:]
                if val.lower() == 'all':
                    radius = None
                else:
                    radius = int(val)
            except ValueError:
                pass

    # Data structures
    visual_map = defaultdict(set)
    
    center_x = player.room.x
    center_y = player.room.y
    
    # Build Grid from Memory
    for r in player.game.world.rooms.values():
        if z_filter is not None and r.z != z_filter:
            continue
            
        if radius is not None:
            if abs(r.x - center_x) > radius or abs(r.y - center_y) > radius:
                continue
            
        zid = r.zone_id if r.zone_id else "unknown"
        gx, gy = r.x // scale, r.y // scale
        
        if mode == "terrain":
            visual_map[(gx, gy)].add(r.terrain)
        else:
            visual_map[(gx, gy)].add(zid)

    if not visual_map:
        msg = "World is empty."
        if z_filter is not None:
            msg += f" (No rooms at Z={z_filter})"
        player.send_line(msg)
        return

    # Calculate Bounds
    xs = [k[0] for k in visual_map.keys()]
    ys = [k[1] for k in visual_map.keys()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    z_info = f" (Z={z_filter})" if z_filter is not None else " (Z-Flattened)"
    r_info = f" (Radius={radius})" if radius else " (Radius=All)"
    output = [f"{Colors.BOLD}--- World Map (Scale 1:{scale}, Mode: {mode.title()}){z_info}{r_info} ---{Colors.RESET}"]
    
    # Legend & Char Mapping
    zone_chars = {}
    zone_colors = {}
    
    if mode.startswith("kingdom"):
        output.append(f"Legend: {Colors.CYAN}Light{Colors.RESET} {Colors.MAGENTA}Dark{Colors.RESET} {Colors.GREEN}Instinct{Colors.RESET} {Colors.WHITE}Neutral{Colors.RESET}")
    elif mode == "terrain":
        output.append("Legend: Standard Terrain Symbols (Roads, Forests, Water, etc.)")
    else:
        # Zone Mode
        zone_ids = set()
        for s in visual_map.values():
            zone_ids.update(s)
        
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        colors_list = [Colors.CYAN, Colors.YELLOW, Colors.GREEN, Colors.MAGENTA, Colors.BLUE, Colors.RED, Colors.WHITE]
        sorted_zones = sorted(list(zone_ids))
        legend_lines = []
        for i, zid in enumerate(sorted_zones):
            char = chars[i % len(chars)]
            color = colors_list[i % len(colors_list)]
            zone_chars[zid] = char
            zone_colors[zid] = color
            legend_lines.append(f"{color}{char}{Colors.RESET}:{zid}")
        
        # Wrap legend text
        import textwrap
        wrapped_legend = textwrap.wrap(" ".join(legend_lines), width=80)
        output.extend(wrapped_legend)

    output.append(f"Bounds: X[{min_x*scale}, {max_x*scale}] Y[{min_y*scale}, {max_y*scale}]")
    output.append("-" * 40)

    # Render
    for y in range(min_y - 1, max_y + 2):
        row = f"{y*scale:>5} " # Axis label
        for x in range(min_x - 1, max_x + 2):
            zids = visual_map.get((x, y), set())
            
            if not zids:
                row += f"{Colors.BOLD}.{Colors.RESET}"
            elif mode == "terrain":
                # Use centralized priority from mapper
                priority = mapper.TERRAIN_PRIORITY
                
                selected = list(zids)[0]
                found_priority = False
                
                # If scaled down, show the most important feature in the block
                for p in priority:
                    for t in zids:
                        if p in t:
                            selected = t
                            found_priority = True
                            break
                    if found_priority: break
                
                row += mapper.get_terrain_char(selected)
            elif len(zids) > 1 and not mode.startswith("kingdom"):
                row += f"{Colors.RED}!{Colors.RESET}"
            else:
                # Determine dominant zone/kingdom
                zid = list(zids)[0]
                
                if mode.startswith("kingdom"):
                    if "light" in zid:
                        row += f"{Colors.CYAN}#{Colors.RESET}"
                    elif "dark" in zid:
                        row += f"{Colors.MAGENTA}#{Colors.RESET}"
                    elif "instinct" in zid:
                        row += f"{Colors.GREEN}#{Colors.RESET}"
                    else:
                        row += f"{Colors.WHITE}#{Colors.RESET}"
                else:
                    char = zone_chars.get(zid, '?')
                    color = zone_colors.get(zid, Colors.CYAN)
                    row += f"{color}{char}{Colors.RESET}"
        output.append(row)
        
    for line in output:
        player.send_line(line)

@command_manager.register("@zonemap", admin=True)
def zonemap(player, args):
    """
    Surveys all zones, or visualizes a specific zone.
    Usage: @zonemap [zone_id] | @zonemap <width> <height> (Default: 40 40)
    """
    
    # 1. Local Map Visualization (Default or Explicit Dimensions)
    if not args or (len(args.split()) == 2 and args.split()[0].isdigit()):
        width = 40
        height = 40
        
        if args:
            parts = args.split()
            width = int(parts[0])
            height = int(parts[1])
            
        center_x = player.room.x
        center_y = player.room.y
        center_z = player.room.z
        
        # Calculate bounds centered on player
        min_x = center_x - (width // 2)
        max_x = min_x + width
        min_y = center_y - (height // 2)
        max_y = min_y + height
        
        output = [f"\n{Colors.BOLD}--- Local Map ({width}x{height}) ---{Colors.RESET}"]
        output.append(f"Center: {center_x},{center_y},{center_z}")
        
        # Use Vision Engine to ensure consistency with player map (check_los=False to see everything)
        # We calculate a radius that covers the requested width/height
        radius = max(width, height) // 2
        visible_grid = vision_engine.get_visible_rooms(player.room, radius=radius, world=player.game.world, check_los=False, observer=player)
        
        map_lines = mapper.draw_grid(visible_grid, player.room, radius=radius, visited_rooms=None, ignore_fog=True)
        output.extend(map_lines)
            
        for line in output:
            player.send_line(line)
        return

    # 2. Specific Zone Visualization
    target_zone = args.lower()
    
    # Collect rooms
    grid = {}
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    for r in player.game.world.rooms.values():
        if r.zone_id == target_zone:
            grid[(r.x, r.y)] = r
            min_x = min(min_x, r.x)
            max_x = max(max_x, r.x)
            min_y = min(min_y, r.y)
            max_y = max(max_y, r.y)
    
    if not grid:
        player.send_line(f"Zone '{target_zone}' not found or has no rooms.")
        return

    # Ensure player is visible on top of Z-stack
    if player.room.zone_id == target_zone:
        grid[(player.room.x, player.room.y)] = player.room

    output = [f"\n{Colors.BOLD}--- Map of {target_zone} ---{Colors.RESET}"]
    output.append(f"Bounds: X[{min_x}, {max_x}] Y[{min_y}, {max_y}]")
    
    # Render
    pad = 1
    for y in range(min_y - pad, max_y + pad + 1):
        line = ""
        for x in range(min_x - pad, max_x + pad + 1):
            if x == player.room.x and y == player.room.y and player.room.zone_id == target_zone:
                char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}"
                line += f"{char} "
                continue

            if (x, y) in grid:
                r = grid[(x, y)]
                char = mapper.get_terrain_char(r.terrain)
                line += f"{char} "
            else:
                line += "  "
        output.append(line)
        
    for line in output:
        player.send_line(line)

@command_manager.register("@layer", admin=True)
def layer_map(player, args):
    """
    View a specific Z-layer of the map around you.
    Usage: @layer <z_level> [width] [height]
    """
    if not args:
        player.send_line(f"Usage: @layer <z> [width] [height]. Current Z: {player.room.z}")
        return
        
    parts = args.split()
    try:
        target_z = int(parts[0])
    except ValueError:
        player.send_line("Z-level must be an integer.")
        return
        
    width = int(parts[1]) if len(parts) > 1 else 40
    height = int(parts[2]) if len(parts) > 2 else 20
    
    center_x = player.room.x
    center_y = player.room.y
    
    min_x = center_x - (width // 2)
    max_x = min_x + width
    min_y = center_y - (height // 2)
    max_y = min_y + height
    
    from logic.engines import spatial_engine
    spatial = spatial_engine.get_instance(player.game.world)
    
    output = [f"\n{Colors.BOLD}--- Layer Map (Z={target_z}) ---{Colors.RESET}"]
    
    # Render
    for y in range(min_y, max_y):
        line = ""
        for x in range(min_x, max_x):
            room = spatial.get_room(x, y, target_z)
            
            if x == center_x and y == center_y and target_z == player.room.z:
                char = f"{Colors.BOLD}{Colors.RED}@{Colors.RESET}"
            elif room:
                char = mapper.get_terrain_char(room.terrain)
            else:
                char = f"{Colors.BOLD}.{Colors.RESET}" # Empty space
                
            line += f"{char} "
        output.append(line)
        
    for line in output:
        player.send_line(line)

@command_manager.register("@zone", admin=True)
def zone_cmd(player, args):
    """Manage zones (list, create, name, tp, rooms, bounds)."""
    if not args:
        player.send_line("Usage: @zone <list | create | name | tp | rooms | bounds>")
        return
    
    parts = args.split()
    sub = parts[0].lower()
    
    if sub == "list":
        player.send_line("\n--- Zones ---")
        for z_id, z in player.game.world.zones.items():
            player.send_line(f"{z_id:<15} : {z.name}")
            
    elif sub == "create":
        if len(parts) < 2:
            player.send_line("Usage: @zone create <zone_id> [Zone Name]")
            return
        z_id = parts[1].lower()
        z_name = " ".join(parts[2:]) if len(parts) > 2 else f"Zone {z_id}"
        
        if z_id in player.game.world.zones:
            player.send_line(f"Zone '{z_id}' already exists.")
            return
            
        player.game.world.zones[z_id] = Zone(z_id, z_name)
        player.send_line(f"Zone '{z_id}' created.")

    elif sub == "name":
        if len(parts) < 3:
            player.send_line("Usage: @zone name <zone_id> <New Name>")
            return
        z_id = parts[1].lower()
        z_name = " ".join(parts[2:])
        
        if z_id not in player.game.world.zones:
            player.send_line("Zone not found.")
            return
            
        player.game.world.zones[z_id].name = z_name
        player.send_line(f"Zone '{z_id}' renamed to '{z_name}'.")

    elif sub == "rooms":
        if len(parts) < 2:
            player.send_line("Usage: @zone rooms <zone_id>")
            return
        z_id = parts[1]
        if z_id not in player.game.world.zones:
            player.send_line("Zone not found.")
            return
        
        matches = []
        for r_id, r in player.game.world.rooms.items():
            if r.zone_id == z_id:
                matches.append(f"{r_id:<20} : {r.name}")
        
        if not matches and z_id not in player.game.world.zones:
            player.send_line("Zone not found.")
            return

        header = f"\n--- Rooms in {z_id} ({len(matches)}) ---"
        player.send_paginated("\n".join([header] + sorted(matches)))
    elif sub == "tp":
        if len(parts) < 2:
            player.send_line("Teleport to which zone?")
            return
        z_id = parts[1]
        # Find first room in zone
        target = None
        for r in player.game.world.rooms.values():
            if r.zone_id == z_id:
                target = r
                break
        if target:
            teleport(player, target.id)
        else:
            player.send_line("Zone not found or has no rooms.")
    elif sub == "bounds":
        if len(parts) < 2:
            player.send_line("Usage: @zone bounds <zone_id>")
            return
        z_id = parts[1]
        
        # Auto-fix: If zone missing from registry but rooms exist, create it.
        if z_id not in player.game.world.zones:
            has_rooms = any(r.zone_id == z_id for r in player.game.world.rooms.values())
            if has_rooms:
                player.game.world.zones[z_id] = Zone(z_id, f"Zone {z_id}")
                player.send_line(f"Zone '{z_id}' was missing from registry. Created default entry.")
            else:
                player.send_line("Zone not found.")
                return
            
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        min_z, max_z = float('inf'), float('-inf')
        count = 0
        
        for r in player.game.world.rooms.values():
            if r.zone_id == z_id:
                min_x = min(min_x, r.x)
                max_x = max(max_x, r.x)
                min_y = min(min_y, r.y)
                max_y = max(max_y, r.y)
                min_z = min(min_z, r.z)
                max_z = max(max_z, r.z)
                count += 1
        
        if count == 0:
            player.send_line(f"Zone '{z_id}' has no rooms.")
        else:
            player.send_line(f"Zone '{z_id}' Bounds ({count} rooms):")
            player.send_line(f"  X: {min_x} to {max_x}")
            player.send_line(f"  Y: {min_y} to {max_y}")
            player.send_line(f"  Z: {min_z} to {max_z}")

@command_manager.register("@savezone", admin=True)
def save_zone_cmd(player, args):
    """Save a zone's structure to disk."""
    from logic.core import loader
    if not args:
        # Default to current zone
        args = player.room.zone_id
    
    if args.lower() == "all":
        count = 0
        for z_id in player.game.world.zones:
            loader.save_zone(player.game.world, z_id)
            count += 1
        player.send_line(f"Saved {count} zones.")
        return
        
    zone_id = args
    
    # Check for orphan zone (Rooms exist, but Zone object missing)
    if zone_id not in player.game.world.zones:
        has_rooms = any(r.zone_id == zone_id for r in player.game.world.rooms.values())
        if has_rooms:
            player.send_line(f"Zone '{zone_id}' detected in rooms but missing from registry. Creating Zone object...")
            new_zone = Zone(zone_id, f"Zone {zone_id}")
            player.game.world.zones[zone_id] = new_zone
        else:
            player.send_line(f"Zone '{zone_id}' not found.")
            return

    success, msg = loader.save_zone(player.game.world, zone_id)
    player.send_line(msg)
