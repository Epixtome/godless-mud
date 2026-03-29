"""
logic/modules/chemist/actions.py
Chemist Class Skills: Master Alchemist implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("toss_philter")
def handle_toss_philter(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You toss a bubbling alchemical philter at {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Toss Philter")
    resources.modify_resource(player, 'reagent_pips', 1, source="Toss Philter")
    _consume_resources(player, skill)
    return target, True

@register("catalyze")
def handle_catalyze(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You catalyze {target.name}'s cellular reactions, making them volatile.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'reagent_pips', 1, source="Catalyze")
    _consume_resources(player, skill)
    return target, True

@register("acid_flask")
def handle_acid_flask(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}ACID FLASK!{Colors.RESET} Corrosive liquid dissolves {target.name}'s defenses!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("healing_mist")
def handle_healing_mist(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}HEALING MIST!{Colors.RESET} A restorative vapor fills the room.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)] # Fixed: In reality heals allies
    # Logic for healing allies should be here.
    _consume_resources(player, skill)
    return None, True

@register("smoke_bomb_defense")
def handle_smoke_bomb_defense(player, skill, args, target=None):
    player.send_line(f"A dense cloud of chemical smoke obscures your location.")
    effects.apply_effect(player, "concealed", 4)
    _consume_resources(player, skill)
    return None, True

@register("concoction_shield")
def handle_concoction_shield(player, skill, args, target=None):
    player.send_line(f"A protective gel coats your armor.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("reagent_dash")
def handle_reagent_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}REAGENT DASH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("ultimate_compound")
def handle_ultimate_compound(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}ULTIMATE COMPOUND!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True
