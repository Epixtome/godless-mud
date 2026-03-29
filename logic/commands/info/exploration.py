import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from utilities import mapper
from logic.core import perception as vision
from logic.common import get_reverse_direction, find_by_index
from logic.core.utils import display_utils
from logic.core import effects

def _get_status_signals(entity, game):
    """[V7.2] Generates shorthand status symbols for entities."""
    if not hasattr(entity, 'status_effects') or not entity.status_effects:
        return ""
    
    signals = []
    # Key Status Mappings to Shorthand
    MAPPING = {
        "wet": (f"{Colors.CYAN}(W){Colors.RESET}", 1),
        "off_balance": (f"{Colors.MAGENTA}(O){Colors.RESET}", 2),
        "stun": (f"{Colors.YELLOW}(S){Colors.RESET}", 3),
        "dazed": (f"{Colors.YELLOW}(D){Colors.RESET}", 4),
        "prone": (f"{Colors.RED}(P){Colors.RESET}", 5),
        "staggered": (f"{Colors.YELLOW}(St){Colors.RESET}", 6),
        "blinded": (f"{Colors.DGREY}(B){Colors.RESET}", 7),
        "burning": (f"{Colors.RED}(F){Colors.RESET}", 8),
        "frozen": (f"{Colors.BOLD}{Colors.CYAN}(Z){Colors.RESET}", 9)
    }
    
    found = []
    for eff_id in entity.status_effects:
        if eff_id in MAPPING:
            found.append(MAPPING[eff_id])
        else:
            # Fallback for important but unmapped effects
            eff_def = effects.get_effect_definition(eff_id, game)
            if eff_def:
                # [V7.2] Robust metadata extraction
                meta = eff_def.get('metadata', {})
                if isinstance(meta, dict) and meta.get('display_in_prompt'):
                    name = eff_def.get('short_name') or eff_def.get('name', eff_id)
                    found.append((f"({name[:1].upper()})", 99))

    # Sort by priority
    found.sort(key=lambda x: x[1])
    return "".join([x[0] for x in found])

def _get_exit_display(direction, door):
    """[V7.2] Generates shorthand exit markers based on door state."""
    if not door:
        return f"{Colors.GREEN}{direction}{Colors.RESET}"
    
    # [] = Closed, () = Open, {} = Locked
    if door.state == "locked":
        return f"{Colors.RED}{{{direction}}}{Colors.RESET}"
    elif door.state == "closed":
        return f"{Colors.YELLOW}[{direction}]{Colors.RESET}"
    else: # open
        return f"{Colors.GREEN}({direction}){Colors.RESET}"

