from utilities.colors import Colors
from logic.core import status_effects_engine
from utilities import telemetry

def check_pacing(player, weight=1.0, limit=5.0, pool='combat'):
    """
    Tracks actions per tick to prevent spam/macroing.
    Returns (bool, reason).
    """
    game = getattr(player, 'game', None)
    if not game: return True, "OK"
    
    # Immunity Check (Knight's Turtle Stance)
    if status_effects_engine.has_effect(player, "turtle_stance"):
        return True, "OK"
    
    current_tick = game.tick_count
    
    # Determine State Attribute based on Pool
    state_attr = 'pacing_state' if pool == 'combat' else f'pacing_state_{pool}'

    # Init Pacing State
    if not hasattr(player, state_attr):
        setattr(player, state_attr, {'tick': current_tick, 'cost': 0.0})
    
    state = getattr(player, state_attr)
        
    # Reset on new tick
    if state['tick'] != current_tick:
        state['tick'] = current_tick
        state['cost'] = 0.0
        
    # Check Limit
    if state['cost'] + weight > limit:
        telemetry.log_event(player, "STALL_WARNING", {"actions_in_tick": state['cost']})
        status_effects_engine.apply_effect(player, "stalled", 0.25, log_event=False)
        return False, f"{Colors.YELLOW}You are acting too fast! (Stalled){Colors.RESET}"
        
    # Increment
    state['cost'] += weight
    return True, "OK"

def on_status_removed(ctx):
    """
    Event Handler: Checks for queued commands when a status is removed.
    Specifically for 'stalled'.
    """
    player = ctx.get('player')
    status_id = ctx.get('status_id')

    # If the removed status was 'stalled' and we have a command queued
    if status_id == 'stalled' and hasattr(player, 'command_queue') and player.command_queue:
        # Double-check the player is no longer stalled (in case of multiple stacks/sources)
        if "stalled" not in getattr(player, 'status_effects', {}):
            command_to_run = player.command_queue.pop(0)
            
            # Assumes the game object has a method to re-process input
            if hasattr(player, 'game') and hasattr(player.game, 'process_command'):
                player.send_line(f"{Colors.GREEN}Executing queued action: {command_to_run}{Colors.RESET}")
                # This re-injects the command into the top-level command handler
                player.game.process_command(player, command_to_run)