"""
logic/core/math/grammar.py
The 'Verb Calculus' of Godless.
Handles deterministic state transitions and grammar-based combat combos.
"""
import logging
from logic.constants import Tags
from logic.core import effects, resources

logger = logging.getLogger("GodlessMUD")

def resolve_state_transitions(attacker, target, attack_tags):
    """
    Evaluates how the attack's tags interact with the target's current states.
    This is the 'Grammar' that generates new states from existing ones.
    [V6.2] Integrated Gear Grammar Bridge (G_ tags).
    """
    if not target or not attacker: return
    
    active_effects = getattr(target, 'status_effects', {})
    
    # [BRIDGE] Aggregate Grammar Modifiers from Attacker Gear
    grammar_mods = getattr(attacker, 'current_tags', {})
    
    # 1. Structural Transitions
    # [OFF-BALANCE] + [WEIGHT] -> [PRONE]
    if Tags.WEIGHT in attack_tags and "off_balance" in active_effects:
        # Gear Modifier: Extend Prone Duration
        duration = 3 + grammar_mods.get("G_DUR_PRONE", 0)
        effects.apply_effect(target, "prone", duration, log_event=True)
        
        if hasattr(target, 'send_line'):
            target.send_line("Your lack of balance proves fatal as the weight of the blow sends you to the ground!")
        if hasattr(attacker, 'send_line'):
            attacker.send_line(f"You exploit {target.name}'s lack of balance and knock them prone!")

    # 2. Resource Disruption
    # [CONCUSSIVE] -> Heat Spike
    if Tags.CONCUSSIVE in attack_tags:
        heat_mod = 15 + grammar_mods.get("G_HEAT_ADD", 0)
        resources.modify_resource(target, Tags.HEAT, heat_mod, source=attacker.name)
        
    # [DISRUPTION] -> Concentration Drain
    if Tags.DISRUPTION in attack_tags:
        drain_mod = 15 + grammar_mods.get("G_DRAIN_ADD", 0)
        target.resources[Tags.CONCENTRATION] = max(0, target.resources.get(Tags.CONCENTRATION, 0) - drain_mod)

    # 3. Future Grammar Hooks
    # [G_OFFBALANCE_DUR] support (for Gale Force etc)
    if "off_balance" in active_effects and grammar_mods.get("G_DUR_OFFBALANCE", 0) > 0:
         # Extend existing off_balance duration (Note: apply_effect usually refreshes/caps)
         effects.apply_effect(target, "off_balance", 4) 
