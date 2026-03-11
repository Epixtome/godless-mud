"""
logic/modules/cleric/events.py
Cleric Event Listeners: Prompt and Divine Auras.
"""
from logic.core import event_engine
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_build_prompt", on_build_prompt)

def on_build_prompt(ctx):
    """Cleric-specific prompt logic (e.g. Aura display)."""
    player = ctx.get('player')
    prompts = ctx.get('prompts')
    
    if getattr(player, 'active_class', None) == 'cleric':
        aura = player.ext_state.get('cleric', {}).get('aura')
        if aura:
            prompts.append(f"{Colors.YELLOW}[{aura.upper()}]{Colors.RESET}")
