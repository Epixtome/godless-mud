"""
logic/modules/puppet_master/actions.py
Puppet Master Class Skills: Puppet Synergy implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("puppet_strike")
def handle_puppet_strike(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Both you and your puppet strike {target.name} in unison.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Puppet Strike")
    resources.modify_resource(player, 'control_pips', 1, source="Puppet Strike")
    _consume_resources(player, skill)
    return target, True

@register("string_pull")
def handle_string_pull(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You pull {target.name}'s strings, controlling their movement.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'control_pips', 1, source="String Pull")
    _consume_resources(player, skill)
    return target, True

@register("overdrive")
def handle_overdrive(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.RED}OVERDRIVE!{Colors.RESET} Your puppet surpasses its limits.")
    effects.apply_effect(player, "empowered", 5)
    _consume_resources(player, skill)
    return None, True

@register("iron_fury")
def handle_iron_fury(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Your puppet enters a state of iron fury against {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    effects.apply_effect(target, "staggered", 4)
    _consume_resources(player, skill)
    return target, True

@register("iron_guard")
def handle_iron_guard(player, skill, args, target=None):
    player.send_line(f"Your puppet moves to protect you, becoming an iron wall.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("proxy_defense")
def handle_proxy_defense(player, skill, args, target=None):
    player.send_line(f"You shift incoming damage to your puppet.")
    _consume_resources(player, skill)
    return None, True

@register("thread_dash")
def handle_thread_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}THREAD DASH!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("grand_puppeteer")
def handle_grand_puppeteer(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}GRAND PUPPETEER!{Colors.RESET} Absolute control.")
    _consume_resources(player, skill)
    return None, True
