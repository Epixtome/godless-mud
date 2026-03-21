"""
logic/modules/knight/events.py
Knight Event Listeners: Prompt and Resource UI.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, effects
from utilities.colors import Colors

def register_events():
    event_engine.subscribe("on_build_prompt", on_build_prompt)
    event_engine.subscribe("calculate_damage_modifier", on_calculate_damage_modifier)

def on_calculate_damage_modifier(ctx):
    """
    [V7.2] Logic-Data Wall: Execute math moved to JSON potency_rules.
    This listener now only handles unique side-channel modifiers.
    """
    pass

def on_build_prompt(ctx):
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'knight':
        kd = player.ext_state.get('knight', {})
        
        # [V7.2] Status-based prompts
        if effects.has_effect(player, "guarding"):
            prompts.append(f"{Colors.GREEN}[GUARD]{Colors.RESET}")
            
        if player.is_mounted:
            prompts.append(f"{Colors.YELLOW}[MTD]{Colors.RESET}")
        
        if effects.has_effect(player, "braced"):
            prompts.append(f"{Colors.WHITE}[BRCD]{Colors.RESET}")
