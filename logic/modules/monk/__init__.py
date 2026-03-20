"""
logic/modules/monk/__init__.py
"""
from . import actions, events, state

def initialize_monk(player):
    """Initializes the Monk state."""
    state.initialize_monk(player)
