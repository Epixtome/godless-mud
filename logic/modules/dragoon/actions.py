"""
logic/modules/dragoon/actions.py
Dragoon Skill Handlers: Master of the Skies and the Polearm.
Pillar: Position Axis, Higher Ground bonuses, and Lethality plunges.
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

@register("dragoon_thrust")
def handle_dragoon_thrust(player, skill, args, target=None):
    """Setup/Builder: Piercing damage and Jump pips."""
    target = common._get_target(player, args, target, "Thrust at whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You deliver a powerful lunging thrust with your polearm!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "jump_pips", 1, source="Thrust")
    _consume_resources(player, skill)
    return target, True

@register("dragon_breath")
def handle_dragon_breath(player, skill, args, target=None):
    """Setup: [Burning] and [Off-Balance]."""
    target = common._get_target(player, args, target, "Exhale upon whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You exhale a blast of draconic fire, searing through {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "burning", 4)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("leg_sweep")
def handle_leg_sweep(player, skill, args, target=None):
    """Setup: [Prone] applier."""
    target = common._get_target(player, args, target, "Sweep whose legs?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BLUE}A low sweep knocks {target.name} from their feet!{Colors.RESET}")
    effects.apply_effect(target, "prone", 2)
    effects.apply_effect(target, "staggered", 2)
    _consume_resources(player, skill)
    return target, True

@register("dragoon_jump")
def handle_dragoon_jump(player, skill, args, target=None):
    """Payoff/Finisher: massive plunge vs prone."""
    target = common._get_target(player, args, target, "Jump upon whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}JUMP! You launch yourself high into the heavens...{Colors.RESET}")
    # Invincibility frame
    effects.apply_effect(player, "airborne", 2)
    
    # Delayed hit logic (Simulated here)
    if effects.has_effect(target, "prone"):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}The hunter descends! CRITICAL IMPACT!{Colors.RESET}")
        player.jump_multiplier = 4.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'jump_multiplier'): del player.jump_multiplier
    else:
        player.send_line(f"You descend from the sky, but the target has moved from your optimal path.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    player.ext_state['dragoon']['jump_pips'] = 0
    _consume_resources(player, skill)
    return target, True

@register("dragon_dive")
def handle_dragon_dive(player, skill, args, target=None):
    """Payoff/AOE: fire burst vs burning."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}DRAGON DIVE! You plunge into the center of the fray!{Colors.RESET}")
    for m in player.room.monsters:
        if effects.has_effect(m, "burning"):
            player.dive_multiplier = 2.0
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
            if hasattr(player, 'dive_multiplier'): del player.dive_multiplier
        else:
            combat.handle_attack(player, m, player.room, player.game, blessing=skill)
            
    _consume_resources(player, skill)
    return None, True

@register("steel_scale")
def handle_steel_scale(player, skill, args, target=None):
    """Defense: Self-resistances."""
    player.send_line(f"{Colors.CYAN}Your skin glitters with the hardness of draconic scales.{Colors.RESET}")
    effects.apply_effect(player, "scale_guarded", 8)
    _consume_resources(player, skill)
    return None, True

@register("high_jump")
def handle_high_jump(player, skill, args, target=None):
    """Mobility: Blink and haste."""
    player.send_line(f"{Colors.WHITE}High Jump! You leap across the battlefield in a single bound.{Colors.RESET}")
    effects.apply_effect(player, "haste", 4)
    # Movement handled in world engine
    _consume_resources(player, skill)
    return None, True

@register("dragonheart")
def handle_dragonheart(player, skill, args, target=None):
    """Utility/Buff: Ultimate jump power."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}Your dragonheart ignites, fueling your primal strength!{Colors.RESET}")
    effects.apply_effect(player, "jump_multiplier_buff", 2)
    resources.modify_resource(player, "stamina", 30)
    _consume_resources(player, skill)
    return None, True
