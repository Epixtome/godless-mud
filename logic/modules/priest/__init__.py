"""
logic/modules/priest/__init__.py
"""
from . import actions, events, state

def initialize_priest(player):
    """Initializes the Priest state."""
    state.initialize_priest(player)
