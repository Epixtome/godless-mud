"""
logic/modules/thief/actions.py
Thief Skill Handlers: Master of deception, pilfering, and dirty tricks.
Pillar: Vision Axis, Resource Theft, and Disruption.
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

@register("mug")
def handle_mug(player, skill, args, target=None):
    """Setup/Builder: Physical damage and Gold theft."""
    target = common._get_target(player, args, target, "Rob whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike {target.name} and pilfer a stack of coins!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    # Give gold logic
    resources.modify_resource(player, "greed", 5, source="Mug")
    _consume_resources(player, skill)
    return target, True

@register("sand_in_eyes")
def handle_sand_in_eyes(player, skill, args, target=None):
    """Setup: [Blinded] applier."""
    target = common._get_target(player, args, target, "Throw sand at whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Pocket sand! {target.name} is blinded!{Colors.RESET}")
    effects.apply_effect(target, "blinded", 6)
    resources.modify_resource(player, "greed", 10, source="Sand")
    _consume_resources(player, skill)
    return target, True

@register("cheap_shot")
def handle_cheap_shot(player, skill, args, target=None):
    """Setup: [Off-Balance] and [Staggered]."""
    target = common._get_target(player, args, target, "Dirty trick on whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You land a low blow beneath {target.name}'s guard.{Colors.RESET}")
    effects.apply_effect(target, "off_balance", 4)
    effects.apply_effect(target, "staggered", 2)
    if effects.has_effect(target, "blinded"):
        effects.apply_effect(target, "pinned", 2)
        player.send_line(f"{Colors.YELLOW}The target is crippled by your dirty tactics!{Colors.RESET}")
        
    _consume_resources(player, skill)
    return target, True

@register("kidney_shot")
def handle_kidney_shot(player, skill, args, target=None):
    """Payoff/Burst: Disabling blow vs blinded/stunned."""
    target = common._get_target(player, args, target, "Disable whom?")
    if not target: return None, True
    
    if effects.has_effect(target, "blinded") or effects.has_effect(target, "stunned"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}KIDNEY SHOT! You strike a vital node while they stagger!{Colors.RESET}")
        player.kidney_multiplier = 3.0
        effects.apply_effect(target, "exposed", 2)
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'kidney_multiplier'): del player.kidney_multiplier
    else:
        player.send_line(f"You strike with power, but fail to find a vital opening.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("final_heist")
def handle_final_heist(player, skill, args, target=None):
    """Finisher: massive physical strike and item theft."""
    target = common._get_target(player, args, target, "Final score from whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}FINAL HEIST! All your dirty tricks culminate in a single perfect strike!{Colors.RESET}")
    hp_pct = target.hp / target.max_hp
    if hp_pct < 0.25:
        player.heist_multiplier = 4.0
        player.send_line(f"{Colors.YELLOW}A perfect execution of a perfect plan!{Colors.RESET}")
        # Steal random item logic
    else:
        player.heist_multiplier = 1.8
        
    try:
         combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    finally:
         if hasattr(player, 'heist_multiplier'): del player.heist_multiplier
             
    player.ext_state['thief']['greed'] = 0 # Consume images
    _consume_resources(player, skill)
    return target, True

@register("nimble_reflexes")
def handle_nimble_reflexes(player, skill, args, target=None):
    """Defense: Evasion and Pinned clear."""
    player.send_line(f"{Colors.CYAN}You dance effortlessly, slipping through the air.{Colors.RESET}")
    effects.apply_effect(player, "thief_evasion", 6)
    if effects.has_effect(player, "pinned"):
        effects.remove_effect(player, "pinned")
    _consume_resources(player, skill)
    return None, True

@register("pickpocket_dash")
def handle_pickpocket_dash(player, skill, args, target=None):
    """Mobility: dash and steal."""
    target = common._get_target(player, args, target, "Dash past whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.WHITE}You flicker past {target.name}, your hand dipping into their pockets.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return target, True

@register("stealth")
def handle_stealth(player, skill, args, target=None):
    """Utility/Ultimate: Master-level deception."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}You blend into the shadows, becoming one with the dark.{Colors.RESET}")
    effects.apply_effect(player, "concealed", 99) # Permanent until broken
    _consume_resources(player, skill)
    return None, True
