"""
logic/modules/berserker/__init__.py
"""
from . import actions, events, state

def initialize_berserker(player):
    """Initializes the Berserker state."""
    state.initialize_berserker(player)
