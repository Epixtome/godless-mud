"""
Facade for the Blessings Engine.
Exports components from sub-modules to maintain backward compatibility.
"""
from logic.engines.blessings.auditor import Auditor, check_pacing, on_status_removed
from logic.engines.blessings.math_bridge import (
    MathBridge, 
    calculate_power, 
    apply_on_hit, 
    calculate_duration, 
    calculate_weapon_power, 
    resolve_blessing_effect,
    resolve_reaction,
    calculate_gear_damage_mult,
    calculate_gear_power_bonus
)

# Re-export for compatibility
__all__ = [
    'Auditor',
    'MathBridge',
    'calculate_power',
    'apply_on_hit',
    'calculate_duration',
    'calculate_weapon_power',
    'resolve_blessing_effect',
    'resolve_reaction',
    'calculate_gear_damage_mult',
    'calculate_gear_power_bonus',
    'check_pacing',
    'on_status_removed',
]
