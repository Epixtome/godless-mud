"""
logic/modules/thief/__init__.py
"""
from . import actions, events, state

def initialize_thief(player):
    """Initializes the Thief state."""
    state.initialize_thief(player)
