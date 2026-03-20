"""
logic/modules/beastmaster/__init__.py
"""
from . import actions, events, state

def initialize_beastmaster(player):
    """Initializes the Beastmaster state."""
    state.initialize_beastmaster(player)
