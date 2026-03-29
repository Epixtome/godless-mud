"""
logic/modules/ranger/actions.py
Ranger Class Skills: Keen Eyes implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("aim")
def handle_aim(player, skill, args, target=None):
    player.send_line(f"You take a deep breath and aim your shot.")
    resources.modify_resource(player, 'stamina', 20, source="Aim")
    resources.modify_resource(player, 'focus', 1, source="Aim")
    _consume_resources(player, skill)
    return None, True

@register("hunters_mark")
def handle_hunters_mark(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You mark {target.name} as your prey.")
    effects.apply_effect(target, "marked", 10)
    resources.modify_resource(player, 'focus', 1, source="Hunter's Mark")
    _consume_resources(player, skill)
    return target, True

@register("snipe")
def handle_snipe(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}SNIPE!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("piercing_arrow")
def handle_piercing_arrow(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A piercing arrow flys toward {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("disengage")
def handle_disengage(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}DISENGAGE!{Colors.RESET} You leap backward.")
    effects.apply_effect(player, "evasive", 2)
    _consume_resources(player, skill)
    return None, True

@register("camouflage")
def handle_camouflage(player, skill, args, target=None):
    player.send_line(f"You blend into your surroundings.")
    effects.apply_effect(player, "concealed", 10)
    _consume_resources(player, skill)
    return None, True

@register("pinning_shot")
def handle_pinning_shot(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You aim for {target.name}'s legs!")
    effects.apply_effect(target, "rooted", 3)
    _consume_resources(player, skill)
    return target, True

@register("recon_flare")
def handle_recon_flare(player, skill, args, target=None):
    player.send_line(f"{Colors.YELLOW}RECON FLARE!{Colors.RESET} The room is illuminated!")
    _consume_resources(player, skill)
    return None, True
