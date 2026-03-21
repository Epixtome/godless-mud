"""
logic/modules/ninja/events.py
Event subscriptions for the Ninja class (V7.2 Sync).
"""
import logging
import random
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def on_take_damage_substitution(ctx):
    """[V7.2] Kawarimi (Substitution): Negates the first incoming strike."""
    target = ctx.get('target')
    attacker = ctx.get('attacker')
    
    if not target or not attacker: return
    
    if getattr(target, 'active_class', None) == 'ninja':
        if effects.has_effect(target, 'substitution_guarded'):
            # Negate damage
            ctx['damage'] = 0
            effects.remove_effect(target, 'substitution_guarded')
            
            if hasattr(target, 'send_line'):
                target.send_line(f"{Colors.BOLD}{Colors.CYAN}[KAWARIMI] You substitute with a wooden log, negating the strike!{Colors.RESET}")
            if hasattr(attacker, 'send_line'):
                attacker.send_line(f"{Colors.YELLOW}{target.name} vanishes in a puff of smoke, leaving only a log!{Colors.RESET}")

def register_events():
    event_engine.subscribe('on_calculate_mitigation', on_take_damage_substitution)
