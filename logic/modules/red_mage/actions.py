"""
logic/modules/red_mage/actions.py
Red Mage Class Skills: Hybrid Mastery implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("dual_casting")
def handle_dual_casting(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Steel and sorcery strike {target.name} as one.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Dual Casting")
    resources.modify_resource(player, 'balance_pips', 1, source="Dual Casting")
    _consume_resources(player, skill)
    return target, True

@register("balance_point")
def handle_balance_point(player, skill, args, target=None):
    player.send_line(f"You find the perfect equilibrium between physical and magical force.")
    resources.modify_resource(player, 'balance_pips', 2, source="Balance Point")
    effects.apply_effect(player, "focused", 4)
    _consume_resources(player, skill)
    return None, True

@register("spellsword_burst")
def handle_spellsword_burst(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}SPELLSWORD BURST!{Colors.RESET} Reality fractures around {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("arcane_cleave")
def handle_arcane_cleave(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}ARCANE CLEAVE!{Colors.RESET}")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("red_barrier")
def handle_red_barrier(player, skill, args, target=None):
    player.send_line(f"A shifting barrier of red energy protects you.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("displacing_strike")
def handle_displacing_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You strike {target.name} and displace through space.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(player, "evasive", 2)
    _consume_resources(player, skill)
    return target, True

@register("mystic_marching")
def handle_mystic_marching(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}MYSTIC MARCHING!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("chain_spell")
def handle_chain_spell(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CHAIN SPELL!{Colors.RESET} Double cast incoming.")
    _consume_resources(player, skill)
    return None, True
