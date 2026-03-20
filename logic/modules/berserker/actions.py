"""
logic/modules/berserker/actions.py
Berserker Skill Handlers: Master of Pain and Primal Fury.
Pillar: Endurance Axis, High Risk/High Reward finishers.
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

@register("raging_strike")
def handle_raging_strike(player, skill, args, target=None):
    """Setup/Builder: High-impact physical damage and Fury generation."""
    target = common._get_target(player, args, target, "Maul whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You strike with primal fury, building your bloodlust!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "fury", 10, source="Raging Strike")
    _consume_resources(player, skill)
    return target, True

@register("headbutt")
def handle_headbutt(player, skill, args, target=None):
    """Setup: [Staggered] / [Off-Balance] disruptor."""
    target = common._get_target(player, args, target, "Bash heads with whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}CRACK! You slam your forehead into {target.name}'s skull.{Colors.RESET}")
    effects.apply_effect(player, "staggered", 1)
    effects.apply_effect(target, "staggered", 2)
    effects.apply_effect(target, "off_balance", 4)
    resources.modify_resource(player, "fury", 15, source="Headbutt")
    _consume_resources(player, skill)
    return target, True

@register("blood_thirst")
def handle_blood_thirst(player, skill, args, target=None):
    """Setup: [Bleeding] for life-steal setup."""
    target = common._get_target(player, args, target, "Feed whose life to the rage?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}Your blade finds a vital artery, and your hunger grows!{Colors.RESET}")
    effects.apply_effect(target, "bleeding", 6)
    # Buff self with a temporary life-leaver
    effects.apply_effect(player, "thirsting", 6)
    _consume_resources(player, skill)
    return target, True

@register("reckless_abandon")
def handle_reckless_abandon(player, skill, args, target=None):
    """Payoff/Burst: High damage vs your own low HP."""
    target = common._get_target(player, args, target, "Abandon caution against whom?")
    if not target: return None, True
    
    hp_pct = player.hp / player.max_hp
    if hp_pct < 0.5:
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}[RECKLESS] You scream with manic glee as you throw yourself at {target.name}!{Colors.RESET}")
        player.reckless_multiplier = 2.0
        if hp_pct < 0.25:
             player.reckless_multiplier = 3.0
             player.send_line(f"{Colors.WHITE}The world turns red as you descend into madness!{Colors.RESET}")
             
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'reckless_multiplier'): del player.reckless_multiplier
    else:
        player.send_line(f"You strike with power, but lack the desperation of true abandon.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("gorespatter")
def handle_gorespatter(player, skill, args, target=None):
    """Payoff/AOE: Gory explosion vs bleeding target."""
    target = common._get_target(player, args, target, "Execute the final stroke on whom?")
    if not target: return None, True
    
    if effects.has_effect(target, "bleeding"):
        player.send_line(f"{Colors.BOLD}{Colors.RED}GORESPATTER! {target.name}'s blood erupts, blinding others in the room!{Colors.RESET}")
        player.gore_multiplier = 4.0
        for m in player.room.monsters:
            if m != target:
                combat.handle_attack(player, m, player.room, player.game, blessing=skill)
                effects.apply_effect(m, "blinded", 2)
        try:
             combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'gore_multiplier'): del player.gore_multiplier
             
    resources.modify_resource(player, "fury", -99) # Consumes all Fury
    _consume_resources(player, skill)
    return target, True

@register("pain_suppressor")
def handle_pain_suppressor(player, skill, args, target=None):
    """Defense: Self-preservation through rage."""
    player.send_line(f"{Colors.MAGENTA}The spirit of the Juggernaut anchors your body to the material plane.{Colors.RESET}")
    effects.apply_effect(player, "pain_suppressed", 10) # Logic in damage_engine for redirection
    _consume_resources(player, skill)
    return None, True

@register("brute_charge")
def handle_brute_charge(player, skill, args, target=None):
    """Mobility: linear charge and prone."""
    player.send_line(f"{Colors.BOLD}{Colors.WHITE}You charge blindly across the battlefield like a falling mountain!{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "prone", 1)
        effects.apply_effect(m, "staggered", 1)
    _consume_resources(player, skill)
    return None, True

@register("berserker_rage")
def handle_berserker_rage(player, skill, args, target=None):
    """Utility/Buff: Ultimate frenzy mode."""
    player.send_line(f"{Colors.BOLD}{Colors.RED}RAGE! Your heart pounds against your ribs as your soul burns!{Colors.RESET}")
    effects.apply_effect(player, "berserk_buff", 15)
    _consume_resources(player, skill)
    return None, True
