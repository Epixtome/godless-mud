#@favor, @learn, @memorize, @allblessings, @reset, @applyeffect, @clearvisited, @revealmap, @vision
import logic.handlers.command_manager as command_manager
from utilities.colors import Colors

@command_manager.register("@favor", admin=True, category="admin")
def favor(player, args):
    """Grant yourself favor."""
    try:
        amount = int(args)
        # Grant favor to all deities for testing
        for d in player.game.world.deities:
            player.favor[d] = player.favor.get(d, 0) + amount
        player.send_line(f"You grant yourself {amount} Favor (All Deities).")
    except ValueError:
        player.send_line("Usage: @favor <amount>")

@command_manager.register("@learn", admin=True, category="admin")
def learn(player, args):
    """Instantly learn and equip a blessing by ID."""
    if not args:
        player.send_line("Usage: @learn <blessing_id>")
        return
    
    from logic.core import search
    candidates = search.find_matches(player.game.world.blessings.values(), args)
    
    if len(candidates) > 1:
        player.send_line(f"Multiple blessings match '{args}':")
        for c in candidates[:5]:
            player.send_line(f"  {c.name} ({c.id})")
        return
    elif not candidates:
        player.send_line("Blessing ID not found.")
        return
        
    b = candidates[0]
    b_id = b.id

    if b_id not in player.known_blessings:
        player.known_blessings.append(b_id)
        from logic.engines import class_engine
        class_engine.check_unlocks(player)
        player.send_line(f"Learned {b.name} ({b_id}).")
        
    if b_id not in player.equipped_blessings:
        player.equipped_blessings.append(b_id)
        player.send_line(f"Memorized {b.name}.")
        from logic.engines import class_engine, synergy_engine
        class_engine.calculate_identity(player)
        synergy_engine.calculate_synergies(player)
    else:
        player.send_line(f"{b.name} is already in your deck.")

@command_manager.register("@allblessings", admin=True, category="admin")
def all_blessings(player, args):
    """Learn all blessings in the game."""
    count = 0
    for b_id in player.game.world.blessings:
        if b_id not in player.known_blessings:
            player.known_blessings.append(b_id)
            count += 1
            
    from logic.engines import class_engine
    class_engine.check_unlocks(player)
    player.send_line(f"Learned {count} new blessings. You now know all {len(player.known_blessings)} blessings.")

@command_manager.register("@reset", admin=True, category="admin")
def reset_char(player, args):
    """Resets HP, resources, cooldowns, state, and clears deck."""
    # 1. Vitals
    player.hp = player.max_hp
    
    # 2. State
    player.state = "normal"
    player.fighting = None
    player.attackers = []
    player.is_resting = False
    
    # 3. Effects & Cooldowns
    player.status_effects = {}
    player.cooldowns = {}
    player.debug_tags = {}
    
    # 4. Deck
    player.equipped_blessings = []
    player.known_blessings = []
    
    # 5. Recalculate Class/Synergies
    from logic.engines import class_engine, synergy_engine
    class_engine.calculate_identity(player)
    synergy_engine.calculate_synergies(player)
    
    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player)
    
    player.send_line(f"{Colors.GREEN}Character reset. Deck cleared. Vitals restored.{Colors.RESET}")

@command_manager.register("@applyeffect", admin=True, category="admin")
def apply_effect_cmd(player, args):
    """Apply a status effect to yourself for testing."""
    parts = args.split()
    if not parts:
        player.send_line("Usage: @applyeffect <effect_id> [duration_seconds]")
        return
    
    effect_id = parts[0]
    duration = int(parts[1]) if len(parts) > 1 else 10
    
    from logic.core import effects
    effects.apply_effect(player, effect_id, duration)

@command_manager.register("@clearvisited", admin=True, category="admin")
def clear_visited(player, args):
    """Clears your visited rooms history (fixes map ghosts)."""
    player.visited_rooms = []
    if player.room:
        player.mark_room_visited(player.room.id)
    player.send_line("Visited rooms history cleared.")

