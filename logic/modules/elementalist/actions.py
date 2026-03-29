"""
logic/modules/elementalist/actions.py
Elementalist Class Skills: Mana Shifter implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("elemental_strike")
def handle_elemental_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A strike of shifting elemental energy strikes {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Elemental Strike")
    resources.modify_resource(player, 'attunement_pips', 1, source="Elemental Strike")
    _consume_resources(player, skill)
    return target, True

@register("attunement")
def handle_attunement(player, skill, args, target=None):
    player.send_line(f"You shift your internal resonance, aligning with the primal forces.")
    resources.modify_resource(player, 'attunement_pips', 2, source="Attunement")
    effects.apply_effect(player, "focused", 4)
    _consume_resources(player, skill)
    return None, True

@register("elemental_cataclysm")
def handle_elemental_cataclysm(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}ELEMENTAL CATACLYSM!{Colors.RESET} Reality fractures around you.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("shock_cannon")
def handle_shock_cannon(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}SHOCK CANNON!{Colors.RESET} A blast of high voltage!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "staggered", 2)
    _consume_resources(player, skill)
    return target, True

@register("barrier_of_elements")
def handle_barrier_of_elements(player, skill, args, target=None):
    player.send_line(f"A barrier of swirling elements protects you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("flash_freeze")
def handle_flash_freeze(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}FLASH FREEZE!{Colors.RESET} The room's temperature drops instantly.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "chilled", 4)
        effects.apply_effect(t, "stalled", 2)
    _consume_resources(player, skill)
    return None, True

@register("aether_dash")
def handle_aether_dash(player, skill, args, target=None):
    player.send_line(f"You blink through aetheric space.")
    _consume_resources(player, skill)
    return None, True

@register("cinder_shower")
def handle_cinder_shower(player, skill, args, target=None):
    player.send_line(f"A shower of sparks illuminates and warms the room.")
    _consume_resources(player, skill)
    return None, True
