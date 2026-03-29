"""
logic/modules/paladin/actions.py
Paladin Class Skills: Shield of Faith implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("reckoning")
def handle_reckoning(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A reckoning strike crashes into {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Reckoning")
    resources.modify_resource(player, 'holy_pips', 1, source="Reckoning")
    _consume_resources(player, skill)
    return target, True

@register("radiant_flash")
def handle_radiant_flash(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.YELLOW}Blinding light erupts from your shield, blinding {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "blinded", 3)
    resources.modify_resource(player, 'holy_pips', 1, source="Radiant Flash")
    _consume_resources(player, skill)
    return target, True

@register("holy_smite")
def handle_holy_smite(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}HOLY SMITE!{Colors.RESET} Divine fire strikes the target!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("consecration")
def handle_consecration(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}CONSECRATION!{Colors.RESET} The ground beneath you burns with holy fire!")
    # room-wide recurring damage handled by effects usually, here we do AOE once
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("divine_grace")
def handle_divine_grace(player, skill, args, target=None):
    player.send_line(f"You are enveloped in a halo of divine grace.")
    effects.apply_effect(player, "shielded", 4)
    resources.modify_resource(player, 'hp', int(player.max_hp * 0.1), source="Divine Grace")
    _consume_resources(player, skill)
    return None, True

@register("seal_of_justice")
def handle_seal_of_justice(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You bind {target.name} with the Seal of Justice.")
    effects.apply_effect(target, "stalled", 4)
    _consume_resources(player, skill)
    return target, True

@register("pursuit_of_justice")
def handle_pursuit_of_justice(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}PURSUIT OF JUSTICE!{Colors.RESET} You rush your enemy with divine speed.")
    _consume_resources(player, skill)
    return None, True

@register("lay_on_hands")
def handle_lay_on_hands(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}LAY ON HANDS!{Colors.RESET}")
    resources.modify_resource(player, 'hp', player.max_hp, source="Lay on Hands")
    resources.modify_resource(player, 'stamina', -player.resources.get('stamina', 0), source="Lay on Hands")
    _consume_resources(player, skill)
    return None, True
