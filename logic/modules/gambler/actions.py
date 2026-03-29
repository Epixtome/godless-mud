"""
logic/modules/gambler/actions.py
Gambler Class Skills: Favor of Fortune implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("loaded_dice")
def handle_loaded_dice(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"The dice are weighted, and they strike {target.name} for 7!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Loaded Dice")
    resources.modify_resource(player, 'luck_pips', 1, source="Loaded Dice")
    _consume_resources(player, skill)
    return target, True

@register("ante_up")
def handle_ante_up(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You increase the stakes of the current battle.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'luck_pips', 2, source="Ante Up")
    _consume_resources(player, skill)
    return target, True

@register("jackpot")
def handle_jackpot(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}JACKPOT!{Colors.RESET} Everything is coming up your way!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("bad_beat")
def handle_bad_beat(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A bad beat costs {target.name} everything.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("lucky_break")
def handle_lucky_break(player, skill, args, target=None):
    player.send_line(f"Sometimes you just get lucky.")
    _consume_resources(player, skill)
    return None, True

@register("all_in")
def handle_all_in(player, skill, args, target=None):
    player.send_line(f"{Colors.RED}ALL IN!{Colors.RESET} No turning back.")
    _consume_resources(player, skill)
    return None, True

@register("shuffle")
def handle_shuffle(player, skill, args, target=None):
    player.send_line(f"You shuffle your position on the board.")
    _consume_resources(player, skill)
    return None, True

@register("high_stakes")
def handle_high_stakes(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}HIGH STAKES!{Colors.RESET} Victory or ruin.")
    _consume_resources(player, skill)
    return None, True
