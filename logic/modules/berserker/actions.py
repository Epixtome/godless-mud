"""
logic/modules/berserker/actions.py
Berserker Skill Handlers: Master of Pain and Primal Fury.
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

@register("raging_strike")
def handle_raging_strike(player, skill, args, target=None):
    """[V7.2] Setup/Builder: High-impact physical with Ridge Rule."""
    target = common._get_target(player, args, target, "Maul whom?")
    if not target: return None, True
    
    # 1. Physics Gate (Ridge Rule)
    if not perception.can_see(player, target):
        player.send_line("Your wild swings miss the target in the shadows.")
        return None, True

    player.send_line(f"{Colors.YELLOW}You strike with primal fury, building your bloodlust!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    # [V7.2] Fury via URM
    resources.modify_resource(player, "fury", 10, source="Raging Strike")
    
    _consume_resources(player, skill)
    return target, True

@register("headbutt")
def handle_headbutt(player, skill, args, target=None):
    """[V7.2] Setup: Stagger disruptor with Ridge Rule."""
    target = common._get_target(player, args, target, "Bash heads with whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("You charge into a ridge instead of the target.")
        return None, True

    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CRACK! You slam your forehead into {target.name}'s skull.{Colors.RESET}")
    effects.apply_effect(player, "staggered", 1)
    effects.apply_effect(target, "staggered", 2)
    effects.apply_effect(target, "off_balance", 4)
    
    resources.modify_resource(player, "fury", 15, source="Headbutt")
    _consume_resources(player, skill)
    return target, True

@register("blood_thirst")
def handle_blood_thirst(player, skill, args, target=None):
    """[V7.2] Setup: Bleeding for life-steal with Ridge Rule."""
    target = common._get_target(player, args, target, "Feed whose life to the rage?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The scent of blood is cut off by the terrain.")
        return None, True

    player.send_line(f"{Colors.RED}Your blade finds a vital artery, and your hunger grows!{Colors.RESET}")
    effects.apply_effect(target, "bleeding", 6)
    effects.apply_effect(player, "thirsting", 6)
    _consume_resources(player, skill)
    return target, True

@register("reckless_abandon")
def handle_reckless_abandon(player, skill, args, target=None):
    """[V7.2] Payoff/Burst: Scaled damage vs missing HP with Ridge Rule."""
    target = common._get_target(player, args, target, "Abandon caution against whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("You throw yourself at a shadow; the target is hidden.")
        return None, True

    # [V7.2] Multipliers handled in JSON potency_rules (hp_mod).
    hp_pct = player.hp / player.max_hp
    if hp_pct < 0.5:
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[RECKLESS] You scream with manic glee as you throw yourself at {target.name}!{Colors.RESET}")
    else:
        player.send_line(f"You strike with power, but lack the desperation of true abandon.")
        
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("gorespatter")
def handle_gorespatter(player, skill, args, target=None):
    """[V7.2] Payoff/AOE: Gory explosion. Ridge Rule for each target."""
    target = common._get_target(player, args, target, "Execute the final stroke on whom?")
    if not target: return None, True
    
    if not perception.can_see(player, target):
        player.send_line("The finishing blow is obstructed.")
        return None, True

    if effects.has_effect(target, "bleeding"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}GORESPATTER! {target.name}'s blood erupts, blinding others in the room!{Colors.RESET}")
        
        # AOE hit with Ridge Rule check
        for m in player.room.monsters:
            if m != target and perception.can_see(player, m):
                combat.handle_attack(player, m, player.room, player.game, blessing=skill, context_prefix="[Splatter] ")
                effects.apply_effect(m, "blinded", 2)
                
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    else:
        player.send_line(f"You strike with power, but there is no blood to splatter.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
             
    # Consume all Fury via URM
    fury = resources.get_resource(player, "fury")
    resources.modify_resource(player, "fury", -fury, source="Blood Explosion")
    
    _consume_resources(player, skill)
    return target, True

@register("pain_suppressor")
def handle_pain_suppressor(player, skill, args, target=None):
    """Defense: Rage-fueled damage redirection."""
    player.send_line(f"{Colors.MAGENTA}The spirit of the Juggernaut anchors your body to the material plane.{Colors.RESET}")
    effects.apply_effect(player, "pain_suppressed", 10)
    _consume_resources(player, skill)
    return None, True

@register("brute_charge")
def handle_brute_charge(player, skill, args, target=None):
    """[V7.2] Mobility: Linear charge. Linear LoS check (Ridge Rule)."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You charge blindly across the battlefield like a falling mountain!{Colors.RESET}")
    
    # Hits all in room (Standard AoE for now, but Ridge Rule applies)
    for m in player.room.monsters:
        if perception.can_see(player, m):
            effects.apply_effect(m, "prone", 1)
            effects.apply_effect(m, "staggered", 1)
            
    _consume_resources(player, skill)
    return None, True

@register("berserker_rage")
def handle_berserker_rage(player, skill, args, target=None):
    """Utility/Buff: Ultimate frenzy."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}RAGE! Your heart pounds against your ribs as your soul burns!{Colors.RESET}")
    effects.apply_effect(player, "berserk_buff", 15)
    _consume_resources(player, skill)
    return None, True
