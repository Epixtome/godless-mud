"""
logic/modules/warrior/utils.py
Common helpers for the Warrior class.
"""
import logic.common as common

def get_target(player, args, target=None):
    """Standardized target resolution."""
    return common._get_target(player, args, target)
