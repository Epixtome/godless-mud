"""
logic/modules/guardian/actions.py
Guardian Class Skills: Living Wall implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("bastion_strike")
def handle_bastion_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A protective strike hits {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 20, source="Bastion Strike")
    resources.modify_resource(player, 'shield_pips', 1, source="Bastion Strike")
    _consume_resources(player, skill)
    return target, True

@register("interpose")
def handle_interpose(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You interpose your shield between {target.name} and your allies.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'shield_pips', 1, source="Interpose")
    _consume_resources(player, skill)
    return target, True

@register("shield_slam")
def handle_shield_slam(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}SHIELD SLAM!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "stun", 3)
    _consume_resources(player, skill)
    return target, True

@register("iron_curtain")
def handle_iron_curtain(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}IRON CURTAIN!{Colors.RESET} A massive wall of force protects everyone.")
    _consume_resources(player, skill)
    return None, True

@register("invulnerability_stance")
def handle_invulnerability_stance(player, skill, args, target=None):
    player.send_line(f"You enter an immovable, invulnerable stance.")
    effects.apply_effect(player, "shielded", 10)
    _consume_resources(player, skill)
    return None, True

@register("shield_swipe")
def handle_shield_swipe(player, skill, args, target=None):
    player.send_line(f"You swipe your shield in a wide arc, knocking back enemies.")
    _consume_resources(player, skill)
    return None, True

@register("guardian_rush")
def handle_guardian_rush(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}GUARDIAN RUSH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("sacred_bond")
def handle_sacred_bond(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}SACRED BOND!{Colors.RESET} Your lives are one.")
    _consume_resources(player, skill)
    return None, True
