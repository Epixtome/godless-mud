"""
logic/modules/soul_reaver/actions.py
Soul Reaver Class Skills: Life Eater implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("soul_rip")
def handle_soul_rip(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You rip a fragment of soul from {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Soul Rip")
    resources.modify_resource(player, 'essence_pips', 1, source="Soul Rip")
    _consume_resources(player, skill)
    return target, True

@register("essence_drain")
def handle_essence_drain(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Toxic essence drains from {target.name}.")
    effects.apply_effect(target, "weakened", 6)
    resources.modify_resource(player, 'essence_pips', 1, source="Essence Drain")
    _consume_resources(player, skill)
    return target, True

@register("soul_reap")
def handle_soul_reap(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}SOUL REAP!{Colors.RESET} Reclaiming the stolen essences.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'hp', int(player.max_hp * 0.1), source="Soul Reap") # Placeholder heal
    _consume_resources(player, skill)
    return target, True

@register("essence_burst")
def handle_essence_burst(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}ESSENCE BURST!{Colors.RESET}")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("spectral_armor")
def handle_spectral_armor(player, skill, args, target=None):
    player.send_line(f"Spirits of the fallen protect you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("ethereal_form")
def handle_ethereal_form(player, skill, args, target=None):
    player.send_line(f"You become thin, your form ethereal.")
    effects.apply_effect(player, "untargetable", 2)
    _consume_resources(player, skill)
    return None, True

@register("soul_dash")
def handle_soul_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}SOUL DASH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("spiritual_feast")
def handle_spiritual_feast(player, skill, args, target=None):
    player.send_line(f"You feast on the raw spiritual energy around you.")
    resources.modify_resource(player, 'stamina', 50, source="Spiritual Feast")
    _consume_resources(player, skill)
    return None, True
