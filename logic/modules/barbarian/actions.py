"""
logic/modules/barbarian/actions.py
Barbarian Skill Handlers: Master of the Tempo and Endurance Axes.
Pillar: Fury, Bleeding, and Bone-crushing impact.
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

@register("savage_strike")
def handle_savage_strike(player, skill, args, target=None):
    """Setup/Builder: Basic hit, generates fury."""
    target = common._get_target(player, args, target, "Savage whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You hit {target.name} with brute force!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    # Generate Stamina and +5 Fury
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
         # Bonus vs bleeding handled in calculation if possible, else manually here.
         combat.handle_attack(player, t, player.room, player.game, blessing=skill)
         
    _consume_resources(player, skill)
    return None, True

@register("decapitate")
def handle_decapitate(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Prone/Bleeding."""
    target = common._get_target(player, args, target, "Decapitate whom?")
    if not target: return None, True

    if effects.has_effect(target, "prone") or effects.has_effect(target, "bleeding"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}TRY TO SURVIVE THIS!{Colors.RESET} You bring your weapon down on {target.name}'s neck!")
        player.execute_multiplier = 3.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'execute_multiplier'): del player.execute_multiplier
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
    if effects.has_effect(player, "pinned") or effects.has_effect(player, "grappled"):
        effects.remove_effect(player, "pinned")
        effects.remove_effect(player, "grappled")
        player.send_line(f"{Colors.GREEN}You snap free of their hold!{Colors.RESET}")
        
    for t in [m for m in player.room.monsters] + [p for p in player.room.players if p != player]:
         effects.apply_effect(t, "staggered", 1)
         
    _consume_resources(player, skill)
    return None, True

@register("bloodrage")
def handle_bloodrage(player, skill, args, target=None):
    """Utility/Ultimate: CC immunity."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}BLOODRAGE!{Colors.RESET} The logic of mortality no longer applies to you.")
    effects.apply_effect(player, "bloodrage", 10)
    _consume_resources(player, skill)
    return None, True
