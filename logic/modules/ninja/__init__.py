"""
logic/modules/ninja/__init__.py
"""
from . import actions, events, state

def initialize_ninja(player):
    """Initializes the Ninja state."""
    state.initialize_ninja(player)
