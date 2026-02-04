import logic.command_manager as command_manager
from logic.engines import magic_engine
import logic.search as search
from logic.engines.blessings_engine import Auditor, MathBridge
from utilities.colors import Colors

@command_manager.register("cast", category="magic")
def cast(player, args, target_obj=None):
    """Cast a blessing."""
    if not args and not target_obj:
        player.send_line("Cast what?")
        return
        
    # If called internally with target_obj, args is just the spell name
    if target_obj:
        spell_name = args
    else:
        parts = args.split()
        spell_name = parts[0]
        target_name = parts[1] if len(parts) > 1 else None
    
    # 1. Find Blessing
    # Check world prototypes (or equipped in future)
    blessing = search.search_list(player.game.world.blessings.values(), spell_name)
            
    if not blessing:
        player.send_line("You don't know that blessing.")
        return

    # 2. Determine Target
    target = target_obj
    if not target and target_name:
        # Special handling for directional spells (Farsight)
        if "farsight" in blessing.identity_tags or "line" in blessing.identity_tags:
            valid_dirs = {
                'n': 'north', 's': 'south', 'e': 'east', 'w': 'west', 'u': 'up', 'd': 'down',
                'north': 'north', 'south': 'south', 'east': 'east', 'west': 'west', 'up': 'up', 'down': 'down'
            }
            if target_name.lower() in valid_dirs:
                target = valid_dirs[target_name.lower()]
            else:
                player.send_line("Invalid direction.")
                return
        else:
            target = search.find_living(player.room, target_name)
            if not target:
                 player.send_line(f"You don't see '{target_name}' here.")
                 return
    elif not target and not target_name:
        # Default to self ONLY for beneficial spells
        if "heal" in blessing.identity_tags or "buff" in blessing.identity_tags or "utility" in blessing.identity_tags:
            target = player
        elif player.fighting: # Auto-target current enemy
            target = player.fighting
        else:
            player.send_line("Cast on whom?")
            return

    # 3. Checks (Auditor handles Stats, Cooldowns, Resources, Items)
    ok, msg = Auditor.can_invoke(blessing, player)
    if not ok:
        player.send_line(msg)
        return
        
    # 4. Pacing Check
    can_pace, reason_pace = magic_engine.check_pacing(player, blessing)
    if not can_pace:
        player.send_line(reason_pace)
        return

    # 5. Execute
    magic_engine.consume_resources(player, blessing)
    magic_engine.set_cooldown(player, blessing)
    magic_engine.consume_pacing(player, blessing)
    
    # Calculate Power
    power = MathBridge.calculate_power(blessing, player)
    
    success, msg, target_died = magic_engine.process_spell_effect(player, target, blessing, power)
    player.send_line(msg)
    if target != player:
        t_name = target.name if hasattr(target, 'name') else str(target)
        player.room.broadcast(f"{player.name} casts {blessing.name} on {t_name}!", exclude_player=player)
        
        # Trigger Combat if offensive
        is_offensive = not ("heal" in blessing.identity_tags or "buff" in blessing.identity_tags or "utility" in blessing.identity_tags)
        if is_offensive and not target_died and hasattr(target, 'hp'):
            if not player.fighting:
                player.fighting = target
                player.state = "combat"
            
            if hasattr(target, 'fighting'): # Is a mob or player
                if not target.fighting:
                    target.fighting = player
                    if hasattr(target, 'state'): target.state = "combat"
                if player not in target.attackers:
                    target.attackers.append(player)
    return

@command_manager.register("spells", category="information")
def list_spells(player, args):
    """List your known and equipped spells."""
    player.send_line(f"\n--- {Colors.BOLD}Spells{Colors.RESET} ---")
    
    # Equipped Spells
    equipped = []
    for b_id in player.equipped_blessings:
        b = player.game.world.blessings.get(b_id)
        if b and "spell" in b.identity_tags:
            equipped.append(b)
            
    if equipped:
        player.send_line(f"{Colors.YELLOW}Equipped:{Colors.RESET}")
        for b in equipped:
            player.send_line(f"  {b.name} (T{b.tier})")
    else:
        player.send_line("No spells equipped.")

    # Known Spells (not equipped)
    known = []
    for b_id in player.known_blessings:
        if b_id not in player.equipped_blessings:
            b = player.game.world.blessings.get(b_id)
            if b and "spell" in b.identity_tags:
                known.append(b)
    
    if known:
        player.send_line(f"\n{Colors.CYAN}Known:{Colors.RESET}")
        for b in known:
            player.send_line(f"  {b.name} (T{b.tier})")