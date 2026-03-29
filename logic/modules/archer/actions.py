"""
logic/modules/archer/actions.py
Archer Class Skills: Deadeye implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("tracker_scan")
def handle_tracker_scan(player, skill, args, target=None):
    player.send_line(f"You scan the surrounding area for any movement.")
    resources.modify_resource(player, 'stamina', 20, source="Tracker Scan")
    resources.modify_resource(player, 'focus_pips', 1, source="Tracker Scan")
    _consume_resources(player, skill)
    return None, True

@register("target_lock")
def handle_target_lock(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You lock your sights on {target.name}.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'focus_pips', 1, source="Target Lock")
    _consume_resources(player, skill)
    return target, True

@register("heartseeker_snipe")
def handle_heartseeker_snipe(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}HEARTSEEKER SNIPE!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("volley_rain")
def handle_volley_rain(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}VOLLEY RAIN!{Colors.RESET} Arrows rain from the sky!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("catch_arrows")
def handle_catch_arrows(player, skill, args, target=None):
    player.send_line(f"You watch for incoming missiles with absolute focus.")
    effects.apply_effect(player, "missile_reduction", 6)
    _consume_resources(player, skill)
    return None, True

@register("camouflage")
def handle_camouflage(player, skill, args, target=None):
    player.send_line(f"You blend into the shadows.")
    effects.apply_effect(player, "concealed", 3)
    _consume_resources(player, skill)
    return None, True

@register("archers_sprint")
def handle_archers_sprint(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}ARCHER'S SPRINT!{Colors.RESET} A blur of motion.")
    _consume_resources(player, skill)
    return None, True

@register("pinnacle_of_arrows")
def handle_pinnacle_of_arrows(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}PINNACLE OF ARROWS!{Colors.RESET} Your aim is legendary.")
    _consume_resources(player, skill)
    return None, True
