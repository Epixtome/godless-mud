"""
logic/modules/illusionist/__init__.py
"""
from . import actions, events, state

def initialize_illusionist(player):
    """Initializes the Illusionist state."""
    state.initialize_illusionist(player)
