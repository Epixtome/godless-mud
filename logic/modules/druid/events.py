"""
logic/modules/druid/events.py
Event subscriptions for the Druid class (V7.2 Sync).
"""
import logging
from logic.core import event_engine, effects
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def on_calculate_mitigation(ctx):
    """[V7.2] Barkskin Mitigation: 20% flat reduction."""
    target = ctx.get('target')
    if not target or not effects.has_effect(target, 'barkskin_active'):
        return
        
    # Reduce damage by 20%
    ctx['damage'] = int(ctx['damage'] * 0.8)
    
    if hasattr(target, 'send_line'):
        target.send_line(f"{Colors.BOLD}{Colors.GREEN}[BARKSKIN] The earthen shell absorbs some of the impact.{Colors.RESET}")

def register_events():
    event_engine.subscribe('on_calculate_mitigation', on_calculate_mitigation)
