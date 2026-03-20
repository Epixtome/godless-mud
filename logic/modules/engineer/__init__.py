"""
logic/modules/engineer/__init__.py
"""
from . import actions, events, state

def initialize_engineer(player):
    """Initializes the Engineer state."""
    state.initialize_engineer(player)
