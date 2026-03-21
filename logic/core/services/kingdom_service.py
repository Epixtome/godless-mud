"""
logic/core/services/kingdom_service.py
Manages kingdom-wide state, alerts, and shared resource pools (War Chest).
"""
import logging
from utilities.colors import Colors
from logic.core import event_engine, messaging

logger = logging.getLogger("GodlessMUD")

def register_events():
    """Subscribes to kingdom-related events."""
    event_engine.subscribe("kingdom_alert", handle_kingdom_alert)
    event_engine.subscribe("shrine_captured", handle_shrine_captured)
    logger.info("KingdomService events registered.")

def handle_kingdom_alert(context):
    """Broadcasts a warfare alert to all members of a specific kingdom."""
    kingdom = context.get('kingdom')
    message = context.get('message')
    game = context.get('game')
    
    if not kingdom or not message:
        return
        
    # [V7.2 Standard] Filter online players by kingdom
    # If game isn't in context, we'll have to find it or omit (unlikely in this architecture)
    if not game:
        from godless_mud import global_game
        game = global_game
        
    if game:
        for player in game.players.values():
            if player.kingdom == kingdom:
                player.send_line(f"\n{Colors.BOLD}{Colors.YELLOW}>>> KINGDOM ALERT <<<{Colors.RESET}")
                player.send_line(message)
                player.send_line(f"{Colors.YELLOW}>>> ----------------- <<<{Colors.RESET}\n")

def handle_shrine_captured(context):
    """Universal notification for territory changes."""
    shrine = context.get('shrine')
    old_kingdom = context.get('old_kingdom')
    new_kingdom = context.get('new_kingdom')
    
    # This is already handled by a global broadcast in WarfareService for simplicity,
    # but we can add specific kingdom-wide rewards or penalties here.
    pass

def get_kingdom_status(game, kingdom):
    """Calculates the current health of a kingdom (Capital + Controlled Shrines)."""
    from logic.core.systems.influence_service import InfluenceService
    service = InfluenceService.get_instance()
    
    shrines = [s for s in service.shrines.values() if s.kingdom == kingdom]
    total_potency = sum(s.potency for s in shrines)
    capitals = [s for s in shrines if s.is_capital]
    
    return {
        "shrine_count": len(shrines),
        "total_power": total_potency,
        "is_capital_secure": len(capitals) > 0,
        "active_shrines": [s.name for s in shrines]
    }
