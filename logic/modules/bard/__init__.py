"""
logic/modules/bard/__init__.py
"""
from . import actions, events, state

def initialize_bard(player):
    """Initializes the Bard state."""
    state.initialize_bard(player)
