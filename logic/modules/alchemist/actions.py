"""
logic/modules/alchemist/actions.py
Alchemist Skill Handlers: Master of Chemical Reactions and Transmutation.
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

@register("volatile_flask")
def handle_volatile_flask(player, skill, args, target=None):
    """[V7.2] Setup/Builder: Flask toss with Ridge Rule logic."""
    target = common._get_target(player, args, target, "Toss flask at whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("The Ridges block your throw.")
        return None, True

    player.send_line(f"{Colors.RED}You shatter a volatile flask against {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Pip Generation via URM
    resources.modify_resource(player, "alchemical_pips", 1, source="Volatile Flask")
    
    _consume_resources(player, skill)
    return target, True

@register("acid_mist")
def handle_acid_mist(player, skill, args, target=None):
    """[V7.2] Setup: Mist deployment with Ridge Rule."""
    target = common._get_target(player, args, target, "Dissolve whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The mist is contained by the terrain.")
        return None, True

    player.send_line(f"{Colors.GREEN}A thick cloud of acrid mist melts through {target.name}'s defenses.{Colors.RESET}")
    effects.apply_effect(target, "staggered", 2)
    effects.apply_effect(target, "acid_melt", 6)
    _consume_resources(player, skill)
    return target, True

@register("catalytic_bloom")
def handle_catalytic_bloom(player, skill, args, target=None):
    """[V7.2] Setup: Marker with Ridge Rule sync."""
    target = common._get_target(player, args, target, "Catalyze whose spirit?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The catalyst fails to reach the target.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You mark {target.name} with a highly reactive alchemical catalyst.{Colors.RESET}")
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("final_flash")
def handle_final_flash(player, skill, args, target=None):
    """[V7.2] Payoff/Finisher: Status detonation with Ridge Rule & Logic-Data Wall."""
    target = common._get_target(player, args, target, "Ignite the final reagent on whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The ignition spark is blocked by the terrain.")
        return None, True

    has_status = any(effects.has_effect(target, s) for s in ["wet", "burning", "frozen", "poisoned"])
    if has_status:
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}FINAL FLASH! The chemical reaction is catastrophic!{Colors.RESET}")
        # Multipliers handled via potency_rules in JSON.
        
        # Cleanup statuses
        for s in ["wet", "burning", "frozen", "poisoned"]:
             if effects.has_effect(target, s):
                  effects.remove_effect(target, s)
    else:
        player.send_line(f"Your reagents fizzle harmlessly against {target.name}'s neutral state.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("transmute_flesh")
def handle_transmute_flesh(player, skill, args, target=None):
    """[V7.2] Payoff/Burst: Flesh mutation with Ridge Rule."""
    target = common._get_target(player, args, target, "Transmute whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The transmutation beam is obstructed.")
        return None, True

    player.send_line(f"{Colors.MAGENTA}You force a molecular shift within {target.name}, melting their resolve.{Colors.RESET}")
    effects.apply_effect(target, "poisoned", 6)
    effects.apply_effect(target, "off_balance", 4)
    
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("elixir_of_stone")
def handle_elixir_of_stone(player, skill, args, target=None):
    """Defense: Self-hardening."""
    player.send_line(f"{Colors.CYAN}You quaff an elixir of stone, hardening your skin to granite.{Colors.RESET}")
    effects.apply_effect(player, "braced", 10)
    _consume_resources(player, skill)
    return None, True

@register("smokebomb_jump")
def handle_smokebomb_jump(player, skill, args, target=None):
    """[V7.2] Mobility: Blink and blind AoE."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}POOF! You vanish in a cloud of dense ash.{Colors.RESET}")
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "blinded", 4)
            
    _consume_resources(player, skill)
    return None, True

@register("create_philter")
def handle_create_philter(player, skill, args, target=None):
    """[V7.2] Utility: Consumption of Pips via URM."""
    pips = resources.get_resource(player, "alchemical_pips")
    if pips < 3:
         player.send_line(f"You need at least 3 alchemy pips to distillation a philter.")
         return None, True
         
    player.send_line(f"{Colors.GREEN}You mix your active pips into a glowing philter of renewal.{Colors.RESET}")
    
    # Heal via URM for consistency
    heal_amt = int(player.max_hp * (0.10 + (pips * 0.05)))
    resources.modify_resource(player, "hp", heal_amt, source="Philter of Renewal")
    resources.modify_resource(player, "stamina", 20, source="Philter Stimulation")
    
    # Consume pips
    resources.modify_resource(player, "alchemical_pips", -pips, source="Distillation")
    
    _consume_resources(player, skill)
    return None, True
