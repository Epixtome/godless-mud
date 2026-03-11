"""
logic/modules/archer/events.py
Archer Event Listeners: Prompt and Scaling.
"""
from logic.core import event_engine
from utilities.colors import Colors

def register_events():
    event_engine.subscribe('on_build_prompt', on_build_prompt)

def on_build_prompt(ctx):
    player = ctx.get('player')
    prompts = ctx.get('prompts')

    if getattr(player, 'active_class', None) == 'archer':
        state = player.ext_state.get('archer', {})
        res = state.get('resource', 0)
        prompts.append(f"{Colors.CYAN}ARCHER: {res}{Colors.RESET}")
