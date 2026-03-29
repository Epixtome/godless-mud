"""
logic/modules/berserker/actions.py
Berserker Class Skills: Blood God's Chosen implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("raging_strike")
def handle_raging_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.RED}A raging strike fueled by blood!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Raging Strike")
    resources.modify_resource(player, 'fury', 5, source="Raging Strike")
    _consume_resources(player, skill)
    return target, True

@register("blood_thirst")
def handle_blood_thirst(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You thirst for {target.name}'s blood.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'fury', 10, source="Blood Thirst")
    _consume_resources(player, skill)
    return target, True

@register("reckless_abandon")
def handle_reckless_abandon(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}RECKLESS ABANDON!{Colors.RESET} You throw safety to the wind!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'hp', -int(player.hp * 0.1), source="Reckless Abandon")
    _consume_resources(player, skill)
    return target, True

@register("gorespatter")
def handle_gorespatter(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}GORESPATTER!{Colors.RESET} A fountain of blood erupts!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "bleeding", 6)
    _consume_resources(player, skill)
    return None, True

@register("pain_suppressor")
def handle_pain_suppressor(player, skill, args, target=None):
    player.send_line(f"You turn your pain into strength.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("headbutt")
def handle_headbutt(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You slam your skull into {target.name}!")
    effects.apply_effect(target, "stun", 2)
    _consume_resources(player, skill)
    return target, True

@register("brute_charge")
def handle_brute_charge(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}BRUTE CHARGE!{Colors.RESET} Nothing can stop you.")
    _consume_resources(player, skill)
    return None, True

@register("berserker_rage")
def handle_berserker_rage(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}BERSERKER RAGE!{Colors.RESET}")
    effects.apply_effect(player, "berserking", 15)
    resources.modify_resource(player, 'hp', -(player.hp - 1), source="Berserker Rage")
    _consume_resources(player, skill)
    return None, True
