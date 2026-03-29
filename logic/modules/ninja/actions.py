"""
logic/modules/ninja/actions.py
Ninja Class Skills: Way of the Shinobi implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("kunai_throw")
def handle_kunai_throw(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A quick kunai throw strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Kunai Throw")
    resources.modify_resource(player, 'mudra_pips', 1, source="Kunai Throw")
    _consume_resources(player, skill)
    return target, True

@register("mudra_weaving")
def handle_mudra_weaving(player, skill, args, target=None):
    player.send_line(f"You weave your hands in complex spiritual patterns.")
    resources.modify_resource(player, 'mudra_pips', 2, source="Mudra Weaving")
    effects.apply_effect(player, "focused", 4)
    _consume_resources(player, skill)
    return None, True

@register("fire_style_fireball")
def handle_fire_style_fireball(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}FIRE STYLE: FIREBALL!{Colors.RESET} An eruption of heat!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("water_style_flood")
def handle_water_style_flood(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}WATER STYLE: FLOOD!{Colors.RESET} A massive wave!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "saturated", 8)
    _consume_resources(player, skill)
    return None, True

@register("kawarimi")
def handle_kawarimi(player, skill, args, target=None):
    player.send_line(f"{Colors.MAGENTA}KAWARIMI!{Colors.RESET} You vanish, leaving a log behind.")
    effects.apply_effect(player, "concealed", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadow_clone")
def handle_shadow_clone(player, skill, args, target=None):
    player.send_line(f"A shadow sibling appears beside you.")
    effects.apply_effect(player, "evasive", 4)
    _consume_resources(player, skill)
    return None, True

@register("ninja_stride")
def handle_ninja_stride(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}NINJA STRIDE!{Colors.RESET} A blur of shadow.")
    _consume_resources(player, skill)
    return None, True

@register("ninjutsu_mastery")
def handle_ninjutsu_mastery(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}NINJUTSU MASTERY!{Colors.RESET} All signs are one.")
    _consume_resources(player, skill)
    return None, True
