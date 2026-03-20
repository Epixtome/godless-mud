"""
logic/modules/dragoon/__init__.py
"""
from . import actions, events, state

def initialize_dragoon(player):
    """Initializes the Dragoon state."""
    state.initialize_dragoon(player)
