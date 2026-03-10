"""
logic/core/services/class_service.py
Service layer for managing class-specific discovery and activation.
"""
import importlib
import logging

logger = logging.getLogger("GodlessMUD")

def get_class_module(class_name):
    """
    Dynamically imports and returns the module for the specified class name.
    """
    if not class_name:
         return None
         
    try:
        return importlib.import_module(f"logic.modules.{class_name.lower()}")
    except ImportError:
        logger.error(f"ClassService: Could not import module for class '{class_name}'")
        return None

def initialize_player_class(player, class_name):
    """
    Initializes a player for a specific class kit.
    Delegates to the class-specific module if it has an 'initialize' function.
    """
    module = get_class_module(class_name)
    if module and hasattr(module, f"initialize_{class_name.lower()}"):
        init_func = getattr(module, f"initialize_{class_name.lower()}")
        init_func(player)
        return True
    return False
