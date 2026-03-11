"""
logic/modules/assassin/__init__.py
Assassin class initialization.
"""
from .actions import *
from .events import register_events

def initialize(player):
    from .state import initialize_assassin
    initialize_assassin(player)
