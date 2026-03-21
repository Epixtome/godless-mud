"""
logic/modules/knight/actions.py
Knight Skill Handlers: The Anchor of Endurance and Position.
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

@register("crippling_strike")
def handle_crippling_strike(player, skill, args, target=None):
    """Setup: Low-cost builder."""
    target = common._get_target(player, args, target, "Cripple whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BLUE}You strike low, hampering your target's stride!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] URM
    resources.modify_resource(player, "stamina", 5, source="Crippling Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("shield_bash")
def handle_shield_bash(player, skill, args, target=None):
    """Setup: [Off-Balance] applier."""
    target = common._get_target(player, args, target, "Shield bash whom?")
    if not target: return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You slam your shield into {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("execute")
def handle_execute(player, skill, args, target=None):
    """Payoff/Finisher: massive damage vs Prone.
    [V7.2] Logic-Data Wall: Multiplier in JSON.
    """
    target = common._get_target(player, args, target, "Deliver the final blow to whom?")
    if not target: return None, True

    if effects.has_effect(target, "prone"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}EXECUTE! You bring your sword down with crushing finality!{Colors.RESET}")
    else:
        player.send_line(f"You deliver a heavy blow, but {target.name} is still standing.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("retribution")
def handle_retribution(player, skill, args, target=None):
    """Payoff/Counter: Multiplier if guarding or after a block.
    [V7.2] Logic-Data Wall: Multipliers in JSON.
    """
    target = common._get_target(player, args, target, "Strike back at whom?")
    if not target: return None, True
    
    if effects.has_effect(player, "guarding") or effects.has_effect(player, "blocked_recently"):
         player.send_line(f"{Colors.YELLOW}[RETRIBUTION] You exploit their over-extension!{Colors.RESET}")
         
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)

    _consume_resources(player, skill)
    return target, True

@register("brace")
def handle_brace(player, skill, args, target=None):
    """Defense: Stability buff."""
    player.send_line(f"{Colors.BOLD}{Colors.CYAN}You plant your shield and brace for the storm.{Colors.RESET}")
    effects.apply_effect(player, "braced", 4)
    _consume_resources(player, skill)
    return None, True

@register("shield_wall")
def handle_shield_wall(player, skill, args, target=None):
    """Defense: Guarding buff."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}SHIELD WALL! You form an iron line of defense.{Colors.RESET}")
    effects.apply_effect(player, "guarding", 6)
    _consume_resources(player, skill)
    return None, True

@register("charge")
def handle_charge(player, skill, args, target=None):
    """Mobility: Rush target."""
    target = common._get_target(player, args, target, "Charge whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.CYAN}You burst forward, initiating combat!{Colors.RESET}")
    if effects.has_effect(player, "stalled"):
        effects.remove_effect(player, "stalled")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    _consume_resources(player, skill)
    return target, True

@register("war_cry")
def handle_war_cry(player, skill, args, target=None):
    """Utility/Support."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}AAAARRRRGH!{Colors.RESET} Your thunderous shout echoes through the room.")
    
    # Restore Posture/Stamina
    resources.modify_resource(player, "stamina", 20, source="War Cry")
    
    _consume_resources(player, skill)
    return None, True
