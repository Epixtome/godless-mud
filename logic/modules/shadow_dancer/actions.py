"""
logic/modules/shadow_dancer/actions.py
Shadow Dancer Class Skills: Shadow Flow implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("dance_of_shadows")
def handle_dance_of_shadows(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A dance of flowing shadow strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Dance of Shadows")
    resources.modify_resource(player, 'flow_pips', 1, source="Dance of Shadows")
    _consume_resources(player, skill)
    return target, True

@register("veiled_motion")
def handle_veiled_motion(player, skill, args, target=None):
    player.send_line(f"Your movements become veiled in shifting shadows.")
    resources.modify_resource(player, 'flow_pips', 1, source="Veiled Motion")
    effects.apply_effect(player, "haste", 4)
    _consume_resources(player, skill)
    return None, True

@register("twilight_finale")
def handle_twilight_finale(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}TWILIGHT FINALE!{Colors.RESET} A series of spectral strikes.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("spinning_shadow")
def handle_spinning_shadow(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}SPINNING SHADOW!{Colors.RESET}")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("illusory_double")
def handle_illusory_double(player, skill, args, target=None):
    player.send_line(f"An illusory double fades into focus beside you.")
    effects.apply_effect(player, "evasive", 2)
    _consume_resources(player, skill)
    return None, True

@register("graceful_evasion")
def handle_graceful_evasion(player, skill, args, target=None):
    player.send_line(f"You move as if part of the dark.")
    effects.apply_effect(player, "evasive", 6)
    _consume_resources(player, skill)
    return None, True

@register("shadow_leap")
def handle_shadow_leap(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}SHADOW LEAP!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("shadow_melter")
def handle_shadow_melter(player, skill, args, target=None):
    player.send_line(f"You melt into the surrounding shadows.")
    effects.apply_effect(player, "concealed", 4)
    _consume_resources(player, skill)
    return None, True
