"""
logic/modules/samurai/__init__.py
"""
from . import actions, events, state

def initialize_samurai(player):
    """Initializes the Samurai state."""
    state.initialize_samurai(player)
