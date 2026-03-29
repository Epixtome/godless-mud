"""
logic/modules/mage/actions.py
Mage Class Skills: Black Weaver implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("ignite")
def handle_ignite(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.RED}A flash of fire erupts on {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "burned", 8)
    resources.modify_resource(player, 'concentration', 15, source="Ignite")
    _consume_resources(player, skill)
    return target, True

@register("frost_bolt")
def handle_frost_bolt(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BLUE}A bolt of frost strikes {target.name}.{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "chilled", 6)
    _consume_resources(player, skill)
    return target, True

@register("lightning_bolt")
def handle_lightning_bolt(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}LIGHTNING BOLT!{Colors.RESET} Arcane electricity crackles!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("pyroclasm")
def handle_pyroclasm(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}PYROCLASM!{Colors.RESET} The earth erupts in a fountain of fire!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "burned", 8)
    _consume_resources(player, skill)
    return None, True

@register("phase_shift")
def handle_phase_shift(player, skill, args, target=None):
    player.send_line(f"You briefly phase out of reality.")
    effects.apply_effect(player, "untargetable", 1)
    _consume_resources(player, skill)
    return None, True

@register("arcane_ward")
def handle_arcane_ward(player, skill, args, target=None):
    player.send_line(f"{Colors.BLUE}A shield of shimmering mana surrounds you.{Colors.RESET}")
    effects.apply_effect(player, "shielded", 3)
    _consume_resources(player, skill)
    return None, True

@register("blink")
def handle_blink(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}BLINK!{Colors.RESET} You teleport instantly.")
    for s in ["stalled", "immobilized"]:
        if effects.has_effect(player, s):
            effects.remove_effect(player, s)
    _consume_resources(player, skill)
    return None, True

@register("arcane_surge")
def handle_arcane_surge(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}ARCANE SURGE!{Colors.RESET} Your power reaches its peak!")
    effects.apply_effect(player, "empowered", 15)
    resources.modify_resource(player, 'concentration', 100, source="Arcane Surge")
    _consume_resources(player, skill)
    return None, True