@command_manager.register("look", "l", category="information")
def look(player, args, with_prompt=True):
    """Look at the current room or an object."""
    output = []

    def send(msg):
        output.append(str(msg))

    def flush():
        if not output:
            return
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
        
        for item in room.items:
            if target_name in item.name.lower() and vision.can_see(player, item):
                send(f"{Colors.MAGENTA}{item.description}{Colors.RESET}"); flush(); return
        for mob in room.monsters:
            if target_name in mob.name.lower() and vision.can_see(player, mob):
                signals = _get_status_signals(mob, player.game)
                status_str = f" {signals}" if signals else ""
                
                # [V7.2] Premium Tactical Scan
                send(f"{Colors.RED}{mob.description}{Colors.RESET}{status_str}")
                
                # Health Bar
                hp_pct = (mob.hp / mob.max_hp) * 100 if mob.max_hp > 0 else 0
                hp_bar = display_utils.render_progress_bar(mob.hp, mob.max_hp, 20, color=Colors.RED)
                
                # GCR Power Level
                from logic.core.math import rating
                m_cr = rating.calculate_entity_rating(mob)
                p_cr = rating.calculate_entity_rating(player)
                diff = m_cr - p_cr
                threat = f"{Colors.RED}DANGEROUS" if diff > 5 else (f"{Colors.YELLOW}FAIR" if abs(diff) <= 5 else f"{Colors.GREEN}DOMINANT")
                
                # Status Effects
                effects_line = ""
                if hasattr(mob, 'status_effects') and mob.status_effects:
                     eff_list = [display_utils.highlight_status_keywords(str(e).upper()) for e in mob.status_effects]
                     effects_line = f"\n {Colors.CYAN}{Colors.BOLD}EFFECTS:{Colors.RESET} {', '.join(eff_list)}"
                
                # Posture / Shields
                bal = mob.resources.get('balance', 100)
                max_bal = mob.resources.get('balance_max', 100) # Check for max balance else fallback
                if max_bal == 100 and hasattr(mob, 'level'): max_bal = 20 + (mob.level * 5)
                
                send(f" {hp_bar} {Colors.WHITE}{int(hp_pct)}%{Colors.RESET} | {Colors.YELLOW}Power: {m_cr} GCR{Colors.RESET} ({threat}{Colors.RESET})")
                send(f" {Colors.MAGENTA}POSTURE: {bal}/{max_bal}{Colors.RESET}{effects_line}")
                
                flush(); return
        for p in room.players:
            if p != player and target_name in p.name.lower() and vision.can_see(player, p):
                signals = _get_status_signals(p, player.game)
                status_str = f" {signals}" if signals else ""
                send(f"{Colors.BLUE}{p.name} is here.{Colors.RESET}{status_str}"); flush(); return

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

    perception = vision.get_perception(player, radius=local_radius, context=vision.NAVIGATION)
    
    map_lines = mapper.draw_grid(
        perception, 
        visited_rooms=player.visited_rooms, 
        discovered_rooms=getattr(player, 'discovered_rooms', []),
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
    # [V7.2] Shorthand Exit Symbols
    for direction, target_id in room.exits.items():
        door = room.doors.get(direction)
        exits.append(_get_exit_display(direction, door))
    send(f"{Colors.YELLOW}Exits: {', '.join(exits)}{Colors.RESET}")
    
    for item in room.items:
        if vision.can_see(player, item): 
            id_str = f" {Colors.DGREY}[{getattr(item, 'prototype_id', 'None')}]{Colors.RESET}" if getattr(player, 'admin_vision', False) else ""
            send(f"{Colors.MAGENTA}{item.description}{Colors.RESET}{id_str}")
            
    for mob in room.monsters:
        if vision.can_see(player, mob):
            signals = _get_status_signals(mob, player.game)
            status_str = f" {signals}" if signals else ""
            id_str = f" {Colors.DGREY}[{getattr(mob, 'prototype_id', 'None')}]{Colors.RESET}" if getattr(player, 'admin_vision', False) else ""
            desc = display_utils.highlight_status_keywords(mob.description)
            send(f"{Colors.RED}{desc}{Colors.RESET}{status_str}{id_str}")
            
    for p in [p for p in room.players if p != player]:
        if vision.can_see(player, p):
            signals = _get_status_signals(p, player.game)
            status_str = f" {signals}" if signals else ""
            # Highlight any state keywords in the player notice if they exist
            player_line = display_utils.highlight_status_keywords(f"{p.name} is here.")
            send(f"{Colors.BLUE}{player_line}{Colors.RESET}{status_str}")

    # [V7.2] Sovereign Shrines
    from logic.core.systems.influence_service import InfluenceService
    inf_service = InfluenceService.get_instance()
    # Find shrines at these specific coordinates
    for s in inf_service.shrines.values():
        if s.coords[0] == room.x and s.coords[1] == room.y and s.coords[2] == room.z:
            k_color = Colors.CYAN if s.captured_by == "light" else (Colors.MAGENTA if s.captured_by == "dark" else Colors.GREEN)
            send(f"{Colors.BOLD}{k_color}[SHRINE] {s.name}{Colors.RESET}")
            send(f"  {Colors.DARK_GRAY}{s.description}{Colors.RESET} {Colors.YELLOW}(Potency: {int(s.potency)}){Colors.RESET}")

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
    
    if 'tracked_entities' in player.ext_state:
        now = time.time()
        player.ext_state['tracked_entities'] = {eid: exp for eid, exp in player.ext_state['tracked_entities'].items() if exp > now}

    perception = vision.get_perception(player, radius=radius, context=vision.TACTICAL)
    
    map_lines = mapper.draw_grid(
        perception,
        visited_rooms=player.visited_rooms, 
        discovered_rooms=getattr(player, 'discovered_rooms', []),
        ignore_fog=getattr(player, 'ignore_fog', False), 
        indent=5, 
        world=player.game.world, 
        shading=True,
        show_dynamic=True
    )

    header = mapper.get_map_header(player.room, player.game.world)
    weather_info = ""
    weather_id = player.room.get_weather() if hasattr(player.room, 'get_weather') else "clear"
    if weather_id != "clear":
        weather_info = f" {Colors.CYAN}[Env: {weather_id.replace('_', ' ').title()}]{Colors.RESET}"
    
    player.send_line(f"--- Map: {header} [Elev: {player.room.elevation}]{weather_info} ---")
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
    """Scan for enemies in the immediate area (Radius 1) and track them for 60s."""
    import time
    player.send_line(f"\n{Colors.BOLD}Scanning area...{Colors.RESET}")
    
    if 'tracked_entities' not in player.ext_state:
        player.ext_state['tracked_entities'] = {}

    radius = 1
    perception = vision.get_perception(player, radius=radius, context=vision.INTELLIGENCE)
    
    now = time.time()
    expiry = now + 60
    
    def get_pos_label(rx, ry):
        d = {(0,-1): "North", (0,1): "South", (1,0): "East", (-1,0): "West"}
        return d.get((rx, ry), "Nearby")

    found_any = False
    # [V7.2 BUG 6 FIX] Coordinates must include current room (0,0) and radius 1 neighbors (dist <= 1).
    coords = [c for c in perception.entities.keys() if max(abs(c[0]), abs(c[1])) <= 1]
    coords = sorted(coords, key=lambda c: max(abs(c[0]), abs(c[1])))
    
    for (rx, ry) in coords:
        label = get_pos_label(rx, ry)
        color = Colors.YELLOW if (rx == 0 and ry == 0) else Colors.CYAN
        player.send_line(f"{color}{label}:{Colors.RESET}")
        
        for m in perception.entities[(rx, ry)]:
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
    
    for item in player.room.items + player.inventory:
        if target_name in item.name.lower():
            return player.send_line(f"{Colors.MAGENTA}{item.description}{Colors.RESET}")
            
    return consider(player, args)
