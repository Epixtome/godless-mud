import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from utilities import mapper
from logic.core import perception as vision
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
            if target_name in item.name.lower() and vision.can_see(player, item):
                send(f"{Colors.MAGENTA}{item.description}{Colors.RESET}"); flush(); return
        for mob in room.monsters:
            if target_name in mob.name.lower() and vision.can_see(player, mob):
                status_str = ""
                if hasattr(mob, 'status_effects') and mob.status_effects:
                    visible = []
                    for s in mob.status_effects:
                        from logic.core import effects
                        eff_def = effects.get_effect_definition(s, player.game)
                        if eff_def:
                            name = eff_def.get('name', s.replace('_', ' ').title())
                            visible.append(name)
                    if visible:
                        status_str = f" {Colors.YELLOW}[{', '.join(visible)}]{Colors.RESET}"
                send(f"{Colors.RED}{mob.description}{Colors.RESET}{status_str}"); flush(); return
        for p in room.players:
            if p != player and target_name in p.name.lower() and vision.can_see(player, p):
                send(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}"); flush(); return

        # Fallback: Check Inventory
        for item in player.inventory:
            if target_name in item.name.lower():
                send(f"{Colors.YELLOW}[Inventory] {Colors.MAGENTA}{item.description}{Colors.RESET}"); flush(); return

        send(f"You look at '{args}', but see nothing special."); flush(); return

    # Default Room View
    header = mapper.get_map_header(player.room, player.game.world)
    send(header)
    
    local_radius = 3
    if hasattr(player, 'identity_tags') and "eagle_eye" in player.identity_tags: local_radius += 2
    if hasattr(player, 'status_effects'):
        if "eagle_eye" in player.status_effects: local_radius += 2
        if "farsight" in player.status_effects: local_radius += 1

    # [V6.8 Refactor] Navigation Mode: Shows infrastructure while respecting Fog (V7.2).
    perception = vision.get_perception(player, radius=local_radius, context=vision.NAVIGATION)
    map_lines = mapper.draw_grid(
        perception, 
        visited_rooms=player.visited_rooms, 
        ignore_fog=getattr(player, 'ignore_fog', False), 
        indent=5, 
        world=player.game.world, 
        shading=True,
        show_dynamic=False
    )
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
        if vision.can_see(player, item): 
            id_str = f" {Colors.DGREY}[{getattr(item, 'prototype_id', 'None')}]{Colors.RESET}" if getattr(player, 'admin_vision', False) else ""
            send(f"{Colors.MAGENTA}{item.description}{Colors.RESET}{id_str}")
    for mob in room.monsters:
        if vision.can_see(player, mob):
            status_str = ""
            if hasattr(mob, 'status_effects') and mob.status_effects:
                visible = []
                for s in mob.status_effects:
                    from logic.core import effects
                    eff_def = effects.get_effect_definition(s, player.game)
                    if eff_def:
                        name = eff_def.get('name', s.replace('_', ' ').title())
                        visible.append(name)
                if visible:
                    status_str = f" {Colors.YELLOW}[{', '.join(visible)}]{Colors.RESET}"
            
            id_str = f" {Colors.DGREY}[{getattr(mob, 'prototype_id', 'None')}]{Colors.RESET}" if getattr(player, 'admin_vision', False) else ""
            send(f"{Colors.RED}{mob.description}{Colors.RESET}{status_str}{id_str}")
    for p in [p for p in room.players if p != player]:
        if vision.can_see(player, p): send(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}")

    # [V6.0] Trap Vision for Assassins & Owners
    if hasattr(room, 'metadata') and 'traps' in room.metadata:
        for trap in room.metadata['traps']:
            if trap.get('owner') == player.name or player.active_class == 'assassin':
                t_type = trap.get('type', 'generic').title()
                owner_tag = f"Your" if trap.get('owner') == player.name else f"{trap.get('owner')}'s"
                send(f"{Colors.BLUE}[TRAP] {owner_tag} {t_type} trap lies hidden here.{Colors.RESET}")

    flush()

