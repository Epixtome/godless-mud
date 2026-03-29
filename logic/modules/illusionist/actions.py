"""
logic/modules/illusionist/actions.py
Illusionist Class Skills: Reality Warp implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("color_spray")
def handle_color_spray(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.MAGENTA}A dazzling spray of colors blinds {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "blinded", 3)
    resources.modify_resource(player, 'concentration', 15, source="Color Spray")
    resources.modify_resource(player, 'illusion_pips', 1, source="Color Spray")
    _consume_resources(player, skill)
    return target, True

@register("mirror_image")
def handle_mirror_image(player, skill, args, target=None):
    player.send_line(f"Three identical versions of you appear.")
    effects.apply_effect(player, "evasive", 2)
    resources.modify_resource(player, 'illusion_pips', 1, source="Mirror Image")
    _consume_resources(player, skill)
    return None, True

@register("phantasmal_inferno")
def handle_phantasmal_inferno(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}PHANTASMAL INFERNO!{Colors.RESET} False flames consume {target.name}'s mind!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("mind_shatter")
def handle_mind_shatter(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}MIND SHATTER!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "stun", 2)
    _consume_resources(player, skill)
    return target, True

@register("prism_cloak")
def handle_prism_cloak(player, skill, args, target=None):
    player.send_line(f"Your form shifts and bends like light through a prism.")
    effects.apply_effect(player, "concealed", 3)
    _consume_resources(player, skill)
    return None, True

@register("hallucinate")
def handle_hallucinate(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You force {target.name} to see a terrifying hallucination.")
    effects.apply_effect(target, "dazed", 4)
    _consume_resources(player, skill)
    return target, True

@register("phase_shift")
def handle_phase_shift(player, skill, args, target=None):
    player.send_line(f"You blink across the room.")
    _consume_resources(player, skill)
    return None, True

@register("invisibility")
def handle_invisibility(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}INVISIBILITY!{Colors.RESET} You vanish from sight completely.")
    effects.apply_effect(player, "concealed", 15)
    _consume_resources(player, skill)
    return None, True
