"""
logic/modules/paladin/events.py
Event subscriptions for the Paladin class (V7.2 Sync).
"""
import logging
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def on_retribution_strike(ctx):
    """[V7.2] Retribution Aura: Reflects 10% damage back to attackers while shielded."""
    target = ctx.get('target')
    attacker = ctx.get('attacker')
    damage = ctx.get('damage', 0)
    
    if not target or not attacker: return
    
    if getattr(target, 'active_class', None) == 'paladin':
        if effects.has_effect(target, 'shielded'):
            reflect_dmg = max(1, int(damage * 0.1))
            combat.apply_damage(attacker, reflect_dmg, source=target, context="Retribution Aura")
            if hasattr(target, 'send_line'):
                target.send_line(f"{Colors.YELLOW}Your divine shield lashes out, reflecting {reflect_dmg} damage!{Colors.RESET}")

def register_events():
    event_engine.subscribe('on_combat_hit', on_retribution_strike)
