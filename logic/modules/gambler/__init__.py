"""
logic/modules/gambler/__init__.py
"""
from . import actions, events, state

def initialize_gambler(player):
    """Initializes the Gambler state."""
    state.initialize_gambler(player)
