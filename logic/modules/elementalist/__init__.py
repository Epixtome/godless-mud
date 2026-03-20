"""
logic/modules/elementalist/__init__.py
"""
from . import actions, events, state

def initialize_elementalist(player):
    """Initializes the Elementalist state."""
    state.initialize_elementalist(player)
