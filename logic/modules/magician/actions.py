"""
logic/modules/magician/actions.py
Magician Class Skills: Pure Arcane implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("arcane_missile")
def handle_arcane_missile(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BLUE}A bolt of pure mana strikes {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Arcane Missile")
    resources.modify_resource(player, 'mana_pips', 1, source="Arcane Missile")
    _consume_resources(player, skill)
    return target, True

@register("mana_infusion")
def handle_mana_infusion(player, skill, args, target=None):
    player.send_line(f"You overcharge your mana pool with arcane energy.")
    resources.modify_resource(player, 'mana_pips', 2, source="Mana Infusion")
    effects.apply_effect(player, "empowered", 4)
    _consume_resources(player, skill)
    return None, True

@register("arcane_barrage")
def handle_arcane_barrage(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}ARCANE BARRAGE!{Colors.RESET} A stream of bolts hits {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("mana_burst")
def handle_mana_burst(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}MANA BURST!{Colors.RESET} An eruption of force!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("arcane_shield")
def handle_arcane_shield(player, skill, args, target=None):
    player.send_line(f"An arcane shield shimmers into place.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("spell_lock")
def handle_spell_lock(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You lock {target.name}'s spiritual flow.")
    effects.apply_effect(target, "silenced", 4)
    _consume_resources(player, skill)
    return target, True

@register("arcane_dash")
def handle_arcane_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}ARCANE DASH!{Colors.RESET} You blink through space.")
    _consume_resources(player, skill)
    return None, True

@register("enchant_weapon")
def handle_enchant_weapon(player, skill, args, target=None):
    player.send_line(f"You enchant your weapons with pure mana.")
    _consume_resources(player, skill)
    return None, True
