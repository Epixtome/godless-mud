"""
logic/modules/assassin/events.py
Assassin Event Listeners: Stealth and UI.
"""
from logic.core import event_engine, effects
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("on_enter_room", on_enter_room)

def on_enter_room(ctx):
    """Triggers traps when someone enters a room."""
    entity = ctx.get('entity') or ctx.get('player')
    room = ctx.get('room')
    if entity and room:
        from .utility import trigger_traps
        trigger_traps(entity, room)

def on_build_prompt(ctx):
    """Injects Stealth status into the prompt for Assassins."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'assassin':
        if "concealed" in getattr(player, 'status_effects', {}):
            prompts.append(f"{Colors.BLUE}[STEALTH]{Colors.RESET}")
