import logging

logger = logging.getLogger("GodlessMUD")

# Registry: tag/id -> handler_function
SKILL_REGISTRY = {}
SKILL_HANDLERS = SKILL_REGISTRY

def register(*tags):
    """
    Decorator to register a handler function for specific skill tags or IDs.
    Usage: @register("fireball", "fire")
    """
    def decorator(func):
        for tag in tags:
            SKILL_REGISTRY[tag] = func
        return func
    return decorator

# Import common module and specific helpers
from . import common
from .common import _apply_damage

# Import handler modules to register their skills
from . import martial
from . import mystic
from . import rogue
from . import feral
from . import survival
from . import ranger
from . import bard
from . import utility
from . import ninja
from . import dragoon
from . import temporal
from . import gambler

# Initialize Hooks Package
from . import basic_hooks
from . import status_hooks

print(" [DEBUG] Handlers & Hooks Loaded.")
