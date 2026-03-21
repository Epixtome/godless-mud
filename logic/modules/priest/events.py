"""
logic/modules/priest/events.py
Priest Event Listeners: Prompt and Resource UI.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe('on_build_prompt', on_build_prompt)

def on_build_prompt(ctx):
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'priest':
        # [V7.2] URM integration for mana prompt
        mana = resources.get_resource(player, 'mana')
        max_mana = player.get_max_resource('mana')
        prompts.append(f"{Colors.LIGHT_CYAN}[MANA:{mana}/{max_mana}]{Colors.RESET}")
