import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from utilities import mapper
from logic.engines import vision_engine
from logic.common import get_reverse_direction, find_by_index
from logic.core.utils import display_utils

@command_manager.register("look", "l", category="information")
def look(player, args, with_prompt=True):
    """Look at the current room or an object."""
    output = []

    def send(msg):
        output.append(str(msg))

    def flush():
        if not output:
            return
        # Filter None and strip trailing empty lines but preserve internal breaks
        cleaned = [str(line) for line in output]
        full_text = "\r\n".join(cleaned).strip()
        
        if with_prompt:
            player.send_raw(full_text + "\r\n", include_prompt=True)
            player.suppress_engine_prompt = True
        else:
            player.send_line(full_text)
        output.clear()

    room = player.room
    if args.lower().startswith("in "):
        target_name = args[3:].strip()
        target = find_by_index(room.items + player.inventory, target_name)
        if not target: send("You don't see that here.")
        elif not hasattr(target, 'inventory'): send("That is not a container.")
        else:
            send(f"Inside {target.name}:")
            if not target.inventory: send("  Nothing.")
            for item in target.inventory: send(f"  {item.name}")
        flush(); return

    if args:
        target_name = args.lower()
        if target_name.startswith("at "): target_name = target_name[3:].strip()
        
        # Check items, monsters, players
        for item in room.items:
            if target_name in item.name.lower() and vision_engine.can_see(player, item):
                send(f"{Colors.MAGENTA}{item.description}{Colors.RESET}"); flush(); return
        for mob in room.monsters:
            if target_name in mob.name.lower() and vision_engine.can_see(player, mob):
                send(f"{Colors.RED}{mob.description}{Colors.RESET}"); flush(); return
        for p in room.players:
            if p != player and target_name in p.name.lower() and vision_engine.can_see(player, p):
                send(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}"); flush(); return

        send(f"You look at '{args}', but see nothing special."); flush(); return

    # Default Room View
    header = mapper.get_map_header(player.room, player.game.world)
    send(header)
    
    local_radius = 2
    if hasattr(player, 'identity_tags') and "eagle_eye" in player.identity_tags: local_radius += 2
    if hasattr(player, 'status_effects'):
        if "eagle_eye" in player.status_effects: local_radius += 2
        if "farsight" in player.status_effects: local_radius += 1

    visible_grid = vision_engine.get_visible_rooms(player.room, radius=local_radius, world=player.game.world, check_los=True, observer=player)
    map_lines = mapper.draw_grid(visible_grid, player.room, radius=local_radius, visited_rooms=None, ignore_fog=True, indent=5, world=player.game.world)
    for line in map_lines: send(line)

    if getattr(player, 'admin_vision', False):
        send(f"{Colors.MAGENTA}[DEBUG] ID: {room.id} | XYZ: {room.x},{room.y},{room.z}{Colors.RESET}")

    desc = room.description.strip()
    send(f"{Colors.WHITE}{desc}{Colors.RESET}")
    
    exits = []
    for direction, target_id in room.exits.items():
        door = room.doors.get(direction)
        door_info = f" ({door.name} [{door.state}])" if door else ""
        exits.append(f"{Colors.GREEN}{direction}{door_info}{Colors.RESET}")
    send(f"{Colors.YELLOW}Exits: {', '.join(exits)}{Colors.RESET}")
    
    for item in room.items:
        if vision_engine.can_see(player, item): send(f"{Colors.MAGENTA}{item.description}{Colors.RESET}")
    for mob in room.monsters:
        if vision_engine.can_see(player, mob): send(f"{Colors.RED}{mob.description}{Colors.RESET}")
    for p in [p for p in room.players if p != player]:
        if vision_engine.can_see(player, p): send(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}")

    flush()

@command_manager.register("map", category="information")
def show_map(player, args):
    """Shows a large map of visited areas."""
    radius = 7 + getattr(player.room, 'elevation', 0)
    radius = max(2, min(15, radius))
    visible_grid = vision_engine.get_visible_rooms(player.room, radius=radius, world=player.game.world, check_los=False, observer=player)
    map_lines = mapper.draw_grid(visible_grid, player.room, radius=radius, visited_rooms=player.visited_rooms, ignore_fog=False, indent=5, world=player.game.world)

    player.send_line(f"--- Map: {mapper.get_map_header(player.room, player.game.world)} [Elev: {player.room.elevation}] ---")
    for line in map_lines: player.send_line(line)

@command_manager.register("where", category="information")
def where(player, args):
    """Show current location or find a target."""
    room = player.room
    if not args:
        zone_name = player.game.world.zones[room.zone_id].name if room.zone_id in player.game.world.zones else room.zone_id
        player.send_line(f"\n {Colors.BOLD}Location:{Colors.RESET}")
        player.send_line(f"  Zone: {Colors.CYAN}{zone_name}{Colors.RESET}")
        player.send_line(f"  Room: {Colors.WHITE}{room.name}{Colors.RESET}")
        return

    target_name = args.lower()
    if not room.zone_id: return player.send_line("You are not in a defined zone.")

    found = []
    for r in player.game.world.rooms.values():
        if r.zone_id == room.zone_id:
            for mob in r.monsters:
                if target_name in mob.name.lower(): found.append((mob, r))
    
    if not found: player.send_line(f"No match for '{args}' here.")
    else:
        player.send_line(f"\n{display_utils.render_header(f'Scanning for {args}', 60)}")
        for mob, r in found: player.send_line(f"  {mob.name:<25} in {Colors.WHITE}{r.name}{Colors.RESET}")

@command_manager.register("scan", category="information")
def scan(player, args):
    """Scan for enemies in the immediate area."""
    player.send_line(f"\n{Colors.BOLD}Scanning area...{Colors.RESET}")
    visible_grid = vision_engine.get_visible_rooms(player.room, radius=1, world=player.game.world, check_los=True, observer=player)
    
    # Predefined directional map
    dirs = {(0,0): "Here", (0,1): "North", (0,-1): "South", (1,0): "East", (-1,0): "West"}
    
    for (rx, ry) in dirs.keys():
        room = visible_grid.get((rx, ry))
        if room and room.monsters:
            color = Colors.YELLOW if (rx == 0 and ry == 0) else Colors.CYAN
            player.send_line(f"{color}{dirs[(rx, ry)]}:{Colors.RESET}")
            for m in room.monsters:
                player.send_line(f"  {m.name}")
