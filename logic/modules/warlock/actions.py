"""
logic/modules/warlock/actions.py
Warlock Class Skills: Echoes of the Void implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("eldritch_blast")
def handle_eldritch_blast(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.MAGENTA}A crackling beam of void energy strikes {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'entropy', 1, source="Eldritch Blast")
    resources.modify_resource(player, 'concentration', 15, source="Eldritch Blast")
    _consume_resources(player, skill)
    return target, True

@register("curse_of_agony")
def handle_curse_of_agony(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You inflict agony on {target.name}!")
    effects.apply_effect(target, "cursed", 10)
    resources.modify_resource(player, 'entropy', 2, source="Curse of Agony")
    _consume_resources(player, skill)
    return target, True

@register("soul_cleave")
def handle_soul_cleave(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}SOUL CLEAVE!{Colors.RESET} You tear into {target.name}'s soul!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("oblivion_strike")
def handle_oblivion_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}OBLIVION STRIKE!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("void_ward")
def handle_void_ward(player, skill, args, target=None):
    player.send_line(f"A ward of entropic void shield surrounds you.")
    effects.apply_effect(player, "shielded", 3)
    _consume_resources(player, skill)
    return None, True

@register("hex_of_weakness")
def handle_hex_of_weakness(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You weaken {target.name}'s will to fight.")
    effects.apply_effect(target, "weakened", 4)
    _consume_resources(player, skill)
    return target, True

@register("netherstep")
def handle_netherstep(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}NETHERSTEP!{Colors.RESET} You vanish through the void.")
    _consume_resources(player, skill)
    return None, True

@register("pact_of_sacrifice")
def handle_pact_of_sacrifice(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}PACT OF SACRIFICE!{Colors.RESET} You trade your life for power!")
    resources.modify_resource(player, 'hp', -int(player.hp * 0.25), source="Pact of Sacrifice")
    resources.modify_resource(player, 'entropy', 10, source="Pact of Sacrifice")
    resources.modify_resource(player, 'concentration', 100, source="Pact of Sacrifice")
    _consume_resources(player, skill)
    return None, True
