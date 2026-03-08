import asyncio
from utilities.colors import Colors

class ActionTask:
    """
    Represents a delayed action currently being performed by an entity.
    """
    def __init__(self, task, tag, on_interrupt=None):
        self.task = task
        self.tag = tag
        self.on_interrupt = on_interrupt

def start_action(entity, duration, callback, tag="generic", fail_msg="Action interrupted.", on_interrupt=None):
    """
    Starts a delayed action for an entity.
    
    Args:
        entity: The Player or Monster performing the action.
        duration (float): Time in seconds to wait.
        callback (coroutine): The async function to call upon completion.
        tag (str): A label for the action type (e.g., "casting", "crafting").
        fail_msg (str): Message to send if interrupted.
        on_interrupt (function): Sync function called if action is cancelled.
    """
    # 1. Interrupt any existing action
    interrupt(entity)

    # 2. Determine and Set State
    target_state = None
    if hasattr(entity, 'state'):
        if tag in ["casting", "channeling", "ritual", "crafting", "harvesting", "bandaging", "picking", "disarming"]:
            target_state = "casting"
        elif tag == "resting":
            target_state = "resting"
        
        if target_state and entity.state in ["normal", "combat"]:
            entity.state = target_state

    # 3. Define the wrapper
    async def _runner():
        try:
            await asyncio.sleep(duration)
            # Action completed successfully
            entity.current_action = None 
            
            # Revert State
            if target_state and hasattr(entity, 'state') and entity.state == target_state:
                entity.state = "combat" if getattr(entity, 'fighting', None) else "normal"
                
            await callback()
            
            # [REAPER] Process any deaths triggered by this action immediately.
            from logic.engines import combat_lifecycle
            involved_players = []
            if hasattr(entity, 'game') and entity.game:
                involved_players = combat_lifecycle.process_dead_queue(entity.game)

            # [SNAPPY FEEDBACK] Force push any text (including the action results)
            # Find everyone in the entity's current room. If no death occurred, involved_players is empty.
            if hasattr(entity, 'room') and entity.room:
                for p in entity.room.players:
                    if p not in involved_players: # Don't double-prompt if Reaper already did
                        p.send_prompt()
                        if hasattr(p, 'drain'):
                            asyncio.create_task(p.drain())

        except asyncio.CancelledError:
            # Action was interrupted
            if fail_msg and hasattr(entity, 'send_line'):
                entity.send_line(f"{Colors.YELLOW}{fail_msg}{Colors.RESET}")
            
            # Revert State
            if target_state and hasattr(entity, 'state') and entity.state == target_state:
                entity.state = "combat" if getattr(entity, 'fighting', None) else "normal"
                
            if on_interrupt:
                on_interrupt()
            
            # [SNAPPY FEEDBACK] Refresh prompt on fail as well
            if hasattr(entity, 'send_prompt'): 
                entity.send_prompt()
                if hasattr(entity, 'drain'):
                    asyncio.create_task(entity.drain())

    # 4. Schedule and Store
    task = asyncio.create_task(_runner())
    entity.current_action = ActionTask(task, tag, on_interrupt)
    return task

def interrupt(entity):
    """Cancels the entity's current action, if any."""
    if hasattr(entity, 'current_action') and entity.current_action:
        # The cancellation triggers the CancelledError in _runner, 
        # which calls on_interrupt.
        entity.current_action.task.cancel()
        
        # Immediate state revert to prevent race conditions with input hooks
        if hasattr(entity, 'state') and entity.state in ["casting", "resting"]:
            entity.state = "combat" if getattr(entity, 'fighting', None) else "normal"
            
        entity.current_action = None