"""
logic/modules/summoner/actions.py
Summoner Class Skills: Veil Walker implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("spirit_lash")
def handle_spirit_lash(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A lash of spectral aether strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Spirit Lash")
    resources.modify_resource(player, 'aether_pips', 1, source="Spirit Lash")
    _consume_resources(player, skill)
    return target, True

@register("veil_opening")
def handle_veil_opening(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You crack the veil near {target.name}, marking them for deletion.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'aether_pips', 2, source="Veil Opening")
    _consume_resources(player, skill)
    return target, True

@register("grand_invocation")
def handle_grand_invocation(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}GRAND INVOCATION!{Colors.RESET} A massive spectral form strikes {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("synergy_explosion")
def handle_synergy_explosion(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}SYNERGY EXPLOSION!{Colors.RESET} Spectral fire erupts around your servant.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("spirit_shield")
def handle_spirit_shield(player, skill, args, target=None):
    player.send_line(f"Protective spirits surround you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("banish")
def handle_banish(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You banish {target.name} to the void briefly.")
    effects.apply_effect(target, "stun", 2)
    _consume_resources(player, skill)
    return target, True

@register("veil_step")
def handle_veil_step(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}VEIL STEP!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("call_avatar")
def handle_call_avatar(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CALL AVATAR!{Colors.RESET} The king of the void arrives.")
    _consume_resources(player, skill)
    return None, True
