"""
logic/modules/temporalist/actions.py
Temporalist Class Skills: Time Master implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("time_slice")
def handle_time_slice(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A slice of time pauses {target.name} briefly.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Time Slice")
    resources.modify_resource(player, 'chrono_pips', 1, source="Time Slice")
    _consume_resources(player, skill)
    return target, True

@register("temporal_anchor")
def handle_temporal_anchor(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You anchor {target.name} in their current timeline.")
    effects.apply_effect(target, "slowed", 10)
    resources.modify_resource(player, 'chrono_pips', 1, source="Temporal Anchor")
    _consume_resources(player, skill)
    return target, True

@register("temporal_stasis")
def handle_temporal_stasis(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}TEMPORAL STASIS!{Colors.RESET} Time stops for {target.name}.")
    effects.apply_effect(target, "stun", 6)
    _consume_resources(player, skill)
    return target, True

@register("chrono_burst")
def handle_chrono_burst(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}CHRONO BURST!{Colors.RESET} Acceleration!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(player, "haste", 4)
    _consume_resources(player, skill)
    return target, True

@register("rewind_death")
def handle_rewind(player, skill, args, target=None):
    player.send_line(f"You rewind your personal timeline, erasing injuries.")
    _consume_resources(player, skill)
    return None, True

@register("time_dilation")
def handle_time_dilation(player, skill, args, target=None):
    player.send_line(f"Time dilates around you, making reality feel sluggish.")
    _consume_resources(player, skill)
    return None, True

@register("chrono_blink")
def handle_chrono_blink(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}CHRONO BLINK!{Colors.RESET} You vanish from the present.")
    _consume_resources(player, skill)
    return None, True

@register("accelerated_destiny")
def handle_accelerated_destiny(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}ACCELERATED DESTINY!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
