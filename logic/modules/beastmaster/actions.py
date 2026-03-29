"""
logic/modules/beastmaster/actions.py
Beastmaster Class Skills: Pack Alpha implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("wild_strike")
def handle_wild_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You strike with primal ferocity at {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Wild Strike")
    resources.modify_resource(player, 'bond_pips', 1, source="Wild Strike")
    _consume_resources(player, skill)
    return target, True

@register("tame_beast")
def handle_tame_beast(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You establish a psychic bond with {target.name}.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'bond_pips', 1, source="Tame Beast")
    _consume_resources(player, skill)
    return target, True

@register("bestial_wrath")
def handle_bestial_wrath(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}BESTIAL WRATH!{Colors.RESET} Your companion enters a frenzy!")
    _consume_resources(player, skill)
    return None, True

@register("coordinated_kill")
def handle_coordinated_kill(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}COORDINATED KILL!{Colors.RESET} You and your companion strike as one!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("pack_bond")
def handle_pack_bond(player, skill, args, target=None):
    player.send_line(f"You link your life force with your pack.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("intimidating_roar")
def handle_intimidating_roar(player, skill, args, target=None):
    player.send_line(f"A deafening roar shatters the room's morale.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "stun", 2)
    _consume_resources(player, skill)
    return None, True

@register("feral_leap")
def handle_feral_leap(player, skill, args, target=None):
    player.send_line(f"You leap with predatory grace.")
    _consume_resources(player, skill)
    return None, True

@register("call_companion")
def handle_call_companion(player, skill, args, target=None):
    player.send_line(f"You call your beast back to your side.")
    _consume_resources(player, skill)
    return None, True
