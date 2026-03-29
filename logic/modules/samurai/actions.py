"""
logic/modules/samurai/actions.py
Samurai Class Skills: Master of Precision and Lethality.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("iaido_draw")
def handle_iaido_draw(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.YELLOW}You draw your blade with unreal speed!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Iaido Draw")
    resources.modify_resource(player, 'bushido_pips', 1, source="Iaido Draw")
    _consume_resources(player, skill)
    return target, True

@register("meditative_stance")
def handle_meditative_stance(player, skill, args, target=None):
    player.send_line(f"{Colors.BLUE}You breathe deeply, focusing your spirit on the next strike.{Colors.RESET}")
    resources.modify_resource(player, 'bushido_pips', 1, source="Meditative Stance")
    effects.apply_effect(player, "focused", 4)
    _consume_resources(player, skill)
    return None, True

@register("hissatsu_chidori")
def handle_hissatsu_chidori(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}HISSATSU: CHIDORI!{Colors.RESET} Lightning crackles at your fingertips!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("tsubame_gaeshi")
def handle_tsubame_gaeshi(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}TSUBAME GAESHI!{Colors.RESET} Two strikes in a single breath!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    combat.handle_attack(player, target, player.room, player.game, blessing=skill, context_prefix="Second Strike: ")
    _consume_resources(player, skill)
    return target, True

@register("sever_spirit")
def handle_sever_spirit(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.RED}You cut through {target.name}'s balance.{Colors.RESET}")
    effects.apply_effect(target, "dazed", 4)
    _consume_resources(player, skill)
    return target, True

@register("dragons_breath")
def handle_dragons_breath(player, skill, args, target=None):
    player.send_line(f"You enter a stance to parry and counter.")
    effects.apply_effect(player, "counter_stance", 2)
    _consume_resources(player, skill)
    return None, True

@register("shadow_dash")
def handle_shadow_dash(player, skill, args, target=None):
    player.send_line(f"{Colors.BLACK}You flicker into the shadows.{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("way_of_the_warrior")
def handle_way_of_the_warrior(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}WAY OF THE WARRIOR!{Colors.RESET} Your soul and blade are one.")
    _consume_resources(player, skill)
    return None, True
