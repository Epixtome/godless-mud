"""
logic/modules/rogue/events.py
Rogue Event Listeners: Prompt and Scaling.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe('on_build_prompt', on_build_prompt)

def on_build_prompt(ctx):
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'rogue':
        # [V7.2] Rogue uses standard stamina prompt
        pass
