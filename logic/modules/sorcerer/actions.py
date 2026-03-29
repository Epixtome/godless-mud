"""
logic/modules/sorcerer/actions.py
Sorcerer Class Skills: Chaos Born implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("chaos_bolt")
def handle_chaos_bolt(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.MAGENTA}A bolt of shifting energy strikes {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Chaos Bolt")
    resources.modify_resource(player, 'chaos_pips', 1, source="Chaos Bolt")
    _consume_resources(player, skill)
    return target, True

@register("unstable_affliction")
def handle_unstable_affliction(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You curse {target.name} with unstable energy.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'chaos_pips', 1, source="Unstable Affliction")
    _consume_resources(player, skill)
    return target, True

@register("chaos_cataclysm")
def handle_chaos_cataclysm(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}CHAOS CATACLYSM!{Colors.RESET} The room erupting in random elements!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("mental_burn")
def handle_mental_burn(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}MENTAL BURN!{Colors.RESET} You incinerate {target.name}'s mind!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "blinded", 3)
    _consume_resources(player, skill)
    return target, True

@register("shimmering_skin")
def handle_shimmering_skin(player, skill, args, target=None):
    player.send_line(f"Your form becomes hazy and unstable.")
    effects.apply_effect(player, "evasive", 6)
    _consume_resources(player, skill)
    return None, True

@register("unstable_shield")
def handle_unstable_shield(player, skill, args, target=None):
    player.send_line(f"An unstable field of energy surrounds you.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("chaos_blink")
def handle_chaos_blink(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}CHAOS BLINK!{Colors.RESET}")
    effects.apply_effect(player, "untargetable", 1)
    _consume_resources(player, skill)
    return None, True

@register("wild_magic_surge")
def handle_wild_magic_surge(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}WILD MAGIC SURGE!{Colors.RESET} Pure chaos.")
    _consume_resources(player, skill)
    return None, True
