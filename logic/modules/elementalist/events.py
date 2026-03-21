"""
logic/modules/elementalist/events.py
Event subscriptions for the Elementalist class (V7.2 Sync).
"""
import logging
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def on_calculate_mitigation_reflect(ctx):
    """[V7.2] Elemental Reflection: Redirects damage back to attacker."""
    target = ctx.get('target')
    attacker = ctx.get('attacker')
    damage = ctx.get('damage', 0)
    
    if not target or not attacker: return
    
    if getattr(target, 'active_class', None) == 'elementalist':
        if effects.has_effect(target, 'elemental_reflection'):
            # Only reflect elemental tags
            tags = ctx.get('tags', set())
            elemental_tags = {"fire", "ice", "lightning", "water", "wind", "earth"}
            
            if tags & elemental_tags:
                reflect_dmg = max(1, int(damage * 0.3))
                combat.apply_damage(attacker, reflect_dmg, source=target, context="Elemental Reflection")
                if hasattr(target, 'send_line'):
                    target.send_line(f"{Colors.BOLD}{Colors.MAGENTA}[REFLECT] The elemental barrier lashes back at {attacker.name}!{Colors.RESET}")
                
                # Consume focus? (Optional)
                resources.modify_resource(target, "concentration", -5, source="Reflection Stabilizer")

def register_events():
    """Subscribes Elementalist listeners to the global event engine."""
    event_engine.subscribe('on_calculate_mitigation', on_calculate_mitigation_reflect)
