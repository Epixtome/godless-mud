"""
logic/modules/machinist/actions.py
Machinist Class Skills: Gadget Master implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("shot_burst")
def handle_shot_burst(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Bang! Bang! Bang! A rapid burst from your auto-pistol hits {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Shot Burst")
    resources.modify_resource(player, 'ammo_pips', 1, source="Shot Burst")
    _consume_resources(player, skill)
    return target, True

@register("tech_mark")
def handle_tech_mark(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You paint {target.name} with a tracking laser.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'ammo_pips', 1, source="Tech Mark")
    _consume_resources(player, skill)
    return target, True

@register("satellite_beam")
def handle_satellite_beam(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}SATELLITE BEAM!{Colors.RESET} Light from the heavens incinerates everything.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("ballistic_barrage")
def handle_ballistic_barrage(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}BALLISTIC BARRAGE!{Colors.RESET} A constant stream of lead strikes {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("auto_barrier")
def handle_auto_barrier(player, skill, args, target=None):
    player.send_line(f"A defensive drone generates a barrier around you.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("recharge_protocol")
def handle_recharge_protocol(player, skill, args, target=None):
    player.send_line(f"Safety protocols engaged. Systems recharging.")
    resources.modify_resource(player, 'hp', int(player.max_hp * 0.1), source="Recharge Protocol")
    resources.modify_resource(player, 'stamina', 50, source="Recharge Protocol")
    _consume_resources(player, skill)
    return None, True

@register("rocket_jump")
def handle_rocket_jump(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}ROCKET JUMP!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("drone_swarm")
def handle_drone_swarm(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}DRONE SWARM!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
