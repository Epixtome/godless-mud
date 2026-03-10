"""
logic/commands/admin/visual_map_commands.py
Analytical mapping tools: World maps, Zone surveys, and Layer visualization.
"""
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from collections import defaultdict
from utilities import mapper
from logic.engines import spatial_engine, vision_engine

@command_manager.register("@worldmap", admin=True)
def world_map_visual(player, args):
    """Visualizes the global world grid."""
    parts = args.split() if args else []
    scale, mode, z_filter, radius = 20, "terrain", None, 300
    for arg in parts:
        if arg.isdigit(): scale = max(1, int(arg))
        elif arg.lower() in ["zones", "kingdoms", "terrain"]: mode = arg.lower()
        elif arg.lower().startswith('z'):
            try: z_filter = int(arg[1:])
            except: pass
        elif arg.lower().startswith('r'):
            try: radius = None if arg[1:].lower() == 'all' else int(arg[1:])
            except: pass

    visual_map = defaultdict(set)
    cx, cy = player.room.x, player.room.y
    for r in player.game.world.rooms.values():
        if z_filter is not None and r.z != z_filter: continue
        if radius is not None and (abs(r.x - cx) > radius or abs(r.y - cy) > radius): continue
        gx, gy = r.x // scale, r.y // scale
        visual_map[(gx, gy)].add(r.terrain if mode == "terrain" else r.zone_id)

    if not visual_map:
        player.send_line(f"No results found.{' (Z='+str(z_filter)+')' if z_filter is not None else ''}")
        return

    xs, ys = [k[0] for k in visual_map.keys()], [k[1] for k in visual_map.keys()]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    
    player.send_line(f"{Colors.BOLD}--- World Map (1:{scale}, {mode.title()}) ---{Colors.RESET}")
    
    for y in range(min_y - 1, max_y + 2):
        row = f"{y*scale:>5} "
        for x in range(min_x - 1, max_x + 2):
            opts = visual_map.get((x, y), set())
            if not opts: row += f"{Colors.BOLD}.{Colors.RESET}"
            elif mode == "terrain":
                sel = next((p for p in mapper.TERRAIN_PRIORITY if any(p in t for t in opts)), list(opts)[0])
                row += mapper.get_terrain_char(sel)
            else:
                zid = list(opts)[0]
                row += f"{Colors.CYAN}#{Colors.RESET}" if "light" in zid else f"{Colors.MAGENTA}#{Colors.RESET}" if "dark" in zid else "#"
        player.send_line(row)

@command_manager.register("@zonemap", admin=True)
def zonemap(player, args):
    """Local or specific zone visualization."""
    parts = args.split()
    if not args or (len(parts) == 2 and parts[0].isdigit()):
        w, h = (int(parts[0]), int(parts[1])) if args else (40, 20)
        rad = max(w, h) // 2
        grid = vision_engine.get_visible_rooms(player.room, radius=rad, world=player.game.world, check_los=False)
        for line in mapper.draw_grid(grid, player.room, radius=rad, ignore_fog=True):
            player.send_line(line)
    else:
        zid = args.lower()
        rooms = [r for r in player.game.world.rooms.values() if r.zone_id == zid]
        if not rooms:
            player.send_line(f"Zone '{zid}' empty."); return
        min_x = min(r.x for r in rooms); max_x = max(r.x for r in rooms)
        min_y = min(r.y for r in rooms); max_y = max(r.y for r in rooms)
        for y in range(min_y - 1, max_y + 2):
            line = ""
            for x in range(min_x - 1, max_x + 2):
                if r := next((r for r in rooms if r.x == x and r.y == y), None):
                    line += f"{mapper.get_terrain_char(r)} "
                else: line += "  "
            player.send_line(line)

@command_manager.register("@layer", admin=True)
def layer_map(player, args):
    """View a specific Z-layer."""
    parts = args.split()
    if not parts: return
    tz = int(parts[0])
    w, h = (int(parts[1]), int(parts[2])) if len(parts) > 2 else (40, 20)
    cx, cy = player.room.x, player.room.y
    spatial = spatial_engine.get_instance(player.game.world)
    if not spatial:
        player.send_line("Spatial index unavailable."); return
    player.send_line(f"--- Layer {tz} ---")
    for y in range(cy - h//2, cy + h//2):
        line = ""
        for x in range(cx - w//2, cx + w//2):
            r = spatial.get_room(x, y, tz)
            line += f"{Colors.RED}@{Colors.RESET} " if (x==cx and y==cy and tz==player.room.z) else f"{mapper.get_terrain_char(r)} " if r else ". "
        player.send_line(line)
