"""
logic/modules/bard/actions.py
Bard Skill Handlers: Master of Tempo and Utility.
V7.2 Standard Refactor (Baking Branch).
"""
import logging
from logic.actions.registry import register
from logic.core import effects, resources, combat, perception
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

logger = logging.getLogger("GodlessMUD")

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("discordant_note")
def handle_discordant_note(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Sonic damage and Rhythm generation with Ridge Rule."""
    target = common._get_target(player, args, target, "Jar which ear?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Your discordant notes are muffled by the terrain.")
        return None, True

    player.send_line(f"{Colors.BLUE}You strike a jarring chord that resonates within {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Rhythm Generation via URM
    resources.modify_resource(player, "rhythm", 5, source="Discordant Note")
    
    _consume_resources(player, skill)
    return target, True

@register("fascinate")
def handle_fascinate(player, skill, args, target=None):
    """[V7.2] Setup: [Dazed] applier with Ridge Rule."""
    target = common._get_target(player, args, target, "Fascinate whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The hypnotic melody fails to reach the target.")
        return None, True

    player.send_line(f"{Colors.CYAN}You weave a hypnotic melody that captivates {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "dazed", 4)
    _consume_resources(player, skill)
    return target, True

@register("echoing_verse")
def handle_echoing_verse(player, skill, args, target=None):
    """[V7.2] Setup: [Marked] with Ridge Rule."""
    target = common._get_target(player, args, target, "Mark whose soul?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The echo dissipates against the ridges.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You mark the resonance of {target.name}'s spirit.{Colors.RESET}")
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("crescendo")
def handle_crescendo(player, skill, args, target=None):
    """[V7.2] Payoff/Finisher: Sonic burst vs Dazed. Logic-Data Wall sync."""
    target = common._get_target(player, args, target, "Unleash the peak upon whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The crescendo is swallowed by the terrain.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules.
    if effects.has_effect(target, "dazed"):
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}CRESCENDO! The world shatters around {target.name}!{Colors.RESET}")
        effects.remove_effect(target, "dazed")
    else:
        player.send_line(f"Your performance peaks, but {target.name} isn't properly fascinated.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("soul_requiem")
def handle_soul_requiem(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Sonic detonation. Ridge Rule for each target."""
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}SOUL REQUIEM! A mournful dirge echoes...{Colors.RESET}")
    
    # Hit each marked target
    for m in player.room.monsters:
        if effects.has_effect(m, "marked") and perception.can_see(player, m):
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
        
    # [V7.2] Team Heal via URM for consistency
    for p in player.room.players:
        heal_amt = int(p.max_hp * 0.1)
        resources.modify_resource(p, "hp", heal_amt, source="Soul Requiem", context="Hymnal Mending")
        p.send_line(f"{Colors.GREEN}The requiem heals you for {heal_amt} health.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return None, True

@register("serenade_of_safety")
def handle_serenade_of_safety(player, skill, args, target=None):
    """Defense: AOE Shielding."""
    player.send_line(f"{Colors.CYAN}A protective lullaby surrounds your party.{Colors.RESET}")
    for p in player.room.players:
        effects.apply_effect(p, "shielded", 4)
        effects.apply_effect(p, "braced", 4)
        
    _consume_resources(player, skill)
    return None, True

@register("allegro_step")
def handle_allegro_step(player, skill, args, target=None):
    """[V7.2] Mobility: Escape and Haste."""
    player.send_line(f"{Colors.WHITE}Allegro! You dash forward with supernatural speed.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    # Clear slowing effects
    if effects.has_effect(player, "slowed"):
        effects.remove_effect(player, "slowed")
        player.send_line(f"{Colors.CYAN}You shake off the slowing rhythm.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return None, True

@register("hymn_of_regeneration")
def handle_hymn_of_regeneration(player, skill, args, target=None):
    """[V7.2] Utility: Persistent HoT. Consumes Rhythm via URM."""
    player.send_line(f"{Colors.GREEN}You begin an ancient hymn of natural mending.{Colors.RESET}")
    
    # [V7.2] Rhythm access via URM
    rhythm = resources.get_resource(player, "rhythm")
    duration = 10 + (rhythm // 10)
    
    for p in player.room.players:
        effects.apply_effect(p, "regeneration", duration)
        
    # Consume all rhythm
    resources.modify_resource(player, "rhythm", -rhythm, source="Hymn Consumption")
    _consume_resources(player, skill)
    return None, True
