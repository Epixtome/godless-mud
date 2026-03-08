"""
logic/actions/registry.py
The Router: Dispatches skills to specific handlers or the generic executor.
"""
from . import base_executor

# Registry of special handlers
SKILL_HANDLERS = {}

def register(*tags):
    """
    Decorator to register a function as a handler for specific skill tags/IDs.
    """
    def decorator(func):
        for tag in tags:
            SKILL_HANDLERS[tag] = func
        return func
    return decorator

def get_handler(skill):
    """
    Retrieves the handler for a skill.
    Returns the specific handler if registered, otherwise returns the Base Executor.
    """
    # Check for specific handler override in skill data, or use ID
    handler_key = getattr(skill, 'handler', skill.id)
    
    # Return specific handler or fallback to generic engine
    return SKILL_HANDLERS.get(handler_key, base_executor.execute)
