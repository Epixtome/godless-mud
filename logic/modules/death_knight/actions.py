"""
logic/modules/death_knight/actions.py
Death Knight Class Skills: Lord of Woe implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("death_strike")
def handle_death_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A necrotic strike from your blade drains {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Death Strike")
    resources.modify_resource(player, 'death_pips', 1, source="Death Strike")
    _consume_resources(player, skill)
    return target, True

@register("frost_fever")
def handle_frost_fever(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You infect {target.name} with a freezing disease.")
    effects.apply_effect(target, "chilled", 4)
    resources.modify_resource(player, 'death_pips', 1, source="Frost Fever")
    _consume_resources(player, skill)
    return target, True

@register("oblivion_strike")
def handle_oblivion_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}OBLIVION STRIKE!{Colors.RESET} A hit from the void.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("death_and_decay")
def handle_death_and_decay(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}DEATH AND DECAY!{Colors.RESET} The ground beneath you rots.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("bone_shield")
def handle_bone_shield(player, skill, args, target=None):
    player.send_line(f"A shield of whirling bones surrounds you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("unbreakable_will")
def handle_unbreakable_will(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}UNBREAKABLE WILL!{Colors.RESET}")
    effects.apply_effect(player, "unstoppable", 2)
    _consume_resources(player, skill)
    return None, True

@register("death_grip")
def handle_death_grip(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.MAGENTA}DEATH GRIP!{Colors.RESET} You pull {target.name} close.")
    _consume_resources(player, skill)
    return target, True

@register("army_of_the_dead")
def handle_army_of_the_dead(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}ARMY OF THE DEAD!{Colors.RESET} The fallen rise.")
    _consume_resources(player, skill)
    return None, True