@command_manager.register("@revealmap", admin=True, category="admin")
def reveal_map(player, args):
    """Reveals all rooms in the world (removes Fog of War)."""
    player.visited_rooms = list(player.game.world.rooms.keys())[-200:]
    player.send_line(f"Map revealed. You have now 'visited' {len(player.visited_rooms)} rooms.")

@command_manager.register("@vision", admin=True, category="admin")
def toggle_vision(player, args):
    """Toggle admin debug vision (Room IDs, Coords)."""
    player.admin_vision = not getattr(player, 'admin_vision', False)
    state = "enabled" if player.admin_vision else "disabled"
    player.send_line(f"Admin vision {state}.")

@command_manager.register("@godmode", admin=True, category="admin")
def god_mode(player, args):
    """Toggles God Mode (Invulnerability, No Aggro, Infinite Resources)."""
    player.godmode = not getattr(player, 'godmode', False)
    state = "enabled" if player.godmode else "disabled"
    player.send_line(f"{Colors.YELLOW}God Mode {state}.{Colors.RESET}")
    
    if player.godmode:
        # Restore stats immediately
        player.hp = player.max_hp
        
        # Clear combat state
        player.fighting = None
        player.attackers = []
        player.state = "normal"

@command_manager.register("@class", "@become", admin=True, category="admin")
def become_class(player, args):
    """
    Instantly become a specific class by auto-learning/equipping necessary blessings.
    Usage: @class <class_id>
    """
    if not args:
        player.send_line("Usage: @become <class_id>")
        return

    from logic.core import search
    candidates = search.find_matches(player.game.world.classes.values(), args)
    
    if len(candidates) > 1:
        player.send_line(f"Multiple classes match '{args}':")
        for c in candidates:
            player.send_line(f"  {c.name} ({c.id})")
        return
    elif not candidates:
        player.send_line(f"Class '{args}' not found.")
        return

    target_class = candidates[0]
    class_id = target_class.id

    # Try applying via kit first (Standardized V4.5+)
    from logic.engines import class_engine
    success, msg = class_engine.apply_kit(player, class_id)
    if success:
        player.send_line(f"{Colors.GREEN}{msg}{Colors.RESET}")
        return

    # Fallback to Greedy Search (V4.5 Legacy for unkitted classes)
    player.send_line(f"{Colors.CYAN}No kit found for {target_class.name}, performing greedy blessing search...{Colors.RESET}")
    requirements = getattr(target_class, 'recipe', {})
    if not requirements:
        player.send_line(f"{target_class.name} has no tag requirements.")
        return

    player.equipped_blessings = [] # Reset deck
    needed = requirements.copy()
    iterations = 0
    
    while any(v > 0 for v in needed.values()) and iterations < 20:
        iterations += 1
        best_blessing = None
        best_score = 0
        
        for b in player.game.world.blessings.values():
            if b.id in player.equipped_blessings: continue
            
            score = 0
            for tag in b.identity_tags:
                if needed.get(tag, 0) > 0:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_blessing = b
        
        if best_blessing:
            player.equipped_blessings.append(best_blessing.id)
            if best_blessing.id not in player.known_blessings:
                player.known_blessings.append(best_blessing.id)
            
            for tag in best_blessing.identity_tags:
                if tag in needed:
                    needed[tag] = max(0, needed[tag] - 1)
        else:
            break

    from logic.engines import class_engine, synergy_engine
    class_engine.check_unlocks(player)
    class_engine.calculate_identity(player, preferred_class=class_id)
    synergy_engine.calculate_synergies(player)
    
    # Full State Sync
    if hasattr(player, 'reset_resources'):
        player.reset_resources()

    from logic.engines.resonance_engine import ResonanceAuditor
    ResonanceAuditor.calculate_resonance(player, preferred_class=class_id)

    if player.active_class == class_id:
        player.send_line(f"{Colors.GREEN}You have become a {target_class.name}!{Colors.RESET}")
    else:
        player.send_line(f"{Colors.YELLOW}Equipped best fit, but could not fully meet requirements for {target_class.name}.{Colors.RESET}")
        player.send_line(f"Current Class: {player.active_class}")
