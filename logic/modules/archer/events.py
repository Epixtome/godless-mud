"""
logic/modules/archer/events.py
Archer Event Listeners: Prompt and Resource UI.
V7.2 Standard Refactor (Baking Branch).
"""
from logic.core import event_engine, resources
from utilities.colors import Colors

def register_events():
    event_engine.subscribe('on_build_prompt', on_build_prompt)
    event_engine.subscribe('on_combat_hit', on_combat_hit)

def on_build_prompt(ctx):
    player, prompts = ctx.get('player'), ctx.get('prompts')
    if getattr(player, 'active_class', None) == 'archer':
        # [V7.2] URM integration for prompt display
        focus = resources.get_resource(player, 'focus')
        prompts.append(f"{Colors.CYAN}[FOC:{focus}]{Colors.RESET}")

def on_combat_hit(ctx):
    """
    [V7.2] URM Generation: Successful hits generate focus.
    """
    attacker = ctx.get('attacker')
    if getattr(attacker, 'active_class', None) == 'archer':
        resources.modify_resource(attacker, "focus", 2, source="Combat Momentum")
