"""
logic/modules/warlock/__init__.py
"""
from . import actions, events, state

def initialize_warlock(player):
    """Initializes the Warlock state."""
    state.initialize_warlock(player)
