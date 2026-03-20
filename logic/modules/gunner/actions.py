"""
logic/modules/gunner/actions.py
Gunner Skill Handlers: Master of Ballistics and Firearm Tactics.
Pillar: Position Axis, Lethality payloads, and Ballistic Control.
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import action_manager, magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("double_tap")
def handle_double_tap(player, skill, args, target=None):
    """Setup/Builder: Two quick shots and ammo regeneration."""
    target = common._get_target(player, args, target, "Shoot whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}BANG-BANG! Your bullets fly towards {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "bullets", 1, source="Double Tap")
    _consume_resources(player, skill)
    return target, True

@register("flashbang")
def handle_flashbang(player, skill, args, target=None):
    """Setup: [Blinded] applier."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}FLASH! A high-intensity magnesium flare blinds everyone in sight.{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "blinded", 4)
    _consume_resources(player, skill)
    return None, True

@register("hollow_point")
def handle_hollow_point(player, skill, args, target=None):
    """Setup: [Bleeding] and [Marked]."""
    target = common._get_target(player, args, target, "Bleed whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}Your hollow-point round explodes with catastrophic results upon {target.name}.{Colors.RESET}")
    effects.apply_effect(target, "bleeding", 6)
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("gunner_headshot")
def handle_gunner_headshot(player, skill, args, target=None):
    """Payoff/Finisher: massive burst vs status."""
    target = common._get_target(player, args, target, "Seek the head of whom?")
    if not target: return None, True
    
    if any(effects.has_effect(target, s) for s in ["blinded", "stunned", "exposed"]):
        player.send_line(f"{Colors.BOLD}{Colors.RED}HEADSHOT! The impact is catastrophic!{Colors.RESET}")
        player.headshot_multiplier = 4.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'headshot_multiplier'): del player.headshot_multiplier
    else:
        player.send_line(f"BANG! Your shot strikes home, but misses the vital center.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("buckshot")
def handle_buckshot(player, skill, args, target=None):
    """Payoff/AOE: Frontal cone damage."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}BUCKSHOT! You clear the room with a wall of lead!{Colors.RESET}")
    for m in player.room.monsters:
        # Range check: distance(player, m) < close_range?
        player.buck_multiplier = 2.0
        combat.handle_attack(player, m, player.room, player.game, blessing=skill)
        if hasattr(player, 'buck_multiplier'): del player.buck_multiplier
            
    _consume_resources(player, skill)
    return None, True

@register("covering_fire")
def handle_covering_fire(player, skill, args, target=None):
    """Defense: Suppression logic."""
    player.send_line(f"{Colors.CYAN}Covering Fire! You keep the enemy's heads down.{Colors.RESET}")
    effects.apply_effect(player, "suppressing_fire", 6) # Self counter logic
    _consume_resources(player, skill)
    return None, True

@register("tactical_slide")
def handle_tactical_slide(player, skill, args, target=None):
    """Mobility: slide and reload."""
    player.send_line(f"{Colors.WHITE}You slide beneath the line of fire, chambering fresh rounds.{Colors.RESET}")
    resources.modify_resource(player, "bullets", 2)
    # Movement handled in world engine
    _consume_resources(player, skill)
    return None, True

@register("rapid_fire")
def handle_rapid_fire(player, skill, args, target=None):
    """Utility/Buff: Ultimate speed."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}RAPID FIRE! You fan the hammer and unleash hell!{Colors.RESET}")
    effects.apply_effect(player, "rapid_fire_buff", 8)
    _consume_resources(player, skill)
    return None, True
