"""
logic/modules/cleric/__init__.py
Cleric class initialization.
"""
from .actions import *
from .events import register_events

def initialize(player):
    from .state import initialize_cleric
    initialize_cleric(player)
