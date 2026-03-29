"""
logic/modules/barbarian/actions.py
Barbarian Class Skills: Juggernaut of the North implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("savage_strike")
def handle_savage_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.RED}You deliver a savage strike to {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Savage Strike")
    resources.modify_resource(player, 'fury', 5, source="Savage Strike")
    _consume_resources(player, skill)
    return target, True

@register("headbutt")
def handle_headbutt(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You slam your forehead into {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "staggered", 3)
    resources.modify_resource(player, 'fury', 10, source="Headbutt")
    _consume_resources(player, skill)
    return target, True

@register("lacerate")
def handle_lacerate(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.RED}You tear into {target.name}'s flesh!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "bleeding", 6)
    resources.modify_resource(player, 'fury', 10, source="Lacerate")
    _consume_resources(player, skill)
    return target, True

@register("whirlwind")
def handle_whirlwind(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}WHIRLWIND!{Colors.RESET} You spin in a lethal circle!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("decapitate")
def handle_decapitate(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}DECAPITATE!{Colors.RESET} A final, thunderous blow!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("savage_brace")
def handle_savage_brace(player, skill, args, target=None):
    player.send_line(f"{Colors.YELLOW}You tense your muscles for impact.{Colors.RESET}")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("leap")
def handle_leap(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}LEAP!{Colors.RESET} You burst into the air!")
    for s in ["stalled", "immobilized"]:
        if effects.has_effect(player, s):
            effects.remove_effect(player, s)
    _consume_resources(player, skill)
    return None, True

@register("bloodrage")
def handle_bloodrage(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}BLOODRAGE!{Colors.RESET} Pure Primal Fury!")
    effects.apply_effect(player, "berserking", 10)
    _consume_resources(player, skill)
    return None, True
