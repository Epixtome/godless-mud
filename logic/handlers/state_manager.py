import logging 
from logic.engines import interaction_engine


logger = logging.getLogger("GodlessMUD")

# Registry of state handlers
# Format: { "state_name": handler_function }
STATE_HANDLERS = {}

def register(state_name):
    """Decorator to register a function as a handler for a specific player state.""" 
    def decorator(func):
        STATE_HANDLERS[state_name] = func
        return func
    return decorator

def dispatch(player, command_line):
    """
    Dispatches input to the appropriate handler based on player.state.
    Returns True if the input was handled (consumed), False otherwise.
    """ 
    state = getattr(player, "state", "normal")
    
    if state == "normal":
        return False
        
    if state == "interaction":
        # Defer to the specialized interaction engine 
        return interaction_engine.dispatch(player, command_line)
        
    handler = STATE_HANDLERS.get(state)
    if handler:
        try:
            # State handlers receive (player, command_line)
            # They should return True to stop processing, or False to fall through (rare)
            return handler(player, command_line)
        except Exception as e:
            logger.error(f"Error in state handler '{state}': {e}", exc_info=True)
            player.send_line("An error occurred. Returning to normal state.")
            player.state = "normal"
            return True
    else:
        # Unknown state, reset to normal
        logger.warning(f"Player {player.name} is in unknown state '{state}'. Resetting.")
        player.state = "normal"
        return False
