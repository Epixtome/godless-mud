"""
logic/modules/gunner/actions.py
Gunner Class Skills: Ballistic Specialist implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("double_tap")
def handle_double_tap(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Pop! Pop! You double tap {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Double Tap")
    resources.modify_resource(player, 'ammo_pips', 1, source="Double Tap")
    _consume_resources(player, skill)
    return target, True

@register("hollow_point")
def handle_hollow_point(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You load hollow-point rounds, aiming for {target.name}'s vitals.")
    effects.apply_effect(target, "bleeding", 8)
    resources.modify_resource(player, 'ammo_pips', 1, source="Hollow Point")
    _consume_resources(player, skill)
    return target, True

@register("gunner_headshot")
def handle_headshot(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}HEADSHOT!{Colors.RESET} Point of precision.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("buckshot")
def handle_buckshot(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}BUCKSHOT!{Colors.RESET} Lead fills the room!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("covering_fire")
def handle_covering_fire(player, skill, args, target=None):
    player.send_line(f"Suppressive fire! Enemies are pinned down.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "weakened", 4)
    _consume_resources(player, skill)
    return None, True

@register("flashbang")
def handle_flashbang(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}FLASHBANG!{Colors.RESET} Blinding everyone.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "blinded", 2)
        effects.apply_effect(t, "dazed", 2)
    _consume_resources(player, skill)
    return None, True

@register("tactical_slide")
def handle_tactical_slide(player, skill, args, target=None):
    player.send_line(f"You slide into position, breaking free of any restrictions.")
    _consume_resources(player, skill)
    return None, True

@register("rapid_fire")
def handle_rapid_fire(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}RAPID FIRE!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
