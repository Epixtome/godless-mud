"""
logic/modules/paladin/__init__.py
"""
from . import actions, events, state

def initialize_paladin(player):
    """Initializes the Paladin state."""
    state.initialize_paladin(player)
