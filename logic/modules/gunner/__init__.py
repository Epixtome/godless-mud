"""
logic/modules/gunner/__init__.py
"""
from . import actions, events, state

def initialize_gunner(player):
    """Initializes the Gunner state."""
    state.initialize_gunner(player)
