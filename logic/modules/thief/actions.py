"""
logic/modules/thief/actions.py
Thief Skill Handlers: Master of deception, pilfering, and dirty tricks.
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

@register("mug")
def handle_mug(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Physical damage and Greed generation with Ridge Rule."""
    target = common._get_target(player, args, target, "Rob whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("You can't mug what you can't see; the shadows hide your mark.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You strike {target.name} and pilfer a stack of coins!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Greed via URM
    resources.modify_resource(player, "greed", 5, source="Mug")
    
    _consume_resources(player, skill)
    return target, True

@register("sand_in_eyes")
def handle_sand_in_eyes(player, skill, args, target=None):
    """[V7.2] Setup: Blinded applier with Ridge Rule."""
    target = common._get_target(player, args, target, "Throw sand at whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The sand is caught by a sudden gust against a ridge.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Pocket sand! {target.name} is blinded!{Colors.RESET}")
    effects.apply_effect(target, "blinded", 6)
    resources.modify_resource(player, "greed", 10, source="Sand")
    _consume_resources(player, skill)
    return target, True

@register("cheap_shot")
def handle_cheap_shot(player, skill, args, target=None):
    """[V7.2] Setup: Off-Balance with Ridge Rule gate."""
    target = common._get_target(player, args, target, "Dirty trick on whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("You can't reach their vitals from behind this ridge.")
        return None, True

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
    """[V7.2] Payoff/Burst: Disabling blow with Ridge Rule & Logic-Data Wall."""
    target = common._get_target(player, args, target, "Disable whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The vital points are hidden by the terrain.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules.
    if effects.has_effect(target, "blinded") or effects.has_effect(target, "stunned"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}KIDNEY SHOT! You strike a vital node while they stagger!{Colors.RESET}")
        effects.apply_effect(target, "exposed", 2)
    else:
        player.send_line(f"You strike with power, but fail to find a vital opening.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("final_heist")
def handle_final_heist(player, skill, args, target=None):
    """[V7.2] Finisher: Mass payoff via Greed with Ridge Rule."""
    target = common._get_target(player, args, target, "Final score from whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The heist is cancelled; LoS is blocked.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}FINAL HEIST! All your dirty tricks culminate in a single perfect strike!{Colors.RESET}")
    
    # [V7.2] Multipliers in JSON.
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Consume all Greed via URM
    greed = resources.get_resource(player, "greed")
    resources.modify_resource(player, "greed", -greed, source="Perfect Heist")
             
    _consume_resources(player, skill)
    return target, True

@register("nimble_reflexes")
def handle_nimble_reflexes(player, skill, args, target=None):
    """Defense: Evasion."""
    player.send_line(f"{Colors.CYAN}You dance effortlessly, slipping through the air.{Colors.RESET}")
    effects.apply_effect(player, "thief_evasion", 6)
    if effects.has_effect(player, "pinned"):
        effects.remove_effect(player, "pinned")
    _consume_resources(player, skill)
    return None, True

@register("pickpocket_dash")
def handle_pickpocket_dash(player, skill, args, target=None):
    """[V7.2] Mobility: Linear dash with Ridge Rule logic."""
    target = common._get_target(player, args, target, "Dash past whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("You cannot dash past a shadow.")
        return None, True

    player.send_line(f"{Colors.WHITE}You flicker past {target.name}, your hand dipping into their pockets.{Colors.RESET}")
    effects.apply_effect(player, "haste", 2)
    _consume_resources(player, skill)
    return target, True

@register("stealth")
def handle_stealth(player, skill, args, target=None):
    """Utility/Ultimate: Master-level deception."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}You blend into the shadows, becoming one with the dark.{Colors.RESET}")
    # Set hidden state in ext_state
    if 'thief' in player.ext_state:
        player.ext_state['thief']['is_hidden'] = True
    effects.apply_effect(player, "concealed", 99)
    _consume_resources(player, skill)
    return None, True
