import logic.command_manager as command_manager
from logic.common import get_reverse_direction, find_by_index
from utilities.colors import Colors
from logic import mapper, search
from logic.engines import vision_engine

@command_manager.register("look", "l", category="information")
def look(player, args):
    """Look at the current room or an object."""
    room = player.room
    
    # Handle "look in <container>"
    if args.lower().startswith("in "):
        target_name = args[3:].strip()
        target = find_by_index(room.items + player.inventory, target_name)
        
        if not target:
            player.send_line("You don't see that here.")
            return
            
        if not hasattr(target, 'inventory'):
            player.send_line("That is not a container.")
            return
            
        player.send_line(f"Inside {target.name}:")
        if not target.inventory:
            player.send_line("  Nothing.")
        for item in target.inventory:
            player.send_line(f"  {item.name}")
        return

    if args:
        # Look at specific item/mob
        target_name = args.lower()
        
        # Check items
        for item in room.items:
            if target_name in item.name.lower():
                player.send_line(f"{Colors.MAGENTA}{item.description}{Colors.RESET}")
                return
        
        # Check monsters
        for mob in room.monsters:
            if target_name in mob.name.lower():
                player.send_line(f"{Colors.RED}{mob.description}{Colors.RESET}")
                return
                
        # Check players
        for p in room.players:
            if p != player and target_name in p.name.lower():
                player.send_line(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}")
                return

        player.send_line(f"You look at '{args}', but see nothing special.")
        return

    # Header
    header = mapper.get_map_header(player.room, player.game.world)
    player.send_line(header)

    # Display the 5x5 mini-map using the new coordinate-based system
    visible_grid = vision_engine.get_visible_rooms(player.room, radius=2, world=player.game.world, check_los=True)
    # Mini-map: Ignore Fog of War (ignore_fog=True), Indent 5 spaces
    map_lines = mapper.draw_grid(visible_grid, player.room, radius=2, visited_rooms=None, ignore_fog=True, indent=5)
    for line in map_lines:
        player.send_line(line)

    if getattr(player, 'admin_vision', False):
        r = player.room
        player.send_line(f"{Colors.MAGENTA}[DEBUG] ID: {r.id} | Zone: {r.zone_id} | XYZ: {r.x}, {r.y}, {r.z} | Terrain: {r.terrain}{Colors.RESET}")

    player.send_line(f"{Colors.WHITE}{room.description}{Colors.RESET}")
    
    # Exits
    exits = []
    for direction, target in room.exits.items():
        # Check doors
        door = room.doors.get(direction)
        door_info = ""
        if door:
            status = f"[{door.state}]"
            door_info = f" ({door.name} {status})"
            
        # Check for one-way exits using common logic
        rev_dir = get_reverse_direction(direction)
        one_way = " (One-way)" if rev_dir and rev_dir not in target.exits else ""
            
        exits.append(f"{Colors.GREEN}{direction}{door_info}{one_way}{Colors.RESET}")
    player.send_line(f"{Colors.YELLOW}Exits: {', '.join(exits)}{Colors.RESET}")
    
    # Items
    for item in room.items:
        player.send_line(f"{Colors.MAGENTA}{item.description}{Colors.RESET}")
        
    # Monsters
    for mob in room.monsters:
        status = ""
        if mob.fighting:
            status = f" {Colors.YELLOW}[Fighting: {mob.fighting.name}]{Colors.RESET}"
        player.send_line(f"{Colors.RED}{mob.description}{status}{Colors.RESET}")
        
    # Players
    other_players = [p for p in room.players if p != player]
    if other_players:
        for p in other_players:
            player.send_line(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}")

@command_manager.register("map", category="information")
def show_map(player, args):
    """
    Shows a large map of visited areas.
    Usage: map
    """
    radius = 7  # Default 15x15 grid

    # Use the new coordinate-based vision engine
    # check_los=False allows seeing rooms behind doors/walls if they are in memory (visited)
    visible_grid = vision_engine.get_visible_rooms(player.room, radius=radius, world=player.game.world, check_los=False)

    # The new mapper function will draw the grid, respecting Fog of War
    # Large map: Respect Fog of War (ignore_fog=False), Indent 5 spaces
    map_lines = mapper.draw_grid(visible_grid, player.room, radius=radius, visited_rooms=player.visited_rooms, ignore_fog=False, indent=5)

    header = mapper.get_map_header(player.room, player.game.world)
    player.send_line(f"--- Map: {header} ---")
    
    for line in map_lines:
        player.send_line(line)

    if getattr(player, 'admin_vision', False):
        r = player.room
        player.send_line(f"{Colors.MAGENTA}[DEBUG] Center: {r.x},{r.y},{r.z} | Zone: {r.zone_id}{Colors.RESET}")

