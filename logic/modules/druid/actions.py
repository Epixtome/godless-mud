"""
logic/modules/druid/actions.py
Druid Class Skills: Forest Warden implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("nature_lash")
def handle_nature_lash(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You lash out at {target.name} with a barbed vine.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Nature Lash")
    resources.modify_resource(player, 'stamina', 10, source="Nature Lash")
    _consume_resources(player, skill)
    return target, True

@register("saturate")
def handle_saturate(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You drench {target.name} in primordial waters.")
    effects.apply_effect(target, "saturated", 8)
    resources.modify_resource(player, 'concentration', 20, source="Saturate")
    _consume_resources(player, skill)
    return target, True

@register("gale_force")
def handle_gale_force(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.CYAN}GALE FORCE!{Colors.RESET} A massive blast of wind strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("tempest_wrath")
def handle_tempest_wrath(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}TEMPEST WRATH!{Colors.RESET} Lightning crashes into the room!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "shocked", 4)
    _consume_resources(player, skill)
    return None, True

@register("barkskin")
def handle_barkskin(player, skill, args, target=None):
    player.send_line(f"Your skin hardens like wood.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("wild_growth")
def handle_wild_growth(player, skill, args, target=None):
    player.send_line(f"Vines erupt from the floor, trapping your enemies.")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        effects.apply_effect(t, "rooted", 3)
    _consume_resources(player, skill)
    return None, True

@register("nature_stride")
def handle_nature_stride(player, skill, args, target=None):
    player.send_line(f"{Colors.GREEN}NATURE STRIDE!{Colors.RESET} You merge into the world.")
    _consume_resources(player, skill)
    return None, True

@register("natural_focus")
def handle_natural_focus(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}NATURAL FOCUS!{Colors.RESET} Peace fills your body.")
    resources.modify_resource(player, 'hp', int(player.max_hp * 0.4), source="Natural Focus")
    resources.modify_resource(player, 'concentration', 100, source="Natural Focus")
    _consume_resources(player, skill)
    return None, True
