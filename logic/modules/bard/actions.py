"""
logic/modules/bard/actions.py
Bard Class Skills: Harmonic Flow implementation.
V7.2 Standard Refactor.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from utilities.colors import Colors

def _consume_resources(player, skill):
    from logic.engines import magic_engine
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)

@register("discordant_note")
def handle_discordant_note(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A jarring, discordant note strikes {target.name}.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'stamina', 15, source="Discordant Note")
    resources.modify_resource(player, 'rhythm', 1, source="Discordant Note")
    _consume_resources(player, skill)
    return target, True

@register("fascinate")
def handle_fascinate(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"Your hypnotic melody fascinates {target.name}.")
    effects.apply_effect(target, "stalled", 4)
    resources.modify_resource(player, 'rhythm', 1, source="Fascinate")
    _consume_resources(player, skill)
    return target, True

@register("crescendo")
def handle_crescendo(player, skill, args, target=None):
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}CRESCENDO!{Colors.RESET} An orchestral blast fills the room!")
    targets = [m for m in player.room.monsters if combat.is_target_valid(player, m)]
    for t in targets:
        combat.handle_attack(player, t, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return None, True

@register("soul_requiem")
def handle_soul_requiem(player, skill, args, target=None):
    from .utils import get_target
    target = get_target(player, args, target)
    if not target: return None, True
    player.send_line(f"A mournful song drains {target.name}'s life.")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, 'concentration', 30, source="Soul Requiem")
    _consume_resources(player, skill)
    return target, True

@register("serenade_of_safety")
def handle_serenade_of_safety(player, skill, args, target=None):
    player.send_line(f"A soothing melody protects you and your allies.")
    effects.apply_effect(player, "shielded", 4)
    _consume_resources(player, skill)
    return None, True

@register("allegro_step")
def handle_allegro_step(player, skill, args, target=None):
    player.send_line(f"{Colors.CYAN}ALLEGRO!{Colors.RESET} You dance out of the way.")
    effects.apply_effect(player, "evasive", 2)
    _consume_resources(player, skill)
    return None, True

@register("hymn_of_regeneration")
def handle_hymn_of_regeneration(player, skill, args, target=None):
    player.send_line(f"A song of health fills the air.")
    effects.apply_effect(player, "regeneration", 10)
    _consume_resources(player, skill)
    return None, True

@register("echoing_verse")
def handle_echoing_verse(player, skill, args, target=None):
    player.send_line(f"An echo of your song repeats in the distance.")
    _consume_resources(player, skill)
    return None, True
