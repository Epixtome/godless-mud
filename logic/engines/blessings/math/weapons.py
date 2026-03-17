"""
logic/engines/blessings/math/weapons.py
Calculates weapon power based on scaling tags and resonance.
"""
import math
import logging
from utilities.utils import roll_dice
from logic import calibration

logger = logging.getLogger("GodlessMUD")

def calculate_weapon_power(weapon, player, avg=False):
    """
    Calculates weapon damage with V6.0 scaling and resonance.
    Pillar: Physics should live in Data (Weapons/Stats).
    """
    # 1. Base Harvest
    stats = getattr(weapon, 'stats', {})
    damage_dice = stats.get('damage_dice') or getattr(weapon, 'damage_dice', "1d4")
    
    if avg:
        try:
            dice_count, dice_sides = map(int, damage_dice.split('d'))
            base = dice_count * (dice_sides + 1) / 2
        except (ValueError, AttributeError, TypeError): base = 1
    else:
        base = roll_dice(damage_dice) or 1
        
    # 2. Voltage Scaling (Tag Synergy)
    scaling_tag = stats.get('scaling_tag') or getattr(weapon, 'scaling_tag', 'martial')
    scaling_mult = stats.get('scaling_mult') or getattr(weapon, 'scaling_mult', 1.0)
    
    if not stats.get('scaling_tag'):
        legacy = getattr(weapon, 'scaling', {})
        if isinstance(legacy, dict) and 'tag' in legacy:
            scaling_tag = legacy.get('tag', scaling_tag)
            scaling_mult = legacy.get('mult', scaling_mult)
            
    voltage = player.get_global_tag_count(scaling_tag) if player and hasattr(player, 'get_global_tag_count') else 0
    
    # [V6.0] Non-Linear Scaling (Diminishing Returns)
    dr_mult = math.sqrt(voltage) * calibration.ScalingRules.DR_COEFFICIENT * scaling_mult
    
    # Breakthrough Milestone
    if voltage >= calibration.ScalingRules.BREAKTHROUGH_THRESHOLD:
        dr_mult += calibration.ScalingRules.BREAKTHROUGH_BONUS
        
    power_mult = 1.0 + dr_mult
    total = int(base * power_mult)
    
    # 3. Resonance Bonus (Flat Thresholds)
    resonance = getattr(weapon, 'resonance', {})
    if resonance and player and hasattr(player, 'get_global_tag_count'):
        r_tag = resonance.get('tag')
        r_thresh = resonance.get('threshold', 0)
        if r_tag and player.get_global_tag_count(r_tag) >= r_thresh:
            total += resonance.get('bonus_dmg', 0)
                
    return max(1, total)
