"""
logic/modules/necromancer/actions.py
Necromancer Class Skills: Lord of Decay implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("bone_spike")
def handle_bone_spike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A spike of bone erupts from the ground into {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Bone Spike")
    resources.modify_resource(player, 'soul_pips', 1, source="Bone Spike")
    _consume_resources(player, skill)
    return target, True

@register("soul_shackles")
def handle_soul_shackles(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Ghostly shackles bind {target.name}'s spirit.")
    effects.apply_effect(target, "sluggish", 4)
    resources.modify_resource(player, 'soul_pips', 1, source="Soul Shackles")
    _consume_resources(player, skill)
    return target, True

@register("corpse_explosion")
def handle_corpse_explosion(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}CORPSE EXPLOSION!{Colors.RESET} The room erupts in necrotic fire!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("deaths_embrace")
def handle_deaths_embrace(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.MAGENTA}Death's embrace drains the life from {target.name}.{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'hp', 20, source="Death's Embrace")
    _consume_resources(player, skill)
    return target, True

@register("bone_shield")
def handle_bone_shield(player, skill, args, target=None):
    player.send_line(f"A shield of interlocking rib bones protects you.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("rotting_touch")
def handle_rotting_touch(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Your touch causes {target.name}'s flesh to putrefy.")
    effects.apply_effect(target, "weakened", 6)
    _consume_resources(player, skill)
    return target, True

@register("nether_grip")
def handle_nether_grip(player, skill, args, target=None):
    player.send_line(f"The void pulls you through.")
    _consume_resources(player, skill)
    return None, True

@register("raise_dead")
def handle_raise_dead(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}RISE!{Colors.RESET} A skeletal servant crawls from the earth.")
    _consume_resources(player, skill)
    return None, True
