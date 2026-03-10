import logic.handlers.command_manager as command_manager
from utilities.colors import Colors

@command_manager.register("commune", category="interaction")
def commune(player, args):
    """
    Enter a deep communion with the deity of the current shrine.
    """
    room = player.room
    deity_id = getattr(room, 'deity_id', None)
    
    # If no shrine is present, check for Deity Avatars (Mobs)
    if not deity_id:
        # Build list of valid deity IDs
        valid_deity_ids = set()
        if isinstance(player.game.world.deities, dict):
            valid_deity_ids = set(player.game.world.deities.keys())
        else:
            valid_deity_ids = {d['id'] for d in player.game.world.deities}
            
        for mob in room.monsters:
            for tag in mob.tags:
                if tag in valid_deity_ids:
                    deity_id = tag
                    break
            if deity_id: break

    if not deity_id:
        player.send_line("There is no presence to commune with here.")
        return

    # Find deity name
    deity_name = deity_id.title()
    if isinstance(player.game.world.deities, dict):
        d_data = player.game.world.deities.get(deity_id)
        if d_data:
            if isinstance(d_data, dict):
                deity_name = d_data.get('name', deity_name)
            else:
                deity_name = getattr(d_data, 'name', deity_name)
    else:
        for d in player.game.world.deities:
            if isinstance(d, dict) and d.get('id') == deity_id:
                deity_name = d['name']
                break

    # Enter Interaction State
    player.state = "interaction"
    player.interaction_data = {
        "type": "commune",
        "deity_id": deity_id,
        "deity_name": deity_name
    }
    
    player.send_line(f"\nYou enter a trance, communing with {Colors.YELLOW}{deity_name}{Colors.RESET}.")
    player.send_line(f"Your Favor: {Colors.CYAN}{player.favor.get(deity_id, 0)}{Colors.RESET}")
    player.send_line(f"{Colors.BOLD}Commands:{Colors.RESET} list, buy <id>, memorize <id>, forget <id>, deck, exit")
