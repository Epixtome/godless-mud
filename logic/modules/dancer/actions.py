"""
logic/modules/dancer/actions.py
Dancer Class Skills: Perfect Tempo implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("step_strike")
def handle_step_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A rhythmic strike finds {target.name} between beats.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Step Strike")
    resources.modify_resource(player, 'rhythm_pips', 1, source="Step Strike")
    _consume_resources(player, skill)
    return target, True

@register("graceful_entry")
def handle_graceful_entry(player, skill, args, target=None):
    player.send_line(f"You enter the battlefield with poetic motion.")
    resources.modify_resource(player, 'rhythm_pips', 2, source="Graceful Entry")
    effects.apply_effect(player, "haste", 4)
    _consume_resources(player, skill)
    return None, True

@register("bladed_waltz")
def handle_bladed_waltz(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}BLADED WALTZ!{Colors.RESET} A blur of steel and grace.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("pirouette_slam")
def handle_pirouette_slam(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You spin gracefully, slamming your blade into {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "staggered", 4)
    _consume_resources(player, skill)
    return target, True

@register("defensive_dance")
def handle_defensive_dance(player, skill, args, target=None):
    player.send_line(f"You focus entirely on avoiding incoming strikes through dance.")
    effects.apply_effect(player, "evasive", 6)
    _consume_resources(player, skill)
    return None, True

@register("enchanting_sway")
def handle_enchanting_sway(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Your hypnotic movements daze {target.name}.")
    effects.apply_effect(target, "dazed", 2)
    _consume_resources(player, skill)
    return target, True

@register("flourish_dash")
def handle_flourish_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}FLOURISH DASH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("finale_encore")
def handle_finale_encore(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}FINALE ENCORE!{Colors.RESET} The performance continues.")
    _consume_resources(player, skill)
    return None, True
