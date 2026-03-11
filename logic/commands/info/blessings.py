import logic.handlers.command_manager as command_manager
from utilities.colors import Colors
from logic.core.utils import display_utils

@command_manager.register("deck", category="information")
def deck(player, args):
    """View your currently equipped blessings (Deck)."""
    width = 60
    cls_id = player.active_class or "wanderer"
    cls_obj = player.game.world.classes.get(cls_id)
    cls_name = cls_obj.name if cls_obj else cls_id.capitalize()
    
    player.send_line(f"\n{display_utils.render_header(f'{cls_name} Deck', width, '=')}")
    
    if not player.equipped_blessings:
        player.send_line(f"  {Colors.WHITE}No blessings equipped. Use 'memorize <id>' to fill your soul.{Colors.RESET}")
    else:
        blessings = []
        for b_id in player.equipped_blessings:
            b = player.game.world.blessings.get(b_id)
            if b: blessings.append(b)
        blessings.sort(key=lambda x: x.tier)

        for b in blessings:
            if "hidden" in getattr(b, 'identity_tags', []): continue

            tier_color = Colors.WHITE
            if b.tier == 2: tier_color = Colors.GREEN
            elif b.tier == 3: tier_color = Colors.CYAN
            elif b.tier == 4: tier_color = Colors.MAGENTA
            elif b.tier == 5: tier_color = Colors.YELLOW

            tags = " ".join([f"#{t}" for t in b.identity_tags if t != "hidden"])
            
            # Formatted Layout: Name and Desc on same line, Tags under
            player.send_line(f" {tier_color}T{b.tier}{Colors.RESET} | {Colors.BOLD}{b.name:<18}{Colors.RESET} - {Colors.ITALIC}{b.description}{Colors.RESET}")
            if tags:
                player.send_line(f"      {Colors.DGREY}{tags}{Colors.RESET}")
    
    player.send_line(display_utils.render_line(width))
    
    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player)
    breakthroughs = [t.title() for t, v in player.current_tags.items() if v >= 10]
    
    if breakthroughs:
        player.send_line(f" {Colors.CYAN}{Colors.BOLD}BREAKTHROUGHS:{Colors.RESET} {', '.join(breakthroughs)}")
        player.send_line(display_utils.render_line(width))
    
    # Show Deck Utilization
    from logic.calibration import MaxValues
    usage = len(player.equipped_blessings)
    bar = display_utils.render_progress_bar(usage, MaxValues.DECK_SIZE, 20)
    player.send_line(f" Capacity: {bar} {usage}/{MaxValues.DECK_SIZE}")
    player.send_line(f"{display_utils.render_line(width, '=')}")

@command_manager.register("blessings", "abilities", "spells", "skills", category="information")
def list_blessings(player, args):
    """Lists all known blessings with descriptions."""
    if not player.known_blessings:
        return player.send_line("You haven't learned any blessings yet.")

    search_term = args.lower() if args else None
    cat = {"Skills": [], "Spells": [], "Songs": [], "Passives": []}

    for b_id in player.known_blessings:
        b = player.game.world.blessings.get(b_id)
        if not b: continue
        if search_term and (search_term not in b.name.lower() and search_term not in (getattr(b, 'description', '') or '').lower()):
            continue

        tags = getattr(b, 'identity_tags', [])
        status = f"{Colors.GREEN}[Equipped]{Colors.RESET}" if b.id in player.equipped_blessings else ""
        d_id = getattr(b, 'deity_id', None)
        origin = f" ({d_id.title()})" if d_id else ""
        info = f"{Colors.CYAN}{b.name}{Colors.RESET}{origin}: {b.description} {status}"
        
        if "skill" in tags: cat["Skills"].append(info)
        elif "spell" in tags: cat["Spells"].append(info)
        elif "song" in tags: cat["Songs"].append(info)
        else: cat["Passives"].append(info)

    player.send_line(f"\n{display_utils.render_header('Known Blessings', 60)}")
    for title, list_ in cat.items():
        if list_:
            player.send_line(f"\n {Colors.BOLD}{title}{Colors.RESET}")
            for item in sorted(list_): player.send_line(f"  {item}")

@command_manager.register("passives", "bonuses", "effects", "afflictions", category="information")
def list_passives(player, args):
    """List active passive blessings and status effects."""
    player.send_line(f"\n{display_utils.render_header('Active Passives', 60)}")
    
    found = False
    for b_id in player.known_blessings:
        b = player.game.world.blessings.get(b_id)
        if b and "passive" in b.identity_tags:
            player.send_line(f" {Colors.GREEN}{b.name}{Colors.RESET}: {b.description}")
            found = True
    if not found: player.send_line(" No passive blessings.")
        
    player.send_line(f"\n{display_utils.render_header('Active Effects', 60, '-')}")
    if player.status_effects:
        for eff_id, expiry in player.status_effects.items():
            eff_data = player.game.world.status_effects.get(eff_id, {})
            desc = eff_data.get('description', eff_id)
            rem = (expiry - player.game.tick_count) * 2
            player.send_line(f" {Colors.CYAN}{eff_id:<20}{Colors.RESET} ({rem}s): {desc}")
    else: player.send_line(" No active effects.")
@command_manager.register("memorize", "equip", category="information")
def memorize(player, args):
    """Equip a known blessing to your active deck."""
    if not args:
        player.send_line("Usage: memorize <blessing_id>")
        return

    b_id = args.lower()
    if b_id not in player.known_blessings:
        player.send_line(f"You don't know the blessing '{b_id}'.")
        return

    if b_id in player.equipped_blessings:
        player.send_line("That blessing is already equipped.")
        return

    from logic.calibration import MaxValues
    if len(player.equipped_blessings) >= MaxValues.DECK_SIZE:
        player.send_line(f"{Colors.RED}Your deck is full ({MaxValues.DECK_SIZE}/{MaxValues.DECK_SIZE}). Forget a blessing first.{Colors.RESET}")
        return

    player.equipped_blessings.append(b_id)
    player.send_line(f"{Colors.GREEN}You have memorized {b_id}.{Colors.RESET}")
    from logic.engines import class_engine
    class_engine.calculate_identity(player)

@command_manager.register("forget", "unequip", category="information")
def forget(player, args):
    """Remove a blessing from your active deck (you keep the knowledge)."""
    if not args:
        player.send_line("Usage: forget <blessing_id>")
        return

    b_id = args.lower()
    if b_id not in player.equipped_blessings:
        player.send_line(f"'{b_id}' is not currently in your deck.")
        return

    player.equipped_blessings.remove(b_id)
    player.send_line(f"{Colors.YELLOW}You have forgotten {b_id}.{Colors.RESET}")
    from logic.engines import class_engine
    class_engine.calculate_identity(player)
