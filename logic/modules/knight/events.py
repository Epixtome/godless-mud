"""
logic/modules/knight/events.py
Knight Event Listeners: Prompt and Resource UI.
"""
from logic.core import event_engine, effects
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_build_prompt", on_build_prompt)

def on_build_prompt(ctx):
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'knight':
        # Add Guarded status to prompt if active
        kd = player.ext_state.get('knight', {})
        if kd.get('is_guarded') and kd.get('guarded_target'):
            prompts.append(f"{Colors.GREEN}[GARD:{kd['guarded_target'].name}]{Colors.RESET}")
        
        if player.is_mounted:
            prompts.append(f"{Colors.YELLOW}[MTD]{Colors.RESET}")
        
        if effects.has_effect(player, "braced"):
            prompts.append(f"{Colors.WHITE}[BRCD]{Colors.RESET}")
