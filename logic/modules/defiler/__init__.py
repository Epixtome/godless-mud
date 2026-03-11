"""
logic/modules/defiler/__init__.py
Defiler class initialization.
"""
from .actions import *
from .events import register_events

def initialize(player):
    from .state import initialize_defiler
    initialize_defiler(player)
