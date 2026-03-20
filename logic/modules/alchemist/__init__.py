"""
logic/modules/alchemist/__init__.py
"""
from . import actions, events, state

def initialize_alchemist(player):
    """Initializes the Alchemist state."""
    state.initialize_alchemist(player)
