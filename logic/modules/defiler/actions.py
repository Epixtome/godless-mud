"""
logic/modules/defiler/actions.py
Defiler Class Skills: Rot Lord implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("putrid_strike")
def handle_putrid_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A toxic, rot-infused strike hits {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Putrid Strike")
    resources.modify_resource(player, 'rot_pips', 1, source="Putrid Strike")
    _consume_resources(player, skill)
    return target, True

@register("festering_wound")
def handle_festering_wound(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You create a festering wound in {target.name}.")
    effects.apply_effect(target, "bleeding", 6)
    resources.modify_resource(player, 'rot_pips', 1, source="Festering Wound")
    _consume_resources(player, skill)
    return target, True

@register("toxic_collapse")
def handle_toxic_collapse(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}TOXIC COLLAPSE!{Colors.RESET} Corruption bursts from {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("miasma_explosion")
def handle_miasma_explosion(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}MIASMA EXPLOSION!{Colors.RESET}")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "toxic", 4)
    _consume_resources(player, skill)
    return None, True

@register("carapace_of_decay")
def handle_carapace_of_decay(player, skill, args, target=None):
    player.send_line(f"A shell of decaying matter protects you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("necrotic_stasis")
def handle_necrotic_stasis(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You lock {target.name} in a state of necrotic stasis.")
    effects.apply_effect(target, "stalled", 4)
    _consume_resources(player, skill)
    return target, True

@register("sludge_dash")
def handle_sludge_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}SLUDGE DASH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("plague_of_oblivion")
def handle_plague_of_oblivion(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}PLAGUE OF OBLIVION!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
