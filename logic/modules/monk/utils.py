"""
logic/modules/monk/utils.py
Helper functions and constants for the Monk Kinetic Engine.
"""
import logic.common as common
from logic.engines import magic_engine

CHI_MAX = 5

def consume_chi(player, amount):
    """Consumes chi from the player's ext_state."""
    monk_data = player.ext_state.setdefault('monk', {})
    current = monk_data.get('chi', 0)
    if current >= amount:
        monk_data['chi'] = current - amount
        return True
    return False

def get_target(player, args, target=None):
    """Standardized target resolution."""
    return common._get_target(player, args, target)

def consume_resources(player, skill):
    """Unified resource and pacing consumption."""
    magic_engine.consume_resources(player, skill)
    magic_engine.set_cooldown(player, skill)
    magic_engine.consume_pacing(player, skill)
