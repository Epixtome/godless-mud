"""
logic/modules/soul_weaver/actions.py
Soul Weaver Class Skills: Spirit Master implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("weave_strike")
def handle_weave_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A strike that knots the spirit hits {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Weave Strike")
    resources.modify_resource(player, 'thread_pips', 1, source="Weave Strike")
    _consume_resources(player, skill)
    return target, True

@register("spirit_infusion")
def handle_spirit_infusion(player, skill, args, target=None):
    player.send_line(f"You infuse yourself with raw spiritual force.")
    resources.modify_resource(player, 'thread_pips', 2, source="Spirit Infusion")
    effects.apply_effect(player, "focused", 4)
    _consume_resources(player, skill)
    return None, True

@register("soul_mend")
def handle_soul_mend(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}SOUL MEND!{Colors.RESET} You knit spiritual threads back together.")
    resources.modify_resource(player, 'hp', int(player.max_hp * 0.5), source="Soul Mend")
    _consume_resources(player, skill)
    return None, True

@register("weave_explosion")
def handle_weave_explosion(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}WEAVE EXPLOSION!{Colors.RESET} Spiritual threads detonate!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "blinded", 2)
    _consume_resources(player, skill)
    return None, True

@register("spiritual_shield")
def handle_spiritual_shield(player, skill, args, target=None):
    player.send_line(f"Threads of spirit form a protective weave around you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("thread_of_fate_blink")
def handle_fate_blink(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}FATE BLINK!{Colors.RESET}")
    effects.apply_effect(player, "untargetable", 1)
    _consume_resources(player, skill)
    return None, True

@register("weaving_dash")
def handle_weaving_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}WEAVING DASH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("grand_weave_revival")
def handle_grand_weave(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}GRAND WEAVE!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
