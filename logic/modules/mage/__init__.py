"""
logic/modules/mage/__init__.py
"""
from . import actions, events, state

def initialize_mage(player):
    """Initializes the Mage state."""
    state.initialize_mage(player)
