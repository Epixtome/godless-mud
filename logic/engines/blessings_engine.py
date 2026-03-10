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
    process_red_mage_mechanics
)
from logic.engines.blessings.stance_hooks import on_calculate_cooldown

# Re-export for compatibility
__all__ = [
    'Auditor',
    'MathBridge',
    'calculate_power',
    'apply_on_hit',
    'calculate_duration',
    'calculate_weapon_power',
    'resolve_blessing_effect',
    'check_pacing',
    'process_red_mage_mechanics',
    'on_status_removed',
    'on_calculate_cooldown'
]
