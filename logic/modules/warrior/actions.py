"""
logic/modules/warrior/actions.py
Warrior Class Skills: Veteran's Grit implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("warriors_strike")
def handle_warriors_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A veteran's strike finds {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 20, source="Warrior's Strike")
    resources.modify_resource(player, 'combat_pips', 1, source="Warrior's Strike")
    _consume_resources(player, skill)
    return target, True

@register("battle_cry")
def handle_battle_cry(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}WAR CRY!{Colors.RESET} {target.name} is visibly shaken.")
    effects.apply_effect(target, "weakened", 6)
    resources.modify_resource(player, 'combat_pips', 1, source="Battle Cry")
    _consume_resources(player, skill)
    return target, True

@register("brutal_cleave")
def handle_brutal_cleave(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}BRUTAL CLEAVE!{Colors.RESET} A massive, bloody swing.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("overpowering_blow")
def handle_overpowering_blow(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You overpower {target.name}'s defenses!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "staggered", 4)
    _consume_resources(player, skill)
    return target, True

@register("ignore_pain")
def handle_ignore_pain(player, skill, args, target=None):
    player.send_line(f"You grit your teeth and ignore the pain.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("berserk_leap")
def handle_berserk_leap(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}BERSERK LEAP!{Colors.RESET}")
    effects.apply_effect(player, "unstoppable", 2)
    _consume_resources(player, skill)
    return None, True

@register("war_path")
def handle_war_path(player, skill, args, target=None):
    player.send_line(f"The path of war is all you know.")
    _consume_resources(player, skill)
    return None, True

@register("unbreakable_will")
def handle_unbreakable_will(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}UNBREAKABLE WILL!{Colors.RESET} Life will not leave you.")
    _consume_resources(player, skill)
    return None, True
