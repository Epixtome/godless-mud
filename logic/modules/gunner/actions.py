"""
logic/modules/gunner/actions.py
Gunner Skill Handlers: Master of Ballistics and Firearm Tactics.
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

@register("double_tap")
def handle_double_tap(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Two quick shots with Ridge Rule."""
    target = common._get_target(player, args, target, "Shoot whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("The line of fire is obstructed by the terrain.")
        return None, True

    player.send_line(f"{Colors.YELLOW}BANG-BANG! Your bullets fly towards {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Ammo Check/Generate logic (Legacy used generation, standard uses consumption)
    # We maintain the resource mod for the 'Reload' mechanic.
    resources.modify_resource(player, "bullets", 1, source="Double Tap Recoil")
    
    _consume_resources(player, skill)
    return target, True

@register("flashbang")
def handle_flashbang(player, skill, args, target=None):
    """[V7.2] Setup: AOE Blind with Ridge Rule LoS."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}FLASH! A high-intensity magnesium flare blinds everyone in sight.{Colors.RESET}")
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "blinded", 4)
    _consume_resources(player, skill)
    return None, True

@register("hollow_point")
def handle_hollow_point(player, skill, args, target=None):
    """[V7.2] Setup: Bleeding/Marked with Ridge Rule."""
    target = common._get_target(player, args, target, "Bleed whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("You can't get a clear shot at their vitals.")
        return None, True

    player.send_line(f"{Colors.RED}Your hollow-point round explodes with catastrophic results upon {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "bleeding", 6)
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("gunner_headshot")
def handle_gunner_headshot(player, skill, args, target=None):
    """[V7.2] Payoff/Finisher: Dead-eye accuracy with Ridge Rule & Logic-Data Wall."""
    target = common._get_target(player, args, target, "Seek the head of whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The target's head is hidden behind a ridge.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules.
    if any(effects.has_effect(target, s) for s in ["blinded", "stunned", "exposed"]):
        player.send_line(f"{Colors.BOLD}{Colors.RED}HEADSHOT! The impact is catastrophic!{Colors.RESET}")
    else:
        player.send_line(f"BANG! Your shot strikes home, but misses the vital center.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("buckshot")
def handle_buckshot(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Spread fire. Ridge Rule per target."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}BUCKSHOT! You clear the room with a wall of lead!{Colors.RESET}")
    for m in player.room.monsters:
        if perception.can_see(player, m):
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
            
    _consume_resources(player, skill)
    return None, True

@register("covering_fire")
def handle_covering_fire(player, skill, args, target=None):
    """Defense: Suppression."""
    player.send_line(f"{Colors.CYAN}Covering Fire! You keep the enemy's heads down.{Colors.RESET}")
    effects.apply_effect(player, "suppressing_fire", 6)
    _consume_resources(player, skill)
    return None, True

@register("tactical_slide")
def handle_tactical_slide(player, skill, args, target=None):
    """[V7.2] Mobility: Slide and partial reload via URM."""
    player.send_line(f"{Colors.WHITE}You slide beneath the line of fire, chambering fresh rounds.{Colors.RESET}")
    resources.modify_resource(player, "bullets", 2, source="Tactical Slide")
    _consume_resources(player, skill)
    return None, True

@register("rapid_fire")
def handle_rapid_fire(player, skill, args, target=None):
    """Utility/Buff: High-speed fanning."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}RAPID FIRE! You fan the hammer and unleash hell!{Colors.RESET}")
    effects.apply_effect(player, "rapid_fire_buff", 8)
    _consume_resources(player, skill)
    return None, True
