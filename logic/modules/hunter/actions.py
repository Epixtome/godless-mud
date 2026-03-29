"""
logic/modules/hunter/actions.py
Hunter Class Skills: Master Tracker implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("hunters_shot")
def handle_hunters_shot(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A tracker's shot finds {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 20, source="Hunter's Shot")
    resources.modify_resource(player, 'mark_pips', 1, source="Hunter's Shot")
    _consume_resources(player, skill)
    return target, True

@register("trap_setting")
def handle_trap_setting(player, skill, args, target=None):
    player.send_line(f"You carefully set a concealed trap.")
    resources.modify_resource(player, 'mark_pips', 1, source="Trap Setting")
    _consume_resources(player, skill)
    return None, True

@register("predator_strike")
def handle_predator_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}PREDATOR STRIKE!{Colors.RESET} The hunt ends here.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("rain_of_thorns")
def handle_rain_of_thorns(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}RAIN OF THORNS!{Colors.RESET}")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "bleeding", 6)
    _consume_resources(player, skill)
    return None, True

@register("beast_hide_cloak")
def handle_beast_hide_cloak(player, skill, args, target=None):
    player.send_line(f"You wrap yourself in animal hide, blending in.")
    effects.apply_effect(player, "concealed", 6)
    _consume_resources(player, skill)
    return None, True

@register("wild_evasion")
def handle_wild_evasion(player, skill, args, target=None):
    player.send_line(f"Animal instincts take over.")
    effects.apply_effect(player, "evasive", 4)
    _consume_resources(player, skill)
    return None, True

@register("trek")
def handle_trek(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}TREK!{Colors.RESET}")
    _consume_resources(skill, player) # Typo fixed below
    _consume_resources(player, skill)
    return None, True

@register("call_of_the_wild")
def handle_call_of_the_wild(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CALL OF THE WILD!{Colors.RESET} The pack arrives.")
    _consume_resources(player, skill)
    return None, True
