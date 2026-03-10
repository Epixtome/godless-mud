"""
logic/commands/movement/utility_movement.py
Non-directional movement: Recall, Portals, and Instant transport.
"""
from logic.handlers import command_manager
from logic.common import find_by_index
from utilities.colors import Colors

def _move_player_instant(player, target_room, method="teleport"):
    """Helper for instant movement (teleport/portal)."""
    from logic.commands.info.exploration import look
    if player.room:
        if player in player.room.players:
            player.room.players.remove(player)
        player.room.broadcast(f"{player.name} vanishes via {method}.", exclude_player=player)
        
    player.room = target_room
    target_room.players.append(player)
    target_room.broadcast(f"{player.name} arrives via {method}.", exclude_player=player)
    look(player, "")

@command_manager.register("recall", category="movement")
def recall(player, args):
    """Teleport to the starting room."""
    if player.is_in_combat():
        player.send_line("You cannot recall while fighting!")
        return
    
    kingdom = player.identity_tags[0] if player.identity_tags else "neutral"
    target_id = getattr(player.game.world, 'landmarks', {}).get(f"{kingdom}_cap")
    
    target_room = None
    if target_id and target_id in player.game.world.rooms:
        target_room = player.game.world.rooms[target_id]
    
    if not target_room:
        from logic.engines import spatial_engine
        target_room = spatial_engine.get_instance(player.game.world).get_room(0, 0, 0)

    if not target_room:
        target_room = player.game.world.start_room or list(player.game.world.rooms.values())[0]

    if not target_room:
        player.send_line("You have nowhere to recall to.")
        return
        
    player.send_line(f"{Colors.CYAN}You focus your mind on your home...{Colors.RESET}")
    _move_player_instant(player, target_room, "recall")

@command_manager.register("enter", category="movement")
def enter_portal(player, args):
    """Enter a portal or nexus."""
    if not args:
        player.send_line("Enter what?")
        return
        
    target = find_by_index(player.room.items, args)
    if not target:
        player.send_line("You don't see that here.")
        return
        
    if "portal" not in getattr(target, 'flags', []):
        player.send_line("You cannot enter that.")
        return
        
    if "nexus" in target.flags:
        p_kingdom = player.identity_tags[0] if player.identity_tags else "neutral"
        portal_kingdom = target.metadata.get("kingdom", "neutral")
        if p_kingdom != portal_kingdom:
            player.send_line(f"The Nexus rejects you! It is bound to the {portal_kingdom.title()} Kingdom.")
            return
            
    dest_id = target.metadata.get("destination")
    if not dest_id:
        player.send_line("The portal leads nowhere.")
        return
        
    target_room = player.game.world.rooms.get(dest_id)
    if not target_room:
        player.send_line("The destination has crumbled into the void.")
        return
        
    player.send_line(f"You step into the {target.name}...")
    _move_player_instant(player, target_room, "portal")
