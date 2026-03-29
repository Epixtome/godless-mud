"""
logic/modules/assassin/actions.py
Assassin Class Skills: Silent Death implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("assassin_opening")
def handle_assassin_opening(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A surgical strike finds a weak point on {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Assassin Opening")
    resources.modify_resource(player, 'kill_pips', 1, source="Assassin Opening")
    _consume_resources(player, skill)
    return target, True

@register("toxic_blade")
def handle_toxic_blade(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You coat your blade with lethal neurotoxin.")
    effects.apply_effect(target, "toxic", 8)
    resources.modify_resource(player, 'kill_pips', 1, source="Toxic Blade")
    _consume_resources(player, skill)
    return target, True

@register("death_stroke")
def handle_death_stroke(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}DEATH STROKE!{Colors.RESET} A final, quiet puncture.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("throat_slit")
def handle_throat_slit(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You silence {target.name} with a surgical cut.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "silenced", 4)
    _consume_resources(player, skill)
    return target, True

@register("smoke_screen")
def handle_smoke_screen(player, skill, args, target=None):
    player.send_line(f"A dense cloud of smoke fills the room.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "blinded", 3)
    effects.apply_effect(player, "concealed", 3)
    _consume_resources(player, skill)
    return None, True

@register("evasive_maneuver")
def handle_evasive_maneuver(player, skill, args, target=None):
    player.send_line(f"You focus entirely on agility.")
    effects.apply_effect(player, "evasive", 4)
    _consume_resources(player, skill)
    return None, True

@register("assassin_jump")
def handle_assassin_jump(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}ASSASSIN JUMP!{Colors.RESET} Cold precision.")
    _consume_resources(player, skill)
    return None, True

@register("killer_instinct")
def handle_killer_instinct(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}KILLER INSTINCT!{Colors.RESET} Your focus is absolute.")
    _consume_resources(player, skill)
    return None, True
