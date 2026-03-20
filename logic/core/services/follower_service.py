# logic/core/services/follower_service.py
import logging
from logic.core import factory

logger = logging.getLogger("GodlessMUD")

def spawn_follower(player, prototype_id, entity_type="monster"):
    """
    [V6.5] Universal service for spawning and binding minions to players.
    Supports 'monster' (active pets/summons) and 'structure' (stationary turrets/barricades).
    """
    if not player or not player.room:
        return None
        
    game = getattr(player, 'game', None)
    world = getattr(game, 'world', None) if game else None
    room = player.room
    
    if not world:
        logger.error(f"FollowerService: Could not resolve world for player {player.name}")
        return None
        
    # 1. Instantiate via Factory
    if entity_type == "structure":
        follower = factory.get_structure(prototype_id, world)
    else:
        follower = factory.get_monster(prototype_id, world)
        
    if not follower:
        logger.error(f"FollowerService: Factory failed to produce {prototype_id} ({entity_type})")
        return None
        
    # 2. Ownership & Branding
    follower.owner_id = player.id
    follower.leader = player
    follower.room = room
    follower.game = game
    
    # [V6.5] Inheritance: Minor mobs inherit some power from owner level/stats
    # (Future Scaling logic can go here)
    
    # 3. Placement
    # All active combat entities live in room.monsters for targeting compatibility
    room.monsters.append(follower)
    
    # 4. Trigger Initialization (if minion has class logic)
    if hasattr(follower, 'refresh_class'):
        follower.refresh_class()
        
    logger.info(f"[FOLLOWER] {follower.name} ({entity_type}) deployed by {player.name} in {room.id}")
    return follower

def bind_follower(player, follower):
    """
    [V6.5] Binds an existing world entity to a player as a follower.
    Handles faction reset and leadership alignment.
    """
    if not player or not follower:
        return None
        
    follower.owner_id = player.id
    follower.leader = player
    follower.game = getattr(player, 'game', None)
    
    # Reset combat state: Don't attack your new master!
    from logic.core import combat
    combat.stop_combat(follower)
    
    # If the mob was aggressive to players, ensure it doesn't immediately re-aggro
    if "aggressive" in getattr(follower, 'tags', []):
        follower.attackers = [a for a in follower.attackers if a != player]
        
    logger.info(f"[BOND] {follower.name} bonded to {player.name}.")
    return follower

def cleanup_follower(follower):
    """Handles the safe removal of a follower from the world."""
    if not follower or not follower.room:
        return
        
    if follower in follower.room.monsters:
        follower.room.monsters.remove(follower)
        
    # Notify owner if needed?
    if follower.leader and hasattr(follower.leader, 'send_line'):
        msg = f"Your {follower.name} has been destroyed/dismissed."
        follower.leader.send_line(msg)
