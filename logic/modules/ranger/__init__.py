"""
logic/modules/ranger/__init__.py
"""
from . import actions, events, state

def initialize_ranger(player):
    """Initializes the Ranger state."""
    state.initialize_ranger(player)
