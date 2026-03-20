"""
logic/modules/druid/__init__.py
"""
from . import actions, events, state

def initialize_druid(player):
    """Initializes the Druid state."""
    state.initialize_druid(player)
