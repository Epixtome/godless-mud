"""
logic/modules/engineer/events.py
Event subscriptions for the Engineer class (V7.2 Sync).
"""
import logging
from logic.core import event_engine, effects, resources, combat
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

def _is_engineer(player):
    return getattr(player, 'active_class', None) == 'engineer'

def on_death_cleanup_constructs(ctx):
    """[V7.2] Construct Termination: Cleans up ext_state when a construct dies."""
    victim = ctx.get('victim')
    if not victim: return
    
    # Check if victim is a construct of an engineer
    owner_id = getattr(victim, 'owner_id', None)
    if not owner_id: return
    
    # Locate the engineer in the game
    game = getattr(victim, 'game', None)
    if not game: return
    
    player = game.get_player_by_id(owner_id)
    if player and _is_engineer(player):
        construct_ids = player.ext_state.get('engineer', {}).get('active_constructs', [])
        if victim.id in construct_ids:
            player.send_line(f"{Colors.RED}Your construct [{victim.name}] has been destroyed!{Colors.RESET}")
            player.ext_state['engineer']['active_constructs'].remove(victim.id)

def register_events():
    """Subscribes Engineer listeners to the global event engine."""
    event_engine.subscribe('on_death', on_death_cleanup_constructs)
    # prompt is handled by systems.py / generic resource logic
