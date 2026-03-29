"""
logic/modules/thief/actions.py
Thief Class Skills: Scoundrel's Luck implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("mug")
def handle_mug(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You mug {target.name} with a quick strike!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Mug")
    resources.modify_resource(player, 'greed_pips', 1, source="Mug")
    _consume_resources(player, skill)
    return target, True

@register("sand_in_eyes")
def handle_sand_in_eyes(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You throw a handful of sand into {target.name}'s eyes!")
    effects.apply_effect(target, "blinded", 3)
    resources.modify_resource(player, 'greed_pips', 1, source="Sand in Eyes")
    _consume_resources(player, skill)
    return target, True

@register("final_heist")
def handle_final_heist(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}FINAL HEIST!{Colors.RESET} The payout is legendary!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("cheap_shot")
def handle_cheap_shot(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A cheap shot to {target.name}'s vitals!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "maimed", 6)
    _consume_resources(player, skill)
    return target, True

@register("thief_reflexes")
def handle_thief_reflexes(player, skill, args, target=None):
    player.send_line(f"You move like a scoundrel, expecting betrayal.")
    effects.apply_effect(player, "evasive", 4)
    _consume_resources(player, skill)
    return None, True

@register("dirty_trick")
def handle_dirty_trick(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You trip {target.name} with a dirty trick.")
    effects.apply_effect(target, "prone", 3)
    _consume_resources(player, skill)
    return target, True

@register("pickpocket_dash")
def handle_pickpocket_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}PICKPOCKET DASH!{Colors.RESET} Your hands are blurred.")
    _consume_resources(player, skill)
    return None, True

@register("stealth")
def handle_stealth(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}STEALTH!{Colors.RESET} You are but a shadow.")
    effects.apply_effect(player, "concealed", 20)
    _consume_resources(player, skill)
    return None, True
