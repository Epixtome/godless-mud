"""
logic/modules/priest/actions.py
Priest Class Skills: Divine Vessel implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("holy_strike")
def handle_holy_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Divine light strikes {target.name} through your weapon!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Holy Strike")
    resources.modify_resource(player, 'faith_pips', 1, source="Holy Strike")
    _consume_resources(player, skill)
    return target, True

@register("divine_mark")
def handle_divine_mark(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You mark {target.name} for divine retribution.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'faith_pips', 1, source="Divine Mark")
    _consume_resources(player, skill)
    return target, True

@register("judgment")
def handle_judgment(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.YELLOW}DIVINE JUDGMENT!{Colors.RESET} Heavenly fire strikes {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("purification")
def handle_purification(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}PURIFICATION!{Colors.RESET} A wave of cleansing light fills the room.")
    _consume_resources(player, skill)
    return None, True

@register("aegis")
def handle_aegis(player, skill, args, target=None):
    player.send_line(f"A holy aegis protects you.")
    effects.apply_effect(player, "shielded", 8)
    _consume_resources(player, skill)
    return None, True

@register("divine_grace")
def handle_divine_grace(player, skill, args, target=None):
    player.send_line(f"You grant divine grace to yourself.")
    effects.apply_effect(player, "unstoppable", 2)
    _consume_resources(player, skill)
    return None, True

@register("beacon_of_light")
def handle_beacon_of_light(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}BEACON OF LIGHT!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("resurrection")
def handle_resurrection(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}RESURRECTION!{Colors.RESET} Arise!")
    _consume_resources(player, skill)
    return None, True
