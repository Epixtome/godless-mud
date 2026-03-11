"""
logic/modules/barbarian/__init__.py
Barbarian class initialization.
"""
from .actions import *
from .events import register_events

def initialize(player):
    from .state import initialize_barbarian
    initialize_barbarian(player)
