"""
logic/modules/archer/__init__.py
"""
from . import actions, events, state

def initialize_archer(player):
    """Initializes the Archer state."""
    state.initialize_archer(player)
