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
    if not consume_flow(player, 5):
        player.send_line(f"{Colors.RED}You need 5 Flow!{Colors.RESET}")
        return None, True
    player.send_line(f"{Colors.RED}IRON PALM!{Colors.RESET} You strike {target.name}!")
    resources.modify_resource(target, "hp", -20, source=player, context="Iron Palm")
    effects.apply_effect(target, "stun", 1)
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
    # Triple attack (Simplified for now, engine handles the repeat if scaled)
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    consume_resources(player, skill)
    return target, True

@register("meditate")
def handle_meditate(player, skill, args, target=None):
    player.send_line(f"{Colors.GREEN}You sit and focus...{Colors.RESET}")
    # Logic is handled by on_skill_execute event
    consume_resources(player, skill)
    return None, True
