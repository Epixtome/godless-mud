"""
logic/modules/knight/actions.py
Knight Class Skills: Stalwart Defender implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("crippling_strike")
def handle_crippling_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You strike {target.name}'s legs, crippling their movement.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "sluggish", 5)
    resources.modify_resource(player, 'stamina', 15, source="Crippling Strike")
    _consume_resources(player, skill)
    return target, True

@register("intervene")
def handle_intervene(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You step in to protect your position relative to {target.name}.")
    effects.apply_effect(target, "marked", 4)
    resources.modify_resource(player, 'stamina', 10, source="Intervene")
    _consume_resources(player, skill)
    return target, True

@register("execute")
def handle_execute(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}EXECUTE!{Colors.RESET} A decisive strike to end the fight!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("retribution")
def handle_retribution(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}RETRIBUTION!{Colors.RESET} You strike back with righteous fury!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("shield_bash")
def handle_shield_bash(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You slam your shield into {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "stun", 2)
    _consume_resources(player, skill)
    return target, True

@register("brace")
def handle_brace(player, skill, args, target=None):
    player.send_line(f"You brace behind your shield, preparing for the storm.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("charge")
def handle_charge(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}CHARGE!{Colors.RESET} You rush your enemy!")
    _consume_resources(player, skill)
    return None, True

@register("war_cry")
def handle_war_cry(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}WAR CRY!{Colors.RESET} Inspiration fills the room!")
    allies = [p for p in player.room.players]
    for a in allies:
        effects.apply_effect(a, "inspired", 10)
    _consume_resources(player, skill)
    return None, True
