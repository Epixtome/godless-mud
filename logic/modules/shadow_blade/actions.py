"""
logic/modules/shadow_blade/actions.py
Shadow Blade Class Skills: Born in Dark implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("shadow_strike")
def handle_shadow_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A strike from the shadows strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Shadow Strike")
    resources.modify_resource(player, 'umbral_pips', 1, source="Shadow Strike")
    _consume_resources(player, skill)
    return target, True

@register("blindside")
def handle_blindside(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You strike {target.name} from an unexpected angle.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'umbral_pips', 1, source="Blindside")
    _consume_resources(player, skill)
    return target, True

@register("nightfall_execute")
def handle_nightfall(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}NIGHTFALL!{Colors.RESET} Absolute darkness for {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("shadow_cleave")
def handle_shadow_cleave(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}SHADOW CLEAVE!{Colors.RESET}")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "blinded", 2)
    _consume_resources(player, skill)
    return None, True

@register("shroud_of_night")
def handle_shroud_of_night(player, skill, args, target=None):
    player.send_line(f"You wrap yourself in the silence of night.")
    effects.apply_effect(player, "concealed", 8)
    _consume_resources(player, skill)
    return None, True

@register("umbral_reflexes")
def handle_umbral_reflexes(player, skill, args, target=None):
    player.send_line(f"Your reflexes are as fluid as a shadow.")
    effects.apply_effect(player, "evasive", 4)
    _consume_resources(player, skill)
    return None, True

@register("shadow_step")
def handle_shadow_step(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}SHADOW STEP!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("dark_vision")
def handle_dark_vision(player, skill, args, target=None):
    player.send_line(f"The shadows no longer hinder you.")
    _consume_resources(player, skill)
    return None, True
