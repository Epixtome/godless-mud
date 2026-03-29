"""
logic/modules/witch/actions.py
Witch Class Skills: Cauldron Master implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("witchs_cackle")
def handle_witchs_cackle(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.MAGENTA}You cackle chillingly at {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 15, source="Witch's Cackle")
    resources.modify_resource(player, 'curse_pips', 1, source="Witch's Cackle")
    _consume_resources(player, skill)
    return target, True

@register("curse_of_misfortune")
def handle_curse_of_misfortune(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"You curse {target.name} with pure bad luck.")
    effects.apply_effect(target, "blinded", 4)
    resources.modify_resource(player, 'curse_pips', 1, source="Curse of Misfortune")
    _consume_resources(player, skill)
    return target, True

@register("voodoo_puncture")
def handle_voodoo_puncture(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"{Colors.BOLD}{Colors.RED}VOODOO PUNCTURE!{Colors.RESET} Internal injuries manifest on {target.name}!")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("cauldron_eruption")
def handle_cauldron_eruption(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.GREEN}CAULDRON ERUPTION!{Colors.RESET} Toxic brew spews everywhere!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
        effects.apply_effect(t, "toxic", 4)
    _consume_resources(player, skill)
    return None, True

@register("obsidian_ward")
def handle_obsidian_ward(player, skill, args, target=None):
    player.send_line(f"Obsidian stones circle you defensively.")
    effects.apply_effect(player, "shielded", 6)
    _consume_resources(player, skill)
    return None, True

@register("mist_form")
def handle_mist_form(player, skill, args, target=None):
    player.send_line(f"You dissolve into a noxious mist.")
    effects.apply_effect(player, "untargetable", 2)
    _consume_resources(player, skill)
    return None, True

@register("broomstick_flight")
def handle_broomstick_flight(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}BROOMSTICK FLIGHT!{Colors.RESET}")
    _consume_resources(player, skill)
    return None, True

@register("grand_hex_of_ruin")
def handle_grand_hex(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}GRAND HEX!{Colors.RESET} The zone is cursed.")
    _consume_resources(player, skill)
    return None, True
