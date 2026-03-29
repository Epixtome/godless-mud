"""
logic/modules/soldier/actions.py
Soldier Class Skills: Combat Veteran implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("soldiers_strike")
def handle_soldiers_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A disciplined strike hits {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 20, source="Soldier's Strike")
    resources.modify_resource(player, 'order_pips', 1, source="Soldier's Strike")
    _consume_resources(player, skill)
    return target, True

@register("shield_bash")
def handle_shield_bash(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You slam your shield into {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "stun", 1)
    resources.modify_resource(player, 'order_pips', 1, source="Shield Bash")
    _consume_resources(player, skill)
    return target, True

@register("phalanx_thrust")
def handle_phalanx_thrust(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}PHALANX THRUST!{Colors.RESET} Power from discipline.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("disciplined_volley")
def handle_disciplined_volley(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}DISCIPLINED VOLLEY!{Colors.RESET} Support fire incoming!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("defensive_hunker")
def handle_defensive_hunker(player, skill, args, target=None):
    player.send_line(f"You hunker down, becoming a bastion.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("tactical_retreat")
def handle_tactical_retreat(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}TACTICAL RETREAT!{Colors.RESET}")
    effects.apply_effect(player, "shielded", 2)
    _consume_resources(player, skill)
    return None, True

@register("marching_pace")
def handle_marching_pace(player, skill, args, target=None):
    player.send_line(f"Forward, march!")
    effects.apply_effect(player, "haste", 4)
    _consume_resources(player, skill)
    return None, True

@register("rally_the_troops")
def handle_rally_the_troops(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}RALLY!{Colors.RESET} Inspiration fills your group.")
    _consume_resources(player, skill)
    return None, True