@command_manager.register("score", "sc", category="information")
def score(player, args):
    """Quick view of status and combat."""
    player.send_line(f"\n{Colors.BOLD}--- Status: {player.name} ---{Colors.RESET}")
    
    # Vitals
    hp_color = Colors.GREEN if player.hp > player.max_hp * 0.5 else Colors.RED
    player.send_line(f"HP: {hp_color}{player.hp}/{player.max_hp}{Colors.RESET}")
    
    res = []
    if 'stamina' in player.resources: res.append(f"ST: {player.resources['stamina']}")
    if 'concentration' in player.resources: res.append(f"MN: {player.resources['concentration']}")
    if 'momentum' in player.resources: res.append(f"MO: {player.resources['momentum']}")
    player.send_line("Resources: " + "  ".join(res))
    
    # State
    state_color = Colors.RED if player.state == "combat" else Colors.WHITE
    player.send_line(f"State: {state_color}{player.state.title()}{Colors.RESET}")
    
    # Combat Info
    if player.fighting:
        t = player.fighting
        t_max = getattr(t, 'max_hp', t.hp) or 1
        player.send_line(f"Target: {Colors.RED}{t.name}{Colors.RESET} (HP: {t.hp}/{t_max})")
    else:
        player.send_line("Target: None")
        
    if player.locked_target:
        player.send_line(f"Locked: {Colors.CYAN}{player.locked_target.name}{Colors.RESET}")
        
    # Manifestations
    if player.status_effects:
        player.send_line(f"\n{Colors.BOLD}[Manifestations]{Colors.RESET}")
        for effect, duration in player.status_effects.items():
            player.send_line(f"  {effect} ({duration}s)")

@command_manager.register("attributes", "attr", "sheet", category="information")
def attributes(player, args):
    """View character stats and background."""
    player.send_line(f"\n{Colors.BOLD}--- Character Sheet: {player.name} ---{Colors.RESET}")
    
    # General Info
    p_class = player.active_class.replace('_', ' ').title() if player.active_class else "Wanderer"
    kingdom = player.identity_tags[0].title() if player.identity_tags else "None"
    
    player.send_line(f"Class   : {p_class}")
    player.send_line(f"Kingdom : {kingdom}")
    player.send_line(f"Gold    : {player.gold}")
    rp = getattr(player, 'raid_points', 0)
    player.send_line(f"Raid Pts: {rp}")
    
    player.send_line(f"\n{Colors.BOLD}[Attributes]{Colors.RESET}")
    # Table format for stats
    stats = list(player.base_stats.keys())
    # 2 columns
    for i in range(0, len(stats), 2):
        s1 = stats[i]
        v1 = player.get_stat(s1)
        b1 = player.base_stats[s1]
        
        line = f"  {s1.upper():<3}: {v1:<3} ({b1})"
        
        if i + 1 < len(stats):
            s2 = stats[i+1]
            v2 = player.get_stat(s2)
            b2 = player.base_stats[s2]
            line += f"      {s2.upper():<3}: {v2:<3} ({b2})"
            
        player.send_line(line)
        
    # Tags
    player.send_line(f"\n{Colors.BOLD}[Identity Tags]{Colors.RESET}")
    player.send_line(f"  {', '.join(player.identity_tags)}")

@command_manager.register("favor", category="information")
def favor(player, args):
    """List favor with deities."""
    kingdoms = {"light": [], "dark": [], "instinct": []}
    
    for d in player.game.world.deities.values():
        if d.kingdom in kingdoms:
            kingdoms[d.kingdom].append(d)
            
    player.send_line(f"\n{Colors.BOLD}--- Divine Favor ---{Colors.RESET}")
    
    for k, deities in kingdoms.items():
        player.send_line(f"\n{Colors.CYAN}{k.title()} Kingdom{Colors.RESET}")
        for d in sorted(deities, key=lambda x: x.name):
            amount = player.favor.get(d.id, 0)
            player.send_line(f"  {d.name:<25}: {amount}")

@command_manager.register("where", category="information")
def where(player, args):
    """Show your current location, or find a target in your zone."""
    if not args:
        room = player.room
        zone_name = "Unknown Zone"
        if room.zone_id and room.zone_id in player.game.world.zones:
            zone_name = player.game.world.zones[room.zone_id].name
        elif room.zone_id:
            zone_name = room.zone_id.replace('_', ' ').title()
            
        player.send_line(f"\n{Colors.BOLD}Location:{Colors.RESET}")
        player.send_line(f"  Zone: {Colors.CYAN}{zone_name}{Colors.RESET}")
        player.send_line(f"  Room: {Colors.WHITE}{room.name}{Colors.RESET}")
        return

    # Search for target in the current zone
    target_name = args.lower()
    current_zone_id = player.room.zone_id
    
    if not current_zone_id:
        player.send_line("You are not in a defined zone.")
        return

    found_targets = []
    for room in player.game.world.rooms.values():
        if room.zone_id == current_zone_id:
            for mob in room.monsters:
                if target_name in mob.name.lower():
                    found_targets.append((mob, room))
        
    if not found_targets:
        player.send_line(f"You cannot find '{args}' in this zone.")
    else:
        player.send_line(f"\n{Colors.BOLD}--- Locations for '{args}' ---{Colors.RESET}")
        for mob, room in found_targets:
            player.send_line(f"  {mob.name} is in {Colors.WHITE}{room.name}{Colors.RESET}")

