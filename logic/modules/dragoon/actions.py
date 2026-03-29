"""
logic/modules/dragoon/actions.py
Dragoon Class Skills: Sky Master implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("dragoon_thrust")
def handle_dragoon_thrust(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A long-range polearm thrust strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Dragoon Thrust")
    resources.modify_resource(player, 'jump_pips', 1, source="Dragoon Thrust")
    _consume_resources(player, skill)
    return target, True

@register("dragon_breath")
def handle_dragon_breath(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You exhale a burst of heat upon {target.name}.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'jump_pips', 1, source="Dragon Breath")
    _consume_resources(player, skill)
    return target, True

@register("dragon_dive")
def handle_dragon_dive(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}DRAGON DIVE!{Colors.RESET} You strike from the heavens!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("leg_sweep")
def handle_leg_sweep(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You sweep {target.name}'s feet with your polearm.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "prone", 3)
    _consume_resources(player, skill)
    return target, True

@register("steel_scale")
def handle_steel_scale(player, skill, args, target=None):
    player.send_line(f"Your muscles tense like armor plates.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("high_jump_defense")
def handle_high_jump_defense(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}HIGH JUMP!{Colors.RESET} You leap high above the fray.")
    effects.apply_effect(player, "untargetable", 1)
    _consume_resources(player, skill)
    return None, True

@register("dragoon_jump")
def handle_dragoon_jump(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}DRAGOON JUMP!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("dragonheart")
def handle_dragonheart(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}DRAGONHEART!{Colors.RESET} Absolute focus.")
    _consume_resources(player, skill)
    return None, True
