"""
logic/modules/monk/utils.py
Helper functions and constants for the Monk class.
"""
import logic.common as common
from logic.engines import magic_engine

FLOW_MAX = 10

def consume_flow(player, amount):
    """Consumes flow from the player's ext_state."""
    monk_data = player.ext_state.setdefault('monk', {})
    current = monk_data.get('flow_pips', 0)
    if current >= amount:
        monk_data['flow_pips'] = current - amount
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
