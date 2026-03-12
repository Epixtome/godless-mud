"""
logic/modules/monk/monk.py
The Monk Domain: Entry point for the Monk class logic.
"""
from . import actions, events, stances, state

# Initialize Class Events

def initialize_monk(player):
    """Initializes Monk-specific state on the player."""
    state.initialize_monk(player)
