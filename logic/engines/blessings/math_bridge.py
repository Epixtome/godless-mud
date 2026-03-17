"""
logic/engines/blessings/math_bridge.py
Facade for the Godless Blessings Math Engine.
Reworked (V6.0) to shard logic across specialized evaluators.
"""
import logging
from .math.evaluators import calculate_power
from .math.weapons import calculate_weapon_power
from .math.on_hit import apply_on_hit
from .math.reactions import resolve_reaction
from .math.gear import calculate_gear_damage_mult, calculate_gear_power_bonus

logger = logging.getLogger("GodlessMUD")

def calculate_duration(blessing, player):
    """Fallback duration logic."""
    if hasattr(blessing, 'metadata') and blessing.metadata:
        return blessing.metadata.get('duration', 30)
    return 30

def resolve_blessing_effect(player, blessing):
    """Entry point for simple power resolution."""
    return calculate_power(blessing, player)

class MathBridge:
    """Legacy shim for backward compatibility."""
    @staticmethod
    def calculate_power(blessing, player, target=None):
        return calculate_power(blessing, player, target)
    @staticmethod
    def calculate_weapon_power(weapon, player, avg=False):
        return calculate_weapon_power(weapon, player, avg)
    @staticmethod
    def apply_on_hit(player, target, blessing):
        return apply_on_hit(player, target, blessing)
    @staticmethod
    def calculate_duration(blessing, player):
        return calculate_duration(blessing, player)
