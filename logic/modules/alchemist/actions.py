"""
logic/modules/alchemist/actions.py
Alchemist Skill Handlers: Master of Chemical Reactions and Transmutation.
Pillar: Elemental Synergy, Utility Philters, and Area Denial.
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

@register("volatile_flask")
def handle_volatile_flask(player, skill, args, target=None):
    """Setup/Builder: Fire damage and Alchemy pips."""
    target = common._get_target(player, args, target, "Toss flask at whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.RED}You shatter a volatile flask against {target.name}!{Colors.RESET}")
    combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    resources.modify_resource(player, "alchemical_pips", 1, source="Volatile Flask")
    
    _consume_resources(player, skill)
    return target, True

@register("acid_mist")
def handle_acid_mist(player, skill, args, target=None):
    """Setup: [Staggered] and Resistance reduction."""
    target = common._get_target(player, args, target, "Dissolve whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.GREEN}A thick cloud of acrid mist melts through {target.name}'s defenses.{Colors.RESET}")
    effects.apply_effect(target, "staggered", 2)
    # Custom effect: Acid Melt
    effects.apply_effect(target, "acid_melt", 6)
    _consume_resources(player, skill)
    return target, True

@register("catalytic_bloom")
def handle_catalytic_bloom(player, skill, args, target=None):
    """Setup: [Marked] for elemental payoff."""
    target = common._get_target(player, args, target, "Catalyze whose spirit?")
    if not target: return None, True
    
    player.send_line(f"{Colors.YELLOW}You mark {target.name} with a highly reactive alchemical catalyst.{Colors.RESET}")
    effects.apply_effect(target, "marked", 8)
    _consume_resources(player, skill)
    return target, True

@register("final_flash")
def handle_final_flash(player, skill, args, target=None):
    """Payoff/Finisher: massive elemental detonation vs status."""
    target = common._get_target(player, args, target, "Ignite the final reagent on whom?")
    if not target: return None, True
    
    has_status = any(effects.has_effect(target, s) for s in ["wet", "burning", "frozen", "poisoned"])
    if has_status:
        player.send_line(f"{Colors.BOLD}{Colors.WHITE}FINAL FLASH! The chemical reaction is catastrophic!{Colors.RESET}")
        player.alch_multiplier = 4.0
        try:
            combat.handle_attack(player, target, player.room, player.game, blessing=skill)
        finally:
             if hasattr(player, 'alch_multiplier'): del player.alch_multiplier
             # Clear statuses
             for s in ["wet", "burning", "frozen", "poisoned"]:
                 effects.remove_effect(target, s)
    else:
        player.send_line(f"Your reagents fizzle harmlessly against {target.name}'s neutral state.")
        combat.handle_attack(player, target, player.room, player.game, blessing=skill)
    
    _consume_resources(player, skill)
    return target, True

@register("transmute_flesh")
def handle_transmute_flesh(player, skill, args, target=None):
    """Payoff/Burst: Poison and Off-Balance."""
    target = common._get_target(player, args, target, "Transmute whom?")
    if not target: return None, True
    
    player.send_line(f"{Colors.MAGENTA}You force a molecular shift within {target.name}, melting their resolve.{Colors.RESET}")
    effects.apply_effect(target, "poisoned", 6)
    effects.apply_effect(target, "off_balance", 4)
    _consume_resources(player, skill)
    return target, True

@register("elixir_of_stone")
def handle_elixir_of_stone(player, skill, args, target=None):
    """Defense: Self-protection."""
    player.send_line(f"{Colors.CYAN}You quaff an elixir of stone, hardening your skin to granite.{Colors.RESET}")
    effects.apply_effect(player, "braced", 10)
    # Add physical resist logic
    _consume_resources(player, skill)
    return None, True

@register("smokebomb_jump")
def handle_smokebomb_jump(player, skill, args, target=None):
    """Mobility: Blink and Blind."""
    player.send_line(f"{Colors.BOLD}{Colors.BLACK}POOF! You vanish in a cloud of dense ash.{Colors.RESET}")
    for m in player.room.monsters:
        effects.apply_effect(m, "blinded", 4)
    _consume_resources(player, skill)
    return None, True

@register("create_philter")
def handle_create_philter(player, skill, args, target=None):
    """Utility: Heal and Stamina restoration."""
    pips = player.ext_state.get('alchemist', {}).get('alchemical_pips', 0)
    if pips < 5:
         player.send_line(f"You need 5 Alchemy Pips to brew a perfect philter.")
         return None, True
         
    player.send_line(f"{Colors.GREEN}You mix your active pips into a glowing philter of renewal.{Colors.RESET}")
    # Heal ally or self
    target = player
    heal_amt = int(target.max_hp * 0.15)
    target.modify_hp(heal_amt)
    resources.modify_resource(target, "stamina", 20)
    
    player.ext_state['alchemist']['alchemical_pips'] = 0
    _consume_resources(player, skill)
    return None, True
