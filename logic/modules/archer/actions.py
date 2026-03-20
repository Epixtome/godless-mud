"""
logic/modules/archer/actions.py
Archer Skill Handlers: Master of Reach and Tracking.
Pillar: Vision Axis, Crowding control, and Precision Payoffs.
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

@register("quick_shot")
def handle_quick_shot(player, skill, args, target=None):
    """Setup/Builder: High-speed arrow and Focus generation."""
    target = common._get_target(player, args, target, "Quickly shoot whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You loose an arrow in the blink of an eye!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "focus", 5, source="Quick Shot")
    
    _consume_resources(player, skill)
    return target, True

@register("pinning_shot")
def handle_pinning_shot(player, skill, args, target=None):
    """Setup: [Pinned] applier."""
    target = common._get_target(player, args, target, "Pin whose legs?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BLUE}You aim for {target.name}'s legs, pinning them to the earth.{Colors.RESET}")
    effects.apply_effect(target, "pinned", 2)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("tracer_arrow")
def handle_tracer_arrow(player, skill, args, target=None):
    """Setup: [Marked] for vision awareness."""
    target = common._get_target(player, args, target, "Track whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.CYAN}A tracer arrow marks {target.name} with a faint glowing beacon.{Colors.RESET}")
    effects.apply_effect(target, "marked", 12)
    _consume_resources(player, skill)
    return target, True

@register("rain_of_arrows")
def handle_rain_of_arrows(player, skill, args, target=None):
    """Payoff/AOE: Arrow volley based on Pinned targets."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}RAIN OF ARROWS! You blanket the entire room in iron!{Colors.RESET}")
    for m in player.room.monsters:
        if effects.has_effect(m, "pinned"):
            player.rain_multiplier = 2.0
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
            if hasattr(player, 'rain_multiplier'): del player.rain_multiplier
        else:
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
            
    _consume_resources(player, skill)
    return None, True

@register("heartseeker_shot")
def handle_heartseeker_shot(player, skill, args, target=None):
    """Payoff/Finisher: massive burst vs marked."""
    target = common._get_target(player, args, target, "Seek whose heart?")
    if not target: return None, True
    
    if effects.has_effect(target, "marked"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}HEARTSEEKER SHOT! The arrow finds the beacon with deadly precision!{Colors.RESET}")
        player.heart_multiplier = 4.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'heart_multiplier'): del player.heart_multiplier
    else:
        player.send_line(f"You fire blindly into the target's center, but fail to find a vital path.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("dodge_roll")
def handle_dodge_roll(player, skill, args, target=None):
    """Defense: Self-evasion."""
    player.send_line(f"{Colors.CYAN}You roll to the side, maintaining your distance.{Colors.RESET}")
    effects.apply_effect(player, "nimble_roll", 1) # Custom evasion logic in game core
    _consume_resources(player, skill)
    return None, True

@register("backstep_shot")
def handle_backstep_shot(player, skill, args, target=None):
    """Mobility: retreat and fire."""
    player.send_line(f"{Colors.WHITE}You leap backwards and fire a slowing shot mid-air!{Colors.RESET}")
    # Movement handled in world engine?
    effects.apply_effect(player, "haste", 1)
    _consume_resources(player, skill)
    return None, True

@register("eagle_eye")
def handle_eagle_eye(player, skill, args, target=None):
    """Utility/Buff: Accuracy and Vision Awareness."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}Eagle Eye! Your vision pierces the fog of war.{Colors.RESET}")
    effects.apply_effect(player, "accuracy_buff", 20)
    # Vision logic update in Perception Matrix
    _consume_resources(player, skill)
    return None, True
