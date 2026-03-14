from logic.actions.registry import register
from logic.core import resources, effects, combat
from logic import common
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

def _add_echo(player):
    state = player.ext_state.setdefault('illusionist', {})
    if state.get('echoes', 0) < state.get('max_echoes', 3):
        state['echoes'] = state.get('echoes', 0) + 1
        return True
    return False

@register("color_spray")
def handle_color_spray(player, skill, args, target=None):
    """Builder: Deals light damage, blinds, and generates 1 Echo."""
    target = common._get_target(player, args, target, "Spray colors at whom?")
    if not target: return None, True

    # Generate Echo
    if _add_echo(player):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}[ECHO] An illusory double coalesces!{Colors.RESET}")
    
    # Blind
    effects.apply_effect(target, "blind", 8)
    
    # Damage
    dmg = combat.calculate_damage(player, target) // 2 # Builder dmg is low
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("screaming_wall")
def handle_screaming_wall(player, skill, args, target=None):
    """Breaker: Spawns a disruptive wall that deals balance damage."""
    from logic import mob_manager
    wall = mob_manager.spawn_mob(player.room, "screaming_wall", player.game)
    if wall:
        wall.owner_id = player.id
        player.send_line(f"{Colors.MAGENTA}You manifest a Screaming Wall of spectral faces!{Colors.RESET}")
        player.room.broadcast(f"A wall of wailing spectral faces rises to guard {player.name}!", exclude_player=player)
        
        # If in combat, have the wall target our enemy
        if player.fighting:
            wall.fighting = player.fighting
            
    _consume_resources(player, skill)
    return None, True

@register("decoy")
def handle_decoy(player, skill, args, target=None):
    """Tech: Drops aggro, forces retargeting to a new echo, and generates 1 Echo."""
    from logic import mob_manager
    
    # Drop Aggro logic
    if player.fighting:
        old_target = player.fighting
        player.fighting = None
        
        # Spawn Decoy
        decoy = mob_manager.spawn_mob(player.room, "illusionist_echo", player.game)
        if decoy:
            decoy.owner_id = player.id
            decoy.name = f"{player.name}'s Echo"
            decoy.fighting = old_target
            
            # Force target to fight decoy
            if hasattr(old_target, 'fighting'):
                old_target.fighting = decoy
            
            player.send_line(f"{Colors.CYAN}You blink away, leaving a decoy in your wake!{Colors.RESET}")
            player.room.broadcast(f"{player.name} shimmers and vanishes, but a double remains!", exclude_player=player)
    else:
        player.send_line("You conjure a decoy beside you.")
        mob_manager.spawn_mob(player.room, "illusionist_echo", player.game)

    _add_echo(player)
    _consume_resources(player, skill)
    return None, True

@register("haste")
def handle_haste(player, skill, args, target=None):
    """Buff: Increases attack frequency and evasion."""
    effects.apply_effect(player, "haste", 45)
    player.send_line(f"{Colors.YELLOW}Time slows down as your pulse quickens...{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("phantasmal_inferno")
def handle_phantasmal_inferno(player, skill, args, target=None):
    """Payoff: Consumes all Echoes for massive Psychic/Fire damage."""
    target = common._get_target(player, args, target, "Unleash the inferno on whom?")
    if not target: return None, True

    state = player.ext_state.get('illusionist', {})
    echo_count = state.get('echoes', 0)
    
    if echo_count == 0:
        player.send_line(f"{Colors.RED}You have no echoes to fuel the phantasm!{Colors.RESET}")
        return None, True

    # Massive Base Scaled by Echoes
    base_dmg = 20 + (echo_count * 20) # 40, 60, 80
    
    # Fire + Psychic tags for maximum coverage
    skill_tags = {"fire", "psychic", "illusion", "payoff"}
    
    player.send_line(f"{Colors.BOLD}{Colors.RED}You shatter your echoes into a raging Phantasmal Inferno!{Colors.RESET}")
    player.room.broadcast(f"The illusory doubles around {player.name} ignite into a psychic firestorm!", exclude_player=player)
    
    # Manual damage application for the payoff
    from logic.core.utils import combat_logic
    combat_logic.check_posture_break(target, base_dmg, source=player, tags=skill_tags)
    resources.modify_resource(target, "hp", -base_dmg, source=player, context="Phantasmal Inferno")
    
    # Reset Echoes
    state['echoes'] = 0
    
    _consume_resources(player, skill)
    return target, True
