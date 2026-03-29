"""
logic/modules/rogue/actions.py
Rogue Class Skills: Shadow Blade implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("rogue_quick_strike")
def handle_rogue_quick_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A quick dagger strike finds its mark on {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "bleeding", 4)
    resources.modify_resource(player, 'stamina', 15, source="Quick Strike")
    _consume_resources(player, skill)
    return target, True

@register("mark_target")
def handle_mark_target(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You mark {target.name} for certain death.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'stamina', 25, source="Mark Target")
    _consume_resources(player, skill)
    return target, True

@register("backstab")
def handle_backstab(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}BACKSTAB!{Colors.RESET} A lethal strike from the shadows!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("visceral_strike")
def handle_visceral_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You deliver a visceral strike to {target.name}'s vitals.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "maimed", 6)
    _consume_resources(player, skill)
    return target, True

@register("vanish")
def handle_vanish(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}VANISH!{Colors.RESET} You disappear into thin air.")
    effects.apply_effect(player, "concealed", 3)
    _consume_resources(player, skill)
    return None, True

@register("evasion")
def handle_evasion(player, skill, args, target=None):
    player.send_line(f"You focus entirely on dodging incoming blows.")
    effects.apply_effect(player, "evasive", 6)
    _consume_resources(player, skill)
    return None, True

@register("shadowstep")
def handle_shadowstep(player, skill, args, target=None):
    player.send_line(f"{Colors.MAGENTA}SHADOWSTEP!{Colors.RESET} You reappear behind your foe.")
    for s in ["stalled", "immobilized"]:
        if effects.has_effect(player, s):
            effects.remove_effect(player, s)
    _consume_resources(player, skill)
    return None, True

@register("smoke_bomb")
def handle_smoke_bomb(player, skill, args, target=None):
    player.send_line(f"A smoke bomb shatters at your feet, blinding everyone.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "blinded", 2)
    effects.apply_effect(player, "concealed", 2)
    _consume_resources(player, skill)
    return None, True
