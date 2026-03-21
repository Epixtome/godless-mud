"""
logic/modules/dragoon/actions.py
Dragoon Skill Handlers: Master of the Skies and the Polearm.
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

@register("dragoon_thrust")
def handle_dragoon_thrust(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Piercing damage and Jump pips with Ridge Rule."""
    target = common._get_target(player, args, target, "Thrust at whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("The lunge is blocked by a terrain obstruction.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You deliver a powerful lunging thrust with your polearm!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Jump Pips via URM
    resources.modify_resource(player, "jump_pips", 1, source="Dragoon Thrust")
    
    _consume_resources(player, skill)
    return target, True

@register("dragon_breath")
def handle_dragon_breath(player, skill, args, target=None):
    """[V7.2] Setup: Burning and Off-Balance with Ridge Rule."""
    target = common._get_target(player, args, target, "Exhale upon whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The fire plumes dissipate against the ridges.")
        return None, True

    player.send_line(f"{Colors.RED}You exhale a blast of draconic fire, searing through {target.name}!{Colors.RESET}")
    effects.apply_effect(target, "burning", 4)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("leg_sweep")
def handle_leg_sweep(player, skill, args, target=None):
    """[V7.2] Setup: Prone applier with Ridge Rule gate."""
    target = common._get_target(player, args, target, "Sweep whose legs?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("You sweep into the dirt; the target is hidden.")
        return None, True

    player.send_line(f"{Colors.BLUE}A low sweep knocks {target.name} from their feet!{Colors.RESET}")
    effects.apply_effect(target, "prone", 2)
    effects.apply_effect(target, "staggered", 2)
    _consume_resources(player, skill)
    return target, True

@register("dragoon_jump")
def handle_dragoon_jump(player, skill, args, target=None):
    """[V7.2] Payoff/Finisher: Plunge from the sky with Ridge Rule and Logic-Data Wall."""
    target = common._get_target(player, args, target, "Jump upon whom?")
    if not target: return None, True
    
    # Jumps can sometimes ignore local ridges if 'Vertical' tag is present (future hook)
    if not perception.can_see(player, target):
        player.send_line("You descend blindly; the target is no longer in sight.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}JUMP! You launch yourself high into the heavens...{Colors.RESET}")
    # Airborne state
    effects.apply_effect(player, "airborne", 2)
    
    # [V7.2] Multipliers handled in JSON potency_rules.
    if effects.has_effect(target, "prone"):
        player.send_line(f"{Colors.BOLD}{Colors.CYAN}The hunter descends! CRITICAL IMPACT!{Colors.RESET}")
    else:
        player.send_line(f"You descend from the sky, but the target has moved from your optimal path.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # Consume Jump Pips via URM
    pips = resources.get_resource(player, "jump_pips")
    resources.modify_resource(player, "jump_pips", -pips, source="Plunge Execution")
    
    _consume_resources(player, skill)
    return target, True

@register("dragon_dive")
def handle_dragon_dive(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Plunge burst. Ridge Rule for each target."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}DRAGON DIVE! You plunge into the center of the fray!{Colors.RESET}")
    
    # Hit each visible target
    for m in player.room.monsters:
        if perception.can_see(player, m):
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
    """[V7.2] Mobility: Linear LoS bypass leap."""
    player.send_line(f"{Colors.WHITE}High Jump! You leap across the battlefield in a single bound.{Colors.RESET}")
    effects.apply_effect(player, "haste", 4)
    if effects.has_effect(player, "immobilized"):
        effects.remove_effect(player, "immobilized")
        player.send_line(f"{Colors.CYAN}You break free from movement blocks.{Colors.RESET}")
        
    _consume_resources(player, skill)
    return None, True

@register("dragonheart")
def handle_dragonheart(player, skill, args, target=None):
    """[V7.2] Utility/Buff: Energy recovery via URM."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}Your dragonheart ignites, fueling your primal strength!{Colors.RESET}")
    effects.apply_effect(player, "jump_multiplier_buff", 2)
    resources.modify_resource(player, "stamina", 30, source="Dragonheart Ignition")
    _consume_resources(player, skill)
    return None, True
