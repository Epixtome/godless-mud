"""
logic/modules/necromancer/__init__.py
"""
from . import actions, events, state

def initialize_necromancer(player):
    """Initializes the Necromancer state."""
    state.initialize_necromancer(player)
