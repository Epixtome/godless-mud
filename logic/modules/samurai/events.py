"""
logic/modules/samurai/events.py
Event subscriptions for the Samurai class (V7.2 Sync).
"""
import logging
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def on_take_damage_counter(ctx):
    """[V7.2] Hissatsu Counter: Retaliates when hit while in counter_stance."""
    target = ctx.get('target')
    attacker = ctx.get('attacker')
    
    if not target or not attacker: return
    
    if getattr(target, 'active_class', None) == 'samurai':
        if effects.has_effect(target, 'counter_stance'):
            player = target
            player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}[CHIDORI] Hissatsu Strike! You counter {attacker.name} with blinding precision!{Colors.RESET}")
            
            # Use physiology bonus if active
            counter_mod = 1.0
            if blessings := getattr(player, 'blessings', []):
                 if any(b.id == 'samurai_physiology' for b in blessings):
                      counter_mod = 1.5
            
            # Execute counter hit (base damage + mod)
            counter_dmg = int(combat.calculate_base_damage(player, attacker) * counter_mod)
            combat.apply_damage(attacker, counter_dmg, source=player, context="Hissatsu Counter")
            
            # Consume 1 spirit per counter? (Optional design choice)
            resources.modify_resource(player, "spirit", -1, source="Counter Consumption")
            
            # Extend focused if active? No, just the strike.
            if resources.get_resource(player, "spirit") <= 0:
                 effects.remove_effect(player, 'counter_stance')

def register_events():
    event_engine.subscribe('on_calculate_mitigation', on_take_damage_counter)
