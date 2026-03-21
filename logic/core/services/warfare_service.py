"""
logic/core/services/warfare_service.py
Manages capture rituals (Drain Crystal) and kingdom warfare alerts.
"""
import logging
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

_ACTIVE_RITUALS = {} # shrine_id -> {kingdom, timer, player_id}

def start_ritual(player, shrine):
    """Initiates a Drain Crystal ritual at a shrine."""
    from logic.core.systems.influence_service import InfluenceService
    service = InfluenceService.get_instance()
    rating = service.get_security_rating(shrine.coords[0], shrine.coords[1], shrine.coords[2])

    # 1. Validation & Security Retaliation
    if rating >= 1.0 or shrine.is_capital:
        from logic import mob_manager
        mob_manager.spawn_mob(player.room, "capital_guardian", player.game)
        player.send_line(f"{Colors.BOLD}{Colors.RED}The Capital of {shrine.kingdom.title()} is under absolute protection. Lethal guardians arrive!{Colors.RESET}")
        return False
        
    if rating >= 0.5:
        from logic import mob_manager
        mob_manager.spawn_mob(player.room, "sovereignty_sentinel", player.game)
        mob_manager.spawn_mob(player.room, "sovereignty_sentinel", player.game)
        player.send_line(f"{Colors.BOLD}{Colors.YELLOW}Sovereignty Sentinels phase into reality to defend the Outpost!{Colors.RESET}")
        
    if shrine.id in _ACTIVE_RITUALS:
        player.send_line("A ritual is already in progress at this shrine.")
        return False
        
    if shrine.kingdom == player.kingdom:
        player.send_line("You cannot drain your own kingdom's shrine!")
        return False
        
    # 2. Start Ritual (10 Minutes = 300 world ticks)
    # Testing: 20 ticks (40 seconds) for demonstration? No, let's stick to 300 for realism.
    # Actually, let's use a constant for the duration.
    RITUAL_DURATION = 300 
    
    _ACTIVE_RITUALS[shrine.id] = {
        "kingdom": player.kingdom,
        "timer": RITUAL_DURATION,
        "player_id": player.name,
        "shrine_id": shrine.id
    }
    
    # 3. Alerts
    player.send_line(f"{Colors.BOLD}{Colors.MAGENTA}You begin draining the lifeblood of {shrine.name}...{Colors.RESET}")
    player.send_line(f"The ground shudders. The {shrine.kingdom.title()} Kingdom has been alerted!")
    
    # Broadcast to all players in the kingdom being attacked
    from logic.core import event_engine
    event_engine.dispatch("kingdom_alert", {
        "kingdom": shrine.kingdom,
        "message": f"{Colors.BOLD}{Colors.RED}[WARFARE]{Colors.RESET} {shrine.name} at ({shrine.coords[0]}, {shrine.coords[1]}) is being DRAINED by the {player.kingdom.upper()}!",
        "shrine": shrine
    })
    
    return True

def pulse(game):
    """Heartbeat task to process active rituals."""
    completed = []
    for s_id, ritual in _ACTIVE_RITUALS.items():
        ritual['timer'] -= 1
        
        # Periodic Alerts (Every minute / 30 ticks)
        if ritual['timer'] % 30 == 0 and ritual['timer'] > 0:
            shrine = game.world.shrines.get(s_id)
            if shrine:
                from logic.core import event_engine
                event_engine.dispatch("kingdom_alert", {
                    "kingdom": shrine.kingdom,
                    "message": f"{Colors.BOLD}{Colors.RED}[WARFARE]{Colors.RESET} {shrine.name} drainage at {ritual['timer']//3}s remaining!",
                    "shrine": shrine
                })

        if ritual['timer'] <= 0:
            completed.append(s_id)
            
    for s_id in completed:
        _finish_ritual(game, s_id)

def _finish_ritual(game, shrine_id):
    ritual = _ACTIVE_RITUALS.pop(shrine_id)
    shrine = game.world.shrines.get(shrine_id)
    if not shrine: return
    
    old_kingdom = shrine.kingdom
    new_kingdom = ritual['kingdom']
    
    # 1. Flip Sovereignty
    shrine.kingdom = new_kingdom
    # Potency resets to a base value upon capture
    shrine.potency = 500 
    
    # 2. Global Broadcast
    from logic.core.utils import messaging
    messaging.broadcast_global(game, f"\n{Colors.BOLD}{Colors.YELLOW}[WORLD EVENT]{Colors.RESET} {shrine.name} has fallen to the {new_kingdom.upper()}!")
    
    # 3. Clear Influence Cache
    from logic.core.systems.influence_service import InfluenceService
    InfluenceService.get_instance().clear_cache()
    
    # 4. Trigger Guardian Logic (Phase 3)
    from logic.core import event_engine
    event_engine.dispatch("shrine_captured", shrine=shrine, old_kingdom=old_kingdom, new_kingdom=new_kingdom)

def cancel_ritual(shrine_id, reason="The ritual has been interrupted."):
    if shrine_id in _ACTIVE_RITUALS:
        ritual = _ACTIVE_RITUALS.pop(shrine_id)
        # Alert the attacker?
        return True
    return False

def init_warfare(game):
    """Registers the warfare pulse with the game engine."""
    if hasattr(game, 'subscribers'):
        game.subscribers.append(pulse)
        logger.info("WarfareService pulse registered.")
