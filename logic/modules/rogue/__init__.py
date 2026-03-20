"""
logic/modules/rogue/__init__.py
"""
from . import actions, events, state

def initialize_rogue(player):
    """Initializes the Rogue state."""
    state.initialize_rogue(player)