@command_manager.register("map", category="information")
def show_map(player, args):
    """Shows a large map of visited areas with live intelligence."""
    import time
    radius = 7 + getattr(player.room, 'elevation', 0)
    radius = max(2, min(15, radius))
    
    # Prune expired tracked entities
    if 'tracked_entities' in player.ext_state:
        now = time.time()
        player.ext_state['tracked_entities'] = {eid: exp for eid, exp in player.ext_state['tracked_entities'].items() if exp > now}

    # [V6.8 Refactor] Tactical Mode: Uses structural privacy and highlights building shells.
    perception = vision.get_perception(player, radius=radius, context=vision.TACTICAL)
    
    map_lines = mapper.draw_grid(
        perception,
        visited_rooms=player.visited_rooms, 
        ignore_fog=getattr(player, 'ignore_fog', False), 
        indent=5, 
        world=player.game.world, 
        shading=True,
        show_dynamic=True
    )

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
    """Scan for enemies in the immediate area (Radius 3) and track them for 60s."""
    import time
    player.send_line(f"\n{Colors.BOLD}Scanning area...{Colors.RESET}")
    
    # Initialize tracking if missing
    if 'tracked_entities' not in player.ext_state:
        player.ext_state['tracked_entities'] = {} # id -> expiry_time

    radius = 1
    # [V6.8 Fix] Strict Intelligence query: Radius 1, Cardinal Only.
    perception = vision.get_perception(player, radius=radius, context=vision.INTELLIGENCE)
    
    now = time.time()
    expiry = now + 60 # Track for 60 seconds
    
    # Map offsets to direction labels
    def get_pos_label(rx, ry):
        d = {(0,-1): "North", (0,1): "South", (1,0): "East", (-1,0): "West"}
        return d.get((rx, ry), "Nearby")

    found_any = False
    # Filter for CARDINAL ONLY (N, S, E, W)
    coords = [c for c in perception.entities.keys() if abs(c[0]) + abs(c[1]) == 1]
    coords = sorted(coords, key=lambda c: max(abs(c[0]), abs(c[1])))
    
    for (rx, ry) in coords:
        label = get_pos_label(rx, ry)
        color = Colors.YELLOW if (rx == 0 and ry == 0) else Colors.CYAN
        player.send_line(f"{color}{label}:{Colors.RESET}")
        
        for m in perception.entities[(rx, ry)]:
            # Add to persistent tracking (Tactical Map will show 'm' if in_sight)
            player.ext_state['tracked_entities'][str(id(m))] = expiry
            player.send_line(f"  {m.name} [Pinged]")
            found_any = True
    
    if not found_any:
        player.send_line("No life signatures detected nearby.")
    else:
        player.send_line(f"{Colors.GREEN}Signals locked on Tactical Map for 60s.{Colors.RESET}")

@command_manager.register("consider", "con", category="information")
def consider(player, args):
    """Size up a living target to compare their strength to yours."""
    if not args:
        return player.send_line("Consider who?")
        
    target_name = args.lower()
    target = None
    for mob in player.room.monsters:
        if target_name in mob.name.lower():
            target = mob
            break
            
    if not target:
        for p in player.room.players:
            if target_name in p.name.lower() and p != player:
                target = p
                break
                
    if not target:
        return player.send_line(f"You don't see anyone named '{args}' here.")
        
    hp_ratio = target.hp / max(1, player.hp)
    
    if hp_ratio < 0.3:
        msg = f"{Colors.GREEN}{target.name} looks like a weakling. You could crush them easily.{Colors.RESET}"
    elif hp_ratio < 0.7:
        msg = f"{Colors.CYAN}{target.name} looks weaker than you.{Colors.RESET}"
    elif hp_ratio < 1.3:
        msg = f"{Colors.YELLOW}{target.name} appears to be an even match.{Colors.RESET}"
    elif hp_ratio < 2.0:
        msg = f"{Colors.RED}{target.name} looks stronger than you. Be careful.{Colors.RESET}"
    elif hp_ratio < 4.0:
        msg = f"{Colors.RED}{Colors.BOLD}{target.name} would probably turn you into paste.{Colors.RESET}"
    else:
        msg = f"{Colors.MAGENTA}{Colors.BOLD}Flee immediately. {target.name} is a god compared to you.{Colors.RESET}"
        
    player.send_line(f"\n{Colors.BOLD}Considering {target_name.capitalize()}:{Colors.RESET}")
    player.send_line(f" {msg}")
    
    # [V6.0] Deterministic Combat Rating comparison
    from logic.core.math import rating
    p_cr = rating.calculate_entity_rating(player)
    t_cr = rating.calculate_entity_rating(target)
    
    diff = t_cr - p_cr
    trend = f"{Colors.RED}DANGEROUS" if diff > 5 else (f"{Colors.YELLOW}FAIR" if abs(diff) <= 5 else f"{Colors.GREEN}DOMINANT")
    
    player.send_line(f" Power Level: {Colors.BOLD}{Colors.YELLOW}{t_cr}{Colors.RESET} GCR ({trend}{Colors.RESET} vs your {p_cr})")

@command_manager.register("examine", "ex", category="information")
def examine(player, args):
    """Examine an object or target in detail."""
    if not args:
        return player.send_line("Examine what?")
        
    target_name = args.lower()
    
    # Priority 1: Items in inventory or room
    for item in player.room.items + player.inventory:
        if target_name in item.name.lower():
            return player.send_line(f"{Colors.MAGENTA}{item.description}{Colors.RESET}")
            
    # Priority 2: Living targets (Calls consider logic)
    return consider(player, args)

