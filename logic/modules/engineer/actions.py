"""
logic/modules/engineer/actions.py
Engineer Class Skills: Master Architect implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("wrench_strike")
def handle_wrench_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A heavy wrench smash catches {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Wrench Strike")
    resources.modify_resource(player, 'tech_pips', 1, source="Wrench Strike")
    _consume_resources(player, skill)
    return target, True

@register("targeted_pheromone")
def handle_targeted_pheromone(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You mark {target.name} for your turrets.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'tech_pips', 1, source="Targeted Pheromone")
    _consume_resources(player, skill)
    return target, True

@register("autoturret")
def handle_autoturret(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}AUTO-TURRET!{Colors.RESET} Deployed and seeking targets.")
    _consume_resources(player, skill)
    return None, True

@register("shock_grenade")
def handle_shock_grenade(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLUE}SHOCK GRENADE!{Colors.RESET} A blast of static!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "stun", 2)
    _consume_resources(player, skill)
    return None, True

@register("portable_barrier")
def handle_portable_barrier(player, skill, args, target=None):
    player.send_line(f"A hard-light field shimmers into focus.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("overdrive")
def handle_overdrive(player, skill, args, target=None):
    player.send_line(f"{Colors.RED}OVERDRIVE!{Colors.RESET} Safety protocols disengaged.")
    effects.apply_effect(player, "haste", 10)
    _consume_resources(player, skill)
    return None, True

@register("jetpack_boost")
def handle_jetpack_boost(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}JETPACK BOOST!{Colors.RESET} To the sky!")
    _consume_resources(player, skill)
    return None, True

@register("repair_protocol")
def handle_repair_protocol(player, skill, args, target=None):
    player.send_line(f"Field repairs initiated.")
    resources.modify_resource(player, 'hp', int(player.max_hp * 0.3), source="Repair Protocol")
    _consume_resources(player, skill)
    return None, True