@command_manager.register("scan", category="information")
def scan(player, args):
    """Scan for enemies in the immediate area."""
    player.send_line(f"\n{Colors.BOLD}Scanning area...{Colors.RESET}")
    
    # Use Vision Engine to get rooms within range (e.g., 2)
    visible_grid = vision_engine.get_visible_rooms(player.room, radius=2, world=player.game.world, check_los=True)
    
    # Sort by distance (approximate based on x/y)
    sorted_rooms = sorted(visible_grid.items(), key=lambda item: abs(item[0][0]) + abs(item[0][1]))
    
    for (rx, ry), room in sorted_rooms:
        if rx == 0 and ry == 0:
            prefix = f"{Colors.YELLOW}Here:{Colors.RESET}"
        else:
            # Determine rough direction string
            dirs = []
            if ry < 0: dirs.append("North")
            if ry > 0: dirs.append("South")
            if rx < 0: dirs.append("West")
            if rx > 0: dirs.append("East")
            prefix = f"{Colors.CYAN}{'-'.join(dirs)}:{Colors.RESET}"
            
        if room.monsters:
            player.send_line(prefix)
            for m in room.monsters:
                status = f" [Fighting: {m.fighting.name}]" if m.fighting else ""
                player.send_line(f"  {m.name}{status}")
        elif rx == 0 and ry == 0:
             player.send_line(f"{prefix} Nothing.")

@command_manager.register("blessings", "known", category="information")
def list_known_blessings(player, args):
    """List all blessings you have learned."""
    player.send_line(f"\n--- {Colors.BOLD}Known Blessings{Colors.RESET} ---")
    
    if not player.known_blessings:
        player.send_line("You have not learned any blessings yet.")
        return

    # Header
    player.send_line(f"{'Tier':<5} {'Name':<25} {'Deity':<15} {'Status'}")
    player.send_line("-" * 60)

    # Group by Tier
    by_tier = {1: [], 2: [], 3: [], 4: []}
    for b_id in player.known_blessings:
        b = player.game.world.blessings.get(b_id)
        if b:
            by_tier[b.tier].append(b)

    for t in range(1, 5):
        if by_tier[t]:
            for b in sorted(by_tier[t], key=lambda x: x.name):
                status = f"{Colors.GREEN}[Equipped]{Colors.RESET}" if b.id in player.equipped_blessings else ""
                d_id = getattr(b, 'deity_id', None)
                deity_name = d_id.title() if d_id else "---"
                
                line = f"{b.tier:<5} {b.name:<25} {deity_name:<15} {status}"
                player.send_line(line)

@command_manager.register("who", category="information")
def who(player, args):
    """List all online players."""
    player.send_line(f"\n{Colors.BOLD}--- Online Players ---{Colors.RESET}")
    
    # Access sessions safely (handles both list and dict implementations)
    sessions = getattr(player.game, 'sessions', [])
    if isinstance(sessions, dict):
        sessions = list(sessions.values())
        
    count = 0
    for session in sessions:
        if hasattr(session, 'player') and session.player:
            p = session.player
            # Build status string
            status = ""
            if p.state == "combat":
                status = f" {Colors.RED}(Fighting){Colors.RESET}"
            elif p.state == "rest":
                status = f" {Colors.BLUE}(Resting){Colors.RESET}"
                
            # Class info
            cls_name = p.active_class.replace('_', ' ').title() if p.active_class else "Wanderer"
            
            player.send_line(f"[{cls_name}] {p.name}{status}")
            count += 1
            
    player.send_line(f"\nTotal Players: {count}")

@command_manager.register("finger", category="information")
def finger(player, args):
    """Get details about a player."""
    if not args:
        player.send_line("Finger whom?")
        return
        
    target_name = args.lower()
    target = None
    
    sessions = getattr(player.game, 'sessions', [])
    if isinstance(sessions, dict):
        sessions = list(sessions.values())
        
    for session in sessions:
        if hasattr(session, 'player') and session.player:
            if session.player.name.lower() == target_name:
                target = session.player
                break
    
    if not target:
        player.send_line(f"No player named '{args}' is currently online.")
        return
        
    player.send_line(f"\n{Colors.BOLD}--- {target.name} ---{Colors.RESET}")
    player.send_line(f"Class: {target.active_class.replace('_', ' ').title() if target.active_class else 'Wanderer'}")
    player.send_line(f"Kingdom: {target.identity_tags[0].title() if target.identity_tags else 'None'}")
    
    # Location
    loc = "Unknown"
    if target.room:
        zone_name = target.room.zone_id
        if zone_name in player.game.world.zones:
            zone_name = player.game.world.zones[zone_name].name
        loc = f"{target.room.name} ({zone_name})"
    player.send_line(f"Location: {loc}")
    
    if target.description:
        player.send_line(f"Description: {target.description}")

@command_manager.register("motd", category="information")
def motd(player, args):
    """Show the Message of the Day."""
    try:
        with open('data/motd.txt', 'r') as f:
            player.send_line(f"\n{Colors.CYAN}{f.read()}{Colors.RESET}")
    except FileNotFoundError:
        player.send_line("No MOTD set.")