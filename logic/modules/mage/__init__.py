"""
logic/modules/mage/__init__.py
Mage class initialization.
"""
from .actions import *
from .events import register_events

def initialize(player):
    from .state import initialize_mage
    initialize_mage(player)
