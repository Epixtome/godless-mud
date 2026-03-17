"""
logic/engines/blessings/math/evaluators.py
Primary power calculation hub for the Godless Blessings engine.
"""
import math
import logging
from logic.core import event_engine
from logic import calibration
from utilities.utils import roll_dice
from .potency import process_potency_modifiers
from .payoffs import calculate_grammar_bonus
from .gear import calculate_gear_power_bonus

logger = logging.getLogger("GodlessMUD")

def calculate_power(blessing, player, target=None):
    """
    Calculates the final power output based on base_power, scaling, and grammar.
    V6.0: Sharded Evaluation Logic.
    """
    base = getattr(blessing, 'base_power', 0)
    
    if base == 0:
        d_dice = getattr(blessing, 'damage_dice', None)
        if d_dice: base = roll_dice(d_dice) or 0
    
    scaling_bonus = 0
    scaling = getattr(blessing, 'scaling', [])
    if isinstance(scaling, dict): scaling = [scaling]
    
    # 1. Voltage Scaling (Tag Synergy)
    if player and scaling:
        for entry in scaling:
            tag = entry.get('scaling_tag')
            mult = entry.get('multiplier', 1.0)
            if tag:
                voltage = player.get_global_tag_count(tag) if hasattr(player, 'get_global_tag_count') else 0
                
                # Curve: Reward early points, taper off at high voltage (Square Root)
                dr_mult = math.sqrt(voltage) * calibration.ScalingRules.DR_COEFFICIENT * mult
                
                # Breakthrough Milestone
                if voltage >= calibration.ScalingRules.BREAKTHROUGH_THRESHOLD:
                    dr_mult += calibration.ScalingRules.BREAKTHROUGH_BONUS
                    
                scaling_bonus += int(base * dr_mult) 

    # 2. Grammar Bonus (Tactical Interaction Payoffs)
    if target:
        scaling_bonus += calculate_grammar_bonus(blessing, player, target, base)
    
    # 3. Gear Grammar (Material/Property Synergy)
    if player:
        scaling_bonus += calculate_gear_power_bonus(blessing, player, target, base)
    
    total = base + scaling_bonus
    
    # 3. Dynamic Potency Rules (Pip/Resource Scaling)
    dyn_mult, dyn_flat = process_potency_modifiers(blessing, player, target)
    
    # 4. Attacker-Side Passives
    if player and hasattr(player, 'equipped_blessings'):
        for b_id in player.equipped_blessings:
            if b_id == blessing.id: continue
            pass_blessing = player.game.world.blessings.get(b_id) if hasattr(player, 'game') else None
            if pass_blessing and getattr(pass_blessing, 'logic_type', None) == 'passive':
                p_mult, p_flat = process_potency_modifiers(pass_blessing, player, target)
                dyn_mult *= p_mult
                dyn_flat += p_flat

    # 5. Target-Side Passives (Mitigation/Defense)
    if target and hasattr(target, 'equipped_blessings'):
        for b_id in target.equipped_blessings:
            pass_blessing = target.game.world.blessings.get(b_id) if hasattr(target, 'game') else None
            if pass_blessing and getattr(pass_blessing, 'logic_type', None) == 'passive':
                # Target passives use process_potency_modifiers with r_type 'mitigation_mod'
                t_mult, _ = process_potency_modifiers(pass_blessing, target, player)
                dyn_mult *= t_mult 

    final_total = (total * dyn_mult) + dyn_flat

    # 6. Legacy Dispatch Modifier Event
    ctx = {'attacker': player, 'blessing': blessing, 'target': target, 'multiplier': 1.0, 'bonus_flat': 0, 'power': final_total}
    event_engine.dispatch("calculate_damage_modifier", ctx)
    
    final_total = int(ctx['power'] * ctx['multiplier']) + ctx['bonus_flat']
    return max(1, final_total)
