from logic.core import status_effects_engine
from logic.core import event_engine

STANCE_CD_MODIFIERS = {"crane_stance": 0.7, "turtle_stance": 1.2}

def on_calculate_cooldown(ctx):
    """Event Handler: Modifies cooldowns based on Stances."""
    player = ctx.get('player')
    skill = ctx.get('skill')
    if not player or not skill: return
    
    # Generic Stance Interaction
    # Skills can opt-in via metadata: "stance_sensitive": true
    if getattr(skill, 'metadata', {}).get('stance_sensitive', False):
        for stance, mod in STANCE_CD_MODIFIERS.items():
            if status_effects_engine.has_effect(player, stance):
                ctx['cooldown'] *= mod

event_engine.subscribe("magic_calculate_cooldown", on_calculate_cooldown)