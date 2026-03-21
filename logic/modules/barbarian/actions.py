"""
logic/modules/barbarian/actions.py
Barbarian Skill Handlers: Master of the Tempo and Endurance Axes.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.actions.registry import register
from logic.core import effects, resources, combat
from logic.engines import magic_engine
from utilities.colors import Colors
from logic import common

def _consume_resources(player, skill):
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)

@register("savage_strike")
def handle_savage_strike(player, skill, args, target=None):
    """Setup/Builder: Basic hit, generates fury."""
    target = common._get_target(player, args, target, "Savage whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You hit {target.name} with brute force!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] URM integration
    resources.modify_resource(player, "stamina", 15, source="Savage Strike")
    resources.modify_resource(player, "fury", 5, source="Savage Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("headbutt")
def handle_headbutt(player, skill, args, target=None):
    """Setup: [Off-Balance] applier."""
    target = common._get_target(player, args, target, "Headbutt whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}KRONK!{Colors.RESET} You slam your forehead into {target.name}'s skull!")
    effects.apply_effect(target, "off_balance", 3)
    resources.modify_resource(player, "fury", 10, source="Headbutt")
    
    _consume_resources(player, skill)
    return target, True

@register("lacerate")
def handle_lacerate(player, skill, args, target=None):
    """Setup: [Bleeding] applier."""
    target = common._get_target(player, args, target, "Lacerate whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You sweep your blade through {target.name}'s side!{Colors.RESET}")
    effects.apply_effect(target, "bleeding", 6)
    resources.modify_resource(player, "fury", 10, source="Lacerate")
    
    _consume_resources(player, skill)
    return target, True

@register("whirlwind")
def handle_whirlwind(player, skill, args, target=None):
    """Payoff/AOE: Consumes 50 Fury."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}WHIRLWIND!{Colors.RESET} You spin in a lethal blur of steel!")
    
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    for t in targets:
         combat.handle_attack(player, t, player.room, player.game, blessing=skill, context_prefix="[Spin] ")
         
    _consume_resources(player, skill)
    return None, True

@register("decapitate")
def handle_decapitate(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Prone/Bleeding.
    [V7.2] Logic-Data Wall: 3x Multiplier handles via JSON potency_rules.
    """
    target = common._get_target(player, args, target, "Decapitate whom?")
    if not target: return None, True

    if effects.has_effect(target, "prone") or effects.has_effect(target, "bleeding"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}TRY TO SURVIVE THIS!{Colors.RESET} You bring your weapon down on {target.name}'s neck!")
    else:
        player.send_line(f"You deliver a heavy blow, but {target.name} keeps their head.")
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("savage_brace")
def handle_savage_brace(player, skill, args, target=None):
    """Defense: Mitigation."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}You tense for impact, welcoming the fury of pain.{Colors.RESET}")
    effects.apply_effect(player, "savage_brace", 4)
    _consume_resources(player, skill)
    return None, True

@register("leap")
def handle_leap(player, skill, args, target=None):
    """Mobility: Leap and slam arrival."""
    player.send_line(f"{Colors.CYAN}You leap into the air, falling onto your foes with catastrophic force!{Colors.RESET}")
    
    # Breaks movement restrictions
    for state in ["pinned", "grappled", "prone"]:
        if effects.has_effect(player, state):
            effects.remove_effect(player, state)
            
    # AOE Impact
    targets = [m for m in player.room.monsters] + [p for p in player.room.players if p != player]
    for t in targets:
         effects.apply_effect(t, "staggered", 1)
         
    _consume_resources(player, skill)
    return None, True

@register("bloodrage")
def handle_bloodrage(player, skill, args, target=None):
    """Utility/Ultimate: CC immunity."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}BLOODRAGE!{Colors.RESET} Your blood screams for slaughter.")
    effects.apply_effect(player, "bloodrage", 10)
    _consume_resources(player, skill)
    return None, True
