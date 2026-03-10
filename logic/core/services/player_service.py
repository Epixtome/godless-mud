"""
logic/core/services/player_service.py
Service layer for managing Player lifecycle (Join, Disconnect, Save).
"""
import logging

logger = logging.getLogger("GodlessMUD")

def handle_disconnect(game, player):
    """
    Safely removes a player from the world and saves their state.
    Breaking the network_engine -> room/combat dependency.
    """
    if not player:
        return

    logger.info(f"Player Service: Handling disconnect for {player.name}")
    
    # 1. Persistence
    player.save()
    
    # 2. Spatial Cleanup
    if player.room:
        if player in player.room.players:
            player.room.players.remove(player)
        
        # Room Cleanup broadcast
        player.room.broadcast(f"{player.name} has vanished.", exclude_player=player)

    # 3. Combat Cleanup (Anemic Delegation)
    # Ensure mobs attacking this player stop or reset
    if player.room:
        for mob in player.room.monsters:
            if mob.fighting == player:
                mob.fighting = None
            if player in getattr(mob, 'attackers', []):
                mob.attackers.remove(player)

    # 4. Game Registry Cleanup
    if player.name in game.players:
        del game.players[player.name]
