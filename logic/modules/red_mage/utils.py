"""
logic/modules/red_mage/utils.py
Common helpers for the Red Mage class.
"""
import logic.common as common

def get_target(player, args, target=None):
    """Standardized target resolution."""
    return common._get_target(player, args, target)
