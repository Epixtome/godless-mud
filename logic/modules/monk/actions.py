"""
logic/modules/monk/actions.py
Monk Class Skills: Palm Strike, Dragon Strike, Triple Kick, etc.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors
from logic.modules.monk.utils import consume_flow, get_target, consume_resources

@register("iron_palm")
def handle_iron_palm(player, skill, args, target=None):
    target = get_target(player, args, target)
    if not target: return None, True
    
    # [V4.5] Unified Combat Facade: No fixed damage.
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}IRON PALM!{Colors.RESET} You strike {target.name} with focused force!")
    player.room.broadcast(f"{player.name} strikes {target.name} with a heavy iron palm!", exclude_player=player)
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Specialized Status (Dazed) - Chance based on tier
    effects.apply_effect(target, "dazed", 2) # Dazed now blocks skills!
    
    consume_resources(player, skill)
    return target, True

@register("palm_strike")
def handle_palm_strike(player, skill, args, target=None):
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.YELLOW}Palm Strike!{Colors.RESET}")
    effects.apply_effect(target, "stun", 1)
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    consume_resources(player, skill)
    return target, True

@register("dragon_strike")
def handle_dragon_strike(player, skill, args, target=None):
    target = get_target(player, args, target)
    if not target: return None, True
    flow = player.ext_state.get('monk', {}).get('flow_pips', 0)
    if flow < 1:
        player.send_line(f"{Colors.RED}You need Flow!{Colors.RESET}"); return None, True
    player.send_line(f"{Colors.CYAN}DRAGON STRIKE!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    consume_resources(player, skill)
    return target, True

@register("triple_kick")
def handle_triple_kick(player, skill, args, target=None):
    target = get_target(player, args, target)
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}Triple Kick!{Colors.RESET}")
    player.room.broadcast(f"{player.name} unleashes a rapid series of kicks!", exclude_player=player)

    # Triple attack (Calls handle_attack 3x to simulate three separate strikes)
    for i in range(3):
        if not combat.is_target_valid(player, target) or target.hp <= 0:
            break
            
        # [V4.5] We use handle_attack with the skill to ensure correct scaling/events for each bolt
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        
    consume_resources(player, skill)
    return target, True

@register("meditate")
def handle_meditate(player, skill, args, target=None):
    from logic.engines import action_manager
    if player.fighting:
        player.send_line("You cannot meditate while fighting!")
        return None, True
        
    if "meditating" in getattr(player, 'status_effects', {}):
        player.send_line("You are already meditating.")
        return None, True
        
    async def _finish_rest():
        player.send_line(f"{Colors.GREEN}You feel completely rested and focused.{Colors.RESET}")
        effects.remove_effect(player, "meditating")

    def _cleanup_rest():
        effects.remove_effect(player, "meditating")

    player.send_line(f"{Colors.GREEN}You sit and focus into a meditative state...{Colors.RESET}")
    effects.apply_effect(player, "meditating", 10, verbose=False)
    action_manager.start_action(player, 6.0, _finish_rest, tag="resting", fail_msg="You stand up, breaking your meditation.", on_interrupt=_cleanup_rest)
    consume_resources(player, skill)
    return None, True
